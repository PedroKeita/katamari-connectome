import { useEffect, useRef } from 'react';
import { getSnapshot } from '../../data/sessionStore';
import { createRenderGate } from '../../three/renderGate';
import { LIF } from '../../content/project';
import { emit } from '../../data/events';

const WINDOW_MS = 400;       // visible history
const SIM_PER_FRAME = 4;     // ms of simulated time per animation frame (≈ ¼ speed)
// Frame the sub-threshold climb (−52 → −45 mV): that is where "leaky
// integration" is visible. Spikes are drawn as stems clipped at the top.
const V_MIN = -54;
const V_MAX = -40;
const SPIKE_PEAK = -5;

/**
 * One LIF neuron integrated in the browser with the project's parameters
 * (brain/circuits/flywire.py:69). Input current follows the motor drive of the
 * current frame. Illustrative only, and the figure says so.
 */
export function stepLif(state, I) {
  const { V_rest, V_reset, V_thresh, tau_m, t_ref, dt } = LIF;
  if (state.ref > 0) {
    state.ref -= dt;
    return { v: V_reset, spike: false };
  }
  state.V += ((V_rest - state.V) / tau_m + I) * dt;
  if (state.V >= V_thresh) {
    state.V = V_reset;
    state.ref = t_ref;
    return { v: SPIKE_PEAK, spike: true };
  }
  return { v: state.V, spike: false };
}

export default function LifTrace({ reducedMotion }) {
  const ref = useRef(null);
  const rmRef = useRef(reducedMotion);
  rmRef.current = reducedMotion;

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    const neuron = { V: LIF.V_rest, ref: 0 };
    const trace = new Float32Array(WINDOW_MS).fill(LIF.V_rest);
    let head = 0;
    let seed = 1;
    const noise = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647 - 0.5; };

    const css = getComputedStyle(document.documentElement);
    const C = {
      line: css.getPropertyValue('--paper').trim() || '#fff0e8',
      thresh: css.getPropertyValue('--yellow').trim() || '#FFDA00',
      spike: css.getPropertyValue('--magenta').trim() || '#FF3F8E',
      grid: 'rgba(255,240,232,0.08)',
      label: css.getPropertyValue('--paper-3').trim() || '#b08898',
    };

    function advance(ms) {
      const mag = getSnapshot().frame.mag;
      for (let i = 0; i < ms; i++) {
        // Rheobase is 0.35 (V∞ = V_rest + I·τ_m must exceed −45 mV): silent at zero drive,
        // firing faster as drive rises.
        const I = 0.3 + mag * 0.4 + noise() * 0.1;
        const step = stepLif(neuron, I);
        trace[head] = step.v;
        if (step.spike) emit('lif:spike'); // lets the V_thresh row in the table react
        head = (head + 1) % WINDOW_MS;
      }
    }

    function draw() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (!w || !h) return;
      if (canvas.width !== Math.round(w * dpr)) {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const PAD_T = 22;
      const PAD_B = 26;
      const ph = h - PAD_T - PAD_B;
      const y = (v) => PAD_T + ph - ((Math.min(v, V_MAX) - V_MIN) / (V_MAX - V_MIN)) * ph;

      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textBaseline = 'bottom';
      ctx.textAlign = 'left';
      ctx.lineWidth = 1;
      [[LIF.V_rest, 'rest −52 mV', C.label, []], [LIF.V_thresh, 'threshold −45 mV', C.thresh, [4, 4]]].forEach(
        ([v, label, color, dash]) => {
          ctx.strokeStyle = color === C.label ? C.grid : color;
          ctx.setLineDash(dash);
          ctx.beginPath();
          ctx.moveTo(0, y(v));
          ctx.lineTo(w, y(v));
          ctx.stroke();
          ctx.fillStyle = color;
          ctx.fillText(label, 6, y(v) - 4);
        },
      );
      ctx.setLineDash([]);

      // Spikes first, so the membrane line sits on top.
      ctx.fillStyle = C.spike;
      for (let i = 0; i < WINDOW_MS; i++) {
        if (trace[(head + i) % WINDOW_MS] === SPIKE_PEAK) {
          const x = (i / (WINDOW_MS - 1)) * w;
          ctx.fillRect(x - 1, PAD_T - 10, 2, y(LIF.V_thresh) - PAD_T + 10);
        }
      }

      ctx.beginPath();
      for (let i = 0; i < WINDOW_MS; i++) {
        const v = trace[(head + i) % WINDOW_MS];
        const x = (i / (WINDOW_MS - 1)) * w;
        const yy = v === SPIKE_PEAK ? y(LIF.V_thresh) : y(v);
        if (i === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
      }
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 100 ms scale bar.
      const bar = (100 / WINDOW_MS) * w;
      ctx.fillStyle = C.label;
      ctx.fillRect(8, h - 10, bar, 1.5);
      ctx.textAlign = 'left';
      ctx.fillText('100 ms', 8, h - 13);
    }

    advance(WINDOW_MS);
    draw();

    const gate = createRenderGate(canvas);
    let raf;
    let last = 0;
    function frame(now) {
      raf = requestAnimationFrame(frame);
      if (!gate.active) return;
      if (rmRef.current) {
        // Reduced motion: refresh a still trace once a second.
        if (now - last < 1000) return;
        last = now;
        advance(WINDOW_MS);
      } else {
        advance(SIM_PER_FRAME);
      }
      draw();
    }
    raf = requestAnimationFrame(frame);
    const ro = new ResizeObserver(draw);
    ro.observe(canvas);

    return () => {
      cancelAnimationFrame(raf);
      gate.dispose();
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={ref}
      role="img"
      aria-label="Membrane potential of one simulated leaky integrate-and-fire neuron. The voltage climbs from rest toward the −45 mV threshold, spikes, resets to −52 mV and repeats; it fires faster when the motor drive is higher."
    />
  );
}
