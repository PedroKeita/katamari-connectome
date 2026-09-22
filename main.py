"""
Arquitetura corrigida:
  - SensoryEncoder gera L/C/R (rápido, confiável — base do movimento)
  - FlyWire roda em thread separada com n_steps=30, atualiza a cada ~5 frames
  - Resultado FlyWire modula dopamine e turn_sensitivity do integrador
  - Se FlyWire não carregou, comportamento idêntico ao v0.4

Teclas debug: Q=sair  P=pausar  D=dopamine  F=toggle FlyWire modulation
"""

import argparse
import logging
import threading
import time
import os

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_ITEMS_GUARD = 60
DATA_DIR = "data"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",    action="store_true")
    p.add_argument("--debug",      action="store_true")
    p.add_argument("--fps",        type=int,   default=30)
    p.add_argument("--monitor",    type=int,   default=2)
    p.add_argument("--dopamine",   type=float, default=1.0)
    p.add_argument("--no-flywire", action="store_true")
    p.add_argument("--escape", action="store_true",
                   help="Ativa EscapeCircuit (wall detector + SHIFT+CTRL)")
    return p.parse_args()


# ------------------------------------------------------------------
# FlyWire background runner
# ------------------------------------------------------------------

class FlyWireRunner:
    """
    Roda os circuitos FlyWire em thread separada.
    O loop principal lê .lateral_bias a cada frame.

    lateral_bias : float em [-1, 1]
        > 0 = bias para direita
        < 0 = bias para esquerda
        0   = neutro
    """

    def __init__(self, circuits: dict):
        self.circuits      = circuits   # {"reward": FlyWireCircuit, ...}
        self.lateral_bias  = 0.0        # resultado mais recente
        self.active        = True
        self._lock         = threading.Lock()
        self._left_str     = 0.0
        self._right_str    = 0.0
        self._thread       = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update_input(self, left: float, right: float):
        """Atualiza o estímulo de entrada (chamado pelo loop principal)."""
        with self._lock:
            self._left_str  = float(left)
            self._right_str = float(right)

    def _run(self):
        while self.active:
            with self._lock:
                ls = self._left_str
                rs = self._right_str

            if ls + rs < 0.01:
                with self._lock:
                    self.lateral_bias = 0.0
                time.sleep(0.05)
                continue

            try:
                # Reward: ORNs→PNs→KCs→PAMs com n_steps=30
                L_r, C_r, R_r = self.circuits["reward"].stimulate_lateral(
                    left_strength  = ls * 3.0,
                    right_strength = rs * 3.0,
                    n_steps        = 30,
                )

                # Orientation: DNs lateralizados
                L_o, C_o, R_o = self.circuits["orient"].stimulate_lateral(
                    left_strength  = ls * 2.0,
                    right_strength = rs * 2.0,
                    n_steps        = 30,
                )

                # Bias = diferença R-L ponderada pelos dois circuitos
                bias_r = R_r - L_r   # >0 = mais PAM direito ativo
                bias_o = R_o - L_o   # >0 = mais DN direito ativo
                bias   = 0.7 * bias_r + 0.3 * bias_o

                with self._lock:
                    self.lateral_bias = float(np.clip(bias, -1.0, 1.0))

            except Exception as e:
                logger.debug(f"FlyWire thread erro: {e}")

            time.sleep(0.05)   # ~20Hz

    def stop(self):
        self.active = False


def load_flywire(data_dir: str):
    try:
        from brain.flywire_loader  import FlyWireLoader
        from brain.flywire_circuit import FlyWireCircuit

        if not os.path.exists(os.path.join(data_dir, "neuron_annotations.tsv")):
            return None

        logger.info("Carregando circuitos FlyWire v783...")
        loader   = FlyWireLoader(data_dir=data_dir, min_weight=3)
        reward_c = loader.load_reward_circuit()
        escape_c = loader.load_escape_circuit()
        orient_c = loader.load_orientation_circuit()
        logger.info(f"  {reward_c.summary()}")
        logger.info(f"  {escape_c.summary()}")
        logger.info(f"  {orient_c.summary()}")

        return {
            "reward": FlyWireCircuit(reward_c),
            "escape": FlyWireCircuit(escape_c),
            "orient": FlyWireCircuit(orient_c),
        }
    except Exception as e:
        logger.warning(f"FlyWire não carregou: {e}")
        return None


