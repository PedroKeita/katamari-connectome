const S = {
  wrap: {
    borderTop: '1px solid var(--border)',
    padding: '64px 0 80px',
    background: 'var(--bg)',
  },
  inner: {
    maxWidth: 860,
    margin: '0 auto',
    padding: '0 32px',
  },
  sectionGap: { marginBottom: 80 },
  eyebrow: {
    fontSize: 11, color: 'var(--magenta)', letterSpacing: 2,
    marginBottom: 12, fontFamily: 'Courier New, monospace', opacity: 0.8,
  },
  h2: {
    fontSize: 26, fontWeight: 700, color: 'var(--yellow)',
    marginBottom: 16, letterSpacing: 0.3,
    fontFamily: "'JetBrains Mono', 'Courier New', monospace",
  },
  h3: {
    fontSize: 13, fontWeight: 700, color: 'var(--orange)',
    marginBottom: 8, letterSpacing: 1,
    fontFamily: 'Courier New, monospace',
  },
  p: {
    fontSize: 15, color: '#d4b8c0', lineHeight: 1.85,
    marginBottom: 14, maxWidth: 660,
  },
  divider: {
    height: 1,
    background: 'linear-gradient(90deg, transparent, var(--magenta-dim), transparent)',
    margin: '64px 0',
    opacity: 0.5,
  },
  table: {
    width: '100%', borderCollapse: 'collapse',
    fontSize: 11, fontFamily: 'Courier New, monospace',
  },
  th: {
    padding: '8px 16px', textAlign: 'left',
    color: 'var(--text-dim)', letterSpacing: 2, fontSize: 9,
    borderBottom: '1px solid var(--border)',
  },
  td: {
    padding: '10px 16px', color: '#c8a8b0', fontSize: 13,
    borderBottom: '1px solid var(--border)',
  },
  tdAccent: {
    padding: '10px 16px', color: 'var(--yellow)', fontSize: 12,
    borderBottom: '1px solid var(--border)',
    fontFamily: 'Courier New, monospace',
  },
  card: {
    border: '1px solid var(--border)', borderRadius: 8,
    padding: '20px 24px', marginBottom: 12,
    background: '#26182066',
  },
  tag: (color) => ({
    display: 'inline-block',
    fontSize: 9, letterSpacing: 2,
    color: color ?? 'var(--magenta)',
    border: `1px solid ${color ?? 'var(--magenta)'}`,
    borderRadius: 4, padding: '2px 8px',
    marginRight: 6, marginBottom: 4,
    opacity: 0.85,
  }),
  mono: {
    fontFamily: 'Courier New, monospace',
    fontSize: 11, color: 'var(--yellow)', background: '#1a0c14',
    padding: '12px 16px', borderRadius: 8,
    border: '1px solid var(--border)',
    lineHeight: 1.8, whiteSpace: 'pre', overflowX: 'auto',
    display: 'block', marginBottom: 16,
  },
};

function Divider() { return <div style={S.divider} />; }

