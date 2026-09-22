"""
main.py — Fly Brain Katamari  v0.6

Arquitetura:
  - SensoryEncoder gera L/C/R (rápido, confiável — base do movimento)
  - FlyWire roda em thread separada (~20Hz), modula lateral_bias
  - PPL / PCB / CX / VisualCircuit em threads background
  - GameState centraliza todo o estado mutável do loop
  - DebugHUD encapsula janela cv2 + hotkeys (só com --debug)

Uso:
  python main.py --monitor 1 --escape
  python main.py --debug --monitor 1 --escape
  python main.py --monitor 1 --no-flywire
"""

import argparse
import logging
import threading
import time
import pathlib
import webbrowser
from dataclasses import dataclass
from typing import Callable

import numpy as np

from brain.runners.flywire import FlyWireRunner
from brain.loaders import load_flywire, load_ppl, load_pcb, load_cx, load_visual_circuit
from brain.domain.game_state import GameState
from control.integrator import ControlOutput

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_ITEMS_GUARD = 60
DATA_DIR        = "data"


@dataclass(frozen=True)
class CircuitLoaders:
    """Dependências de carregamento usadas durante a composição da aplicação."""

    flywire: Callable[[str], object | None]
    ppl: Callable[[str], object | None]
    pcb: Callable[[str], object | None]
    cx: Callable[[str], object | None]
    visual: Callable[[str], object | None]


# ------------------------------------------------------------------
# Args
# ------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",    action="store_true")
    p.add_argument("--debug",      action="store_true")
    p.add_argument("--fps",        type=int,   default=30)
    p.add_argument("--monitor",    type=int,   default=2)
    p.add_argument("--dopamine",   type=float, default=1.0)
    p.add_argument("--no-flywire", action="store_true")
    p.add_argument("--escape",     action="store_true",
                   help="Ativa EscapeCircuit (LPLC2→DNp01 + fallback estagnação)")
    return p.parse_args()


# ------------------------------------------------------------------
# Bootstrap dos circuitos
# ------------------------------------------------------------------

def setup_circuits(args, data_dir: str = DATA_DIR,
                   loaders: CircuitLoaders | None = None):
    """Carrega todos os circuitos neurais e retorna runners prontos."""
    loaders = loaders or CircuitLoaders(
        flywire=load_flywire,
        ppl=load_ppl,
        pcb=load_pcb,
        cx=load_cx,
        visual=load_visual_circuit,
    )

    fw_runner      = None
    ppl_runner     = None
    pcb_runner     = None
    cx_runner      = None
    visual_circuit = None

    if not args.no_flywire:
        fw_circuits = loaders.flywire(data_dir)
        if fw_circuits:
            fw_runner = FlyWireRunner(fw_circuits)
            logger.info("FlyWire: ativo (thread background)")
        else:
            logger.info("FlyWire: desativado")

        ppl_runner = loaders.ppl(data_dir)
        if ppl_runner:
            logger.info("PPL: ativo (sinal aversivo em thread background)")

        pcb_runner = loaders.pcb(data_dir)
        if pcb_runner:
            logger.info("PCB: ativo (integração bilateral em thread background)")

        cx_runner = loaders.cx(data_dir)
        if cx_runner:
            logger.info("Complexo Central: ativo (bússola interna em thread background)")

        if args.escape:
            visual_circuit = loaders.visual(data_dir)
            if visual_circuit:
                logger.info("Sistema visual: ativo (46k neurônios em thread background)")

    return fw_runner, ppl_runner, pcb_runner, cx_runner, visual_circuit


# ------------------------------------------------------------------
# Aplicação de bias ao output
# ------------------------------------------------------------------