def load_visual_circuit(data_dir: str):
    """Carrega o sistema visual completo em thread separada."""
    try:
        from brain.visual_loader  import VisualLoader
        from brain.visual_circuit import VisualCircuit

        if not os.path.exists(os.path.join(data_dir, "neuron_annotations.tsv")):
            return None

        logger.info("Carregando sistema visual FlyWire (R1-6 → L → T4/T5 → LPLC2 → DNp01)...")
        loader  = VisualLoader(data_dir=data_dir, min_weight=3)
        circuit = loader.load_visual_circuit()

        vc = VisualCircuit(circuit)
        # Passa as posições dos fotorreceptores calculadas pelo loader
        if hasattr(circuit, '_r_positions'):
            vc._r_positions = circuit._r_positions

        return vc
    except Exception as e:
        logger.warning(f"Sistema visual não carregou: {e}")
        return None





# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    args = parse_args()

    from vision.capture        import ScreenCapture
    from vision.detect         import detect_items, draw_detections, CollectionDetector
    from vision.visual_field   import items_to_visual_field
    from vision.pause_detector import PauseDetector
    from vision.wall_detector  import WallDetector
    from brain.sensory_encoder import SensoryEncoder
    from brain.reward          import RewardCircuit
    from control.integrator    import CircuitIntegrator
    from control.gamepad       import GamepadController

    logger.info("=== FLY BRAIN KATAMARI v0.5 ===")

    fw_circuits = None if args.no_flywire else load_flywire(DATA_DIR)
    fw_runner   = FlyWireRunner(fw_circuits) if fw_circuits else None
    use_flywire = fw_runner is not None
    logger.info(f"FlyWire: {'ativo (thread background)' if use_flywire else 'desativado'}")

    # Sistema visual completo (R1-6 → L → T4/T5 → LPLC2 → DNp01)
    visual_circuit = None
    if args.escape and not args.no_flywire:
        visual_circuit = load_visual_circuit(DATA_DIR)
        if visual_circuit:
            logger.info("Sistema visual: ativo (46k neurônios em thread background)")

    from brain.neural_server  import NeuralServer
    from brain.session_logger import SessionLogger
    import webbrowser, pathlib

    session_log = SessionLogger()
    logger.info(f"Sessão: {session_log.session_id}")

    neural_server = NeuralServer(port=8765)
    neural_server.start()

    viz_path = pathlib.Path(__file__).parent / "visualizer.html"
    if viz_path.exists():
        webbrowser.open(viz_path.as_uri())
        logger.info(f"Visualizador aberto: {viz_path}")

    capture      = ScreenCapture(monitor=args.monitor)
    encoder      = SensoryEncoder()
    circuit_lif  = RewardCircuit()
    integrator   = CircuitIntegrator(dopamine=args.dopamine)
    gamepad      = GamepadController(dry_run=args.dry_run)
    col_detect   = CollectionDetector()
    pause_detect = PauseDetector()
    wall_detect  = WallDetector()

    # Estado do escape circuit
    _escape_active     = False
    _escape_frames     = 0
    ESCAPE_HOLD_FRAMES = 12      # ~400ms a 30fps — tempo suficiente para o quick turn
    STAGNATION_LIMIT   = 180     # frames sem coleta para ativar escape (~6s a 30fps)
    _frames_since_col  = 0       # frames desde a última coleta

    # Detector de freeze por valores L/C/R
    _last_lcr         = (0.0, 0.0, 0.0)
    _lcr_freeze_count = 0
    LCR_FREEZE_LIMIT  = 60   # 2s a 30fps — se L/C/R idênticos por 2s = jogo congelado

    dopamine              = args.dopamine
    focus_patience        = 0
    PATIENCE_LIMIT        = 90
    skip_focus            = 0
    total_collected       = 0
    last_collection_frame = -999
    fw_bias               = 0.0

    frame_n   = 0
    fps_t     = time.time()
    fps_disp  = 0.0
    interval  = 1.0 / args.fps
    paused_ui = False

    # --- Hotkeys globais (funcionam independente de qual janela está em foco) ---
    # F1 = pausar/retomar   F2 = dopamine toggle   F3 = FlyWire toggle   F4 = sair
    _stop_flag = threading.Event()

    if args.debug:
        from pynput import keyboard as _kb

        def _on_press(key):
            nonlocal paused_ui, use_flywire
            try:
                if key == _kb.Key.f1:
                    paused_ui = not paused_ui
                    logger.info(f"{'PAUSADO' if paused_ui else 'Retomado'} (F1)")
                elif key == _kb.Key.f2:
                    args.dopamine = 2.0 if args.dopamine == 1.0 else 1.0
                    logger.info(f"Dopamine base → {args.dopamine} (F2)")
                elif key == _kb.Key.f3:
                    use_flywire = (not use_flywire) and (fw_runner is not None)
                    logger.info(f"FlyWire {'ativo' if use_flywire else 'desativado'} (F3)")
                elif key == _kb.Key.f4:
                    logger.info("Encerrando (F4)")
                    _stop_flag.set()
            except Exception:
                pass

        _listener = _kb.Listener(on_press=_on_press)
        _listener.start()
        logger.info("Hotkeys globais: F1=pausar  F2=dopamine  F3=FlyWire  F4=sair")

        # Descobre a posição do monitor 2 via mss
        import mss as _mss
        with _mss.mss() as _sct:
            _monitors = _sct.monitors
            if len(_monitors) > 2:
                _mon2 = _monitors[2]
                _win_x = _mon2["left"]
                _win_y = _mon2["top"]
                _win_w = min(_mon2["width"],  1280)
                _win_h = min(_mon2["height"], 720)
            else:
                _win_x, _win_y, _win_w, _win_h = 80, 80, 1280, 720

        cv2.namedWindow("Fly Brain v0.5", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Fly Brain v0.5", _win_w, _win_h)
        cv2.moveWindow("Fly Brain v0.5", _win_x, _win_y)

    logger.info(f"Monitor={args.monitor}  FPS={args.fps}  dry-run={args.dry_run}")

    if not args.dry_run:
        logger.info("Clique na janela do Katamari nos próximos 4 segundos...")
        for i in range(4, 0, -1):
            logger.info(f"  Iniciando em {i}s...")
            time.sleep(1)
        logger.info("GO!")

    try:
        while not _stop_flag.is_set():
            t0 = time.time()
            frame   = capture.capture()
            h, w    = frame.shape[:2]
            frame_n += 1

            if paused_ui:
                logger.info(f"STOP: paused_ui frame={frame_n}")
                gamepad.reset()
                if args.debug:
                    vis = frame.copy()
                    cv2.putText(vis, "PAUSADO (P)", (w//2-100, h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,200), 3)
                    cv2.imshow("Fly Brain v0.5", vis)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), 27): break
                    if key == ord('p'): paused_ui = False
                time.sleep(0.05); continue

            if pause_detect.check(frame):
                logger.info(f"STOP: pause_detect ativado frame={frame_n}")
                gamepad.reset()
                col_detect.reset()
                if args.debug:
                    vis = frame.copy()
                    cv2.putText(vis, "JOGO PAUSADO", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,140,255), 2)
                    cv2.imshow("Fly Brain v0.5", vis)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), 27): break
                    if key == ord('p'): paused_ui = True
                elapsed = time.time() - t0
                if interval - elapsed > 0: time.sleep(interval - elapsed)
                continue

            items_raw, _ = detect_items(frame)
            if len(items_raw) > MAX_ITEMS_GUARD:
                logger.info(f"STOP: MAX_ITEMS_GUARD itens={len(items_raw)} frame={frame_n}")
                gamepad.reset()
                elapsed = time.time() - t0
                if interval - elapsed > 0: time.sleep(interval - elapsed)
                continue
            items = items_raw

            just_collected = col_detect.check(frame)
            if just_collected:
                total_collected      += 1
                focus_patience        = 0
                skip_focus            = 0
                last_collection_frame = frame_n
                dopamine = min(args.dopamine * 1.6, 2.0)
                integrator.dopamine = dopamine
                logger.info(f"COLETADO #{total_collected}  frame={frame_n}")
                session_log.log_event(frame_n, "COLETADO", f"#{total_collected}")
            else:
                if dopamine > args.dopamine:
                    dopamine = max(dopamine - 0.04, args.dopamine)
                    integrator.dopamine = dopamine

            if items:
                focus_patience += 1
                if focus_patience >= PATIENCE_LIMIT:
                    focus_patience = 0
                    skip_focus = min(skip_focus + 1, len(items) - 1)
                    logger.info(f"Pulando para candidato #{skip_focus}")
                    session_log.log_event(frame_n, "PULANDO", f"#{skip_focus}")
            else:
                focus_patience = 0; skip_focus = 0

            if skip_focus > 0 and len(items) > skip_focus:
                items = items[skip_focus:] + items[:skip_focus]

            # --- Campo visual → L/C/R (base do movimento) ---
            visual_field        = items_to_visual_field(items, w, h)
            left, center, right = encoder.encode(visual_field)

            # Detector de freeze: se L/C/R não mudaram por LCR_FREEZE_LIMIT frames
            lcr_now = (round(left, 3), round(center, 3), round(right, 3))
            if lcr_now == _last_lcr and lcr_now != (0.0, 0.0, 0.0):
                _lcr_freeze_count += 1
            else:
                _lcr_freeze_count = 0
                _last_lcr = lcr_now

            if _lcr_freeze_count >= LCR_FREEZE_LIMIT:
                gamepad.reset()
                elapsed = time.time() - t0
                if interval - elapsed > 0: time.sleep(interval - elapsed)
                continue

            # --- FlyWire: alimenta a thread e lê o bias mais recente ---
            if use_flywire and (left + right) > 0.05:
                fw_runner.update_input(left, right)
                fw_bias = fw_runner.lateral_bias

                # O bias FlyWire ajusta sutilmente o dx
                # bias > 0 = PAMs direitos mais ativos → empurra para direita
                # bias < 0 = PAMs esquerdos mais ativos → empurra para esquerda
                fw_bias_scaled = 0.0  # desativado — viés anatômico fêmea causa giro constante
            else:
                fw_bias_scaled = 0.0

            # --- Circuito LIF genérico (sempre roda para manter o spike) ---
            spikes = circuit_lif.step(left, center, right)

            # --- Integrador: L/C/R base + bias FlyWire ---
            # O bias ajusta o dx sem sobrescrever a magnitude
            output = integrator.integrate(left, center, right, spikes)

            # Aplica bias FlyWire ao dx resultante
            if use_flywire and abs(fw_bias_scaled) > 0.01:
                new_x = float(np.clip(output.x + fw_bias_scaled, -1.0, 1.0))
                from control.integrator import ControlOutput
                output = ControlOutput(
                    x=new_x,
                    y=output.y,
                    magnitude=output.magnitude
                )

            # --- EscapeCircuit: LPLC2 → DNp01 → SHIFT+CTRL ---
            # Ativa quando há estagnação (sem coleta por STAGNATION_LIMIT frames)
            # Biologicamente: baixa dopamina → sistema de escape assume controle

            escape_rate = 0.0

            if just_collected:
                _frames_since_col = 0
            else:
                _frames_since_col += 1

            # Alimenta o circuito visual com o frame atual
            if visual_circuit:
                visual_circuit.push_frame(frame)
                visual_escape_bias = visual_circuit.escape_bias
            else:
                visual_escape_bias = 0.0

            if _escape_active:
                _escape_frames -= 1
                if _escape_frames <= 0:
                    _escape_active = False
                    _frames_since_col = 0
                    gamepad.release_escape()
                    logger.info("Escape: Giant Fiber desativado — nova direção")
                escape_rate = 0.8
            elif args.escape:
                # Circuito visual: DNp01 dispara quando detecta looming
                visual_threat = visual_circuit and abs(visual_escape_bias) > 0.35
                # Estagnação: sempre ativo como fallback biológico
                # (baixa dopamina → sistema de escape assume controle)
                stagnation_threat = _frames_since_col >= STAGNATION_LIMIT

                if visual_threat or stagnation_threat:
                    _escape_active = True
                    _escape_frames = ESCAPE_HOLD_FRAMES
                    gamepad.trigger_escape()
                    if visual_threat:
                        trigger = f"visual bias={visual_escape_bias:+.2f}"
                    else:
                        trigger = f"estagnação={_frames_since_col} frames"
                    logger.info(f"ESCAPE! {trigger} → Giant Fiber ativado")
                    session_log.log_event(frame_n, "ESCAPE", trigger)
                    escape_rate = 1.0

            # Durante escape: só SHIFT+CTRL, sem teclas de movimento
            if not _escape_active:
                gamepad.send(output)

            neural_server.push({
                "escape_active": _escape_active,
                "threat_level":  round(float(_frames_since_col) / STAGNATION_LIMIT, 3),
                "fw_bias":      round(float(fw_bias), 4),
                "left":         round(float(left),    3),
                "center":       round(float(center),  3),
                "right":        round(float(right),   3),
                "mag":          round(float(output.magnitude), 3),
                "collected":    total_collected,
                "pressed_keys": list(gamepad._pressed),
                "circuits": {
                    "reward": {"rate": round(abs(float(fw_bias))*0.05, 4)},
                    "escape": {"rate": round(escape_rate, 3)},
                    "orient": {"rate": round(abs(float(fw_bias))*0.02, 4)},
                },
            })

            # Logging científico
            session_log.log_frame(
                frame        = frame_n,
                fps          = fps_disp,
                left         = float(left),
                center       = float(center),
                right        = float(right),
                x            = float(output.x),
                magnitude    = float(output.magnitude),
                fw_bias      = float(fw_bias),
                visual_bias  = float(visual_escape_bias) if visual_circuit else 0.0,
                escape_active= _escape_active,
                dopamine     = dopamine,
                items        = len(items),
                skip_focus   = skip_focus,
                collected    = total_collected,
                reward_rate  = abs(float(fw_bias)) * 0.05,
                escape_rate  = escape_rate,
                orient_rate  = abs(float(fw_bias)) * 0.02,
            )

            if frame_n % args.fps == 0:
                now = time.time()
                fps_disp = args.fps / (now - fps_t)
                fps_t = now
                fw_str = f"  fw_bias={fw_bias:+.2f}" if use_flywire else ""
                logger.info(
                    f"FPS={fps_disp:.1f}  itens={len(items):2d}"
                    f"  L={left:.2f} C={center:.2f} R={right:.2f}"
                    f"  x={output.x:+.2f} mag={output.magnitude:.2f}"
                    f"  coletados={total_collected}{fw_str}"
                )

            if args.debug:
                # Feed do jogo com bounding boxes verdes
                vis = draw_detections(frame, items)

                # Flash de coleta
                if frame_n - last_collection_frame < 45:
                    cv2.putText(vis, f"COLETADO #{total_collected}",
                                (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 0, 0), 4, cv2.LINE_AA)
                    cv2.putText(vis, f"COLETADO #{total_collected}",
                                (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 220, 80), 2, cv2.LINE_AA)

                # HUD minimalista
                fw_str = f"fw={fw_bias:+.2f}" if use_flywire else "LIF"
                hud = [
                    f"FPS {fps_disp:.0f}  itens {len(items):2d}  coletados {total_collected}",
                    f"L={left:.2f} C={center:.2f} R={right:.2f}  mag={output.magnitude:.2f}",
                    f"x={output.x:+.2f}  dopa={dopamine:.1f}  {fw_str}",
                ]
                for i, line in enumerate(hud):
                    y = 22 + i * 22
                    cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.48, (0, 0, 0), 3, cv2.LINE_AA)
                    cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.48, (200, 255, 200), 1, cv2.LINE_AA)

                cv2.imshow("Fly Brain v0.5", vis)
                cv2.waitKey(1)

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0: time.sleep(sleep)

    except KeyboardInterrupt:
        logger.info("Interrompido.")
    finally:
        neural_server.stop()
        if visual_circuit: visual_circuit.stop()
        if fw_runner: fw_runner.stop()
        gamepad.close()
        capture.close()
        if args.debug:
            try: _listener.stop()
            except Exception: pass
            cv2.destroyAllWindows()
        logger.info(f"Total coletados: {total_collected}")
        summary = session_log.close()
        logger.info(f"Sessão salva: {summary['frame_file']}")
        logger.info(f"  {summary['frames']} frames · {summary['events']} eventos · {summary['duration_s']}s")
        logger.info("=== ENCERRADO ===")


if __name__ == "__main__":
    main()