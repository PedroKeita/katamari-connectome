import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';

const MAT = {
  body:     new THREE.MeshPhongMaterial({ color: 0xac592a, shininess: 40, specular: 0x442211 }),
  red:      new THREE.MeshPhongMaterial({ color: 0xcc0708, shininess: 50, specular: 0x441111 }),
  ocelli:   new THREE.MeshPhongMaterial({ color: 0x200c04, shininess: 80 }),
  black:    new THREE.MeshPhongMaterial({ color: 0x111111, shininess: 55 }),
  lower:    new THREE.MeshPhongMaterial({ color: 0xcc9c62, shininess: 35 }),
  brown:    new THREE.MeshPhongMaterial({ color: 0x341407, shininess: 40 }),
  membrane: new THREE.MeshPhongMaterial({
    color: 0x8aaece, shininess: 90, specular: 0xaaccee,
    transparent: true, opacity: 0.45, side: THREE.DoubleSide,
  }),
};

function matForFile(name) {
  if (name.includes('_membrane'))                                 return MAT.membrane;
  if (name.includes('_red'))                                      return MAT.red;
  if (name.includes('_ocelli'))                                   return MAT.ocelli;
  if (name.includes('_black'))                                    return MAT.black;
  if (name.includes('bristle-brown') || name.includes('_brown')) return MAT.brown;
  if (name.includes('_lower'))                                    return MAT.lower;
  return MAT.body;
}

function partRole(name) {
  if (name.startsWith('wing_left'))     return 'wingL';
  if (name.startsWith('wing_right'))    return 'wingR';
  if (name.startsWith('haltere_left'))  return 'haltereL';
  if (name.startsWith('haltere_right')) return 'haltereR';
  if (name.startsWith('abdomen'))       return 'abdomen';
  if (name.startsWith('antenna'))       return 'antenna';
  return 'static';
}

const FILES = [
  'abdomen_1_body','abdomen_1_lower','abdomen_2_body','abdomen_2_lower',
  'abdomen_3_body','abdomen_3_lower','abdomen_4_body','abdomen_4_lower',
  'abdomen_5_body','abdomen_5_lower','abdomen_6_body','abdomen_6_lower',
  'abdomen_7_body','abdomen_7_lower','abdomen_8_body',
  'antenna_left_black','antenna_left_body',
  'antenna_right_black','antenna_right_body',
  'coxa_T1_left_body','coxa_T1_right_body',
  'coxa_T2_left_body','coxa_T2_right_body',
  'coxa_T3_left_body','coxa_T3_right_body',
  'femur_T1_left_body','femur_T1_right_body',
  'femur_T2_left_body','femur_T2_right_body',
  'femur_T3_left_body','femur_T3_right_body',
  'haltere_left_body','haltere_right_body',
  'haustellum_black','haustellum_body',
  'head_black','head_body','head_ocelli','head_red',
  'labrum_left_lower','labrum_right_lower',
  'rostrum_body','rostrum_bristle-brown',
  'tarsal_claw_T1_left_brown','tarsal_claw_T1_right_brown',
  'tarsal_claw_T2_left_brown','tarsal_claw_T2_right_brown',
  'tarsal_claw_T3_left_brown','tarsal_claw_T3_right_brown',
  'tarsus_T1_1_left_body','tarsus_T1_1_right_body',
  'tarsus_T1_2_left_body','tarsus_T1_2_right_body',
  'tarsus_T1_3_left_body','tarsus_T1_3_right_body',
  'tarsus_T1_4_left_body','tarsus_T1_4_right_body',
  'tarsus_T2_1_left_body','tarsus_T2_1_right_body',
  'tarsus_T2_2_left_body','tarsus_T2_2_right_body',
  'tarsus_T2_3_left_body','tarsus_T2_3_right_body',
  'tarsus_T2_4_left_body','tarsus_T2_4_right_body',
  'tarsus_T3_1_left_body','tarsus_T3_1_right_body',
  'tarsus_T3_2_left_body','tarsus_T3_2_right_body',
  'tarsus_T3_3_left_body','tarsus_T3_3_right_body',
  'tarsus_T3_4_left_body','tarsus_T3_4_right_body',
  'thorax_black','thorax_body',
  'tibia_T1_left_body','tibia_T1_right_body',
  'tibia_T2_left_body','tibia_T2_right_body',
  'tibia_T3_left_body','tibia_T3_right_body',
  'wing_left_brown','wing_left_membrane',
  'wing_right_brown','wing_right_membrane',
];

