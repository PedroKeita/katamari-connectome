import { useRef, useState } from 'react';
import * as m from 'motion/react-m';
import { useScroll, useTransform } from '../../motion/api';
import Figure from '../ui/Figure';
import BrainCanvas from '../BrainCanvas';
import FlyBody3D from '../FlyBody3D';
import GameplayVideo from './GameplayVideo';
import SessionTimeline from './SessionTimeline';
import MotorOutput from './MotorOutput';
import Threshold from '../../motion/Threshold';
import useCursorDepth from '../../motion/useCursorDepth';
import { useMotionEnv } from '../../motion/MotionProvider';
import { DEPTH, MOBILE_FACTOR, MEMBRANE_EASE, SPRING } from '../../motion/tokens';
import { useReducedMotion } from '../../hooks';
import { CONNECTOME } from '../../content/project';
import styles from './Plate.module.css';

const VIEWS = [
  { id: 'fig-b', label: 'Brain' },
  { id: 'fig-c', label: 'Fly' },
  { id: 'fig-d', label: 'Motor' },
];

// Entrance timeline (seconds). The thesis fires first, then the plate assembles.
const T = { thesis: 0.12, standfirst: 0.52, figA: 0.6, figB: 0.69, figC: 0.78, figD: 0.87 };

/**
 * Act I — the instrument, set as a journal plate.
 * A: gameplay (the replay clock) · B: brain activity · C: fly rig · D: motor output.
 *
 * Motion: a one-time entrance, cursor depth on fine pointers, and a three-speed
 * parallax as the plate scrolls away. The WebGL figures are only ever moved by
 * their wrappers — their render loops are untouched.
 */
export default function Plate() {
  const reducedMotion = useReducedMotion();
  const { compact } = useMotionEnv();
  const [view, setView] = useState('fig-b');
  const ref = useRef(null);

  // Scroll-linked exit: thesis travels fastest, figures slowest.
  const k = compact ? MOBILE_FACTOR : 1;
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });
  const bandY = useTransform(scrollYProgress, [0, 1], [0, reducedMotion ? 0 : -DEPTH.near * k]);
  const gridY = useTransform(scrollYProgress, [0, 1], [0, reducedMotion ? 0 : -DEPTH.far * k]);

  // Cursor depth: layers drift in opposite directions; B and C tilt like objects on a bench.
  const cursor = useCursorDepth();
  const bandX = useTransform(cursor.x, [-1, 1], [6, -6]);
  const figX = useTransform(cursor.x, [-1, 1], [-4, 4]);
  const tiltY = useTransform(cursor.x, [-1, 1], [-3, 3]);
  const tiltX = useTransform(cursor.y, [-1, 1], [3, -3]);
  const depthStyle = cursor.active ? { x: figX, rotateX: tiltX, rotateY: tiltY } : undefined;

  const viewIndex = VIEWS.findIndex((v) => v.id === view);
  // On compact screens the chosen figure rises in; the others stay mounted (canvases
  // must not be torn down) and are hidden by CSS.
  const shown = (id) => (compact ? (view === id ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }) : undefined);

  return (
    <section ref={ref} id="plate" className={styles.plate} aria-labelledby="thesis">
      {/* Depth only, no fade: text must keep full contrast while it is still on screen. */}
      <m.header className={styles.band} style={{ y: bandY, x: cursor.active ? bandX : 0 }}>
        <Threshold
          as="h1"
          id="thesis"
          className={styles.thesis}
          trigger="mount"
          delay={T.thesis}
          segments={[
            { text: 'A fruit fly’s brain plays ' },
            { text: 'Katamari Damacy', em: true, fire: true },
            { text: '.' },
          ]}
        />
        <m.div
          className={styles.standfirst}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: MEMBRANE_EASE, delay: T.standfirst }}
        >
          <p className={styles.lede}>
            The wiring of a real <i>Drosophila</i> brain, the {CONNECTOME.release} connectome,
            is simulated neuron by neuron and connected to a game controller.
            There is no training, no reinforcement learning and no hand-written policy.
          </p>
          <p className={styles.howto}>
            Below is a real 60-second recording replayed against its footage.
            Run <code>main.py</code> locally and this page switches to the live brain.
          </p>
        </m.div>
      </m.header>

      <m.div className={styles.grid} style={{ y: gridY }}>
        <Figure
          letter="A"
          title="Gameplay"
          meta="Katamari Damacy REROLL · screen capture"
          className={styles.figA}
          enter={T.figA}
          caption="What the fly sees. Each tick on the timeline is an item collected; select one to jump there."
        >
          <GameplayVideo reducedMotion={reducedMotion} />
          <SessionTimeline />
        </Figure>

        <div className={styles.switcher} role="group" aria-label="Choose which figure to show">
          <m.span
            className={styles.switchPill}
            aria-hidden="true"
            animate={{ x: `${viewIndex * 100}%` }}
            transition={SPRING.spike}
          />
          {VIEWS.map((v) => (
            <m.button
              key={v.id}
              type="button"
              aria-pressed={view === v.id}
              aria-controls={v.id}
              onClick={() => setView(v.id)}
              whileTap={{ scale: 0.96 }}
            >
              {v.label}
            </m.button>
          ))}
        </div>

        <Figure
          id="fig-b"
          letter="B"
          title="Brain activity"
          meta="drag to rotate"
          className={`${styles.figB} ${view !== 'fig-b' ? styles.mobileHidden : ''}`}
          bodyClassName={styles.canvasBody}
          enter={T.figB}
          style={depthStyle}
          animate={shown('fig-b')}
          transition={SPRING.settle}
          caption="Points flash as each circuit fires. Stylised layout, not real neuron positions."
        >
          <BrainCanvas reducedMotion={reducedMotion} />
          <ul className={styles.legend} aria-label="Circuit colours">
            <li style={{ '--c': 'var(--c-reward)' }}>Reward</li>
            <li style={{ '--c': 'var(--c-orient)' }}>Orientation</li>
            <li style={{ '--c': 'var(--c-escape)' }}>Escape</li>
          </ul>
        </Figure>

        <Figure
          id="fig-c"
          letter="C"
          title="Fly rig"
          meta="flybody meshes"
          className={`${styles.figC} ${view !== 'fig-c' ? styles.mobileHidden : ''}`}
          bodyClassName={styles.canvasBody}
          enter={T.figC}
          style={depthStyle}
          animate={shown('fig-c')}
          transition={SPRING.settle}
          caption="Wing-beat speed follows the motor drive."
        >
          <FlyBody3D />
        </Figure>

        <Figure
          id="fig-d"
          letter="D"
          title="Motor output"
          meta="descending neurons → keys"
          className={`${styles.figD} ${view !== 'fig-d' ? styles.mobileHidden : ''}`}
          enter={T.figD}
          animate={shown('fig-d')}
          transition={SPRING.settle}
          caption="Keys held right now, and the signals that produced them."
        >
          <MotorOutput />
        </Figure>
      </m.div>

      <m.p
        className={styles.plateCaption}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1.3 }}
      >
        <span className={styles.plateLabel}>Plate 1.</span>{' '}
        A closed loop: the screen (<b>A</b>) becomes left, centre and right input currents; leaky
        integrate-and-fire networks built from FlyWire subgraphs respond (<b>B</b>); their output
        beats the wings (<b>C</b>) and presses keys (<b>D</b>). <a href="#method">How each step works ↓</a>
      </m.p>
    </section>
  );
}
