import { useEffect, useRef } from 'react';
import * as THREE from 'three';

// Katamari palette para a mosca
const K_MAGENTA = 0xFF3F8E;
const K_MAGENTA_DIM = 0x7a1a42;
const K_CORAL   = 0xFF5A4E;
const K_LILAC   = 0xC778DD;
const K_BODY    = 0x2a1020;
const K_BODY2   = 0x3d1830;
const K_BODY3   = 0x1a0c14;

function makeMat(color, opacity = 1, wire = false) {
  return new THREE.MeshBasicMaterial({
    color, transparent: opacity < 1, opacity, wireframe: wire,
    side: THREE.DoubleSide,
  });
}

function buildFly(scene) {
  const parts = {};

  const headGeo   = new THREE.SphereGeometry(2.8, 16, 12);
  const thoraxGeo = new THREE.SphereGeometry(3.8, 16, 12);
  thoraxGeo.scale(1, 0.85, 1.1);
  const abdomenGeo = new THREE.SphereGeometry(3.2, 16, 12);
  abdomenGeo.scale(0.85, 1.5, 0.85);

  const head    = new THREE.Mesh(headGeo,   makeMat(K_BODY2));
  const thorax  = new THREE.Mesh(thoraxGeo, makeMat(K_BODY));
  const abdomen = new THREE.Mesh(abdomenGeo, makeMat(K_BODY3));

  head.position.set(0, 9, 0);
  thorax.position.set(0, 4, 0);
  abdomen.position.set(0, -3, 0);

  // Wireframe overlay em magenta suave
  [headGeo, thoraxGeo, abdomenGeo].forEach((g, i) => {
    const wf = new THREE.Mesh(g.clone(), makeMat(K_MAGENTA, 0.12, true));
    wf.position.copy([head, thorax, abdomen][i].position);
    scene.add(wf);
  });

  scene.add(head, thorax, abdomen);

  // Olhos
  const eyeGeo = new THREE.SphereGeometry(1.3, 12, 10);
  const eyeL   = new THREE.Mesh(eyeGeo, makeMat(K_MAGENTA_DIM));
  const eyeR   = new THREE.Mesh(eyeGeo.clone(), makeMat(K_MAGENTA_DIM));
  eyeL.position.set(-1.8, 10.2, 2.0);
  eyeR.position.set( 1.8, 10.2, 2.0);
  scene.add(eyeL, eyeR);

  // Anéis nos olhos em magenta
  [eyeL, eyeR].forEach(eye => {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.4, 0.12, 8, 24),
      makeMat(K_MAGENTA, 0.55)
    );
    ring.position.copy(eye.position);
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);
  });

  // Antenas
  parts.antennae = [];
  [[-1], [1]].forEach(([sx]) => {
    const points = [
      new THREE.Vector3(sx * 1.0, 11.5, 2.2),
      new THREE.Vector3(sx * 2.2, 13.5, 3.0),
      new THREE.Vector3(sx * 3.0, 14.8, 2.0),
    ];
    const curve = new THREE.CatmullRomCurve3(points);
    const geo   = new THREE.TubeGeometry(curve, 8, 0.15, 6, false);
    const ant   = new THREE.Mesh(geo, makeMat(K_BODY2));
    scene.add(ant);

    const tip = new THREE.Mesh(
      new THREE.SphereGeometry(0.45, 8, 8),
      makeMat(K_CORAL, 0.9)
    );
    tip.position.copy(points[2]);
    scene.add(tip);
    parts.antennae.push({ ant, tip, base: points[0].clone() });
  });

  // Asas
  function makeWing(sx) {
    const shape = new THREE.Shape();
    shape.moveTo(0, 0);
    shape.bezierCurveTo(sx * 2, 3,   sx * 10, 5,  sx * 14, 2);
    shape.bezierCurveTo(sx * 16, 0,  sx * 14, -4, sx * 8, -5);
    shape.bezierCurveTo(sx * 4, -4,  sx * 1, -2,  0, 0);

    const geo  = new THREE.ShapeGeometry(shape);
    const mesh = new THREE.Mesh(geo, makeMat(K_LILAC, 0.08));

    // Veia
    const veinPts = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(sx * 14, 1, 0)];
    const veinGeo  = new THREE.BufferGeometry().setFromPoints(veinPts);
    const veinLine = new THREE.Line(veinGeo, new THREE.LineBasicMaterial({ color: K_MAGENTA, transparent: true, opacity: 0.25 }));
    mesh.add(veinLine);

    // Borda
    const edgePts  = shape.getPoints(32).map(p => new THREE.Vector3(p.x, p.y, 0));
    const edgeGeo  = new THREE.BufferGeometry().setFromPoints(edgePts);
    const edgeLine = new THREE.Line(edgeGeo, new THREE.LineBasicMaterial({ color: K_MAGENTA, transparent: true, opacity: 0.3 }));
    mesh.add(edgeLine);

    return mesh;
  }

  const wingPivotL = new THREE.Object3D();
  const wingPivotR = new THREE.Object3D();
  wingPivotL.position.set(-3.8, 4.5, 0);
  wingPivotR.position.set( 3.8, 4.5, 0);
  wingPivotL.add(makeWing(-1));
  wingPivotR.add(makeWing( 1));
  scene.add(wingPivotL, wingPivotR);
  parts.wingPivotL = wingPivotL;
  parts.wingPivotR = wingPivotR;

  // Pernas
  parts.legs = [];
  const legDefs = [
    { y: 5.5,  zOff: 1.5 },
    { y: 3.5,  zOff: 0.5 },
    { y: 1.5,  zOff: -0.5 },
  ];

  legDefs.forEach(({ y, zOff }) => {
    [-1, 1].forEach(sx => {
      const coxa   = new THREE.Vector3(sx * 3.5, y,        zOff);
      const femur  = new THREE.Vector3(sx * 7.0, y - 2,    zOff);
      const tibia  = new THREE.Vector3(sx * 9.5, y - 5,    zOff);
      const tarsus = new THREE.Vector3(sx * 10.5, y - 7.5, zOff + 0.5);

      const segs = [[coxa, femur], [femur, tibia], [tibia, tarsus]];
      const meshes = segs.map(([a, b]) => {
        const geo  = new THREE.BufferGeometry().setFromPoints([a, b]);
        const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: K_BODY2 }));
        scene.add(line);
        return { line, geo, a: a.clone(), b: b.clone() };
      });

      parts.legs.push({ meshes, sx, base: { coxa, femur, tibia, tarsus } });
    });
  });

  // Halteres em coral
  parts.halteres = [];
  [-1, 1].forEach(sx => {
    const geo  = new THREE.SphereGeometry(0.5, 8, 6);
    const mesh = new THREE.Mesh(geo, makeMat(K_CORAL, 0.65));
    mesh.position.set(sx * 3.5, 2, 0.5);
    scene.add(mesh);
    parts.halteres.push(mesh);
  });

  // Anéis de segmentos do abdomen
  for (let i = 0; i < 5; i++) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(3.2 - i * 0.25, 0.12, 6, 20),
      makeMat(K_MAGENTA_DIM, 0.45)
    );
    ring.position.set(0, -1.5 - i * 1.3, 0);
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);
  }

  return parts;
}

