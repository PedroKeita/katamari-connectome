import { useEffect, useRef, useState } from 'react';
import * as m from 'motion/react-m';
import { useTransform, useInView } from '../../motion/api';
import Act, { SubHead, actStyles as a } from './Act';
import LifTrace from './LifTrace';
import Axon, { AxonNode, useFire } from '../../motion/Axon';
import { useReducedMotion, useSession } from '../../hooks';
import { signed } from '../../data/session';
import { on } from '../../data/events';
import { MEMBRANE_EASE, DURATION, IN_VIEW, cascade } from '../../motion/tokens';
import { PIPELINE, LIF_ROWS, CIRCUITS, REPO_URL } from '../../content/project';
import styles from './Method.module.css';

const sourceUrl = (file) =>
  `${REPO_URL}/${file.endsWith('/') ? 'tree' : 'blob'}/main/${file}`;

/** Live value echoed from the plate into the matching pipeline stage. */
function Signal({ kind }) {
  const f = useSession((s) => s.frame);
  if (!kind) return null;
  let value;
  if (kind === 'collected') value = `${f.collected} items`;
  else if (kind === 'lcr') value = `L ${f.left.toFixed(2)} · C ${f.center.toFixed(2)} · R ${f.right.toFixed(2)}`;
  else if (kind === 'bias') value = `bias ${signed(f.fw_bias, 3)}`;
  else if (kind === 'mag') value = `drive ${f.mag.toFixed(2)}`;
  else if (kind === 'keys') value = f.pressed_keys.length ? f.pressed_keys.map((k) => k.toUpperCase()).join(' ') : '—';
  return (
    <span className={styles.signal}>
      <span className={styles.signalDot} aria-hidden="true" />
      <span className="mono">{value}</span>
    </span>
  );
}

// Real thread rates; the pulse runs 10× slower so it can be seen (and stays far below 3 Hz).
const THREADS = [
  { name: 'FlyWire', hz: 20, label: '~20 Hz', color: 'var(--c-reward)' },
  { name: 'Central Complex', hz: 10, label: '10 Hz', color: 'var(--c-cx)' },
  { name: 'PCB', hz: 8, label: '8 Hz', color: 'var(--c-pcb)' },
  { name: 'PPL', hz: 5, label: '5 Hz', color: 'var(--c-ppl)' },
];

function Threads() {
  const ref = useRef(null);
  const visible = useInView(ref, { margin: '100px' });
  const reduced = useReducedMotion();
  const run = visible && !reduced;
  return (
    <>
      <ul ref={ref} className={styles.threads} aria-label="Simulation threads">
        {THREADS.map((t) => (
          <li key={t.name} style={{ '--c': t.color }}>
            <m.span
              className={styles.beat}
              aria-hidden="true"
              animate={run ? { opacity: [0.2, 1, 0.2] } : { opacity: 0.6 }}
              transition={run ? { duration: 10 / t.hz, repeat: Infinity, ease: 'easeInOut' } : { duration: 0 }}
            />
            <span>{t.name}</span><span className="mono">{t.label}</span>
          </li>
        ))}
      </ul>
      <p className={styles.slowed}>Pulses shown 10× slower than the real thread rates.</p>
    </>
  );
}

/** One pipeline stage. It "fires" when the spike on the axon reaches it. */
function Step({ step, i, n }) {
  const fire = useFire(i, n);
  // Colour, not opacity: both ends pass AA on --ink-1 (paper-3 6.05:1 → paper / magenta).
  const idxColor = useTransform(fire, [0, 1], ['#b08898', '#FF3F8E']);
  const stageColor = useTransform(fire, [0, 1], ['#b08898', '#fff0e8']);
  const liveOpacity = useTransform(fire, [0, 1], [0, 1]);
  const liveX = useTransform(fire, [0, 1], [8, 0]);

  return (
    <li className={`${a.row} ${styles.step}`}>
      <AxonNode i={i} n={n} />
      <a className={styles.file} href={sourceUrl(step.file)} target="_blank" rel="noreferrer">
        {step.file}
        <span className="sr-only"> (source on GitHub, opens in a new tab)</span>
      </a>
      <m.h3 className={styles.stage} style={{ color: stageColor }}>
        <m.span className={`mono ${styles.idx}`} style={{ color: idxColor }}>
          {String(i + 1).padStart(2, '0')}
        </m.span>
        {step.stage}
      </m.h3>
      <div className={styles.stepBody}>
        <p>{step.body}</p>
        {step.id === 'simulate' && <Threads />}
      </div>
      <m.div className={styles.live} style={{ opacity: liveOpacity, x: liveX }}>
        {step.signal ? <Signal kind={step.signal} /> : <span className={`mono ${styles.fact}`}>{step.fact}</span>}
      </m.div>
    </li>
  );
}

