import { useEffect } from 'react';
import { useMotionValue, useSpring, useReducedMotion } from './api';
import { useMotionEnv } from './MotionProvider';
import { SPRING } from './tokens';

/**
 * Cursor position as two springy motion values in [-1, 1], relative to the
 * viewport centre. Inert (stays at 0) on touch/coarse pointers and for users
 * who prefer reduced motion. Never re-renders: consumers map it with useTransform.
 */
export default function useCursorDepth() {
  const { finePointer } = useMotionEnv();
  const reduced = useReducedMotion();
  const rawX = useMotionValue(0);
  const rawY = useMotionValue(0);
  const x = useSpring(rawX, SPRING.pointer);
  const y = useSpring(rawY, SPRING.pointer);
  const active = finePointer && !reduced;

  useEffect(() => {
    if (!active) {
      rawX.set(0);
      rawY.set(0);
      return undefined;
    }
    const onMove = (e) => {
      rawX.set((e.clientX / window.innerWidth) * 2 - 1);
      rawY.set((e.clientY / window.innerHeight) * 2 - 1);
    };
    const onLeave = () => { rawX.set(0); rawY.set(0); };
    window.addEventListener('pointermove', onMove, { passive: true });
    document.documentElement.addEventListener('pointerleave', onLeave);
    return () => {
      window.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', onLeave);
    };
  }, [active, rawX, rawY]);

  return { x, y, active };
}
