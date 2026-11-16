/**
 * Session store — one source of neural state for the whole page.
 *
 * Priority: live WebSocket (main.py) → recorded session.json replay → synthetic.
 * The replay clock is the gameplay <video>, so data and footage stay in sync,
 * including when scrubbing. With no usable video, an internal clock takes over.
 *
 * React reads it through useSyncExternalStore; WebGL loops read `getSnapshot()`
 * directly each frame, so neural ticks never re-render the page.
 */
import {
  EMPTY_FRAME, normalizeFrame, frameIndexAt, prepareSession,
  resolveMode, syntheticFrame,
} from './session';

const WS_URL = 'ws://localhost:8765';
const SESSION_URL = `${process.env.PUBLIC_URL || ''}/session.json`;

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

let snapshot = {
  mode: 'loading',
  connected: false,
  replayStatus: 'loading',   // loading | ready | error
  frame: EMPTY_FRAME,
  t: 0,
  duration: 0,
  playing: false,
  session: null,             // { frames, events, duration, total, escapes }
  videoStatus: 'none',       // none | ready | error
};

const listeners = new Set();
function set(patch) {
  snapshot = { ...snapshot, ...patch };
  snapshot.mode = resolveMode(snapshot);
  listeners.forEach((l) => l());
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
export const getSnapshot = () => snapshot;

/* ── Clock ─────────────────────────────────────────────────── */

let video = null;
let internalT = 0;
let lastTick = 0;
let frameIdx = -1;
let lastEmitT = -1;

const videoUsable = () => video && snapshot.videoStatus === 'ready';

function clockDuration() {
  if (videoUsable() && Number.isFinite(video.duration) && video.duration > 0) return video.duration;
  return snapshot.session?.duration || 0;
}

function readClock(now) {
  if (videoUsable()) return video.currentTime;
  const dt = lastTick ? (now - lastTick) / 1000 : 0;
  const dur = snapshot.session?.duration || 60;
  if (snapshot.playing) internalT = (internalT + dt) % dur;
  return internalT;
}

let rafId = 0;
let synthT = 0;
let lastSynth = 0;

function tick(now) {
  rafId = requestAnimationFrame(tick);
  const t = readClock(now);
  lastTick = now;

  const patch = {};
  if (Math.abs(t - lastEmitT) >= 1 / 30 || t < lastEmitT) {
    patch.t = t;
    lastEmitT = t;
  }

  if (!snapshot.connected) {
    if (snapshot.replayStatus === 'ready') {
      const idx = frameIndexAt(snapshot.session.frames, t);
      if (idx !== frameIdx) {
        frameIdx = idx;
        patch.frame = snapshot.session.frames[idx];
      }
    } else if (snapshot.replayStatus === 'error' && now - lastSynth > 50) {
      lastSynth = now;
      synthT += 0.05;
      patch.frame = syntheticFrame(synthT);
    }
  }

  if (Object.keys(patch).length) set(patch);
}

/* ── Video binding ─────────────────────────────────────────── */

export function attachVideo(el) {
  if (!el || el === video) return () => {};
  video = el;

  const onMeta = () => {
    snapshot = { ...snapshot, videoStatus: 'ready' };
    set({ duration: clockDuration(), playing: !el.paused });
  };
  const onError = () => {
    internalT = video?.currentTime || 0;
    set({ videoStatus: 'error', duration: snapshot.session?.duration || 0 });
  };
  const onPlay = () => set({ playing: true });
  const onPause = () => set({ playing: false });

  el.addEventListener('loadedmetadata', onMeta);
  el.addEventListener('error', onError, true);
  el.addEventListener('play', onPlay);
  el.addEventListener('pause', onPause);
  if (el.readyState >= 1) onMeta();
  if (el.error) onError();

  return () => {
    el.removeEventListener('loadedmetadata', onMeta);
    el.removeEventListener('error', onError, true);
    el.removeEventListener('play', onPlay);
    el.removeEventListener('pause', onPause);
    if (video === el) video = null;
  };
}

export function play() {
  if (videoUsable()) video.play().catch(() => set({ playing: false }));
  else set({ playing: true });
}
export function pause() {
  if (videoUsable()) video.pause();
  else set({ playing: false });
}
export function togglePlay() {
  snapshot.playing ? pause() : play();
}
export function seek(t) {
  const dur = clockDuration();
  const clamped = Math.max(0, Math.min(dur || t, t));
  if (videoUsable()) video.currentTime = clamped;
  else internalT = clamped;
  lastEmitT = -1;
  frameIdx = -1;
}

/* ── Live WebSocket (unchanged contract: ws://localhost:8765) ─ */

let ws = null;
let retry = 0;
let retryTimer = 0;
let stopped = false;

function connect() {
  if (stopped) return;
  try {
    ws = new WebSocket(WS_URL);
  } catch {
    scheduleReconnect();
    return;
  }
  ws.onopen = () => { retry = 0; set({ connected: true }); };
  ws.onmessage = (e) => {
    try { set({ frame: normalizeFrame(JSON.parse(e.data)) }); } catch { /* ignore malformed */ }
  };
  ws.onerror = () => ws?.close();
  ws.onclose = () => {
    const was = snapshot.connected;
    frameIdx = -1;   // resync replay frame immediately
    if (was) set({ connected: false });
    scheduleReconnect();
  };
}

function scheduleReconnect() {
  if (stopped) return;
  // 3 s, 6 s, 12 s … capped at 30 s — keeps console noise low when offline.
  const delay = Math.min(30000, 3000 * 2 ** retry);
  retry += 1;
  retryTimer = setTimeout(connect, delay);
}

/* ── Lifecycle ─────────────────────────────────────────────── */

let started = false;

export function start() {
  if (started) return stop;
  started = true;
  stopped = false;

  set({ playing: !prefersReducedMotion() });

  fetch(SESSION_URL)
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((raw) => {
      const session = prepareSession(raw);
      set({ session, replayStatus: 'ready', duration: clockDuration() || session.duration });
    })
    .catch(() => set({ replayStatus: 'error' }));

  connect();
  rafId = requestAnimationFrame(tick);
  return stop;
}

export function stop() {
  started = false;
  stopped = true;
  cancelAnimationFrame(rafId);
  clearTimeout(retryTimer);
  if (ws) { ws.onclose = null; ws.close(); ws = null; }
}
