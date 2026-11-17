import { createContext, useContext, useEffect, useState } from 'react';
import { LazyMotion, MotionConfig, domAnimation } from './api';

const EnvContext = createContext({ finePointer: false, compact: false });

const FINE = '(hover: hover) and (pointer: fine)';
const COMPACT = '(max-width: 760px)';

function useMedia(query) {
  const [match, setMatch] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia?.(query).matches,
  );
  useEffect(() => {
    const mq = window.matchMedia?.(query);
    if (!mq) return undefined;
    const on = () => setMatch(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return match;
}

/**
 * Root of the motion system.
 * - LazyMotion + domAnimation keeps the initial bundle small; `strict` forbids
 *   accidental full `motion.*` components (use `m.*` from motion/react-m).
 * - reducedMotion="user" makes Motion skip transform animations for users who
 *   ask for less motion; primitives additionally pin scroll-linked values.
 */
export default function MotionProvider({ children }) {
  const finePointer = useMedia(FINE);
  const compact = useMedia(COMPACT);
  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <EnvContext.Provider value={{ finePointer, compact }}>{children}</EnvContext.Provider>
      </MotionConfig>
    </LazyMotion>
  );
}

/** { finePointer, compact } — input and size class for scaling motion. */
export const useMotionEnv = () => useContext(EnvContext);
