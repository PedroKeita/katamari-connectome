/**
 * Single source of truth for every fact the site states.
 * Each value is traceable to the root README.md or to the Python source.
 * When the README and the code disagree, the code wins (noted inline).
 */

// git remote "origin" of this repository.
export const REPO_URL = 'https://github.com/heyIsaac/katamari-connectome';

export const CONNECTOME = {
  release: 'FlyWire v783',
  neurons: '138,639',          // README — 2025_Completeness_783.csv
  synapses: '15M',             // README — 2025_Connectivity_783.parquet
  activeNeurons: '~75k',       // README — Active Circuit Summary total
  activeSynapses: '~375k',
  coverage: '~54%',
};

/** README "Active Circuit Summary" + runner sources. `viz` = rendered in Fig. B. */
export const CIRCUITS = [
  {
    id: 'reward', n: 22667, name: 'Reward', color: 'var(--c-reward)',
    path: 'ORNs → PAMs',
    neurons: '22,667', synapses: '59,959',
    rate: '~20 Hz', // brain/runners/flywire.py — "reward + orient" thread
    role: 'Item attraction. Visual saliency stands in for odour, driving PAM dopamine neurons toward large, high-contrast objects.',
    source: 'brain/runners/flywire.py',
    viz: true,
  },
  {
    id: 'visual', n: 46467, name: 'Visual', color: 'var(--c-visual)',
    path: 'R1-6 → L1/L2 → T4/T5 → LPLC2 → DNp01',
    neurons: '46,467', synapses: '239,315',
    rate: '—',
    role: 'Motion and looming. T4/T5 are motion-selective, so the pathway stays silent in static, low-contrast scenes.',
    source: 'brain/circuits/visual.py',
    viz: false,
  },
  {
    id: 'cx', n: 1529, name: 'Central Complex', color: 'var(--c-cx)',
    path: 'EPG → PFL3 → DNs',
    neurons: '~1,529', synapses: '~30,000',
    rate: '10 Hz',
    role: 'Internal compass. Acts as a heading buffer that pulls back toward the last rewarded direction and prevents endless spinning.',
    source: 'brain/runners/cx.py',
    viz: false,
  },
  {
    id: 'pcb', n: 3776, name: 'PCB', color: 'var(--c-pcb)',
    path: 'SMP/SLP/SIP/FB/LAL → DNs',
    neurons: '~3,776', synapses: '~85,000',
    rate: '8 Hz',
    role: 'Bilateral integration. Resolves "turn toward target" against "veer from wall" and weights the two sticks.',
    source: 'brain/runners/pcb.py',
    viz: false,
  },
  {
    id: 'escape', n: 212, name: 'Escape', color: 'var(--c-escape)',
    path: 'LPLC2 → DNp01',
    neurons: '212', synapses: '1,405',
    rate: 'event',
    role: 'Giant Fiber analog. After ~6 s of stagnation (180 frames) it fires a SHIFT+CTRL escape manoeuvre — rarely, by design.',
    source: 'brain/loaders/flywire.py',
    viz: true,
  },
  {
    id: 'orient', n: 265, name: 'Orientation', color: 'var(--c-orient)',
    path: 'DN top-10 → DN top-20',
    neurons: '265', synapses: '284',
    rate: '~20 Hz',
    role: 'Course correction between descending neurons, using their left/right annotation as a proxy for heading.',
    source: 'brain/loaders/flywire.py',
    viz: true,
  },
  {
    id: 'ppl', n: 24, name: 'PPL', color: 'var(--c-ppl)',
    path: 'PPL → Kenyon Cells',
    neurons: '~24 + KCs', synapses: '~1,400+',
    rate: '5 Hz',
    role: 'Aversive dopamine. Gated by stagnation, it discourages the last motor pattern when the katamari is stuck.',
    source: 'brain/runners/ppl.py',
    viz: false,
  },
];