/** The V_thresh row flashes whenever the neuron in Fig. E crosses threshold. */
function ThreshRow({ children }) {
  const [flash, setFlash] = useState(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return undefined;
    let last = 0;
    return on('lif:spike', () => {
      const now = performance.now();
      if (now - last < 500) return; // at most 2 flashes per second
      last = now;
      setFlash((n) => n + 1);
    });
  }, [reduced]);
  return (
    <>
      {/* Remounting by key restarts a short CSS keyframe (opacity only). */}
      {flash > 0 && <span key={flash} className={styles.flash} aria-hidden="true" />}
      {children}
    </>
  );
}

export default function Method() {
  const reducedMotion = useReducedMotion();

  return (
    <Act
      id="method"
      numeral="II"
      kicker="Method"
      title="From pixels to keystrokes"
      lede="The game is never modified. The system reads the screen and presses keys, as a player would. Everything in between is the fly’s wiring. The values on the right are live: they come from the session in Plate 1."
    >
      <Axon className={styles.pipelineWrap}>
        <ol className={styles.pipeline}>
          {PIPELINE.map((step, i) => (
            <Step key={step.id} step={step} i={i} n={PIPELINE.length} />
          ))}
        </ol>
      </Axon>

      <SubHead id="lif" note="brain/circuits/flywire.py">
        Every neuron is the same simple model: it leaks, integrates and fires.
      </SubHead>

      <div className={`${a.row} ${styles.lif}`}>
        <div className={styles.lifText}>
          <p>
            Each neuron is a leaky integrate-and-fire (LIF) unit. The parameters come from
            whole-cell recordings reported by Shiu et al. (<i>Nature</i>, 2024). None were tuned
            for the game: the architecture of the circuits produces the behaviour.
          </p>
          <div className={styles.eqWrap}>
            <m.span
              className={styles.eqRule}
              aria-hidden="true"
              initial={{ scaleY: 0 }}
              whileInView={{ scaleY: 1 }}
              viewport={IN_VIEW}
              transition={{ duration: DURATION.membrane, ease: MEMBRANE_EASE }}
            />
            <pre className={styles.eq}><code>{`dV = ((V_rest − V) / τ_m + I_syn) · dt
I_syn = Wᵀ · spikes   # sparse FlyWire weights
V ≥ V_thresh  →  spike, V = V_reset`}</code></pre>
          </div>
          <table className={styles.params}>
            <caption className="sr-only">LIF parameters</caption>
            <tbody>
              {LIF_ROWS.map(([k, v, d], i) => (
                <m.tr
                  key={k}
                  initial={{ opacity: 0, x: -8 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={IN_VIEW}
                  transition={{ duration: 0.5, ease: MEMBRANE_EASE, delay: cascade(i) }}
                  className={k === 'V_thresh' ? styles.threshRow : undefined}
                >
                  <th scope="row" className="mono">
                    {k === 'V_thresh' ? <ThreshRow>{k}</ThreshRow> : k}
                  </th>
                  <td className="mono">{v}</td>
                  <td>{d}</td>
                </m.tr>
              ))}
            </tbody>
          </table>
        </div>

        <figure className={styles.trace}>
          <div className={styles.traceCanvas}><LifTrace reducedMotion={reducedMotion} /></div>
          <figcaption>
            <span className={styles.figLabel}>Fig. E</span> One neuron, integrated in your browser
            with the parameters above. Its input current follows the motor drive in Plate 1D.
            Each spike lights the threshold row. This is an illustration of the model, not recorded data.
          </figcaption>
        </figure>
      </div>

      <m.p
        className={styles.bridge}
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={IN_VIEW}
        transition={{ duration: DURATION.membrane, ease: MEMBRANE_EASE }}
      >
        {CIRCUITS.length} circuits are built from this one unit. <a href="#circuits">See the circuits ↓</a>
      </m.p>
    </Act>
  );
}
