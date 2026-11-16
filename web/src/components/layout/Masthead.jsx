import { useEffect, useRef } from 'react';
import ProvenanceChip from '../plate/ProvenanceChip';
import { useActiveSection, useReducedMotion } from '../../hooks';
import { REPO_URL } from '../../content/project';
import styles from './Layout.module.css';

const NAV = [
  { id: 'plate', label: 'Plate', n: 'I' },
  { id: 'method', label: 'Method', n: 'II' },
  { id: 'circuits', label: 'Circuits', n: 'III' },
  { id: 'run', label: 'Run it', n: 'IV' },
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

/** The katamari rolls as the reader moves through the page. */
function useRoll(reduced) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) {
      el?.style.setProperty('--roll', '0deg');
      return undefined;
    }
    let raf = 0;
    const update = () => {
      raf = 0;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const p = max > 0 ? window.scrollY / max : 0;
      el.style.setProperty('--roll', `${p * 720}deg`);
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(raf);
    };
  }, [reduced]);
  return ref;
}

export default function Masthead() {
  const active = useActiveSection(IDS);
  const roll = useRoll(useReducedMotion());
  return (
    <header className={styles.masthead}>
      <div className={styles.mastInner}>
        <a className={styles.brand} href="#top" aria-label="Katamari Connectome, back to top">
          <span ref={roll} className={styles.roll}><Mark /></span>
          <span className={styles.wordmark}>Katamari Connectome</span>
        </a>

        <nav className={styles.nav} aria-label="Sections">
          <ol>
            {NAV.map((item) => (
              <li key={item.id}>
                <a href={`#${item.id}`} aria-current={active === item.id ? 'true' : undefined}>
                  {item.label}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className={styles.mastEnd}>
          <ProvenanceChip />
          <a className={styles.gh} href={REPO_URL} target="_blank" rel="noreferrer">
            <svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" /></svg>
            <span className={styles.ghLabel}>Source</span>
            <span className="sr-only"> on GitHub (opens in a new tab)</span>
          </a>
        </div>
      </div>
    </header>
  );
}
