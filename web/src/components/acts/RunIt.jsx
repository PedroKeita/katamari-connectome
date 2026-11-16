import { useState } from 'react';
import Act, { SubHead, actStyles as a } from './Act';
import { RUN_STEPS, FLAGS, WS_SCHEMA, CONTROLS, REFERENCES } from '../../content/project';
import styles from './RunIt.module.css';

function CopyButton({ text, label }) {
  const [state, setState] = useState('idle');
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState('done');
    } catch {
      setState('error');
    }
    setTimeout(() => setState('idle'), 1600);
  }
  return (
    <button type="button" className={styles.copy} onClick={copy} data-state={state}>
      <span aria-live="polite">
        {state === 'done' ? 'Copied' : state === 'error' ? 'Copy failed' : 'Copy'}
      </span>
      <span className="sr-only"> {label}</span>
    </button>
  );
}

function CodeBlock({ code, label, lang }) {
  return (
    <div className={styles.code}>
      <div className={styles.codeBar}>
        <span>{lang}</span>
        <CopyButton text={code.replace(/\s+#.*$/gm, '').replace(/\s+\/\/.*$/gm, '')} label={label} />
      </div>
      <pre tabIndex={0} aria-label={label}><code>{code}</code></pre>
    </div>
  );
}

export default function RunIt() {
  return (
    <Act
      id="run"
      numeral="IV"
      kicker="Run it"
      title="Run it yourself"
      lede="You need Python 3.10 or newer, the FlyWire v783 data and a copy of Katamari Damacy REROLL open on a monitor. Once main.py is running, the plate at the top of this page turns into the live brain."
    >
      <div className={a.row}>
        <ol className={styles.steps}>
          {RUN_STEPS.map((s, i) => (
            <li key={s.title}>
              <h3 className={styles.stepTitle}>
                <span className="mono">{String(i + 1).padStart(2, '0')}</span>
                {s.title}
              </h3>
              <CodeBlock code={s.code} label={s.title} lang={i === 1 ? 'tree' : 'shell'} />
            </li>
          ))}
        </ol>
      </div>

      <div className={`${a.row} ${styles.reference}`}>
        <div className={styles.flags}>
          <h3 className={styles.h4}>Command-line flags</h3>
          <table className={styles.table}>
            <caption className="sr-only">main.py command-line flags</caption>
            <thead>
              <tr><th scope="col">Flag</th><th scope="col">Default</th><th scope="col">Effect</th></tr>
            </thead>
            <tbody>
              {FLAGS.map(([f, d, e]) => (
                <tr key={f}>
                  <th scope="row" className="mono">{f}</th>
                  <td className="mono">{d}</td>
                  <td>{e}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3 className={styles.h4}>Controls</h3>
          <table className={styles.table}>
            <caption className="sr-only">Keyboard mapping</caption>
            <thead>
              <tr><th scope="col">Keys</th><th scope="col">Acts as</th><th scope="col">Driven by</th></tr>
            </thead>
            <tbody>
              {CONTROLS.map(([k, s, d]) => (
                <tr key={k}>
                  <th scope="row" className="mono">{k}</th>
                  <td>{s}</td>
                  <td>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={styles.schema}>
          <h3 className={styles.h4}>WebSocket message</h3>
          <p className={styles.small}>
            <code>ws://localhost:8765</code>, 15 times per second. This page listens for it and
            falls back to the recording when nothing answers.
          </p>
          <CodeBlock code={WS_SCHEMA} label="Example WebSocket message" lang="json" />
        </div>
      </div>

      <SubHead id="references" note="DOIs checked against Crossref">References</SubHead>
      <div className={a.row}>
        <ol className={styles.refs}>
          {REFERENCES.map((r) => (
            <li key={r.title}>
              <p className={styles.refMeta}>
                <span>{r.authors}</span>
                <span>{r.venue}</span>
              </p>
              <p className={styles.refTitle}>
                {r.url ? (
                  <a href={r.url} target="_blank" rel="noreferrer">
                    {r.title}
                    <span className="sr-only"> (opens in a new tab)</span>
                  </a>
                ) : r.title}
              </p>
              <p className={styles.refNote}>{r.note}</p>
            </li>
          ))}
        </ol>
      </div>
    </Act>
  );
}
