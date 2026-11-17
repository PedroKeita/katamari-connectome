import { useEffect, useRef, useState } from 'react';
import * as m from 'motion/react-m';
import { useInView, useSpring, useTransform } from '../../motion/api';
import Act, { SubHead, actStyles as a } from './Act';
import { useReducedMotion, useSession } from '../../hooks';
import { bestWindow } from '../../data/session';
import { MEMBRANE_EASE, SPRING, IN_VIEW, cascade } from '../../motion/tokens';
import { CIRCUITS, CONNECTOME, RESULTS_ROWS, OBSERVATIONS } from '../../content/project';
import styles from './Circuits.module.css';

const TOTAL_N = CIRCUITS.reduce((s, c) => s + c.n, 0);
// Largest circuits assemble first, so the strip "accumulates" like the katamari.
const SIZE_RANK = Object.fromEntries(
  [...CIRCUITS].sort((x, y) => y.n - x.n).map((c, i) => [c.id, i]),
);

/** "~75k" counted up once, from the same neuron counts the strip is built from. */
function Count({ run }) {
  const reduced = useReducedMotion();
  // Overdamped spring: rises smoothly and never overshoots the real total.
  const v = useSpring(0, { stiffness: 80, damping: 30 });
  const label = useTransform(v, (x) => `~${Math.round(x / 1000)}k`);
  useEffect(() => {
    if (!run) return;
    if (reduced) v.jump(TOTAL_N);
    else v.set(TOTAL_N);
  }, [run, reduced, v]);
  return <m.span className="mono">{label}</m.span>;
}

/** Share of simulated neurons per circuit — one stacked strip, same colours as the table. */
function Composition({ focus }) {
  const ref = useRef(null);
  const seen = useInView(ref, { once: true, amount: 0.6 });
  return (
    <figure ref={ref} className={styles.composition}>
      <div className={styles.strip} role="img" aria-label={`Share of the ${CONNECTOME.activeNeurons} simulated neurons by circuit: ${CIRCUITS.map((c) => `${c.name} ${c.neurons}`).join(', ')}.`}>
        {CIRCUITS.map((c) => (
          <m.span
            key={c.id}
            style={{ '--c': c.color, flexGrow: c.n }}
            title={`${c.name} · ${c.neurons} neurons`}
            initial={{ scaleX: 0 }}
            animate={{
              scaleX: seen ? 1 : 0,
              opacity: focus && focus !== c.id ? 0.25 : 1,
            }}
            transition={{
              scaleX: { duration: 0.7, ease: MEMBRANE_EASE, delay: SIZE_RANK[c.id] * 0.08 },
              opacity: { duration: 0.2 },
            }}
          />
        ))}
      </div>
      <figcaption className={styles.stripCaption}>
        <span>Simulated neurons by circuit</span>
        <span><Count run={seen} /> <span className="mono">of {CONNECTOME.neurons}</span></span>
      </figcaption>
    </figure>
  );
}

/** Recorded-session values, computed from session.json with the README's definitions. */
function useRecorded() {
  const session = useSession((s) => s.session);
  const status = useSession((s) => s.replayStatus);
  if (!session) return { status, values: null };
  let onsets = 0;
  let prev = false;
  for (const f of session.frames) {
    if (f.escape_active && !prev) onsets += 1;
    prev = f.escape_active;
  }
  const burst = bestWindow(session.events, 17);
  return {
    status,
    values: {
      duration: `${Math.round(session.duration)} s`,
      total: String(session.total),
      rate: `${(session.total / (session.duration / 60)).toFixed(1)} / min`,
      burst: `${burst.count} items`,
      escapes: String(onsets),
    },
  };
}

