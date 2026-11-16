import { useState } from 'react';
import Figure from '../ui/Figure';
import BrainCanvas from '../BrainCanvas';
import FlyBody3D from '../FlyBody3D';
import GameplayVideo from './GameplayVideo';
import SessionTimeline from './SessionTimeline';
import MotorOutput from './MotorOutput';
import { useReducedMotion } from '../../hooks';
import { CONNECTOME } from '../../content/project';
import styles from './Plate.module.css';

const VIEWS = [
  { id: 'fig-b', label: 'Brain' },
  { id: 'fig-c', label: 'Fly' },
  { id: 'fig-d', label: 'Motor' },
];

/**
 * Act I — the instrument, set as a journal plate.
 * A: gameplay (the replay clock) · B: brain activity · C: fly rig · D: motor output.
 */
export default function Plate() {
  const reducedMotion = useReducedMotion();
  const [view, setView] = useState('fig-b');

  return (
    <section id="plate" className={styles.plate} aria-labelledby="thesis">
      <header className={styles.band}>
        <h1 id="thesis" className={styles.thesis}>
          A fruit fly’s brain plays <em>Katamari&nbsp;Damacy</em>.
        </h1>
        <div className={styles.standfirst}>
          <p className={styles.lede}>
            The wiring of a real <i>Drosophila</i> brain, the {CONNECTOME.release} connectome,
            is simulated neuron by neuron and connected to a game controller.
            There is no training, no reinforcement learning and no hand-written policy.
          </p>
          <p className={styles.howto}>
            Below is a real 60-second recording replayed against its footage.
            Run <code>main.py</code> locally and this page switches to the live brain.
          </p>
        </div>
      </header>

      <div className={styles.grid}>
        <Figure
          letter="A"
          title="Gameplay"
          meta="Katamari Damacy REROLL · screen capture"
          className={styles.figA}
          caption="What the fly sees. Each tick on the timeline is an item collected; select one to jump there."
        >
          <GameplayVideo reducedMotion={reducedMotion} />
          <SessionTimeline />
        </Figure>

        <div
          className={styles.switcher}
          role="group"
          aria-label="Choose which figure to show"
        >
          {VIEWS.map((v) => (
            <button
              key={v.id}
              type="button"
              aria-pressed={view === v.id}
              aria-controls={v.id}
              onClick={() => setView(v.id)}
            >
              {v.label}
            </button>
          ))}
        </div>

        <Figure
          id="fig-b"
          letter="B"
          title="Brain activity"
          meta="drag to rotate"
          className={`${styles.figB} ${view !== 'fig-b' ? styles.mobileHidden : ''}`}
          bodyClassName={styles.canvasBody}
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
          caption="Keys held right now, and the signals that produced them."
        >
          <MotorOutput />
        </Figure>
      </div>

      <p className={styles.plateCaption}>
        <span className={styles.plateLabel}>Plate 1.</span>{' '}
        A closed loop: the screen (<b>A</b>) becomes left, centre and right input currents; leaky
        integrate-and-fire networks built from FlyWire subgraphs respond (<b>B</b>); their output
        beats the wings (<b>C</b>) and presses keys (<b>D</b>). <a href="#method">How each step works ↓</a>
      </p>
    </section>
  );
}
