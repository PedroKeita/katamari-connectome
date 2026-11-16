/**
 * Pure helpers for neural-state frames. No React, no DOM — unit-tested.
 * A frame follows the WebSocket schema emitted by brain/runtime/neural_server.py.
 */

export const EMPTY_FRAME = Object.freeze({
  fw_bias: 0, left: 0, center: 0, right: 0, mag: 0,
  collected: 0, pressed_keys: [],
  escape_active: false,
  circuits: { reward: { rate: 0 }, escape: { rate: 0 }, orient: { rate: 0 } },
});

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);

/** Coerce any incoming payload into a complete, safe frame. */
export function normalizeFrame(raw) {
  if (!raw || typeof raw !== 'object') return EMPTY_FRAME;
  const c = raw.circuits || {};
  return {
    fw_bias: num(raw.fw_bias),
    left: num(raw.left),
    center: num(raw.center),
    right: num(raw.right),
    mag: num(raw.mag),
    collected: num(raw.collected),
    pressed_keys: Array.isArray(raw.pressed_keys) ? raw.pressed_keys : [],
    escape_active: Boolean(raw.escape_active),
    circuits: {
      reward: { rate: num(c.reward?.rate) },
      escape: { rate: num(c.escape?.rate) },
      orient: { rate: num(c.orient?.rate) },
    },
    ...(typeof raw._t === 'number' ? { _t: raw._t } : {}),
  };
}

/**
 * Index of the last frame whose `_t` is <= t (binary search).
 * Before the first timestamp, returns 0. Frames must be sorted by `_t`.
 */
export function frameIndexAt(frames, t) {
  if (!frames || frames.length === 0) return -1;
  if (t <= frames[0]._t) return 0;
  let lo = 0;
  let hi = frames.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (frames[mid]._t <= t) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

/** Times at which the `collected` counter increases. */
export function collectionEvents(frames) {
  const events = [];
  let prev = 0;
  for (const f of frames) {
    if (f.collected > prev) events.push({ t: f._t, count: f.collected });
    prev = Math.max(prev, f.collected);
  }
  return events;
}

/**
 * Most collections inside any window of `seconds` — the README's
 * "best burst" metric, so the recording is measured the same way.
 */
export function bestWindow(events, seconds) {
  let best = { count: 0, start: 0 };
  let j = 0;
  for (let i = 0; i < events.length; i++) {
    if (j < i) j = i;
    while (j < events.length && events[j].t - events[i].t <= seconds) j++;
    if (j - i > best.count) best = { count: j - i, start: events[i].t };
  }
  return best;
}

/** Prepare a recorded session: normalise, sort, derive summary stats. */
export function prepareSession(raw) {
  if (!Array.isArray(raw)) throw new Error('session.json must be an array of frames');
  const frames = raw
    .filter((f) => f && typeof f._t === 'number')
    .map(normalizeFrame)
    .sort((a, b) => a._t - b._t);
  if (frames.length === 0) throw new Error('session.json has no timestamped frames');
  const events = collectionEvents(frames);
  return {
    frames,
    events,
    duration: frames[frames.length - 1]._t,
    total: events.length ? events[events.length - 1].count : 0,
    escapes: frames.filter((f) => f.escape_active).length,
  };
}

/**
 * Data provenance, in priority order. The page must always say which it shows.
 *   live      — WebSocket from a running main.py
 *   replay    — the recorded session.json, synced to the gameplay video
 *   synthetic — generated motion; only when the recording failed to load
 *   loading   — nothing yet
 */
export function resolveMode({ connected, replayStatus }) {
  if (connected) return 'live';
  if (replayStatus === 'ready') return 'replay';
  if (replayStatus === 'error') return 'synthetic';
  return 'loading';
}

const KEY_SETS = [
  ['w', 'a', 'j', 'i'], ['w', 'd', 'l', 'i'], ['w', 'i'], ['a', 'j'],
  ['w', 'a', 'j', 'i'], ['w', 'd', 'l', 'i'], ['s', 'k'], ['w', 'a', 'j', 'i'],
];

/** Fallback generator (kept from the original visualizer). Clearly labelled SIMULATED in the UI. */
export function syntheticFrame(t) {
  const bias = Math.sin(t * 0.4) * 0.7;
  const left = Math.max(0, 0.5 + Math.sin(t * 1.1) * 0.4);
  const center = Math.max(0, 0.6 + Math.sin(t * 0.7) * 0.3);
  const right = Math.max(0, 0.5 - Math.sin(t * 1.1) * 0.4);
  const escape = t % 20 > 17;
  return {
    fw_bias: bias, left, center, right,
    mag: center * 0.6 + Math.max(left, right) * 0.4,
    collected: 0,
    pressed_keys: escape
      ? ['w', 'd', 'l', 'i', 'shift', 'ctrl']
      : KEY_SETS[Math.floor(t / 1.5) % KEY_SETS.length],
    escape_active: escape,
    circuits: {
      reward: { rate: Math.abs(bias) * 0.05 },
      escape: { rate: escape ? 0.8 : 0 },
      orient: { rate: Math.abs(bias) * 0.02 },
    },
  };
}

export function formatTime(s) {
  const v = Math.max(0, Math.floor(num(s)));
  return `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}`;
}

export const signed = (v, digits = 2) => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(digits);
