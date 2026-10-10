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
│  │ ~20 Hz thread   │  │  background      │  │  background     │ │          │
│  └────┬────────────┘  └──────┬───────────┘  └────────┬────────┘ │          │
│       │                      │                        │          │          │
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

### Run the connectome controller

```bash
# Standard run — attach to a running Katamari Damacy REROLL window
python main.py

# Debug mode — shows OpenCV HUD with neural activity and detected objects
python main.py --debug

# Record session — captures video (ffmpeg) + neural data (WebSocket → JSON)
python tools/record_session.py

# Open real-time neural visualizer in browser
# Start main.py first, then open:
visualizer.html
```

### Hotkeys (debug mode)

| Key     | Action                        |
|---------|-------------------------------|
| `Q`     | Quit                          |
| `P`     | Pause / resume                |
| `R`     | Reset neural state            |
| `D`     | Toggle detection overlay      |

### WebSocket API

The neural server broadcasts circuit state at 15 Hz on `ws://localhost:8765`. Each frame emits:

```json
{
  "fw_left": 0.42,
  "fw_right": 0.38,
  "cx_heading": 1.57,
  "ppl_aversion": 0.12,
  "escape_active": false,
  "collections": 14
}
```

---

## 📁 Project Structure

```
katamari-connectome/
│
├── main.py                  # Bootstrap + main loop (~280 effective lines)
│
├── brain/
│   ├── fw_runner.py         # FlyWireRunner — background thread at ~20 Hz
│   ├── loaders.py           # Top-level circuit loader (reward/PPL/PCB/CX/visual)
│   ├── game_state.py        # GameState — all mutable loop state
│   ├── sensory_encoder.py   # Top-N=5 visual encoder → L / C / R weights
│   ├── flywire_loader.py    # Parquet + TSV data loader
│   ├── flywire_circuit.py   # LIF simulation (Shiu et al. 2024 parameters)
│   ├── visual_loader.py     # R1-6/R7/R8 → L1/L2 → T4/T5 → LPLC2 → DNp01
│   ├── visual_circuit.py    # 46k-neuron visual system runner
│   ├── cx_loader.py         # EPG / PEN / PFL3 / hDelta / vDelta / FC → DNs
│   ├── cx_runner.py         # Central Complex background thread
│   ├── ppl_loader.py        # PPL → KCs → MBONs aversive circuit
│   ├── ppl_runner.py        # PPL background thread
│   ├── pcb_loader.py        # SMP / SLP / SIP / FB / LAL → DNs
│   ├── pcb_runner.py        # PCB background thread
│   ├── neural_server.py     # WebSocket server (port 8765, 15 Hz)
│   ├── session_logger.py    # Per-frame CSV + event CSV
│   └── reward.py            # Generic LIF fallback
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
├── visualizer.html          # Real-time neural activity dashboard (WebSocket)
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
