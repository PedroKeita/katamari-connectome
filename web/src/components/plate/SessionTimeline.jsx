import { useSession } from '../../hooks';
import { togglePlay, seek } from '../../data/sessionStore';
import { formatTime } from '../../data/session';
import styles from './SessionTimeline.module.css';

const NO_EVENTS = [];

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

  const dur = duration || 1;
  const pct = Math.min(100, (t / dur) * 100);
  const replay = mode === 'replay';

  return (
    <div className={styles.timeline} data-mode={mode}>
      <button
        type="button"
        className={styles.play}
        onClick={togglePlay}
        aria-label={playing ? 'Pause' : 'Play'}
        aria-pressed={playing}
      >
        {playing ? (
          <svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" /><rect x="9.5" y="2" width="3.5" height="12" /></svg>
        ) : (
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2l10 6-10 6z" /></svg>
        )}
      </button>

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
      </div>

      <p className={styles.readout}>
        <span className={`mono ${styles.time}`}>
          {formatTime(t)}<span className={styles.sep}>/</span>{formatTime(dur)}
        </span>
        {mode === 'live' ? (
          <span className={styles.label}>
            <b key={collected} className={`mono ${styles.countNum}`}>{collected}</b> collected · footage is not live
          </span>
        ) : replay ? (
          <span className={styles.label}>
            <b key={collected} className={`mono ${styles.countNum}`}>{collected}</b>
            <span className="mono"> of {total}</span> items
          </span>
        ) : null}
      </p>
    </div>
  );
}