function WhatIsThis() {
  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>01 / OVERVIEW</div>
      <div style={S.h2}>What is this project?</div>
      <p style={S.p}>
        The <em style={{ color: 'var(--magenta)' }}>Drosophila melanogaster</em> connectome —
        a complete wiring diagram of every neuron and synapse in a fruit fly brain — is used to
        control a video game character in real time.
      </p>
      <p style={S.p}>
        No machine learning. No trained model. No hand-coded rules.
        The fly's actual neural circuits generate the controller inputs. Behavior emerges from biology.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 28 }}>
        {[
          { v: '139,255', l: 'neurons mapped',       sub: 'FlyWire v783',  color: 'var(--magenta)' },
          { v: '50M+',    l: 'synaptic connections', sub: 'Nature 2024',   color: 'var(--yellow)' },
          { v: '0',       l: 'training examples',    sub: 'pure biology',  color: 'var(--coral)' },
        ].map(({ v, l, sub, color }) => (
          <div key={l} style={{ ...S.card, textAlign: 'center' }}>
            <div style={{ fontSize: 28, color, fontWeight: 700, letterSpacing: -1 }}>{v}</div>
            <div style={{ fontSize: 11, color: '#c8a8b0', marginTop: 6 }}>{l}</div>
            <div style={{ fontSize: 9, color: 'var(--text-dim)', marginTop: 4, letterSpacing: 1 }}>{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Connectome() {
  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>02 / CONNECTOME</div>
      <div style={S.h2}>The FlyWire Connectome</div>
      <p style={S.p}>
        Published in <em style={{ color: 'var(--yellow)' }}>Nature</em> (October 2024),
        the FlyWire connectome was built using electron microscopy at 8 nm/voxel resolution,
        producing ~40 trillion pixels of raw image data.
      </p>
      <p style={S.p}>
        This project uses the v783 release — 22,667 neurons and 59,959 synapses in the
        reward/escape/orientation subgraph we simulate.
      </p>

      <table style={S.table}>
        <thead>
          <tr>
            {['Metric', 'Full connectome', 'This project (subgraph)'].map(h => (
              <th key={h} style={S.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[
            ['Neurons',      '139,255',      '22,667'],
            ['Synapses',     '50,000,000+',  '59,959'],
            ['Resolution',   '8 nm/voxel',   '—'],
            ['Coverage',     'Full adult ♀ brain', 'Reward · Escape · Orient'],
            ['Data release', 'FlyWire v783', 'FlyWire v783'],
            ['Published',    'Nature, Oct 2024', '—'],
          ].map(([m, f, p]) => (
            <tr key={m}>
              <td style={S.td}>{m}</td>
              <td style={S.td}>{f}</td>
              <td style={S.tdAccent}>{p}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Circuits() {
  const circuits = [
    {
      id: '01', name: 'Reward Circuit', color: 'var(--magenta)',
      path: 'ORNs → PNs → Kenyon Cells → PAMs (mushroom body)',
      game: 'Pulls Katamari toward bright, colorful collectible items',
      key: 'fw_bias — lateral asymmetry from PAM firing',
      neurons: '~16,900 ORN inputs → 2,000 KCs → 130 PAMs',
      detail: `Olfactory receptor neurons (ORNs) encode stimulus brightness/color via the
visual field. Projection neurons (PNs) relay to Kenyon Cells in the mushroom
body. PAM dopaminergic neurons encode reward value and generate the lateral
bias that steers the katamari toward the highest-value item.`,
    },
    {
      id: '02', name: 'Escape Circuit', color: 'var(--coral)',
      path: 'LPLC2 → DNp01 (Giant Fiber System)',
      game: 'Triggers CTRL+SHIFT override when looming threat or stagnation detected',
      key: 'escape_active — Giant Fiber relay fires, overrides all other outputs',
      neurons: '~120 LPLC2 → 2 Giant Fiber neurons → motor DNs',
      detail: `The fastest escape circuit in the fly brain: LPLC2 neurons in the lobula
plate detect expanding (looming) visual stimuli. A single spike in the Giant
Fiber neuron (DNp01) produces a jump/escape within 1 ms. Here it triggers
the CTRL+SHIFT key combination for an abrupt directional reversal.`,
    },
    {
      id: '03', name: 'Orientation Circuit', color: 'var(--yellow)',
      path: 'EPG → PEN → PFL3 → descending motor neurons (CX compass)',
      game: 'Provides baseline directional drift when reward/escape signals are low',
      key: 'orient.rate — CX compass heading encodes preferred direction',
      neurons: '~1,529 CX neurons including EPG, PEN, PFL3, hDelta, FC',
      detail: `The Central Complex (CX) acts as an internal compass: EPG neurons encode
heading direction in a ring attractor topology. PEN neurons integrate angular
velocity, rotating the heading estimate. PFL3 neurons translate the heading
into asymmetric motor output.`,
    },
  ];

  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>03 / NEURAL CIRCUITS</div>
      <div style={S.h2}>Three circuits, one controller</div>
      <p style={S.p}>
        Rather than simulating all 139k neurons, we instantiate three functional subgraphs
        that map cleanly to the game's demands. They compete via a biologically plausible
        priority hierarchy.
      </p>

      {circuits.map(c => (
        <div key={c.id} style={{
          ...S.card,
          borderColor: `color-mix(in srgb, ${c.color} 30%, transparent)`,
          marginBottom: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 10 }}>
            <span style={{ fontSize: 9, color: 'var(--text-dim)', letterSpacing: 2 }}>{c.id}</span>
            <span style={{ fontSize: 15, color: c.color, fontWeight: 700, letterSpacing: 1 }}>{c.name}</span>
          </div>
          <div style={{ fontFamily: 'Courier New', fontSize: 11, color: c.color, marginBottom: 10, opacity: 0.85 }}>
            {c.path}
          </div>
          <p style={{ ...S.p, marginBottom: 10, fontSize: 12 }}>{c.detail}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
            <span style={S.tag(c.color)}>{c.neurons}</span>
            <span style={S.tag('var(--lilac)')}>{c.game}</span>
          </div>
          <div style={{ marginTop: 10, fontSize: 10, color: 'var(--text-dim)', letterSpacing: 1 }}>
            key signal → <span style={{ color: c.color }}>{c.key}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function LIFModel() {
  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>04 / NEURON MODEL</div>
      <div style={S.h2}>Leaky Integrate-and-Fire (LIF)</div>
      <p style={S.p}>
        Each simulated neuron follows the LIF model, validated against Drosophila recordings
        by Shiu et al. (Nature 2024).
      </p>

      <code style={S.mono}>{`# Parameters from Shiu et al. (Nature 2024)
V_rest   = V_reset = -52 mV
V_thresh = -45 mV          # 7 mV above rest
tau_m    =  20 ms           # membrane time constant
t_ref    =   2 ms           # refractory period
dt       =   1 ms           # simulation timestep
w_scale  =   0.05           # synaptic weight scalar

# Per-timestep update
I_syn = W.T @ spikes        # synaptic current (sparse)
dV    = ((V_rest - V) / tau_m + I_syn) * dt
V[active] += dV[active]

# Fire and reset
fired     = V >= V_thresh
V[fired]  = V_reset
ref[fired] = t_ref`}
      </code>

      <p style={S.p}>
        The sparse weight matrix <code style={{ color: 'var(--yellow)' }}>W</code> is loaded
        directly from the FlyWire connectivity parquet file.
      </p>
    </div>
  );
}

function Pipeline() {
  const steps = [
    { n: '01', label: 'capture.py',        detail: 'mss screenshots at 30 FPS — 1920×1080 BGRA frame' },
    { n: '02', label: 'detect.py',         detail: 'OpenCV HSV + Canny — finds items and walls, outputs L/C/R density map' },
    { n: '03', label: 'sensory_encoder',   detail: 'Maps pixel density to neural input current for ORNs / LPLC2' },
    { n: '04', label: 'FlyWireCircuit',    detail: 'LIF simulation on FlyWire subgraph — sparse matrix multiply per timestep' },
    { n: '05', label: 'FlyWireRunner',     detail: 'Background thread ~20 Hz — computes lateral_bias from PAM output asymmetry' },
    { n: '06', label: 'CircuitIntegrator', detail: 'Merges fw_bias + PPL + CX + visual_escape into ControlOutput (x, y, mag)' },
    { n: '07', label: 'GamepadController', detail: 'vgamepad Xbox360 — sends WASD/IJKL + CTRL/SHIFT to OS input stack' },
    { n: '08', label: 'NeuralServer',      detail: 'asyncio WebSocket on :8765 — pushes JSON state at 30 Hz to this visualizer' },
  ];

  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>05 / PIPELINE</div>
      <div style={S.h2}>From pixels to keystrokes</div>
      <p style={S.p}>
        The system never modifies the game. It runs entirely outside Katamari, reading
        the screen and writing virtual controller inputs — exactly as a human would,
        but driven by neural circuit simulation.
      </p>

      {steps.map((s, idx) => {
        const accent = ['var(--magenta)', 'var(--orange)', 'var(--yellow)', 'var(--coral)', 'var(--lilac)', 'var(--magenta)', 'var(--orange)', 'var(--yellow)'][idx];
        return (
          <div key={s.n} style={{ display: 'flex', gap: 16, marginBottom: 4, alignItems: 'flex-start' }}>
            <span style={{ fontFamily: 'Courier New', fontSize: 9, color: 'var(--text-dim)', paddingTop: 13, minWidth: 24 }}>{s.n}</span>
            <div style={{ flex: 1, borderLeft: `1px solid color-mix(in srgb, ${accent} 30%, transparent)`, paddingLeft: 16, paddingBottom: 12 }}>
              <div style={{ fontFamily: 'Courier New', fontSize: 12, color: accent, marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 12, color: '#c8a8b0' }}>{s.detail}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function KeyboardMapping() {
  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>06 / CONTROLS</div>
      <div style={S.h2}>Keyboard mapping</div>
      <p style={S.p}>
        Katamari Damacy REROLL uses two analog sticks. We emulate them with
        two WASD-layout clusters, now extended with modifier keys for escape behavior.
      </p>

      <table style={S.table}>
        <thead>
          <tr>
            {['Key(s)', 'Stick', 'Direction', 'Neural source'].map(h => (
              <th key={h} style={S.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[
            ['W',            'Left',  'Forward',       'Reward circuit — high center density'],
            ['A',            'Left',  'Left turn',     'fw_bias < 0 — left PAM dominance'],
            ['D',            'Left',  'Right turn',    'fw_bias > 0 — right PAM dominance'],
            ['S',            'Left',  'Reverse',       'PPL aversive signal — stagnation'],
            ['I',            'Right', 'Forward',       'Orientation CX — maintain heading'],
            ['J',            'Right', 'Left',          'CX PFL3 — heading update leftward'],
            ['L',            'Right', 'Right',         'CX PFL3 — heading update rightward'],
            ['K',            'Right', 'Reverse',       'CX correction — overshoot'],
            ['CTRL',         '—',     'Escape trigger','Giant Fiber fires (DNp01)'],
            ['SHIFT',        '—',     'Escape sustain','GF relay — maintains escape ~300 ms'],
            ['CTRL + SHIFT', '—',     'Full escape',   'LPLC2 → GF full burst or stagnation'],
          ].map(([k, s, d, n]) => (
            <tr key={k}>
              <td style={{ ...S.tdAccent }}>{k}</td>
              <td style={S.td}>{s}</td>
              <td style={S.td}>{d}</td>
              <td style={{ ...S.td, fontSize: 11, color: 'var(--text-dim)' }}>{n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}



function References() {
  const refs = [
    { tag: 'Nature 2024',  text: 'Dorkenwald et al. — FlyWire: online community for whole-brain connectomics',                      url: 'https://www.nature.com/articles/s41586-024-07558-y' },
    { tag: 'Nature 2024',  text: 'Shiu et al. — Connectome-constrained deep mechanistic models of the fly visual system',           url: 'https://www.nature.com/articles/s41586-024-07939-3' },
    { tag: 'Nature 2025',  text: 'Vaxenburg et al. — Whole-body physics simulation of fruit fly locomotion (flybody)',              url: 'https://www.nature.com/articles/s41586-025-09029-4' },
    { tag: 'biorXiv 2024', text: 'Lobato-Rios et al. — NeuroMechFly 2.0 / FlyGym — physics-based Drosophila simulation',           url: 'https://github.com/NeLy-EPFL/flygym' },
    { tag: 'J.Physiol 1907', text: 'Lapicque — Recherches quantitatives sur l\'excitation électrique des nerfs — LIF model origin' },
    { tag: 'GitHub',       text: 'TuragaLab/flybody — MuJoCo fruit fly body model (anatomical rig reference)',                      url: 'https://github.com/TuragaLab/flybody' },
  ];

  return (
    <div style={S.sectionGap}>
      <div style={S.eyebrow}>07 / REFERENCES</div>
      <div style={S.h2}>Scientific basis</div>
      {refs.map((r) => (
        <div key={r.text} style={{ display: 'flex', gap: 16, marginBottom: 10, alignItems: 'flex-start' }}>
          <span style={S.tag('var(--lilac)')}>{r.tag}</span>
          {r.url
            ? <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#c8a8b0', lineHeight: 1.6 }}>{r.text}</a>
            : <span style={{ fontSize: 12, color: '#c8a8b0', lineHeight: 1.6 }}>{r.text}</span>
          }
        </div>
      ))}
    </div>
  );
}

export default function ScienceSections() {
  return (
    <div style={S.wrap}>
      <div style={S.inner}>
        <WhatIsThis />
        <Divider />
        <Connectome />
        <Divider />
        <Circuits />
        <Divider />
        <LIFModel />
        <Divider />
        <Pipeline />
        <Divider />
        <KeyboardMapping />
        <Divider />
        <References />
      </div>
    </div>
  );
}