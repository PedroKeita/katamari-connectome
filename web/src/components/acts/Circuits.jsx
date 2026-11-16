import Act, { SubHead, actStyles as a } from './Act';
import { useSession } from '../../hooks';
import { bestWindow } from '../../data/session';
import { CIRCUITS, CONNECTOME, RESULTS_ROWS, OBSERVATIONS } from '../../content/project';
import styles from './Circuits.module.css';

/** Share of simulated neurons per circuit — one stacked strip, same colours as the table. */
function Composition() {
  return (
    <figure className={styles.composition}>
      <div className={styles.strip} role="img" aria-label={`Share of the ${CONNECTOME.activeNeurons} simulated neurons by circuit: ${CIRCUITS.map((c) => `${c.name} ${c.neurons}`).join(', ')}.`}>
        {CIRCUITS.map((c) => (
          <span
            key={c.id}
            style={{ '--c': c.color, flexGrow: c.n }}
            title={`${c.name} · ${c.neurons} neurons`}
          />
        ))}
      </div>
      <figcaption className={styles.stripCaption}>
        <span>Simulated neurons by circuit</span>
        <span className="mono">{CONNECTOME.activeNeurons} of {CONNECTOME.neurons}</span>
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
          {RESULTS_ROWS.map((r) => (
            <tr key={r.key}>
              <th scope="row">{r.label}</th>
              <td>{r.baseline}</td>
              <td>{values ? values[r.key] : pending}</td>
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
          <Composition />
          <table className={styles.table}>
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
              {CIRCUITS.map((c) => (
                <tr key={c.id} style={{ '--c': c.color }}>
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
                </tr>
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
            <li key={o.title}>
              <p className={styles.obsN} aria-hidden="true">{['i', 'ii', 'iii', 'iv'][i]}.</p>
              <h4>{o.title}</h4>
              <p>{o.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </Act>
  );
}
