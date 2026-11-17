import * as m from 'motion/react-m';
import { MEMBRANE_EASE, SPRING } from '../../motion/tokens';
import styles from './Figure.module.css';

/**
 * A lettered figure panel, in the manner of a journal plate.
 * `letter` + `title` head the panel; `meta` sits right-aligned (interaction hint,
 * source); `caption` is a single plain-language sentence beneath.
 *
 * Motion:
 * - `enter` (seconds): entrance delay. The head rule draws, the letter fires,
 *   and a veil (Shutter) lifts off the body — the instrument is already running
 *   underneath, so it is revealed, not switched on. Omit for a static figure.
 * - `style` / `animate`: passed to the outer motion element (depth, mobile switch).
 */
export default function Figure({
  letter, title, meta, caption, className = '', bodyClassName = '', children, id, hidden,
  enter, style, animate, transition,
}) {
  const entering = typeof enter === 'number';
  return (
    <m.figure
      className={`${styles.figure} ${className}`}
      id={id}
      hidden={hidden}
      aria-labelledby={id ? `${id}-title` : undefined}
      style={style}
      animate={animate}
      transition={transition}
    >
      <header className={styles.head}>
        <m.span
          className={styles.rule}
          aria-hidden="true"
          initial={entering ? { scaleX: 0 } : false}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.8, ease: MEMBRANE_EASE, delay: enter ?? 0 }}
        />
        <m.span
          className={styles.letter}
          aria-hidden="true"
          initial={entering ? { opacity: 0, y: 10, scale: 0.6 } : false}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ ...SPRING.spike, delay: (enter ?? 0) + 0.12 }}
        >
          {letter}
        </m.span>
        <span className={styles.title} id={id ? `${id}-title` : undefined}>
          <span className="sr-only">Figure {letter}: </span>{title}
        </span>
        {meta && <span className={styles.meta}>{meta}</span>}
      </header>
      <div className={`${styles.body} ${bodyClassName}`}>
        {children}
        {entering && (
          <m.span
            className={styles.shutter}
            aria-hidden="true"
            initial={{ scaleY: 1 }}
            animate={{ scaleY: 0 }}
            transition={{ duration: 0.9, ease: MEMBRANE_EASE, delay: enter + 0.1 }}
          />
        )}
      </div>
      {caption && (
        <m.figcaption
          className={styles.caption}
          initial={entering ? { opacity: 0 } : false}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: (enter ?? 0) + 0.5 }}
        >
          {caption}
        </m.figcaption>
      )}
    </m.figure>
  );
}
