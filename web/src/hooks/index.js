import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { subscribe, getSnapshot } from '../data/sessionStore';

/**
 * Subscribe to one slice of the session store. Selectors must return a
 * primitive or an object reference already held in the store.
 */
export function useSession(selector) {
  return useSyncExternalStore(subscribe, () => selector(getSnapshot()));
}

const RM_QUERY = '(prefers-reduced-motion: reduce)';

export function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia?.(RM_QUERY).matches,
  );
  useEffect(() => {
    const mq = window.matchMedia?.(RM_QUERY);
    if (!mq) return undefined;
    const on = () => setReduced(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return reduced;
}

/** Adds `.is-in` once an element scrolls into view (CSS handles the motion). */
export function useReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || !('IntersectionObserver' in window)) {
      el?.classList.add('is-in');
      return undefined;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('is-in');
          io.disconnect();
        }
      },
      { rootMargin: '0px 0px -10% 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return ref;
}

/** Which of the given section ids is currently in the reading band. */
export function useActiveSection(ids) {
  const [active, setActive] = useState(ids[0]);
  const key = ids.join('|');
  useEffect(() => {
    if (!('IntersectionObserver' in window)) return undefined;
    const els = key.split('|').map((id) => document.getElementById(id)).filter(Boolean);
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) setActive(e.target.id); });
      },
      { rootMargin: '-40% 0px -55% 0px' },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [key]);
  return active;
}
