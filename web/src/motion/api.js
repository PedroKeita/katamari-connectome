/**
 * The single place the app imports Motion's React API from, so the surface we
 * depend on is explicit and easy to audit for bundle size.
 *
 * Bundle note: never access the `motion/react-m` namespace dynamically
 * (e.g. `m[tag]`). Webpack then has to keep every export of that module,
 * Reorder included. Use static members such as `m.div` or the TAGS map in
 * Threshold.jsx.
 */
export {
  LazyMotion,
  MotionConfig,
  domAnimation,
  AnimatePresence,
  useScroll,
  useSpring,
  useTransform,
  useMotionValue,
  useMotionValueEvent,
  useInView,
  useReducedMotion,
} from 'motion/react';
