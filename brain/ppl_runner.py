"""
Roda o circuito PPL em thread background.

Os PPLs são neurônios dopaminérgicos aversivos — sinalizam punição.
Na mosca real, PPL1 dispara quando o animal recebe um choque elétrico
ou encontra algo desagradável, inibindo os KCs e mudando o comportamento.

No Katamari:
  - Quando preso (stagnation_frames crescendo), estimula os PPLs
  - PPLs inibem KCs → MBONs mudam de estado → sinal aversivo
  - aversive_bias: assimetria L/R nos MBONs → empurra para nova direção

Integração segura:
  - Escala máxima: ±0.10 no dx
  - Só ativa quando stagnation > 60 frames (2s) — complementa o fallback de 180
  - EMA suave para não reagir a spikes individuais
"""

import threading
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PPLRunner:
    """
    Roda o circuito PPL em thread background a ~5Hz.
    Expõe .aversive_bias ∈ [-0.10, 0.10] para o integrador.
    """

    def __init__(self, circuit, hz: float = 5.0, w_scale: float = 0.05):
        from brain.flywire_circuit import FlyWireCircuit
        self.fw = FlyWireCircuit(circuit)
        self.hz = hz
        self.w_scale = w_scale

        self.aversive_bias  = 0.0
        self.active         = True
        self._lock          = threading.Lock()
        self._stagnation    = 0      # frames sem coleta
        self._last_dx       = 0.0   # direção atual

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[PPLRunner] {circuit.n_neurons} neurônios @ {hz:.0f}Hz")

    def update(self, stagnation_frames: int, dx: float):
        """Atualiza estado (chamado pelo loop principal)."""
        with self._lock:
            self._stagnation = stagnation_frames
            self._last_dx    = float(dx)

    def _run(self):
        interval = 1.0 / self.hz

        while self.active:
            t0 = time.time()

            with self._lock:
                stag = self._stagnation
                dx   = self._last_dx

            try:
                # PPL só ativa quando há estagnação significativa (>60 frames ~2s)
                if stag < 60:
                    with self._lock:
                        self.aversive_bias = 0.8 * self.aversive_bias  # decai suavemente
                    time.sleep(interval)
                    continue

                # Intensidade proporcional à estagnação (0 em 60f, máx em 180f)
                intensity = min(1.0, (stag - 60) / 120.0)

                # PPL estimulados uniformemente (sinal aversivo global)
                # Assimetria L/R baseada no dx atual — empurra na direção oposta
                if dx > 0.1:
                    # Indo direita → PPL direito mais ativo → bias para esquerda
                    left_strength  = intensity * 0.5
                    right_strength = intensity * 1.5
                elif dx < -0.1:
                    # Indo esquerda → PPL esquerdo mais ativo → bias para direita
                    left_strength  = intensity * 1.5
                    right_strength = intensity * 0.5
                else:
                    # Indo reto → estimula ambos igualmente
                    left_strength = right_strength = intensity

                L, C, R = self.fw.stimulate_lateral(
                    left_strength  = left_strength,
                    right_strength = right_strength,
                    n_steps        = 15,
                    w_scale        = self.w_scale,
                )

                # Bias aversivo: oposto à direção atual
                raw_bias = float(np.clip(R - L, -1.0, 1.0))
                # PPL são inibitórios sobre KCs → inverte sinal para ser aversivo
                aversive = -raw_bias * 0.2  # máx ±0.20 antes do clip

                bias = float(np.clip(aversive, -0.10, 0.10))

                with self._lock:
                    self.aversive_bias = 0.3 * bias + 0.7 * self.aversive_bias

                logger.debug(
                    f"[PPL] stag={stag} dx={dx:+.2f} intensity={intensity:.2f} "
                    f"L={L:.3f} R={R:.3f} bias={bias:+.3f}"
                )

            except Exception as e:
                logger.debug(f"[PPLRunner] erro: {e}")

            elapsed = time.time() - t0
            sleep = interval - elapsed
            if sleep > 0:
                time.sleep(sleep)

    def stop(self):
        self.active = False