/** From pixels to keystrokes — verified against module paths in the repo. */
export const PIPELINE = [
  {
    id: 'capture', stage: 'Capture', file: 'vision/capture/screen.py', fact: '30 fps',
    body: 'The screen is grabbed with mss at 30 fps by default (--fps). The game is never modified: the system only reads pixels, like a player.',
    signal: null,
  },
  {
    id: 'detect', stage: 'Detect', file: 'vision/detection/items.py',
    body: 'Canny edges and non-maximum suppression find collectible items. A CollectionDetector notices when the katamari picks one up.',
    signal: 'collected',
  },
  {
    id: 'field', stage: 'Visual field', file: 'vision/models/visual_field.py', fact: '5 values per stimulus',
    body: 'Each detection becomes a VisualStimulus with position, size, contrast and velocity.',
    signal: null,
  },
  {
    id: 'encode', stage: 'Encode', file: 'brain/domain/sensory_encoder.py',
    body: 'The five most salient stimuli are kept. Each later one weighs 55% of the one before, and depth is size^⅓. The result is three input currents: left, centre, right.',
    signal: 'lcr',
  },
  {
    id: 'simulate', stage: 'Simulate', file: 'brain/runners/',
    body: 'Four background threads run LIF networks on FlyWire subgraphs: FlyWire (reward + orientation) at ~20 Hz, Central Complex at 10 Hz, PCB at 8 Hz and PPL at 5 Hz.',
    signal: 'bias',
  },
  {
    id: 'integrate', stage: 'Integrate', file: 'control/integrator.py',
    body: 'All circuit outputs merge into one steering vector. Centre dominance damps turning, turn sensitivity is 1.2, and 3% noise is added.',
    signal: 'mag',
  },
  {
    id: 'actuate', stage: 'Actuate', file: 'control/gamepad.py',
    body: 'The vector becomes key presses (via pynput) on two clusters: WASD for movement and IJKL for the camera, with SHIFT+CTRL reserved for escape.',
    signal: 'keys',
  },
  {
    id: 'broadcast', stage: 'Broadcast', file: 'brain/runtime/neural_server.py', fact: ':8765 · 15 Hz',
    body: 'An asyncio WebSocket on :8765 sends the circuit state as JSON at 15 Hz to this page.',
    signal: null,
  },
];

/** brain/circuits/flywire.py — FlyWireCircuit defaults (Shiu et al. 2024). */
export const LIF = {
  V_rest: -52, V_reset: -52, V_thresh: -45, tau_m: 20, t_ref: 2, dt: 1, w_scale: 0.05,
};

export const LIF_ROWS = [
  ['V_rest', '−52 mV', 'Resting membrane potential'],
  ['V_reset', '−52 mV', 'Potential after a spike'],
  ['V_thresh', '−45 mV', 'Spike threshold, 7 mV above rest'],
  ['tau_m', '20 ms', 'Membrane time constant'],
  ['t_ref', '2 ms', 'Absolute refractory period'],
  ['dt', '1 ms', 'Simulation timestep'],
  ['w_scale', '0.05', 'Synaptic weight scalar'],
];

/**
 * README "Results" (181 s baseline) next to the recording replayed in Plate 1.
 * Recorded values are computed from session.json at runtime (null here).
 * Different runs — shown side by side for orientation, not as a controlled comparison.
 */
export const RESULTS_ROWS = [
  { key: 'duration', label: 'Duration', baseline: '181 s' },
  { key: 'total', label: 'Items collected', baseline: '~14' },
  { key: 'rate', label: 'Collection rate', baseline: '4.6 / min' },
  { key: 'burst', label: 'Best 17-second window', baseline: '6 items' },
  { key: 'escapes', label: 'Escape manoeuvres', baseline: '—' },
];

export const OBSERVATIONS = [
  {
    title: 'Burst dynamics resemble fly foraging',
    body: 'The best burst (6 items in 17 s) looks like Drosophila’s episodic, high-gain foraging: short stretches of near-optimal decisions between periods of exploratory wandering.',
  },
  {
    title: 'Two sticks stopped the spinning',
    body: 'WASD alone produced continuous clockwise rotation. Adding the IJKL camera stick, driven by the PCB bilateral output, immediately stabilised forward locomotion.',
  },
  {
    title: 'An anatomical bias, switched off',
    body: 'The female v783 connectome carries a left–right asymmetry (fw_bias_scaled = −0.70) that caused endless spinning. Setting it to 0.0 restored straight locomotion and left every circuit’s dynamics intact.',
  },
  {
    title: 'Vision is stimulus-gated',
    body: 'The R1-6 → DNp01 pathway does not activate in static or low-contrast scenes. That is consistent with T4/T5 being motion-selective: looming detection fires only on fast-expanding objects.',
  },
];

