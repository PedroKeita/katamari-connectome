import Act, { SubHead, actStyles as a } from './Act';
import LifTrace from './LifTrace';
import { useReducedMotion, useSession } from '../../hooks';
import { signed } from '../../data/session';
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

const THREADS = [
  { name: 'FlyWire', hz: '~20 Hz', color: 'var(--c-reward)' },
  { name: 'Central Complex', hz: '10 Hz', color: 'var(--c-cx)' },
  { name: 'PCB', hz: '8 Hz', color: 'var(--c-pcb)' },
  { name: 'PPL', hz: '5 Hz', color: 'var(--c-ppl)' },
];

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
      <ol className={styles.pipeline}>
        {PIPELINE.map((step, i) => (
          <li key={step.id} className={`${a.row} ${styles.step}`}>
            <a className={styles.file} href={sourceUrl(step.file)} target="_blank" rel="noreferrer">
              {step.file}
              <span className="sr-only"> (source on GitHub, opens in a new tab)</span>
            </a>
            <h3 className={styles.stage}>
              <span className={`mono ${styles.idx}`}>{String(i + 1).padStart(2, '0')}</span>
              {step.stage}
            </h3>
            <div className={styles.stepBody}>
              <p>{step.body}</p>
              {step.id === 'simulate' && (
                <ul className={styles.threads} aria-label="Simulation threads">
                  {THREADS.map((t) => (
                    <li key={t.name} style={{ '--c': t.color }}>
                      <span>{t.name}</span><span className="mono">{t.hz}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className={styles.live}>
              {step.signal ? <Signal kind={step.signal} /> : <span className={`mono ${styles.fact}`}>{step.fact}</span>}
            </div>
          </li>
        ))}
      </ol>

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
          <pre className={styles.eq}><code>{`dV = ((V_rest − V) / τ_m + I_syn) · dt
I_syn = Wᵀ · spikes   # sparse FlyWire weights
V ≥ V_thresh  →  spike, V = V_reset`}</code></pre>
          <table className={styles.params}>
            <caption className="sr-only">LIF parameters</caption>
            <tbody>
              {LIF_ROWS.map(([k, v, d]) => (
                <tr key={k}>
                  <th scope="row" className="mono">{k}</th>
                  <td className="mono">{v}</td>
                  <td>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <figure className={styles.trace}>
          <div className={styles.traceCanvas}><LifTrace reducedMotion={reducedMotion} /></div>
          <figcaption>
            <span className={styles.figLabel}>Fig. E</span> One neuron, integrated in your browser
            with the parameters above. Its input current follows the motor drive in Plate 1D.
            This is an illustration of the model, not recorded data.
          </figcaption>
        </figure>
      </div>

      <p className={`${styles.bridge}`}>
        {CIRCUITS.length} circuits are built from this one unit. <a href="#circuits">See the circuits ↓</a>
      </p>
    </Act>
  );
}
