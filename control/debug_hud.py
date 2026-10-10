"""
control/debug_hud.py — Janela de debug, hotkeys globais e HUD

Usado apenas com --debug. Encapsula:
  - Hotkeys globais via pynput (F1-F4)
  - Janela OpenCV posicionada no monitor correto
  - Renderização do HUD e flash de coleta
"""

import logging
import threading

import cv2

logger = logging.getLogger(__name__)

WINDOW_NAME = "Fly Brain v0.5"


class DebugHUD:
    """
    Gerencia a janela de debug e hotkeys globais.

    Parâmetros
    ----------
    monitor_idx : int
        Índice do monitor onde a janela será aberta (mesmo do jogo).
    stop_flag : threading.Event
        Sinaliza encerramento ao pressionar F4.
    on_pause_toggle : callable
        Callback chamado ao pressionar F1 (toggle paused_ui).
    on_dopamine_toggle : callable
        Callback chamado ao pressionar F2 (toggle dopamine 1.0↔2.0).
    on_flywire_toggle : callable
        Callback chamado ao pressionar F3 (toggle FlyWire).
    """

    def __init__(
        self,
        monitor_idx: int,
        stop_flag: threading.Event,
        on_pause_toggle,
        on_dopamine_toggle,
        on_flywire_toggle,
    ):
        self._stop_flag          = stop_flag
        self._on_pause_toggle    = on_pause_toggle
        self._on_dopamine_toggle = on_dopamine_toggle
        self._on_flywire_toggle  = on_flywire_toggle
        self._listener           = None

        self._setup_window(monitor_idx)
        self._setup_hotkeys()

    def _setup_window(self, monitor_idx: int):
        try:
            import mss
            with mss.mss() as sct:
                monitors = sct.monitors
                if len(monitors) > monitor_idx:
                    mon = monitors[monitor_idx]
                    win_x = mon["left"]
                    win_y = mon["top"]
                    win_w = min(mon["width"],  1280)
                    win_h = min(mon["height"], 720)
                else:
                    win_x, win_y, win_w, win_h = 80, 80, 1280, 720
        except Exception:
            win_x, win_y, win_w, win_h = 80, 80, 1280, 720

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, win_w, win_h)
        cv2.moveWindow(WINDOW_NAME, win_x, win_y)

    def _setup_hotkeys(self):
        try:
            from pynput import keyboard as kb

            def _on_press(key):
                try:
                    if key == kb.Key.f1:
                        self._on_pause_toggle()
                    elif key == kb.Key.f2:
                        self._on_dopamine_toggle()
                    elif key == kb.Key.f3:
                        self._on_flywire_toggle()
                    elif key == kb.Key.f4:
                        logger.info("Encerrando (F4)")
                        self._stop_flag.set()
                except Exception:
                    pass

            self._listener = kb.Listener(on_press=_on_press)
            self._listener.start()
            logger.info("Hotkeys globais: F1=pausar  F2=dopamine  F3=FlyWire  F4=sair")
        except Exception as e:
            logger.warning(f"Hotkeys não iniciaram: {e}")

    def render(
        self,
        frame,
        items: list,
        state,           # GameState
        output,          # ControlOutput
        fw_bias: float,
        use_flywire: bool,
        draw_detections_fn,
    ) -> bool:
        """
        Renderiza o frame com HUD. Retorna False se o usuário pediu para sair.
        """
        h, w = frame.shape[:2]
        vis  = draw_detections_fn(frame, items)

        # Flash de coleta
        if state.frame_n - state.last_collection_frame < 45:
            text = f"COLETADO #{state.total_collected}"
            cv2.putText(vis, text, (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(vis, text, (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 80), 2, cv2.LINE_AA)

        # HUD
        fw_str = f"fw={fw_bias:+.2f}" if use_flywire else "LIF"
        hud = [
            f"FPS {state.fps_disp:.0f}  itens {len(items):2d}  coletados {state.total_collected}",
            f"L={output.x:.2f}  mag={output.magnitude:.2f}",
            f"x={output.x:+.2f}  dopa={state.dopamine:.1f}  {fw_str}",
        ]
        for i, line in enumerate(hud):
            y = 22 + i * 22
            cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.48, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(vis, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.48, (200, 255, 200), 1, cv2.LINE_AA)

        cv2.imshow(WINDOW_NAME, vis)
        key = cv2.waitKey(1) & 0xFF
        return key not in (ord('q'), 27)

    def show_paused(self, frame):
        """Exibe tela de pausa."""
        h, w = frame.shape[:2]
        vis  = frame.copy()
        cv2.putText(vis, "PAUSADO (F1)", (w // 2 - 120, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 200), 3)
        cv2.imshow(WINDOW_NAME, vis)
        return cv2.waitKey(1) & 0xFF not in (ord('q'), 27)

    def show_game_paused(self, frame):
        """Exibe aviso de jogo pausado."""
        vis = frame.copy()
        cv2.putText(vis, "JOGO PAUSADO", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 140, 255), 2)
        cv2.imshow(WINDOW_NAME, vis)
        return cv2.waitKey(1) & 0xFF not in (ord('q'), 27)

    def close(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        cv2.destroyAllWindows()