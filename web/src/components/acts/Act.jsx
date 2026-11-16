import { useReveal } from '../../hooks';
import styles from './Act.module.css';

/**
 * Section frame shared by every act: a numeral and kicker in the left
 * gutter, a display heading and lede on the editorial measure.
 */
export default function Act({ id, numeral, kicker, title, lede, children }) {
  const ref = useReveal();
  return (
    <section id={id} className={styles.act} aria-labelledby={`${id}-h`}>
      <header ref={ref} className={`${styles.head} reveal`}>
        <p className={styles.kicker}>
          <span className={styles.numeral} aria-hidden="true">{numeral}</span>
          <span>{kicker}</span>
        </p>
        <h2 id={`${id}-h`} className={styles.title}>{title}</h2>
        {lede && <p className={styles.lede}>{lede}</p>}
      </header>
      {children}
    </section>
  );
}

/** Sub-section heading with optional marginalia in the gutter. */
export function SubHead({ id, children, note }) {
  return (
    <div className={styles.subhead}>
      {note && <p className={styles.subNote}>{note}</p>}
      <h3 id={id} className={styles.h3}>{children}</h3>
    </div>
  );
}

export { styles as actStyles };
