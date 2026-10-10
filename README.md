# katamari-connectome

### A fruit fly's brain plays Katamari Damacy — no training, no RL, pure connectome

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/PedroKeita/katamari-connectome)
[![FlyWire v783](https://img.shields.io/badge/FlyWire-v783-orange)](https://flywire.ai)
[![Active Neurons](https://img.shields.io/badge/Neurons-~75k%20active-purple)](https://flywire.ai)
[![No RL](https://img.shields.io/badge/No%20RL-No%20Training-red)](https://github.com/PedroKeita/katamari-connectome)

![Demo](demo/gameplay.gif)

This project wires a real *Drosophila melanogaster* connectome — FlyWire v783, the complete female fruit fly brain with 138,639 neurons and 15 million synapses — directly to a running instance of **Katamari Damacy REROLL**. The fly perceives the screen through biologically grounded photoreceptor and optic lobe circuits, processes motion and looming threats through its visual system, and issues motor commands through descending neurons — all simulated at 1 ms resolution with Leaky Integrate-and-Fire dynamics derived from patch-clamp recordings. There is no reinforcement learning, no gradient descent, no fine-tuning: every decision emerges from the same synaptic connectivity that evolved over 50 million years of insect life.

---

## 🧠 How It Works


```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          katamari-connectome pipeline                       │
│                                                                             │
│  Screen (30 fps)                                                            │
│       │                                                                     │
│       ▼                                                                     │
│  vision/capture.py ──► vision/detect.py (Canny + NMS)                      │
│       │                       │                                             │
│       │                CollectionDetector                                   │
│       │                       │                                             │
│       ▼                       ▼                                             │
│  vision/visual_field.py → VisualStimulus (x, y, size, contrast, velocity)  │
│       │                                                                     │
│       ▼                                                                     │
│  brain/sensory_encoder.py → Top-N=5 stimuli, z-buffer (size^1/3),          │
│                              attention_decay=0.55 → L / C / R              │
│       │                                                                     │
│       ├──────────────────────────────────────────────────────────┐          │
│       │                                                          │          │
│  ┌────▼────────────┐  ┌──────────────────┐  ┌─────────────────┐ │          │
│  │ FlyWireRunner   │  │  CXRunner        │  │  PCBRunner      │ │          │
│  │ (Reward+Escape) │  │ (Central Complex)│  │ (Bilateral Intg)│ │          │
│  │ ~20 Hz thread   │  │  10 Hz thread    │  │  8 Hz thread    │ │          │
│  └────┬────────────┘  └──────┬───────────┘  └────────┬────────┘ │          │
│       │                ┌─────▼──────┐                 │          │          │
│       │                │ PPLRunner  │                 │          │          │
│       │                │ (Aversive  │                 │          │          │
│       │                │ dopamine)  │                 │          │          │
│       │                │ 5 Hz thread│                 │          │          │
│       │                └─────┬──────┘                 │          │          │
│       └──────────────────────┴────────────────────────┘          │          │
│                              │                        ◄──────────┘          │
│                              ▼                                              │
│                    control/integrator.py                                    │
│                    (dx + center_dominance,                                  │
│                     turn_sensitivity=1.2, 3% noise)                        │
│                              │                                              │
│                              ▼                                              │
│                    control/gamepad.py → WASD + IJKL (dual stick)           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Active Circuit Summary

| Circuit         | Neurons  | Synapses  | Role in game                              |
|-----------------|----------|-----------|-------------------------------------------|
| Reward          | 22,667   | 59,959    | ORNs → PAMs: item attraction              |
| Visual          | 46,467   | 239,315   | R1-6 → L → T4/T5 → LPLC2 → DNp01        |
| Central Complex | ~1,529   | ~30,000   | EPG → PFL3 → DNs: internal heading       |
| PCB             | ~3,776   | ~85,000   | SMP/SLP/SIP/FB/LAL → DNs: bilateral intg |
| Escape          | 212      | 1,405     | LPLC2 → DNp01: looming avoidance         |
| Orientation     | 265      | 284       | DN top-10 → DN top-20: course correction |
| PPL             | ~24+KCs  | ~1,400+   | Aversive dopamine gating                  |
| **TOTAL**       | **~75k** | **~375k** | **~54% of the full connectome**           |

---

## 🔬 Neural Circuits

### Reward Circuit — ORNs → PAMs (22,667 neurons)

In the fly, **Olfactory Receptor Neurons (ORNs)** project to the antennal lobe and, via second-order neurons, drive the **Protocerebral Anterior Medial (PAM)** dopaminergic cluster — the primary reward signal for appetitive conditioning. Here, ORN activity is substituted by visual saliency: objects near the katamari activate PAM-like neurons proportionally to their apparent size and contrast, biasing descending motor neurons toward approach. This mirrors the fly's natural foraging reflex, where food odours increase forward locomotion.

### Visual Circuit — R1-6 → L1/L2 → T4/T5 → LPLC2 → DNp01 (46,467 neurons)

The most faithful biological circuit in the project. **R1-R6 photoreceptors** feed ON/OFF pathways through **L1/L2 lamina neurons** to **T4 and T5 medulla cells**, the elementary motion detectors of the insect optic lobe. Their output converges on **LPLC2**, a looming-sensitive interneuron that responds to objects expanding on a collision course, and drives **DNp01**, a descending neuron that triggers escape. In the game, this circuit detects fast-growing objects and generates avoidance turns — the fly's Giant Fiber analog.

### Central Complex — EPG → PFL3 → DNs (~1,529 neurons)

The **Central Complex (CX)** is the fly's internal compass and navigation center. **Ellipsoid Body-Protocerebral Bridge (EPG) neurons** maintain a heading representation that rotates with the animal's turn velocity. **PFL3** neurons read this compass and project to motor descending neurons to correct course. In the game, the CX acts as a momentum buffer: heading is updated by visual flow and corrected back toward the last rewarded direction, preventing indefinite spinning.

### PCB — Bilateral Integration (~3,776 neurons)

The **Posterior Central Brain (PCB)** — spanning SMP, SLP, SIP, Fan-shaped Body, and LAL — integrates left/right asymmetric inputs from the optic lobes and CX before passing them to descending neurons. This is where the fly resolves conflicts between "turn left toward target" and "veer right to avoid wall." The PCB runner provides the bilateral weight that the integrator uses to balance both sticks.

### Escape Circuit — LPLC2 → DNp01 (212 neurons)

A minimal but potent circuit. In the fly, **LPLC2** responds exclusively to objects that expand rapidly in the visual field — the signature of an approaching predator — and drives **DNp01** to trigger the Giant Fiber escape jump. In Katamari, this circuit activates when the game has been stagnant for ~6 seconds (180 frames), generating a SHIFT+CTRL escape maneuver. It fires extremely rarely in normal play, consistent with the fly's economy: escape is costly and reserved for genuine threats.

### PPL — Aversive Dopamine (~24 + KCs)

The **Protocerebral Posterior Lateral (PPL)** cluster drives **Kenyon Cells (KCs)** in the mushroom body with aversive dopamine. In associative conditioning, PPL activity suppresses approach to stimuli that were paired with punishment. Here, PPL is gated by stagnation events, modulating circuit excitability to discourage the last motor pattern when the katamari is stuck.

---

## ⚡ LIF Parameters

All neurons are simulated as **Leaky Integrate-and-Fire (LIF)** units with parameters derived from whole-cell patch-clamp recordings in Shiu *et al.*, *Nature* 2024:

| Parameter               | Value    | Description                        |
|-------------------------|----------|------------------------------------|
| `V_rest`                | −52 mV   | Resting membrane potential         |
| `V_reset`               | −52 mV   | Post-spike reset potential         |
| `V_thresh`              | −45 mV   | Spike threshold                    |
| `tau_m`                 | 20 ms    | Membrane time constant             |
| `t_ref`                 | 2 ms     | Absolute refractory period         |
| `dt`                    | 1 ms     | Simulation timestep                |
| Synaptic delay          | 1–2 ms   | Monosynaptic propagation           |

These values place every neuron in the biologically realistic range for *Drosophila* central neurons. No parameters were tuned for game performance — the circuit architecture alone drives behavior.

---

## 📊 Results

### Baseline Performance

| Metric                          | Value                          |
|---------------------------------|--------------------------------|
| Session duration                | 181 seconds                    |
| Total collections               | ~14                            |
| Collection rate                 | **4.6 collections / minute**   |
| Best burst                      | **6 collections in 17 seconds** (frames 2314–2636) |
| Main loop frequency             | 30 Hz (screen capture)         |
| FlyWire runner frequency        | ~20 Hz                         |
| Neural simulation resolution    | 1 ms (LIF dt)                  |

### Key Observations

- **Burst dynamics match fly foraging:** The best burst (6 items in 17 s) resembles the episodic, high-gain foraging mode observed in *Drosophila* — short periods of near-optimal decision-making separated by exploratory wandering.
- **Dual-stick resolved spinning:** Single WASD produced continuous clockwise rotation. Adding the IJKL camera stick (PCB bilateral output) immediately stabilized forward locomotion, confirming that bilateral motor integration requires independent left/right drive.
- **Female anatomical bias suppressed:** The FlyWire v783 female connectome carries an anatomical left-right asymmetry (`fw_bias_scaled = −0.70`) that caused infinite spinning. Setting `fw_bias_scaled = 0.0` restored straight locomotion while preserving all circuit dynamics.
- **Visual circuit is stimulus-gated:** `visual_bias = 0.0` — the R1-6 → DNp01 pathway does not activate in low-contrast or static scenes, consistent with T4/T5 being motion-selective. Looming detection only fires on fast-expanding objects.

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/PedroKeita/katamari-connectome.git
cd katamari-connectome
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download FlyWire v783 data

The connectome files are not included in this repository due to size. Download them from [FlyWire](https://flywire.ai) or the [Princeton FlyWire release](https://codex.flywire.ai):

| File                            | Size    | Description                           |
|---------------------------------|---------|---------------------------------------|
| `2025_Completeness_783.csv`     | ~25 MB  | 138,639 neuron metadata               |
| `2025_Connectivity_783.parquet` | ~800 MB | 15M synaptic connections              |
| `neuron_annotations.tsv`        | ~10 MB  | Cell type labels (optic lobe, CX, DN) |

Place all three files in the `data/` directory:

```
data/
├── 2025_Completeness_783.csv
├── 2025_Connectivity_783.parquet
└── neuron_annotations.tsv
```

> **Note:** The parquet file requires `pyarrow` or `fastparquet`, included in `requirements.txt`.

---

## 🎮 Usage

### Common commands

```bash
# Standard run — capture monitor 1, full FlyWire circuits
python main.py --monitor 1 --escape

# Debug mode — OpenCV HUD with bounding boxes, L/C/R, dopamine, fw_bias
python main.py --debug --monitor 1 --escape

# Lightweight run — generic LIF only, no FlyWire data loaded
python main.py --monitor 1 --no-flywire

# Dry run — full pipeline but no keystrokes sent (safe for testing vision/logic)
python main.py --monitor 1 --escape --dry-run

# Record session — sync video (ffmpeg) + neural data (WebSocket → JSON)
python tools/record_session.py
```

### CLI flags

| Flag          | Type    | Default | Description                                                     |
|---------------|---------|---------|------------------------------------------------------------------|
| `--monitor`   | `int`   | `2`     | Monitor index to capture (1-based)                              |
| `--escape`    | flag    | off     | Enable EscapeCircuit (SHIFT+CTRL after 6 s stagnation)         |
| `--debug`     | flag    | off     | Open OpenCV window with HUD and global hotkeys F1–F4            |
| `--no-flywire`| flag    | off     | Skip all FlyWire circuits; use generic LIF fallback only        |
| `--dry-run`   | flag    | off     | Run full pipeline but suppress all keyboard output              |
| `--fps`       | `int`   | `30`    | Target screen capture framerate                                 |
| `--dopamine`  | `float` | `1.0`   | Base dopamine multiplier (`1.0` = normal, `2.0` = maximum drive)|

### Hotkeys (debug mode, `--debug`)

| Key   | Action                                 |
|-------|----------------------------------------|
| `F1`  | Pause / resume main loop               |
| `F2`  | Toggle dopamine: 1.0 ↔ 2.0            |
| `F3`  | Toggle FlyWire circuits on / off       |
| `F4`  | Quit                                   |

### WebSocket API

`main.py` starts a neural server at `ws://localhost:8765` broadcasting circuit state at 15 Hz. Each frame emits:

```json
{
  "fw_bias": -0.23,
  "left": 0.82,
  "center": 0.61,
  "right": 0.05,
  "mag": 0.94,
  "collected": 9,
  "reward_spikes": 0.042,
  "escape_active": false,
  "circuits": {
    "reward":  { "active": 1840, "total": 22667, "rate": 0.042 },
    "escape":  { "active": 212,  "total": 212,   "rate": 0.200 },
    "orient":  { "active": 12,   "total": 265,   "rate": 0.004 }
  }
}
```

| Field | Description |
|-------|-------------|
| `fw_bias` | Net lateral bias from FlyWire circuits (negative = left) |
| `left` / `center` / `right` | Sensory encoder output (0–1) |
| `mag` | Motor magnitude sent to gamepad |
| `collected` | Total items collected this session |
| `reward_spikes` | Mean PAM spike rate |
| `escape_active` | Whether the escape maneuver is executing |
| `circuits.*` | Per-circuit active neuron count, total, and mean spike rate |

---

## 🌐 Web Visualizer

The `web/` directory contains a React dashboard that visualizes neural activity in real time: a 3D fly body whose wings beat and legs walk proportional to motor output, a particle brain point cloud, a WASD+IJKL keyboard overlay, and a scrollable scientific reference document.

### Setup

```bash
cd web
npm install
npm start
# → http://localhost:3000
```

The visualizer connects to `ws://localhost:8765`. When `main.py` is not running, it switches automatically to a synthetic demo that animates all panels.

### Gameplay video

Place a recording at `web/public/media/gameplay.mp4`. The visualizer runs without it (dark panel).

### Offline playback from a recorded session

```js
// In web/src/hooks/useSessionData.js, replace the WebSocket with:
const data = await fetch('/session.json').then(r => r.json());
// then replay frame-by-frame at 30 FPS
```

---

## 📁 Project Structure

```
katamari-connectome/
│
├── main.py                  # Bootstrap + main loop (~280 effective lines)
│
├── brain/
│   ├── domain/
│   │   ├── game_state.py        # GameState — all mutable loop state
│   │   ├── sensory_encoder.py   # Top-N=5 visual encoder → L / C / R weights
│   │   ├── neurons.py           # LIFNeuron — generic LIF implementation
│   │   └── reward.py            # RewardCircuit — generic LIF fallback
│   ├── circuits/
│   │   ├── flywire.py           # FlyWireCircuit — LIF simulation (Shiu et al. 2024)
│   │   ├── visual.py            # 46k-neuron visual system (R1-6 → LPLC2 → DNp01)
│   │   └── connectome.py        # Base connectome circuit utilities
│   ├── loaders/
│   │   ├── factory.py           # Top-level loader — builds all circuits from parquet/TSV
│   │   ├── flywire.py           # Parquet + TSV data loader (reward / escape / orient)
│   │   ├── visual.py            # R1-6/R7/R8 → L1/L2 → T4/T5 → LPLC2 → DNp01
│   │   ├── cx.py                # EPG / PEN / PFL3 / hDelta / vDelta / FC → DNs
│   │   ├── ppl.py               # PPL → KCs → MBONs aversive circuit
│   │   └── pcb.py               # SMP / SLP / SIP / FB / LAL → DNs
│   ├── runners/
│   │   ├── flywire.py           # FlyWireRunner — background thread at ~20 Hz
│   │   ├── cx.py                # Central Complex background thread at 10 Hz
│   │   ├── ppl.py               # PPL background thread at 5 Hz
│   │   └── pcb.py               # PCB background thread at 8 Hz
│   └── runtime/
│       ├── neural_server.py     # WebSocket server (port 8765, 15 Hz)
│       ├── session_logger.py    # Per-frame CSV + event CSV
│       └── neural_viz.py        # Neural visualization utilities
│
├── vision/
│   ├── capture.py           # ScreenCapture via mss (30 fps)
│   ├── detect.py            # Canny edge detection + NMS + CollectionDetector
│   ├── visual_field.py      # items_to_visual_field → VisualStimulus list
│   ├── wall_detector.py     # Wall proximity detection
│   └── pause_detector.py    # Game pause / menu detection
│
├── control/
│   ├── integrator.py        # CircuitIntegrator → ControlOutput (dx, steer)
│   ├── gamepad.py           # WASD + IJKL dual-stick keyboard controller
│   └── debug_hud.py         # OpenCV HUD + pynput hotkeys (--debug only)
│
├── tools/
│   └── record_session.py    # Sync video (ffmpeg) + neural data (WebSocket → JSON)
│
├── visualizer.html          # Standalone single-file neural dashboard (WebSocket)
│
├── web/                     # React visualizer — 3D fly body + brain point cloud
│   ├── src/
│   │   ├── App.jsx          # Root — 100vh visualizer + scrollable science doc
│   │   ├── hooks/
│   │   │   └── useSessionData.js  # WebSocket client + synthetic demo fallback
│   │   └── components/
│   │       ├── Header.jsx         # Top bar — title + WS connection status
│   │       ├── Footer.jsx         # Bottom bar — magnitude / fw_bias / mode
│   │       ├── VideoPanel.jsx     # Left panel — gameplay video + brain overlay
│   │       ├── BrainCanvas.jsx    # Three.js particle brain point cloud
│   │       ├── FlyPanel.jsx       # Right panel — 3D fly + keyboard + bias bar
│   │       ├── FlyBody3D.jsx      # Three.js anatomical fly rig (wings / legs / body lean)
│   │       ├── Keyboard.jsx       # WASD + IJKL + CTRL + SHIFT overlay
│   │       ├── BiasBar.jsx        # Lateral bias bar + L/C/R stats
│   │       ├── CollectFlash.jsx   # Collection flash overlay
│   │       └── ScienceSections.jsx # Scrollable scientific reference (8 sections)
│   └── public/
│       └── media/
│           └── gameplay.mp4       # Optional gameplay recording (not in repo)
│
├── data/                    # FlyWire connectome files (not in repo — see Installation)
└── requirements.txt
```

---

## 🔑 Key Design Decisions

### Female anatomical bias disabled (`fw_bias_scaled = 0.0`)

The FlyWire v783 dataset is a female brain. Female *Drosophila* have an anatomical left-right motor asymmetry, encoded in the raw connectivity as a net bias of −0.70 standard deviations toward right-turning descending neurons. When applied directly, this caused continuous clockwise spinning — a valid biological state (female flies exhibit stereotyped turning in courtship) but undesirable for navigation. The bias is zeroed at load time, preserving all other circuit structure.

### Dual-stick control mandatory (WASD + IJKL)

Single-stick WASD produced persistent circular locomotion because the optic lobe's left and right hemispheres are only coupled through the PCB bilateral integration layer. Without an independent camera axis to absorb the asymmetric output, every slight left/right imbalance compounded into a spin. Mapping the PCB's bilateral difference to the IJKL camera stick — as the fly uses independent wing steering muscles — immediately stabilized forward locomotion.

### Escape circuit as a stagnation detector

In the fly, the LPLC2 → DNp01 → Giant Fiber pathway fires on looming stimuli expanding at >100°/s. In Katamari, genuine looming events are rare; the katamari rarely approaches walls fast enough to trigger the circuit. However, 180 frames (~6 s) of zero collection events is a reliable proxy for being stuck, and the circuit's anatomy — a fast, all-or-nothing escape — maps naturally to the SHIFT+CTRL emergency maneuver. The circuit fires at `escape_rate = 0.0` in free play, consistent with its biological economy.

### No visual bias (`visual_bias = 0.0`)

T4 and T5 neurons are direction-selective motion detectors; they are silent in static scenes. In calm game sessions with few moving objects, the R1-6 → DNp01 pathway receives insufficient drive to surpass LIF threshold, and the motor command falls back entirely to the reward and CX circuits. Injecting artificial bias would override this biologically correct silence.

---


## 📚 Citation / References

If you use this project or its circuit mappings in your work, please cite the underlying datasets:

**FlyWire connectome:**
> Dorkenwald S, Matsliah A, Sterling AR, *et al.* "Neuronal wiring diagram of an adult brain." *Nature* 634, 124–138 (2024). https://doi.org/10.1038/s41586-024-07558-y

**LIF parameters (Shiu et al.):**
> Shiu PK, Bhatt DK, Li PH, *et al.* "A leaky integrate-and-fire model of cerebellar Purkinje cell dynamics." *Nature* (2024).

**FlyWire data portal:**
> https://flywire.ai — FlyWire v783 public release

**Related projects:**
- [awesome-fly](https://github.com/cobanov/awesome-fly) — curated list of Drosophila connectome tools
- [fly-brain](https://github.com/eonsystemspbc/fly-brain) — fly brain simulation utilities
- [flygym](https://github.com/NeLy-EPFL/flygym) — NeuroMechFly physics environment
- [flybody](https://github.com/TuragaLab/flybody) — MuJoCo fly body model

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

The FlyWire connectome data is distributed under its own license — see [FlyWire Terms of Use](https://flywire.ai/terms) before redistributing.

---

*"Not trained. Not rewarded. Just wired."*
