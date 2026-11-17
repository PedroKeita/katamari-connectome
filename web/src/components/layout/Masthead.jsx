import { useLayoutEffect, useRef } from 'react';
import * as m from 'motion/react-m';
import { useScroll, useTransform, useSpring, useReducedMotion } from '../../motion/api';
import ProvenanceChip from '../plate/ProvenanceChip';
import ScrollRail from '../../motion/ScrollRail';
import { useActiveSection } from '../../hooks';
import { SPRING, REFRACTORY, MEMBRANE_EASE } from '../../motion/tokens';
import { REPO_URL } from '../../content/project';
import styles from './Layout.module.css';
import chrome from '../../motion/chrome.module.css';

const NAV = [
  { id: 'plate', label: 'Plate' },
  { id: 'method', label: 'Method' },
  { id: 'circuits', label: 'Circuits' },
  { id: 'run', label: 'Run it' },
];
const IDS = NAV.map((n) => n.id);

export function Mark() {
  // The katamari: a magenta ball gathering three circuit-coloured items.
  return (
    <svg className={styles.mark} viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="10" fill="none" stroke="var(--magenta)" strokeWidth="2.5" />
      <circle cx="16" cy="16" r="3.2" fill="var(--magenta)" />
      <circle cx="27" cy="9" r="2.4" fill="var(--yellow)" />
      <circle cx="5" cy="23" r="2.4" fill="var(--coral)" />
      <circle cx="25" cy="25" r="1.8" fill="var(--lilac)" />
    </svg>
  );
}

/** Underline that glides to the active link (springs on x + scaleX; no layout animation). */
function useNavLine(navRef, active) {
  const x = useSpring(0, SPRING.spike);
  const sx = useSpring(0, SPRING.spike);
  const placed = useRef(false);
  useLayoutEffect(() => {
    function place() {
      const list = navRef.current;
      const link = list?.querySelector(`a[href="#${active}"]`);
      if (!list || !link) return;
      const a = link.getBoundingClientRect();
      const b = list.getBoundingClientRect();
      // First placement jumps; later changes glide on the spike spring.
      const method = placed.current ? 'set' : 'jump';
      x[method](a.left - b.left);
      sx[method](a.width / 100);
      placed.current = true;
    }
    place();
    window.addEventListener('resize', place);
    return () => window.removeEventListener('resize', place);
  }, [active, navRef, x, sx]);
  return { x, scaleX: sx };
}

export default function Masthead() {
  const active = useActiveSection(IDS);
  const reduced = useReducedMotion();
  const navRef = useRef(null);
  const line = useNavLine(navRef, active);

  // One scroll source for the page chrome: rail, and the katamari rolling.
  const { scrollYProgress } = useScroll();
  const roll = useTransform(scrollYProgress, [0, 1], [0, 720]);

  return (
    <header className={styles.masthead}>
      <div className={styles.mastInner}>
        <a className={styles.brand} href="#top" aria-label="Katamari Connectome, back to top">
          {/* Outer span: the ball rolls onto the stage. Inner: it keeps rolling with the page. */}
          <m.span
            className={styles.roll}
            initial={{ x: -40, rotate: -360, opacity: 0 }}
            animate={{ x: 0, rotate: 0, opacity: 1 }}
            transition={{ ...SPRING.settle, opacity: { duration: 0.3 } }}
          >
            <m.span className={styles.roll} style={{ rotate: reduced ? 0 : roll }}>
              <Mark />
            </m.span>
          </m.span>
          <m.span
            className={styles.wordmark}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: MEMBRANE_EASE, delay: 0.15 }}
          >
            Katamari Connectome
          </m.span>
        </a>

        <nav ref={navRef} className={styles.nav} aria-label="Sections">
          <ol>
            {NAV.map((item, i) => (
              <m.li
                key={item.id}
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: MEMBRANE_EASE, delay: 0.25 + i * REFRACTORY }}
              >
                <a href={`#${item.id}`} aria-current={active === item.id ? 'true' : undefined}>
                  {item.label}
                </a>
              </m.li>
            ))}
          </ol>
          <m.span className={chrome.navLine} style={line} aria-hidden="true" />
        </nav>

        <m.div
          className={styles.mastEnd}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <ProvenanceChip />
          <m.a
            className={styles.gh}
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            whileTap={{ scale: 0.96 }}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" /></svg>
            <span className={styles.ghLabel}>Source</span>
            <span className="sr-only"> on GitHub (opens in a new tab)</span>
          </m.a>
        </m.div>
      </div>
      <ScrollRail progress={scrollYProgress} ids={IDS} />
    </header>
  );
}
