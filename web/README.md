# fly-brain-viz

React visualizer for the Fly Brain · Katamari Damacy project.

## Run

```bash
npm install
npm start
# → http://localhost:3000
```

## Files

```
src/
  App.jsx                        # root — 100vh visualizer + scrollable science
  hooks/
    useSessionData.js            # WebSocket ws://localhost:8765 + synthetic demo fallback
  components/
    Header.jsx                   # top bar — title + WS status
    Footer.jsx                   # bottom bar — mag / fw_bias / mode
    PanelLabel.jsx               # reusable panel header strip
    VideoPanel.jsx               # left panel — gameplay video + brain point cloud overlay
    BrainCanvas.jsx              # Three.js particle brain (faithful to original visualizer)
    FlyPanel.jsx                 # right panel — 3D fly + keyboard + bias
    FlyBody3D.jsx                # Three.js anatomical fly rig (inspired by TuragaLab/flybody)
                                 #   wings beat at freq/amp proportional to mag
                                 #   legs animate in tripod gait scaled to speed
                                 #   body leans with fw_bias
                                 #   escape burst → wings splay wide
    Keyboard.jsx                 # WASD + IJKL + CTRL + SHIFT keys
    BiasBar.jsx                  # lateral bias bar + L/C/R stats
    CollectFlash.jsx             # "✓ COLETADO #N" flash on collection
    ScienceSections.jsx          # scrollable scientific doc below the visualizer
                                 #   01 Overview · 02 Connectome · 03 Circuits
                                 #   04 LIF model · 05 Pipeline · 06 Controls
                                 #   07 Roadmap · 08 References
```

## Video

Place your gameplay recording at `public/media/gameplay.mp4`.
The visualizer runs fully without it (dark panel).

## WebSocket

`main.py` serves `ws://localhost:8765`. When disconnected,
a synthetic demo animates all panels automatically.

## session.json playback

```js
// in useSessionData.js, swap the WebSocket for file playback:
const data = await fetch('/session.json').then(r => r.json());
// then replay frame-by-frame at 30 FPS
```

## References

- [TuragaLab/flybody](https://github.com/TuragaLab/flybody) — anatomical rig reference
- [NeLy-EPFL/flygym](https://github.com/NeLy-EPFL/flygym) — NeuroMechFly simulation
- [FlyWire connectome](https://codex.flywire.ai) — neural data source
