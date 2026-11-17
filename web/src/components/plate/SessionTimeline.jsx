import { useEffect, useRef, useState } from 'react';
import * as m from 'motion/react-m';
import { AnimatePresence } from '../../motion/api';
import { useSession } from '../../hooks';
import { togglePlay, seek } from '../../data/sessionStore';
import { formatTime } from '../../data/session';
import { SPRING, MEMBRANE_EASE } from '../../motion/tokens';
import styles from './SessionTimeline.module.css';

const NO_EVENTS = [];
const PULSE_MS = 1100;

/**
 * Collection pulses: one per *increase* of the counter (scrubbing backwards
 * never pulses). Kept in state because they are rare, discrete events.
 */
function useCollectionPulses(collected) {
  const prev = useRef(null);
  const timers = useRef(new Set());
  const [pulses, setPulses] = useState([]);

  useEffect(() => {
    const before = prev.current;
    prev.current = collected;
    if (before === null || collected <= before) return;
    const id = `${collected}-${Date.now()}`;
    setPulses((p) => [...p.slice(-3), { id, count: collected }]);
    // Each pulse removes itself; a quick second collection must not cancel the first.
    const timer = setTimeout(() => {
      timers.current.delete(timer);
      setPulses((p) => p.filter((x) => x.id !== id));
    }, PULSE_MS);
    timers.current.add(timer);
  }, [collected]);

  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach(clearTimeout);
  }, []);

  return pulses;
}

/**
 * Transport for the recorded session: play/pause, an accessible scrubber,
 * and collection events from session.json marked on the track itself.
 */
export default function SessionTimeline() {
  const t = useSession((s) => s.t);
  const duration = useSession((s) => s.duration);
  const playing = useSession((s) => s.playing);
  const mode = useSession((s) => s.mode);
  const events = useSession((s) => s.session?.events ?? NO_EVENTS);
  const total = useSession((s) => s.session?.total ?? 0);
  const collected = useSession((s) => s.frame.collected);
  const pulses = useCollectionPulses(mode === 'replay' || mode === 'live' ? collected : 0);

  const dur = duration || 1;
  const pct = Math.min(100, (t / dur) * 100);
  const replay = mode === 'replay';
  const latest = pulses[pulses.length - 1];

  return (
    <div className={styles.timeline} data-mode={mode}>
      <m.button
        type="button"
        className={styles.play}
        onClick={togglePlay}
        aria-label={playing ? 'Pause' : 'Play'}
        aria-pressed={playing}
        whileTap={{ scale: 0.92 }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <m.svg
            key={playing ? 'pause' : 'play'}
            viewBox="0 0 16 16"
            aria-hidden="true"
            initial={{ opacity: 0, rotate: -90, scale: 0.6 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 90, scale: 0.6 }}
            transition={{ duration: 0.16 }}
          >
            {playing
              ? <><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></>
              : <path d="M4 2l10 6-10 6z" />}
          </m.svg>
        </AnimatePresence>
      </m.button>

      <div className={styles.track} style={{ '--pf': pct / 100 }}>
        <input
          className={styles.range}
          type="range"
          min={0}
          max={dur}
          step={0.1}
          value={Math.min(t, dur)}
          onChange={(e) => seek(Number(e.target.value))}
          aria-label="Session position"
          aria-valuetext={`${formatTime(t)} of ${formatTime(dur)}${replay ? `, ${collected} of ${total} items collected` : ''}`}
        />
        {replay && events.length > 0 && (
          <ol className={styles.ticks} aria-label="Collection events">
            {events.map((ev) => (
              <li key={ev.count} style={{ left: `${(ev.t / dur) * 100}%` }}>
                <button
                  type="button"
                  tabIndex={-1}
                  className={styles.tick}
                  data-past={ev.t <= t || undefined}
                  onClick={() => seek(Math.max(0, ev.t - 1.5))}
                  title={`Item ${ev.count} · ${formatTime(ev.t)}`}
                >
                  <span className="sr-only">Jump to item {ev.count}, collected at {formatTime(ev.t)}</span>
                </button>
              </li>
            ))}
          </ol>
        )}
        {/* A ring expands from the tick of the item just collected. */}
        {replay && pulses.map((p) => {
          const ev = events.find((e) => e.count === p.count) ?? events[events.length - 1];
          if (!ev) return null;
          return (
            <m.span
              key={p.id}
              className={styles.pulse}
              style={{ left: `${(ev.t / dur) * 100}%` }}
              aria-hidden="true"
              initial={{ scale: 0.4, opacity: 0.9 }}
              animate={{ scale: 2.6, opacity: 0 }}
              transition={{ duration: 0.9, ease: MEMBRANE_EASE }}
            />
          );
        })}
      </div>

      <p className={styles.readout}>
        <span className={`mono ${styles.time}`}>
          {formatTime(t)}<span className={styles.sep}>/</span>{formatTime(dur)}
        </span>
        {(mode === 'live' || replay) && (
          <span className={styles.label}>
            <span className={styles.plusSlot} aria-hidden="true">
              <AnimatePresence>
                {latest && (
                  <m.span
                    key={latest.id}
                    className={styles.plus}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0, transition: SPRING.spike }}
                    exit={{ opacity: 0, y: -10, transition: { duration: 0.3 } }}
                  >
                    +1
                  </m.span>
                )}
              </AnimatePresence>
            </span>
            <b className={`mono ${styles.countNum}`}>{collected}</b>
            {replay
              ? <><span className="mono"> of {total}</span> items</>
              : <> collected · footage is not live</>}
          </span>
        )}
      </p>
    </div>
  );
}
