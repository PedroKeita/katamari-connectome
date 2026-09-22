"""
brain/fw_runner.py — FlyWireRunner

Roda os circuitos FlyWire (reward + orient) em thread separada (~20Hz).
O loop principal lê .lateral_bias a cada frame.
"""

import logging
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)


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
        self.circuits     = circuits  # {"reward": FlyWireCircuit, "orient": FlyWireCircuit}
        self.lateral_bias = 0.0
        self._stop_event  = threading.Event()
        self._lock        = threading.Lock()
        self._left_str    = 0.0
        self._right_str   = 0.0
        self._thread      = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update_input(self, left: float, right: float):
        """Atualiza o estímulo de entrada (chamado pelo loop principal)."""
        with self._lock:
            self._left_str  = float(left)
            self._right_str = float(right)

    def _run(self):
        while not self._stop_event.is_set():
            with self._lock:
                ls = self._left_str
                rs = self._right_str

            if ls + rs < 0.01:
                with self._lock:
                    self.lateral_bias = 0.0
                self._stop_event.wait(0.05)
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

            self._stop_event.wait(0.05)  # ~20Hz

    def stop(self) -> None:
        """Request shutdown and wait briefly for the worker to finish."""
        self._stop_event.set()
        self._thread.join(timeout=1.0)