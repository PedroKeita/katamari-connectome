import * as m from 'motion/react-m';
import { AnimatePresence } from '../../motion/api';
import { useSession } from '../../hooks';
import { DURATION, MEMBRANE_EASE } from '../../motion/tokens';
import { formatTime } from '../../data/session';
import styles from './ProvenanceChip.module.css';

const COPY = {
  live: { label: 'Live', detail: 'main.py · ws:8765', title: 'Signals stream live from a running main.py on this machine.' },
  replay: { label: 'Recorded session', detail: null, title: 'Signals replay a real recorded run (session.json) in sync with its gameplay footage.' },
  synthetic: { label: 'Simulated', detail: 'recording unavailable', title: 'The recorded session could not be loaded; panels show generated motion, not brain output.' },
  loading: { label: 'Loading session', detail: null, title: 'Fetching the recorded session…' },
};

/** Always states where the panels' data is coming from. */
export default function ProvenanceChip({ compact = false }) {
  const mode = useSession((s) => s.mode);
  const duration = useSession((s) => s.session?.duration || 0);
  const c = COPY[mode];
  const detail = mode === 'replay' ? `${formatTime(Math.round(duration))} · session.json` : c.detail;

  return (
    <p className={styles.chip} data-mode={mode} title={c.title} aria-live="polite">
      <span className={styles.dot} aria-hidden="true" />
      {/* Mode changes cross-fade: the old label lifts out, the new one rises in. */}
      <AnimatePresence mode="popLayout" initial={false}>
        <m.span
          key={mode}
          className={styles.swap}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: DURATION.quick, ease: MEMBRANE_EASE }}
        >
          <span className={styles.label}>{c.label}</span>
          {!compact && detail && <span className={styles.detail}>{detail}</span>}
        </m.span>
      </AnimatePresence>
      <span className="sr-only">. {c.title}</span>
    </p>
  );
}
