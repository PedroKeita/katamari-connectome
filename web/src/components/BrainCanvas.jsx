import { useEffect, useRef } from 'react';
import * as THREE from 'three';

function sRNG(s) {
  return () => {
    s = Math.imul(s ^ (s >>> 15), s | 1);
    s ^= s + Math.imul(s ^ (s >>> 7), s | 61);
    return ((s ^ (s >>> 14)) >>> 0) / 2 ** 32;
  };
}

function buildNeurons() {
  const rng = sRNG(0xc0ffee);
  const neurons = [];

  function cluster(cx, cy, cz, rx, ry, rz, n, ci) {
    for (let i = 0; i < n; i++) {
      const u = rng(), v = rng(), w = rng();
      const r = Math.cbrt(w) * 0.97;
      const th = Math.acos(2 * u - 1);
      const ph = 2 * Math.PI * v;
      neurons.push({
        x: cx + rx * r * Math.sin(th) * Math.cos(ph),
        y: cy + ry * r * Math.cos(th),
        z: cz + rz * r * Math.sin(th) * Math.sin(ph),
        ci,
        base: 0.15 + rng() * 0.12,
      });
    }
  }

  // Mushroom Body (reward) — bilateral
  cluster(-18, 4, 0, 20, 17, 13, 700, 'R');
  cluster( 18, 4, 0, 20, 17, 13, 700, 'R');
  // Calyx
  cluster(-11, -10, 6, 7, 5, 5, 150, 'R');
  cluster( 11, -10, 6, 7, 5, 5, 150, 'R');
  // Descending (orient)
  cluster(  0, -24, 0, 5, 13, 5, 200, 'O');
  cluster(  0, -37, 0, 4,  7, 4,  80, 'O');
  // Optic lobes (escape)
  cluster(-44,  2, 0, 7, 13, 5,  60, 'E');
  cluster( 44,  2, 0, 7, 13, 5,  60, 'E');

  return neurons;
}

export default function BrainCanvas({ state }) {
  const ref       = useRef(null);
  const stateRef  = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const el  = ref.current;
    if (!el) return;

    const renderer = new THREE.WebGLRenderer({ canvas: el, antialias: true, alpha: true });
    renderer.setClearColor(0, 0);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 110);
    camera.lookAt(0, 0, 0);

    const neurons = buildNeurons();
    const N = neurons.length;

    const pos = new Float32Array(N * 3);
    const col = new Float32Array(N * 3);
    const sz  = new Float32Array(N);

    const CR = new THREE.Color('#7dd4b0');
    const CE = new THREE.Color('#a0e8c8');
    const CO = new THREE.Color('#5aad88');

    neurons.forEach((n, i) => {
      pos[i * 3]     = n.x;
      pos[i * 3 + 1] = n.y;
      pos[i * 3 + 2] = n.z;
      const c = n.ci === 'E' ? CE : n.ci === 'O' ? CO : CR;
      col[i * 3]     = c.r * n.base;
      col[i * 3 + 1] = c.g * n.base;
      col[i * 3 + 2] = c.b * n.base;
      sz[i] = 1.6;
    });

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('pColor',   new THREE.BufferAttribute(col, 3));
    geo.setAttribute('pSize',    new THREE.BufferAttribute(sz,  1));

    const mat = new THREE.ShaderMaterial({
      vertexShader: `
        attribute float pSize;
        attribute vec3 pColor;
        varying vec3 vC;
        void main() {
          vC = pColor;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = pSize * (280.0 / -mv.z);
          gl_Position  = projectionMatrix * mv;
        }
      `,
      fragmentShader: `
        varying vec3 vC;
        void main() {
          float d = length(gl_PointCoord - 0.5) * 2.0;
          if (d > 1.0) discard;
          gl_FragColor = vec4(vC, (1.0 - d * d) * 1.8);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    const points = new THREE.Points(geo, mat);
    scene.add(points);

    // Resize
    function resize() {
      const w = el.clientWidth;
      const h = el.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    // Drag to rotate
    let drag = false, lx = 0, ly = 0, rotX = 0, rotY = 0, autoY = 0;
    el.addEventListener('mousedown', e => { drag = true; lx = e.clientX; ly = e.clientY; });
    window.addEventListener('mouseup',   () => (drag = false));
    window.addEventListener('mousemove', e => {
      if (!drag) return;
      rotY += (e.clientX - lx) * 0.01;
      rotX += (e.clientY - ly) * 0.006;
      rotX  = Math.max(-1.2, Math.min(1.2, rotX));
      lx = e.clientX; ly = e.clientY;
    });

    // RNG for per-frame firing
    function sRNG2(s) {
      return () => {
        s = Math.imul(s ^ (s >>> 15), s | 1);
        s ^= s + Math.imul(s ^ (s >>> 7), s | 61);
        return ((s ^ (s >>> 14)) >>> 0) / 2 ** 32;
      };
    }

    let t = 0, raf;
    function frame() {
      raf = requestAnimationFrame(frame);
      t += 0.016;

      const st    = stateRef.current;
      const bias  = st.fw_bias  ?? 0;
      const rR    = st.circuits?.reward?.rate  ?? 0;
      const rE    = st.circuits?.escape?.rate  ?? 0;
      const rO    = st.circuits?.orient?.rate  ?? 0;
      const pulse = 0.5 + 0.5 * Math.sin(t * 3.5);
      const rng2  = sRNG2(Math.floor(t * 18) & 0xfffff);
      const bL    = Math.max(0, -bias);
      const bR    = Math.max(0,  bias);

      neurons.forEach((n, i) => {
        let rate, c;
        if (n.ci === 'R') { rate = rR * 6 + (n.x > 0 ? bR : bL) * 0.8; c = CR; }
        else if (n.ci === 'E') { rate = rE * 6; c = CE; }
        else { rate = rO * 5 + 0.01; c = CO; }

        const on = rng2() < rate;
        const b  = on ? (n.base + (0.9 + 0.1 * pulse) * Math.min(rate * 2, 1)) : n.base;
        const bs = Math.min(b, 1);
        col[i * 3]     = c.r * bs;
        col[i * 3 + 1] = c.g * bs;
        col[i * 3 + 2] = c.b * bs;
        sz[i] = on ? 4.0 : 1.6;
      });

      geo.attributes.pColor.needsUpdate = true;
      geo.attributes.pSize.needsUpdate  = true;

      if (!drag) autoY += 0.003;
      points.rotation.x = rotX;
      points.rotation.y = rotY + autoY;
      renderer.render(scene, camera);
    }
    frame();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      renderer.dispose();
    };
  }, []);

  return <canvas ref={ref} style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }} />;
}
