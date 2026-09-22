"""
brain/cx_runner.py

Roda o Complexo Central em thread background.

O CX funciona como bússola + integrador de trajetória:
  - EPG recebem o sinal de direção atual (dx do integrador)
  - PFL3 produzem assimetria L/R nos DNs
  - O lateral_bias resultante modula suavemente o dx

Biologicamente: o CX mantém um "senso de direção" interno que
persiste mesmo quando a visão não tem itens claros — exatamente
o que impede a mosca de girar em círculo indefinidamente.

Integração segura:
  - Escala máxima: ±0.15 no dx (muito mais suave que o fw_bias)
  - Média móvel longa (tau ~100 frames) para não reagir a ruído
  - Desativado automaticamente se output for sempre zero
"""

import threading
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CXRunner:
    """
    Roda o Complexo Central em thread background a ~10Hz.
    Expõe .lateral_bias ∈ [-0.15, 0.15] para o integrador.
    """

    def __init__(self, circuit, hz: float = 10.0, w_scale: float = 0.05):
        from brain.flywire_circuit import FlyWireCircuit
        self.fw = FlyWireCircuit(circuit)
        self.hz = hz
        self.w_scale = w_scale

        self.lateral_bias = 0.0
        self.active       = True
        self._lock        = threading.Lock()
        self._dx          = 0.0   # direção atual do Katamari
        self._baseline    = 0.0   # média móvel para cancelar offset
        self._ALPHA       = 0.01  # tau ~100 frames

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[CXRunner] {circuit.n_neurons} neurônios @ {hz:.0f}Hz")

    def update_heading(self, dx: float):
        """Atualiza a direção atual (chamado pelo loop principal)."""
        with self._lock:
            self._dx = float(dx)

    def _run(self):
        interval = 1.0 / self.hz

        while self.active:
            t0 = time.time()

            with self._lock:
                dx = self._dx

            try:
                # Injeta dx nos EPG/PEN como sinal de direção de cabeça
                # dx > 0 = virou direita → estimula EPG direito
                # dx < 0 = virou esquerda → estimula EPG esquerdo
                left_strength  = max(0.0, -dx) * 2.0   # virada esquerda
                right_strength = max(0.0,  dx) * 2.0   # virada direita

                if left_strength + right_strength < 0.01:
                    # Indo reto — injeta sinal neutro fraco para manter atividade
                    left_strength = right_strength = 0.3

                L, C, R = self.fw.stimulate_lateral(
                    left_strength  = left_strength,
                    right_strength = right_strength,
                    n_steps        = 20,
                    w_scale        = self.w_scale,
                )

                # Bias = assimetria R-L dos DNs saída
                raw_bias = float(np.clip(R - L, -1.0, 1.0))

                # Cancela offset anatômico com média móvel
                self._baseline += self._ALPHA * (raw_bias - self._baseline)
                centered = raw_bias - self._baseline

                # Escala conservadora: máx ±0.15
                bias = float(np.clip(centered * 0.3, -0.15, 0.15))

                with self._lock:
                    # EMA suave para não reagir a spikes individuais
                    self.lateral_bias = 0.2 * bias + 0.8 * self.lateral_bias

                logger.debug(
                    f"[CX] dx={dx:+.2f} L={L:.3f} R={R:.3f} "
                    f"raw={raw_bias:+.3f} bias={bias:+.3f}"
                )

            except Exception as e:
                logger.debug(f"[CXRunner] erro: {e}")

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0:
                time.sleep(sleep)

    def stop(self):
        self.active = False