export default function FlyBody3D({ state }) {
  const canvasRef  = useRef(null);
  const stateRef   = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;

    const renderer = new THREE.WebGLRenderer({ canvas: el, antialias: true, alpha: true });
    renderer.setClearColor(0, 0);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 500);
    camera.position.set(0, 2, 42);
    camera.lookAt(0, 2, 0);

    const parts = buildFly(scene);

    function resize() {
      const w = el.clientWidth, h = el.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    let t = 0, raf;

    function frame() {
      raf = requestAnimationFrame(frame);
      t += 0.016;

      const st   = stateRef.current;
      const mag  = st.mag       ?? 0;
      const bias = st.fw_bias   ?? 0;
      const esc  = st.escape_active ?? false;

      const wFreq  = 8 + mag * 14;
      const wAmp   = 0.35 + mag * 0.5;
      const wAngle = Math.sin(t * wFreq) * wAmp;

      if (esc) {
        parts.wingPivotL.rotation.z =  0.9 + Math.sin(t * 25) * 0.15;
        parts.wingPivotR.rotation.z = -0.9 - Math.sin(t * 25) * 0.15;
      } else {
        parts.wingPivotL.rotation.z =  wAngle;
        parts.wingPivotR.rotation.z = -wAngle;
      }

      parts.legs.forEach(({ meshes, sx, base }, legIdx) => {
        const pi = Math.floor(legIdx / 2);
        const phase = t * (4 + mag * 8) + pi * (Math.PI * 2 / 3) + (sx < 0 ? Math.PI : 0);
        const lift  = Math.max(0, Math.sin(phase)) * (1.5 + mag * 1.5);
        const swing = Math.sin(phase) * (0.8 + mag * 0.8);

        const coxa   = base.coxa.clone();
        const femur  = base.femur.clone().add(new THREE.Vector3(sx * swing * 0.4, lift * 0.6, 0));
        const tibia  = base.tibia.clone().add(new THREE.Vector3(sx * swing * 0.8, lift, 0));
        const tarsus = base.tarsus.clone().add(new THREE.Vector3(sx * swing, lift * 0.3, 0));

        [[coxa, femur], [femur, tibia], [tibia, tarsus]].forEach(([a, b], si) => {
          meshes[si].geo.setFromPoints([a, b]);
        });
      });

      scene.rotation.z = bias * -0.15;
      scene.position.y = Math.sin(t * 1.2) * 0.3;
      parts.halteres.forEach((h, i) => {
        h.position.y = 2 + Math.sin(t * wFreq * 0.5 + i * Math.PI) * 0.3;
      });

      renderer.render(scene, camera);
    }

    frame();
    return () => { cancelAnimationFrame(raf); ro.disconnect(); renderer.dispose(); };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  );
}