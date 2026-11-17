import * as m from 'motion/react-m';
import { useScroll, useSpring, useReducedMotion } from './api';
import { SPRING } from './tokens';
import styles from './motion.module.css';

/**
 * Sticky act numeral inside a ring that closes as the act is read —
 * the katamari growing with what it has gathered. Purely decorative
 * (the act heading carries the label), so it is hidden from AT.
 * `targetRef` is the act <section>.
 */
export default function ActRing({ targetRef, numeral, kicker }) {
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ['start 55%', 'end 55%'],
  });
  const smooth = useSpring(scrollYProgress, SPRING.scroll);
  const progress = reduced ? scrollYProgress : smooth;

  return (
    <div className={styles.ringRail} aria-hidden="true">
      <div className={styles.ringSticky}>
        <svg className={styles.ring} viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="29" className={styles.ringTrack} />
          <m.circle
            cx="32"
            cy="32"
            r="29"
            className={styles.ringFill}
            style={{ pathLength: progress }}
            transform="rotate(-90 32 32)"
          />
        </svg>
        <span className={styles.ringNumeral}>{numeral}</span>
        <span className={styles.ringKicker}>{kicker}</span>
      </div>
    </div>
  );
}

/** Hairline at the top of an act that draws across as the act arrives. */
export function Boundary({ targetRef }) {
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: targetRef, offset: ['start end', 'start 55%'] });
  return (
    <m.span
      className={styles.boundary}
      style={{ scaleX: reduced ? 1 : scrollYProgress }}
      aria-hidden="true"
    />
  );
}

