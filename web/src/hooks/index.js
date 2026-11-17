import { useEffect, useState, useSyncExternalStore } from 'react';
import { subscribe, getSnapshot } from '../data/sessionStore';

/**
 * Subscribe to one slice of the session store. Selectors must return a
 * primitive or an object reference already held in the store.
 */
export function useSession(selector) {
  return useSyncExternalStore(subscribe, () => selector(getSnapshot()));
}

/** Single source of truth for reduced motion: Motion's own hook. */
export { useReducedMotion } from '../motion/api';

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
