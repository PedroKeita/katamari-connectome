import { useEffect, useState } from 'react';
import * as m from 'motion/react-m';
import { useSpring, useMotionValueEvent, useReducedMotion } from './api';
import { SPRING, MEMBRANE_EASE } from './tokens';
import styles from './chrome.module.css';

/**
 * The masthead's bottom hairline, turned into reading progress.
 * Act markers sit at each act's start; once passed they stick (turn yellow) —
 * the katamari keeps what it rolls over.
 */
export default function ScrollRail({ progress, ids }) {
  const reduced = useReducedMotion();
  const smooth = useSpring(progress, SPRING.scroll);
  const [marks, setMarks] = useState([]);
  const [passed, setPassed] = useState(0);

  useEffect(() => {
    function measure() {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (max <= 0) return;
      const next = ids
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((el) => Math.min(1, Math.max(0, (el.getBoundingClientRect().top + window.scrollY - 80) / max)));
      setMarks(next);
      const p = progress.get();
      setPassed(next.filter((mk) => p >= mk - 0.001).length);
    }
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(document.body);
    return () => ro.disconnect();
  }, [ids, progress]);

  // Re-render only when the count of passed markers changes.
  useMotionValueEvent(progress, 'change', (p) => {
    const n = marks.filter((mk) => p >= mk - 0.001).length;
    if (n !== passed) setPassed(n);
  });

  return (
    <div className={styles.rail} aria-hidden="true">
      <m.span
        className={styles.railTrack}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.9, ease: MEMBRANE_EASE }}
      />
      <m.span className={styles.railFill} style={{ scaleX: reduced ? progress : smooth }} />
      {marks.map((mk, i) => (
        <span
          key={ids[i]}
          className={styles.railMark}
          data-passed={i < passed || undefined}
          style={{ left: `${mk * 100}%` }}
        />
      ))}
    </div>
  );
}
