import { useRef } from 'react';
import * as m from 'motion/react-m';
import Threshold from '../../motion/Threshold';
import ActRing, { Boundary } from '../../motion/ActRing';
import { MEMBRANE_EASE, DURATION, IN_VIEW } from '../../motion/tokens';
import styles from './Act.module.css';

/**
 * Section frame shared by every act. The boundary hairline draws as the act
 * arrives, the heading crosses the membrane, and (on wide screens) a sticky
 * ring in the gutter closes as the act is read.
 */
export default function Act({ id, numeral, kicker, title, lede, children }) {
  const ref = useRef(null);
  return (
    <section ref={ref} id={id} className={styles.act} aria-labelledby={`${id}-h`}>
      <Boundary targetRef={ref} />
      <ActRing targetRef={ref} numeral={numeral} kicker={kicker} />
      <header className={styles.head}>
        <p className={styles.kicker}>
          <span className={styles.numeral} aria-hidden="true">{numeral}</span>
          <span>{kicker}</span>
        </p>
        <Threshold as="h2" id={`${id}-h`} className={styles.title} text={title} />
        {lede && (
          <m.p
            className={styles.lede}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={IN_VIEW}
            transition={{ duration: DURATION.membrane, ease: MEMBRANE_EASE, delay: 0.25 }}
          >
            {lede}
          </m.p>
        )}
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
      {typeof children === 'string'
        ? <Threshold as="h3" id={id} className={styles.h3} text={children} />
        : <h3 id={id} className={styles.h3}>{children}</h3>}
    </div>
  );
}

export { styles as actStyles };
