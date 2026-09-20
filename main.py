"""
Pipeline limpo:
  frame → detect → VisualField → SensoryEncoder → L/C/R
       → RewardCircuit (LIF) → Integrator → Gamepad

Sem StimulusType.REWARD, sem items_to_stimuli.
O cérebro recebe dados sensoriais brutos.
"""

import argparse
import logging
import time

import cv2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_ITEMS_GUARD = 40


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",  action="store_true")
    p.add_argument("--debug",    action="store_true")
    p.add_argument("--fps",      type=int,   default=30)
    p.add_argument("--monitor",  type=int,   default=2)
    p.add_argument("--dopamine", type=float, default=1.0)
    return p.parse_args()


def main():
    args = parse_args()

    from vision.capture        import ScreenCapture
    from vision.detect         import detect_items, draw_detections, CollectionDetector
    from vision.visual_field   import items_to_visual_field
    from vision.pause_detector import PauseDetector
    from brain.sensory_encoder import SensoryEncoder
    from brain.reward          import RewardCircuit
    from control.integrator    import CircuitIntegrator
    from control.gamepad       import GamepadController

    logger.info("=== FLY BRAIN KATAMARI v0.4 ===")

    capture      = ScreenCapture(monitor=args.monitor)
    encoder      = SensoryEncoder()
    circuit      = RewardCircuit()
    integrator   = CircuitIntegrator(dopamine=args.dopamine)
    gamepad      = GamepadController(dry_run=args.dry_run)
    col_detect   = CollectionDetector()
    pause_detect = PauseDetector()

    dopamine              = args.dopamine
    focus_patience        = 0
    PATIENCE_LIMIT        = 90
    skip_focus            = 0
    total_collected       = 0
    last_collection_frame = -999

    frame_n  = 0
    fps_t    = time.time()
    fps_disp = 0.0
    interval = 1.0 / args.fps
    paused_ui = False

    if args.debug:
        cv2.namedWindow("Fly Brain v0.4", cv2.WINDOW_NORMAL)
        cv2.moveWindow("Fly Brain v0.4", 80, 80)

    logger.info(f"Monitor={args.monitor}  FPS={args.fps}  dry-run={args.dry_run}")

    try:
        while True:
            t0 = time.time()
            frame   = capture.capture()
            h, w    = frame.shape[:2]
            frame_n += 1

            if paused_ui:
                gamepad.reset()
                if args.debug:
                    vis = frame.copy()
                    cv2.putText(vis, "PAUSADO (P)", (w//2-100, h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,200), 3)
                    cv2.imshow("Fly Brain v0.4", vis)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), 27): break
                    if key == ord('p'): paused_ui = False
                time.sleep(0.05); continue

            if pause_detect.check(frame):
                gamepad.reset()
                col_detect.reset()
                if args.debug:
                    vis = frame.copy()
                    cv2.putText(vis, "JOGO PAUSADO", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,140,255), 2)
                    cv2.imshow("Fly Brain v0.4", vis)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord('q'), 27): break
                    if key == ord('p'): paused_ui = True
                elapsed = time.time() - t0
                if interval - elapsed > 0: time.sleep(interval - elapsed)
                continue

            items_raw, _ = detect_items(frame)
            if len(items_raw) > MAX_ITEMS_GUARD:
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
            else:
                focus_patience = 0
                skip_focus = 0

            if skip_focus > 0 and len(items) > skip_focus:
                items = items[skip_focus:] + items[:skip_focus]

            # ---- pipeline sensorial → neural ----
            visual_field        = items_to_visual_field(items, w, h)
            left, center, right = encoder.encode(visual_field)
            spikes              = circuit.step(left, center, right)
            output              = integrator.integrate(left, center, right, spikes)
            gamepad.send(output)

            if frame_n % args.fps == 0:
                now      = time.time()
                fps_disp = args.fps / (now - fps_t)
                fps_t    = now
                logger.info(
                    f"FPS={fps_disp:.1f}  itens={len(items):2d}"
                    f"  L={left:.2f} C={center:.2f} R={right:.2f}"
                    f"  x={output.x:+.2f} mag={output.magnitude:.2f}"
                    f"  coletados={total_collected}"
                )

            if args.debug:
                vis = draw_detections(frame, items)

                if frame_n - last_collection_frame < 45:
                    cv2.putText(vis, f"COLETADO #{total_collected}",
                                (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0,0,0), 4, cv2.LINE_AA)
                    cv2.putText(vis, f"COLETADO #{total_collected}",
                                (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0,220,80), 2, cv2.LINE_AA)

                hud = [
                    f"FPS {fps_disp:.1f}   itens {len(items)}   coletados {total_collected}",
                    f"L={left:.2f}  C={center:.2f}  R={right:.2f}   dopa={dopamine:.1f}",
                    f"spikes L={spikes['left']} C={spikes['center']} R={spikes['right']}",
                    f"ctrl x={output.x:+.2f}  mag={output.magnitude:.2f}  skip={skip_focus}",
                    f"patience {focus_patience}/{PATIENCE_LIMIT}",
                ]
                for i, line in enumerate(hud):
                    y = 22 + i * 22
                    cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.48, (0,0,0), 3, cv2.LINE_AA)
                    cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.48, (255,255,255), 1, cv2.LINE_AA)

                cv2.imshow("Fly Brain v0.4", vis)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), 27):   break
                elif key == ord('p'):       paused_ui = True
                elif key == ord('d'):
                    args.dopamine = 2.0 if args.dopamine == 1.0 else 1.0
                    logger.info(f"Dopamine base -> {args.dopamine}")

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0: time.sleep(sleep)

    except KeyboardInterrupt:
        logger.info("Interrompido.")
    finally:
        gamepad.close()
        capture.close()
        if args.debug:
            cv2.destroyAllWindows()
        logger.info(f"Total coletados: {total_collected}")
        logger.info("=== ENCERRADO ===")


if __name__ == "__main__":
    main()