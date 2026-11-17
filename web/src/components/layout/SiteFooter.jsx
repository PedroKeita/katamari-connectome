import { Mark } from './Masthead';
import { REPO_URL } from '../../content/project';
import styles from './Layout.module.css';

export default function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footInner}>
        <div className={styles.footBrand}>
          <Mark />
          <p>
            <span className={styles.wordmark}>Katamari Connectome</span>
            <span>An experiment in connectome-driven behaviour.</span>
          </p>
        </div>
        <ul className={styles.footLinks}>
          <li><a href={REPO_URL} target="_blank" rel="noreferrer">Source code<span className="sr-only"> (opens in a new tab)</span></a></li>
          <li><a href="https://flywire.ai" target="_blank" rel="noreferrer">FlyWire<span className="sr-only"> (opens in a new tab)</span></a></li>
          <li><a href="https://github.com/TuragaLab/flybody" target="_blank" rel="noreferrer">flybody meshes<span className="sr-only"> (opens in a new tab)</span></a></li>
          <li><a href="#top">Back to top ↑</a></li>
        </ul>
        <p className={styles.fine}>
          Connectome data: FlyWire v783. Fly meshes: TuragaLab/flybody.
          Katamari Damacy is a trademark of Bandai Namco; this project is not affiliated with it.
        </p>
      </div>
    </footer>
  );
}