/** README "Keyboard mapping" as implemented in control/gamepad.py. */
export const CONTROLS = [
  ['W A S D', 'Left stick', 'Movement — forward, turn, reverse'],
  ['I J K L', 'Right stick', 'Camera — heading correction'],
  ['SHIFT + CTRL', 'Modifier', 'Escape manoeuvre after ~6 s stagnation'],
];

export const RUN_STEPS = [
  {
    title: 'Clone and install',
    code: `git clone ${REPO_URL}.git
cd katamari-connectome
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt`,
  },
  {
    title: 'Add the FlyWire v783 data to data/',
    code: `data/
├── 2025_Completeness_783.csv      # ~25 MB · 138,639 neurons
├── 2025_Connectivity_783.parquet  # ~800 MB · 15M connections
└── neuron_annotations.tsv         # ~10 MB · cell type labels`,
  },
  {
    title: 'Run with the game open',
    code: `python main.py --monitor 1 --escape          # full circuits
python main.py --monitor 1 --escape --dry-run  # no keystrokes
python main.py --debug --monitor 1 --escape    # OpenCV HUD`,
  },
];

export const FLAGS = [
  ['--monitor', '2', 'Monitor index to capture (1-based)'],
  ['--escape', 'off', 'Enable the escape circuit'],
  ['--debug', 'off', 'OpenCV HUD; hotkeys F1–F4'],
  ['--no-flywire', 'off', 'Generic LIF fallback, no FlyWire data'],
  ['--dry-run', 'off', 'Full pipeline, no keyboard output'],
  ['--fps', '30', 'Capture framerate'],
  ['--dopamine', '1.0', 'Base dopamine multiplier (up to 2.0)'],
];

export const WS_SCHEMA = `{
  "fw_bias": -0.23,   // − left · + right
  "left": 0.82,      // visual field input
  "center": 0.61,
  "right": 0.05,
  "mag": 0.94,       // motor drive
  "collected": 9,
  "escape_active": false,
  "pressed_keys": ["w", "i", "j", "a"],
  "circuits": {
    "reward": { "rate": 0.042 },
    "escape": { "rate": 0.200 },
    "orient": { "rate": 0.004 }
  }
}`;

/** Verified against Crossref metadata for each DOI. */
export const REFERENCES = [
  {
    venue: 'Nature · 2024', authors: 'Dorkenwald et al.',
    title: 'Neuronal wiring diagram of an adult brain',
    url: 'https://doi.org/10.1038/s41586-024-07558-y',
    note: 'The FlyWire connectome',
  },
  {
    venue: 'Nature · 2024', authors: 'Shiu et al.',
    title: 'A Drosophila computational brain model reveals sensorimotor processing',
    url: 'https://doi.org/10.1038/s41586-024-07763-9',
    note: 'Source of the LIF parameters',
  },
  {
    venue: 'Nature · 2024', authors: 'Lappalainen et al.',
    title: 'Connectome-constrained networks predict neural activity across the fly visual system',
    url: 'https://doi.org/10.1038/s41586-024-07939-3',
    note: 'Visual system modelling',
  },
  {
    venue: 'Nature · 2025', authors: 'Vaxenburg et al.',
    title: 'Whole-body physics simulation of fruit fly locomotion',
    url: 'https://doi.org/10.1038/s41586-025-09029-4',
    note: 'flybody — reference for Fig. C',
  },
  {
    venue: 'GitHub', authors: 'TuragaLab',
    title: 'flybody — MuJoCo fruit fly body model',
    url: 'https://github.com/TuragaLab/flybody',
    note: 'Anatomical meshes in Fig. C',
  },
  {
    venue: 'GitHub', authors: 'NeLy-EPFL',
    title: 'FlyGym / NeuroMechFly',
    url: 'https://github.com/NeLy-EPFL/flygym',
    note: 'Physics-based Drosophila simulation',
  },
  {
    venue: 'J. Physiol. Pathol. Gén. · 1907', authors: 'Lapicque',
    title: 'Recherches quantitatives sur l’excitation électrique des nerfs',
    url: null,
    note: 'Origin of the integrate-and-fire model',
  },
];
