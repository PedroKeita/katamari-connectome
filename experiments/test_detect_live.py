"""
experiments/test_detect_live.py  —  v2

Janela ao vivo com detecção por bordas (v3 do detect.py).
Captura o segundo monitor em tempo real.

Controles:
  Q / ESC  — sair
  +  /  -  — Canny LOW  +/- 5
  [  /  ]  — Canny HIGH +/- 5
  M        — alternar: frame anotado  /  máscara de bordas
  P        — pausar / retomar
  S        — salvar screenshot em debug/
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import mss

try:
    from vision.detection.items import detect_items, draw_detections
    import vision.detection.items as _det
except ImportError:
    import importlib.util, pathlib
    _p    = pathlib.Path(__file__).parent.parent / "vision" / "detect.py"
    _spec = importlib.util.spec_from_file_location("detect", _p)
    _det  = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_det)
    detect_items    = _det.detect_items
    draw_detections = _det.draw_detections

# ------------------------------------------------------------------
MONITOR_INDEX = 1
TARGET_FPS    = 30
WINDOW_NAME   = "Katamari Detector v3 — monitor 2"
SCALE         = 0.65        # escala da janela
# ------------------------------------------------------------------

os.makedirs("debug", exist_ok=True)

sct = mss.mss()
if MONITOR_INDEX >= len(sct.monitors):
    print(f"[ERRO] Monitor {MONITOR_INDEX} não encontrado. "
          f"Disponíveis: 1..{len(sct.monitors)-1}")
    sct.close(); sys.exit(1)

monitor = sct.monitors[MONITOR_INDEX]
print(f"[OK] Monitor {MONITOR_INDEX}: {monitor['width']}x{monitor['height']}")


def capture():
    shot = sct.grab(monitor)
    return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)


def overlay_hud(img, items, fps, paused, mask_mode):
    canny_low  = _det.CANNY_LOW
    canny_high = _det.CANNY_HIGH
    lines = [
        f"FPS: {fps:.1f}   Itens: {len(items)}",
        f"Canny: {canny_low}/{canny_high}   (+/-  [/]  para ajustar)",
        f"Modo: {'BORDAS' if mask_mode else 'FRAME anotado'}  (M para trocar)",
        "PAUSADO — P para retomar" if paused else "P=pausar  S=salvar  Q=sair",
    ]
    y = 22
    for line in lines:
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                    (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                    (255, 255, 255), 1, cv2.LINE_AA)
        y += 22
    return img


cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.moveWindow(WINDOW_NAME, 80, 80)

show_mask    = False
paused       = False
last_frame   = None
last_items   = []
last_mask    = None
save_n       = 0
frame_count  = 0
fps_disp     = 0.0
fps_t        = time.time()
interval     = 1.0 / TARGET_FPS

print()
print("Controles:")
print("  +/-   Canny low +/- 5")
print("  [/]   Canny high +/- 5")
print("  M     frame / máscara de bordas")
print("  P     pausa / retoma")
print("  S     salva screenshot")
print("  Q/ESC sair")
print()

try:
    while True:
        t0 = time.time()

        if not paused:
            raw              = capture()
            items, mask      = detect_items(raw)
            last_frame       = raw
            last_items       = items
            last_mask        = mask
            frame_count     += 1
            if frame_count % 30 == 0:
                now      = time.time()
                fps_disp = 30.0 / (now - fps_t)
                fps_t    = now

        if last_frame is None:
            time.sleep(0.05)
            continue

        if show_mask and last_mask is not None:
            disp = cv2.cvtColor(last_mask, cv2.COLOR_GRAY2BGR)
        else:
            disp = draw_detections(last_frame, last_items)

        disp = overlay_hud(disp, last_items, fps_disp, paused, show_mask)
        dh, dw = disp.shape[:2]
        disp = cv2.resize(disp, (int(dw * SCALE), int(dh * SCALE)),
                          interpolation=cv2.INTER_LINEAR)
        cv2.imshow(WINDOW_NAME, disp)

        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('+'), ord('=')):
            _det.CANNY_LOW = min(_det.CANNY_LOW + 5, _det.CANNY_HIGH - 5)
            print(f"CANNY_LOW → {_det.CANNY_LOW}")
        elif key == ord('-'):
            _det.CANNY_LOW = max(_det.CANNY_LOW - 5, 5)
            print(f"CANNY_LOW → {_det.CANNY_LOW}")
        elif key == ord(']'):
            _det.CANNY_HIGH = min(_det.CANNY_HIGH + 5, 255)
            print(f"CANNY_HIGH → {_det.CANNY_HIGH}")
        elif key == ord('['):
            _det.CANNY_HIGH = max(_det.CANNY_HIGH - 5, _det.CANNY_LOW + 5)
            print(f"CANNY_HIGH → {_det.CANNY_HIGH}")
        elif key in (ord('m'), ord('M')):
            show_mask = not show_mask
            print(f"Modo: {'BORDAS' if show_mask else 'FRAME'}")
        elif key in (ord('p'), ord('P')):
            paused = not paused
            print("PAUSADO" if paused else "Retomado")
        elif key in (ord('s'), ord('S')):
            save_n += 1
            pf = f"debug/live_{save_n:03d}_frame.png"
            pm = f"debug/live_{save_n:03d}_mask.png"
            if last_frame is not None:
                cv2.imwrite(pf, draw_detections(last_frame, last_items))
            if last_mask is not None:
                cv2.imwrite(pm, last_mask)
            print(f"Salvo: {pf}  |  {pm}")

        sleep = interval - (time.time() - t0)
        if sleep > 0:
            time.sleep(sleep)

finally:
    sct.close()
    cv2.destroyAllWindows()
    print("\n=== ENCERRADO ===")