def apply_bias(output: ControlOutput, bias: float) -> ControlOutput:
    """Aplica um bias lateral ao ControlOutput se significativo."""
    if abs(bias) <= 0.01:
        return output
    new_x = float(np.clip(output.x + bias, -1.0, 1.0))
    return ControlOutput(x=new_x, y=output.y, magnitude=output.magnitude)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    args = parse_args()

    from vision.capture import ScreenCapture
    from vision.detection.items import detect_items, draw_detections, CollectionDetector
    from vision.models.visual_field import items_to_visual_field
    from vision.detection.pause import PauseDetector
    from vision.detection.walls import WallDetector
    from brain.domain.sensory_encoder import SensoryEncoder
    from brain.domain.reward import RewardCircuit
    from brain.runtime.neural_server import NeuralServer
    from brain.runtime.session_logger import SessionLogger

    logger.info("=== FLY BRAIN KATAMARI v0.6 ===")

    # --- Circuitos neurais ---
    fw_runner, ppl_runner, pcb_runner, cx_runner, visual_circuit = setup_circuits(args)
    use_flywire = fw_runner is not None

    # --- Infraestrutura ---
    session_log   = SessionLogger()
    logger.info(f"Sessão: {session_log.session_id}")

    neural_server = NeuralServer(port=8765)
    neural_server.start()

    viz_path = pathlib.Path(__file__).parent / "visualizer.html"
    if viz_path.exists():
        webbrowser.open(viz_path.as_uri())
        logger.info(f"Visualizador aberto: {viz_path}")

    # --- Componentes do loop ---
    from control.integrator import CircuitIntegrator
    from control.gamepad    import GamepadController

    capture      = ScreenCapture(monitor=args.monitor)
    encoder      = SensoryEncoder()
    circuit_lif  = RewardCircuit()
    integrator   = CircuitIntegrator(dopamine=args.dopamine)
    gamepad      = GamepadController(dry_run=args.dry_run)
    col_detect   = CollectionDetector()
    pause_detect = PauseDetector()
    wall_detect  = WallDetector()

    # --- Estado ---
    state      = GameState(base_dopamine=args.dopamine)
    _stop_flag = threading.Event()
    fps_t      = time.time()
    interval   = 1.0 / args.fps
    output     = ControlOutput(x=0.0, y=0.0, magnitude=0.0)

    # --- Debug HUD (só com --debug) ---
    hud = None
    if args.debug:
        from control.debug_hud import DebugHUD

        def _toggle_pause():
            state.paused_ui = not state.paused_ui
            logger.info(f"{'PAUSADO' if state.paused_ui else 'Retomado'} (F1)")

        def _toggle_dopamine():
            args.dopamine = 2.0 if args.dopamine == 1.0 else 1.0
            logger.info(f"Dopamine base → {args.dopamine} (F2)")

        def _toggle_flywire():
            nonlocal use_flywire
            use_flywire = (not use_flywire) and (fw_runner is not None)
            logger.info(f"FlyWire {'ativo' if use_flywire else 'desativado'} (F3)")

        hud = DebugHUD(
            monitor_idx        = args.monitor,
            stop_flag          = _stop_flag,
            on_pause_toggle    = _toggle_pause,
            on_dopamine_toggle = _toggle_dopamine,
            on_flywire_toggle  = _toggle_flywire,
        )

    logger.info(f"Monitor={args.monitor}  FPS={args.fps}  dry-run={args.dry_run}")

    if not args.dry_run:
        logger.info("Clique na janela do Katamari nos próximos 4 segundos...")
        for i in range(4, 0, -1):
            logger.info(f"  Iniciando em {i}s...")
            time.sleep(1)
        logger.info("GO!")

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------
    try:
        while not _stop_flag.is_set():
            t0 = time.time()
            frame = capture.capture()
            h, w  = frame.shape[:2]
            state.frame_n += 1

            # --- UI pausada ---
            if state.paused_ui:
                gamepad.reset()
                if hud and not hud.show_paused(frame):
                    break
                time.sleep(0.05)
                continue

            # --- Jogo pausado (detector de tela) ---
            if pause_detect.check(frame):
                gamepad.reset()
                col_detect.reset()
                if hud and not hud.show_game_paused(frame):
                    break
                _sleep(t0, interval)
                continue

            # --- Guard: muitos itens = frame inválido ---
            items_raw, _ = detect_items(frame)
            if len(items_raw) > MAX_ITEMS_GUARD:
                logger.debug(f"MAX_ITEMS_GUARD itens={len(items_raw)} frame={state.frame_n}")
                gamepad.reset()
                _sleep(t0, interval)
                continue
            items = items_raw

            # --- Coleta ---
            just_collected = col_detect.check(frame)
            if just_collected:
                state.on_collected()
                integrator.dopamine = state.dopamine
                logger.info(f"COLETADO #{state.total_collected}  frame={state.frame_n}")
                session_log.log_event(state.frame_n, "COLETADO", f"#{state.total_collected}")
            else:
                state.decay_dopamine()
                integrator.dopamine = state.dopamine

            # --- Foco / skip ---
            skipped = state.update_focus(bool(items), len(items))
            if skipped:
                logger.info(f"Pulando para candidato #{state.skip_focus}")
                session_log.log_event(state.frame_n, "PULANDO", f"#{state.skip_focus}")

            if state.skip_focus > 0 and len(items) > state.skip_focus:
                items = items[state.skip_focus:] + items[:state.skip_focus]

            # --- Sensory encoding → L/C/R ---
            visual_field        = items_to_visual_field(items, w, h)
            left, center, right = encoder.encode(visual_field)

            # --- Freeze detector ---
            if state.check_freeze(left, center, right):
                gamepad.reset()
                _sleep(t0, interval)
                continue

            # --- Bias dos circuitos background ---
            ppl_bias = 0.0
            if ppl_runner:
                ppl_runner.update(
                    stagnation_frames=state.frames_since_col,
                    dx=output.x,
                )
                ppl_bias = ppl_runner.aversive_bias

            pcb_bias = 0.0
            if pcb_runner:
                pcb_runner.update_lcr(left=left, center=center, right=right)
                pcb_bias = pcb_runner.lateral_bias

            cx_bias = 0.0
            if cx_runner:
                cx_runner.update_heading(output.x)
                cx_bias = cx_runner.lateral_bias

            fw_bias        = 0.0
            fw_bias_scaled = 0.0  # desativado — viés anatômico fêmea causa giro constante
            if use_flywire and (left + right) > 0.05:
                fw_runner.update_input(left, right)
                fw_bias = fw_runner.lateral_bias

            # --- LIF genérico + integrador ---
            spikes = circuit_lif.step(left, center, right)
            output = integrator.integrate(left, center, right, spikes)

            # --- Aplica biases em cascata ---
            output = apply_bias(output, ppl_bias)
            output = apply_bias(output, pcb_bias)
            output = apply_bias(output, cx_bias)
            output = apply_bias(output, fw_bias_scaled)

            # --- Escape circuit ---
            escape_rate        = 0.0
            visual_escape_bias = 0.0

            state.tick_stagnation(just_collected)

            if visual_circuit:
                visual_circuit.push_frame(frame)
                visual_escape_bias = visual_circuit.escape_bias

            if state.escape_active:
                ended = state.tick_escape()
                if ended:
                    gamepad.release_escape()
                    logger.info("Escape: Giant Fiber desativado — nova direção")
                escape_rate = 0.8

            elif args.escape:
                visual_threat     = visual_circuit and abs(visual_escape_bias) > 0.35
                stagnation_threat = state.stagnation_threat

                if visual_threat or stagnation_threat:
                    state.trigger_escape()
                    gamepad.trigger_escape()
                    trigger = (
                        f"visual bias={visual_escape_bias:+.2f}"
                        if visual_threat
                        else f"estagnação={state.frames_since_col} frames"
                    )
                    logger.info(f"ESCAPE! {trigger} → Giant Fiber ativado")
                    session_log.log_event(state.frame_n, "ESCAPE", trigger)
                    escape_rate = 1.0

            # --- Envia controle ---
            if not state.escape_active:
                gamepad.send(output)

            # --- WebSocket ---
            neural_server.push({
                "escape_active": state.escape_active,
                "threat_level":  round(state.frames_since_col / GameState.STAGNATION_LIMIT, 3),
                "fw_bias":       round(float(fw_bias), 4),
                "left":          round(float(left),    3),
                "center":        round(float(center),  3),
                "right":         round(float(right),   3),
                "mag":           round(float(output.magnitude), 3),
                "collected":     state.total_collected,
                "pressed_keys":  list(gamepad._pressed),
                "circuits": {
                    "reward": {"rate": round(abs(float(fw_bias)) * 0.05, 4)},
                    "escape": {"rate": round(escape_rate, 3)},
                    "orient": {"rate": round(abs(float(fw_bias)) * 0.02, 4)},
                },
            })

            # --- Log científico ---
            session_log.log_frame(
                frame         = state.frame_n,
                fps           = state.fps_disp,
                left          = float(left),
                center        = float(center),
                right         = float(right),
                x             = float(output.x),
                magnitude     = float(output.magnitude),
                fw_bias       = float(fw_bias),
                visual_bias   = float(visual_escape_bias),
                escape_active = state.escape_active,
                dopamine      = state.dopamine,
                items         = len(items),
                skip_focus    = state.skip_focus,
                collected     = state.total_collected,
                reward_rate   = abs(float(fw_bias)) * 0.05,
                escape_rate   = escape_rate,
                orient_rate   = abs(float(fw_bias)) * 0.02,
            )

            # --- FPS log ---
            if state.frame_n % args.fps == 0:
                now            = time.time()
                state.fps_disp = args.fps / (now - fps_t)
                fps_t          = now
                fw_str         = f"  fw_bias={fw_bias:+.2f}" if use_flywire else ""
                logger.info(
                    f"FPS={state.fps_disp:.1f}  itens={len(items):2d}"
                    f"  L={left:.2f} C={center:.2f} R={right:.2f}"
                    f"  x={output.x:+.2f} mag={output.magnitude:.2f}"
                    f"  coletados={state.total_collected}{fw_str}"
                )

            # --- Debug HUD ---
            if hud:
                if not hud.render(
                    frame             = frame,
                    items             = items,
                    state             = state,
                    output            = output,
                    fw_bias           = fw_bias,
                    use_flywire       = use_flywire,
                    draw_detections_fn= draw_detections,
                ):
                    break

            _sleep(t0, interval)

    except KeyboardInterrupt:
        logger.info("Interrompido.")
    finally:
        neural_server.stop()
        if visual_circuit:  visual_circuit.stop()
        if cx_runner:       cx_runner.stop()
        if ppl_runner:      ppl_runner.stop()
        if pcb_runner:      pcb_runner.stop()
        if fw_runner:       fw_runner.stop()
        gamepad.close()
        capture.close()
        if hud:
            hud.close()
        logger.info(f"Total coletados: {state.total_collected}")
        summary = session_log.close()
        logger.info(f"Sessão salva: {summary['frame_file']}")
        logger.info(f"  {summary['frames']} frames · {summary['events']} eventos · {summary['duration_s']}s")
        logger.info("=== ENCERRADO ===")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _sleep(t0: float, interval: float):
    elapsed = time.time() - t0
    if interval - elapsed > 0:
        time.sleep(interval - elapsed)


if __name__ == "__main__":
    main()