import styles from './Figure.module.css';

/**
 * A lettered figure panel, in the manner of a journal plate.
 * `letter` + `title` head the panel; `meta` sits right-aligned (interaction hint,
 * source); `caption` is a single plain-language sentence beneath.
 */
export default function Figure({
  letter, title, meta, caption, className = '', bodyClassName = '', children, id, hidden,
}) {
  return (
    <figure
      className={`${styles.figure} ${className}`}
      id={id}
      hidden={hidden}
      aria-labelledby={id ? `${id}-title` : undefined}
    >
      <header className={styles.head}>
        <span className={styles.letter} aria-hidden="true">{letter}</span>
        <span className={styles.title} id={id ? `${id}-title` : undefined}>
          <span className="sr-only">Figure {letter}: </span>{title}
        </span>
        {meta && <span className={styles.meta}>{meta}</span>}
      </header>
      <div className={`${styles.body} ${bodyClassName}`}>{children}</div>
      {caption && <figcaption className={styles.caption}>{caption}</figcaption>}
    </figure>
  );
}
