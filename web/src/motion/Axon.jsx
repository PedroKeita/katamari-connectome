import { createContext, useContext, useEffect, useRef } from 'react';
import * as m from 'motion/react-m';
import {
  useScroll, useSpring, useTransform, useMotionValue, useReducedMotion,
} from './api';
import { SPRING } from './tokens';
import styles from './axon.module.css';

const AxonContext = createContext(null);

// A gently wandering line reads as tissue, not a ruler. x(t) in viewBox units.
const WAVE = (t) => 6 + Math.sin(t * Math.PI * 5) * 2.2 + Math.sin(t * Math.PI * 13) * 0.8;
const PATH = (() => {
  let d = '';
  for (let i = 0; i <= 120; i++) {
    const t = i / 120;
    d += `${i ? 'L' : 'M'}${WAVE(t).toFixed(2)} ${(t * 1000).toFixed(1)} `;
  }
  return d.trim();
})();

/**
 * Propagation: a spike travels down an axon as the reader scrolls through a
 * sequence. Children call useFire(i, n) to learn when the signal reaches them.
 * Scroll-linked and reversible — scrolling back up repolarises the steps.
 */
export default function Axon({ children, className = '', offset = ['start 75%', 'end 55%'] }) {
  const ref = useRef(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset });
  const smooth = useSpring(scrollYProgress, SPRING.scroll);
  const progress = reduced ? scrollYProgress : smooth;

  // Spike position along the measured height.
  const height = useMotionValue(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(() => height.set(el.offsetHeight));
    ro.observe(el);
    return () => ro.disconnect();
  }, [height]);
  const spikeY = useTransform([progress, height], ([p, h]) => p * h);
  const spikeX = useTransform(progress, (p) => WAVE(p) - 6);
  const spikeOpacity = useTransform(progress, [0, 0.02, 0.98, 1], [0, 1, 1, 0]);

  return (
    <AxonContext.Provider value={progress}>
      <div ref={ref} className={`${styles.axon} ${className}`}>
        <svg className={styles.line} viewBox="0 0 12 1000" preserveAspectRatio="none" aria-hidden="true">
          <path d={PATH} className={styles.track} vectorEffect="non-scaling-stroke" />
          <m.path
            d={PATH}
            className={styles.signal}
            vectorEffect="non-scaling-stroke"
            style={{ pathLength: progress }}
          />
        </svg>
        <m.span
          className={styles.spike}
          aria-hidden="true"
          style={{ y: spikeY, x: spikeX, opacity: spikeOpacity }}
        />
        {children}
      </div>
    </AxonContext.Provider>
  );
}

/**
 * 0 → 1 as the spike reaches item i of n. Use with useTransform for
 * opacity/colour so items "fire" in order and un-fire on the way back.
 */
export function useFire(i, n) {
  const progress = useContext(AxonContext);
  const fallback = useMotionValue(1);
  const thr = Math.min(0.98, (i + 0.15) / n);
  const fire = useTransform(progress ?? fallback, [Math.max(0, thr - 0.06), thr], [0, 1]);
  return progress ? fire : fallback;
}

/** Node on the axon beside an item: dim until the spike passes, then lit. */
export function AxonNode({ i, n }) {
  const fire = useFire(i, n);
  const scale = useTransform(fire, [0, 1], [0.55, 1]);
  const opacity = useTransform(fire, [0, 1], [0.45, 1]);
  return (
    <m.span className={styles.node} style={{ scale, opacity }} aria-hidden="true">
      <m.span className={styles.nodeLit} style={{ opacity: fire }} />
    </m.span>
  );
}