export default function FlyBody3D({ state, assetsPath = '/assets' }) {
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
    const camera = new THREE.PerspectiveCamera(40, 1, 0.001, 50);
    camera.position.set(0, -0.6, 0);
    camera.lookAt(0, 0, 0);

    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const lR = new THREE.DirectionalLight(0xffffff, 0.7); lR.position.set(0, -1, 1); scene.add(lR);
    const lL = new THREE.DirectionalLight(0xffffff, 0.45); lL.position.set(0, 1, 1); scene.add(lL);
    const lT = new THREE.DirectionalLight(0xffffff, 0.3); lT.position.set(0, 0, 2); scene.add(lT);

    function resize() {
      const w = el.clientWidth, h = el.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    const flyRoot  = new THREE.Group();
    const wingPivL = new THREE.Group();
    const wingPivR = new THREE.Group();
    const halPivL  = new THREE.Group();
    const halPivR  = new THREE.Group();

    // Sem offset — os OBJs já têm coordenadas absolutas corretas
    // A rotação anima em torno da origem onde as asas naturalmente se encaixam

    flyRoot.add(wingPivL, wingPivR, halPivL, halPivR);
    flyRoot.position.z = -0.12; // desloca a mosca para baixo na tela
    scene.add(flyRoot);

    const parts = { wingL: [], wingR: [], haltereL: [], haltereR: [] };
    const loader = new OBJLoader();

    FILES.forEach(name => {
      loader.load(
        `${assetsPath}/${name}.obj`,
        (obj) => {
          const mat  = matForFile(name);
          const role = partRole(name);
          obj.traverse(child => { if (child.isMesh) child.material = mat; });
          obj.scale.setScalar(0.1);
          if      (role === 'wingL')    { wingPivL.add(obj); parts.wingL.push(obj);    }
          else if (role === 'wingR')    { wingPivR.add(obj); parts.wingR.push(obj);    }
          else if (role === 'haltereL') { halPivL.add(obj);  parts.haltereL.push(obj); }
          else if (role === 'haltereR') { halPivR.add(obj);  parts.haltereR.push(obj); }
          else                          { flyRoot.add(obj); }
        },
        undefined,
        () => {}
      );
    });

    let drag = false, lx = 0, ly = 0;
    let rotX = 0, rotY = 0;

    const onDown = e => { drag = true; lx = e.clientX; ly = e.clientY; };
    const onUp   = () => (drag = false);
    const onMove = e => {
      if (!drag) return;
      rotY += (e.clientX - lx) * 0.012;
      rotX += (e.clientY - ly) * 0.007;
      rotX  = Math.max(-Math.PI, Math.min(Math.PI, rotX));
      lx = e.clientX; ly = e.clientY;
    };
    el.addEventListener('mousedown', onDown);
    window.addEventListener('mouseup',   onUp);
    window.addEventListener('mousemove', onMove);

    let t = 0, raf;
    function frame() {
      raf = requestAnimationFrame(frame);
      t += 0.016;

      const st  = stateRef.current;
      const mag = st.mag           ?? 0;
      const esc = st.escape_active ?? false;

      flyRoot.rotation.x = rotX;
      flyRoot.rotation.z = rotY;

      const wFreq = esc ? 28 : (8 + mag * 18);
      const wAmp  = esc ? 1.2 : (0.45 + mag * 0.65);
      const wSin  = Math.sin(t * wFreq) * wAmp;

      // Asas batem simétricas no eixo X (cima/baixo)
      // sem rotação Z que as jogava para lados errados
      wingPivL.rotation.x =  wSin;
      wingPivR.rotation.x =  wSin;

      halPivL.rotation.x = Math.sin(t * wFreq * 0.5 + Math.PI) * 0.3;
      halPivR.rotation.x = Math.sin(t * wFreq * 0.5)            * 0.3;

      renderer.render(scene, camera);
    }
    frame();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      el.removeEventListener('mousedown', onDown);
      window.removeEventListener('mouseup',   onUp);
      window.removeEventListener('mousemove', onMove);
      renderer.dispose();
    };
  }, [assetsPath]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }}
    />
  );
}