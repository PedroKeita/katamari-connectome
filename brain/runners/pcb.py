"""
Roda o Protocerebral Bridge em thread background.

O PCB integra informações dos dois hemisférios cerebrais e coordena
a saída motora bilateral. Na mosca real, coordena viradas que requerem
ativação assimétrica dos músculos de voo.

No Katamari: recebe L/C/R do sensory encoder, produz uma modulação
bilateral dos DNs — complementa o CX (bússola) com integração
sensorial mais direta.

Integração segura:
  - Escala máxima: ±0.12 no dx
  - EMA longa (tau ~80 frames) para sinal estável
  - Cancelamento de offset anatômico via baseline
"""

import threading
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PCBRunner:
    """
    Roda o Protocerebral Bridge em thread background a ~8Hz.
    Expõe .lateral_bias ∈ [-0.12, 0.12] para o integrador.
    """

    def __init__(self, circuit, hz: float = 8.0, w_scale: float = 0.04):
        from brain.circuits.flywire import FlyWireCircuit
        self.fw = FlyWireCircuit(circuit)
        self.hz = hz
        self.w_scale = w_scale

        self.lateral_bias = 0.0
        self._stop_event  = threading.Event()
        self._lock        = threading.Lock()
        self._L = 0.0
        self._C = 1.0
        self._R = 0.0
        self._baseline    = 0.0
        self._ALPHA       = 0.012  # tau ~80 frames

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[PCBRunner] {circuit.n_neurons} neurônios @ {hz:.0f}Hz")

    def update_lcr(self, left: float, center: float, right: float):
        """Atualiza L/C/R do sensory encoder (chamado pelo loop principal)."""
        with self._lock:
            self._L = float(left)
            self._C = float(center)
            self._R = float(right)

    def _run(self):
        interval = 1.0 / self.hz

        while not self._stop_event.is_set():
            t0 = time.time()

            with self._lock:
                L, C, R = self._L, self._C, self._R

            try:
                # LAL/SMP recebem sinal sensorial assimétrico
                left_strength  = max(0.1, L + C * 0.3)
                right_strength = max(0.1, R + C * 0.3)

                L_out, C_out, R_out = self.fw.stimulate_lateral(
                    left_strength  = left_strength,
                    right_strength = right_strength,
                    n_steps        = 25,
                    w_scale        = self.w_scale,
                )

                raw_bias = float(np.clip(R_out - L_out, -1.0, 1.0))

                # Cancela offset anatômico
                self._baseline += self._ALPHA * (raw_bias - self._baseline)
                centered = raw_bias - self._baseline

                bias = float(np.clip(centered * 0.25, -0.12, 0.12))

                with self._lock:
                    self.lateral_bias = 0.15 * bias + 0.85 * self.lateral_bias

                logger.debug(
                    f"[PCB] L={L:.2f} R={R:.2f} "
                    f"out_L={L_out:.3f} out_R={R_out:.3f} bias={bias:+.3f}"
                )

            except Exception as e:
                logger.debug(f"[PCBRunner] erro: {e}")

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0:
                self._stop_event.wait(sleep)

    def stop(self) -> None:
        """Request shutdown and wait briefly for the worker to finish."""
        self._stop_event.set()
        self._thread.join(timeout=1.0)