function Results() {
  const { status, values } = useRecorded();
  const pending = status === 'loading' ? '…' : '—';
  return (
    <div className={styles.results}>
      <table className={styles.compare}>
        <caption className="sr-only">Baseline run and recorded session</caption>
        <thead>
          <tr>
            <td />
            <th scope="col">
              Baseline run
              <span>README · 181 s</span>
            </th>
            <th scope="col">
              Recorded session
              <span>Plate 1 · session.json</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {/* Baseline column settles first, the recording 120 ms later: two measurements, not a scoreboard. */}
          {RESULTS_ROWS.map((r, i) => (
            <tr key={r.key}>
              <th scope="row">{r.label}</th>
              {[r.baseline, values ? values[r.key] : pending].map((val, col) => (
                <m.td
                  key={col}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={IN_VIEW}
                  transition={{ duration: 0.5, ease: MEMBRANE_EASE, delay: col * 0.12 + i * 0.04 }}
                >
                  {val}
                </m.td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className={styles.caveat}>
        Two separate runs, shown side by side for scale, not as a controlled comparison.
        {status === 'error' && ' The recording could not be loaded, so its column is empty.'}
      </p>
    </div>
  );
}

export default function Circuits() {
  // Hovering or focusing a row highlights its share of the strip.
  const [focus, setFocus] = useState(null);
  return (
    <Act
      id="circuits"
      numeral="III"
      kicker="Circuits"
      title="Seven circuits, one controller"
      lede={`Of the ${CONNECTOME.neurons} neurons in ${CONNECTOME.release}, about 75k (roughly 54%) are simulated, in seven functional subgraphs. Each one maps to something the game asks of the fly.`}
    >
      <div className={a.row}>
        <div className={`${a.body} ${styles.tableWrap}`}>
          <Composition focus={focus} />
          <table className={styles.table} onMouseLeave={() => setFocus(null)}>
            <caption className="sr-only">Simulated circuits, sizes and roles</caption>
            <thead>
              <tr>
                <th scope="col">Circuit</th>
                <th scope="col">Pathway</th>
                <th scope="col" className={styles.num}>Neurons</th>
                <th scope="col" className={styles.num}>Synapses</th>
                <th scope="col" className={styles.num}>Rate</th>
                <th scope="col">Role in the game</th>
              </tr>
            </thead>
            <tbody>
              {CIRCUITS.map((c, i) => (
                <m.tr
                  key={c.id}
                  style={{ '--c': c.color }}
                  data-focus={focus === c.id || undefined}
                  onMouseEnter={() => setFocus(c.id)}
                  onFocus={() => setFocus(c.id)}
                  onBlur={() => setFocus(null)}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={IN_VIEW}
                  transition={{ duration: 0.5, ease: MEMBRANE_EASE, delay: cascade(i) }}
                >
                  <th scope="row" className={styles.name}>
                    <span className={styles.swatch} aria-hidden="true" />
                    {c.name}
                    {c.viz && (
                      <a className={styles.inFig} href="#fig-b" title="Rendered in Plate 1B">
                        1B<span className="sr-only">: shown in Plate 1, figure B</span>
                      </a>
                    )}
                  </th>
                  <td data-label="Pathway" className={styles.path}>{c.path}</td>
                  <td data-label="Neurons" className={styles.num}>
                    {c.neurons}
                  </td>
                  <td data-label="Synapses" className={styles.num}>{c.synapses}</td>
                  <td data-label="Rate" className={styles.num}>{c.rate}</td>
                  <td data-label="Role" className={styles.role}>{c.role}</td>
                </m.tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row">Total</th>
                <td />
                <td className={styles.num}>{CONNECTOME.activeNeurons}</td>
                <td className={styles.num}>{CONNECTOME.activeSynapses}</td>
                <td />
                <td className={styles.role}>{CONNECTOME.coverage} of the connectome</td>
              </tr>
            </tfoot>
          </table>
          <p className={styles.note}>
            Circuits tagged <span className={styles.inFigStatic}>1B</span> are the three the
            WebSocket streams, drawn in Plate 1B. Rate is how often each circuit’s simulation
            thread updates. Escape is event-driven.
          </p>
        </div>
      </div>

      <SubHead id="results" note="README · session.json">What it did</SubHead>

      <div className={a.row}>
        <div className={a.body}>
          <Results />
        </div>
      </div>

      <div className={a.row}>
        <ol className={styles.observations}>
          {OBSERVATIONS.map((o, i) => (
            <m.li
              key={o.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={IN_VIEW}
              transition={{ duration: 0.7, ease: MEMBRANE_EASE, delay: cascade(i) }}
            >
              <m.p
                className={styles.obsN}
                aria-hidden="true"
                initial={{ opacity: 0, scale: 0.5 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={IN_VIEW}
                transition={{ ...SPRING.spike, delay: cascade(i) + 0.15 }}
              >
                {['i', 'ii', 'iii', 'iv'][i]}.
              </m.p>
              <h4>{o.title}</h4>
              <p>{o.body}</p>
            </m.li>
          ))}
        </ol>
      </div>
    </Act>
  );
}
