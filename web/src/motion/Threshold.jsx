import * as m from 'motion/react-m';
import { MEMBRANE_EASE, DURATION, REFRACTORY, SPRING, IN_VIEW } from './tokens';
import styles from './motion.module.css';

/**
 * The signature reveal — "integrate, then fire".
 * Each word rises from behind a membrane (a per-word mask) on the slow
 * membrane ease; a segment marked `fire` lands on the stiff spike spring.
 * Real spaces stay in the DOM, so the heading reads normally to assistive tech.
 *
 * segments: [{ text, em?: boolean, fire?: boolean, className?: string }]
 * trigger:  'inView' (default, once) | 'mount'
 */
// Static members only: dynamic access (m[as]) would force the whole
// motion/react-m namespace into the bundle.
const TAGS = { h1: m.h1, h2: m.h2, h3: m.h3, p: m.p };

const container = (delay) => ({
  hidden: {},
  shown: { transition: { delayChildren: delay, staggerChildren: REFRACTORY } },
});

const word = (fire) => ({
  hidden: { y: '108%', opacity: 0 },
  shown: {
    y: '0%',
    opacity: 1,
    transition: fire
      ? { y: SPRING.spike, opacity: { duration: DURATION.fade } }
      : { duration: DURATION.membrane, ease: MEMBRANE_EASE },
  },
});

export default function Threshold({
  as = 'h2', segments, text, className, id, trigger = 'inView', delay = 0,
}) {
  const Tag = TAGS[as] ?? m.h2;
  const segs = segments ?? [{ text }];
  const triggerProps = trigger === 'mount'
    ? { initial: 'hidden', animate: 'shown' }
    : { initial: 'hidden', whileInView: 'shown', viewport: IN_VIEW };

  const nodes = [];
  segs.forEach((seg, si) => {
    // Split on ordinary whitespace only, so a non-breaking space keeps words together.
    const words = seg.text.split(/([ \t\n]+)/);
    const variants = word(seg.fire);
    const inner = words.map((w, wi) => (
      /^[ \t\n]+$/.test(w) || w === ''
        ? w
        : (
          <span key={`${si}-${wi}`} className={styles.mask}>
            <m.span className={styles.word} variants={variants}>{w}</m.span>
          </span>
        )
    ));
    nodes.push(
      seg.em
        ? <em key={si} className={seg.className}>{inner}</em>
        : <span key={si} className={seg.className}>{inner}</span>,
    );
  });

  return (
    <Tag id={id} className={className} variants={container(delay)} {...triggerProps}>
      {nodes}
    </Tag>
  );
}
