"""
Correção principal: a direção (x) é calculada diretamente dos
inputs L/C/R contínuos, NÃO dos spikes binários do LIF.

Os spikes do LIF ainda são usados como "gatilho de atenção" —
confirmam que há estímulo — mas a MAGNITUDE e DIREÇÃO vêm
dos valores analógicos. Isso evita o problema de 2/3 dos frames
não terem spike e o Katamari ir só reto.

Lógica:
    x = (right - left) / max(left + right, ε)
          → negativo = vira esquerda
          → positivo = vira direita
          → zero     = vai reto (itens no centro ou sem itens)

    magnitude = center * dopamine  (quão forte ir para frente)
              + 0.3 * max(left, right)  (lateral também empurra)
"""

from dataclasses import dataclass


@dataclass
class ControlOutput:
    x:         float   # -1 esquerda .. +1 direita
    y:         float   # -1 frente   .. +1 ré
    magnitude: float   # 0 .. 1


class CircuitIntegrator:

    def __init__(
        self,
        dopamine:            float = 1.0,
        dead_zone:           float = 0.05,
        turn_sensitivity:    float = 1.8,   # amplifica viradas
        forward_sensitivity: float = 1.4,   # amplifica avanço
    ):
        self.dopamine            = dopamine
        self.dead_zone           = dead_zone
        self.turn_sensitivity    = turn_sensitivity
        self.forward_sensitivity = forward_sensitivity

    def integrate(
        self,
        left_input:    float,
        center_input:  float,
        right_input:   float,
        reward_spikes: dict,
        escape_spikes: dict | None = None,
        orientation_spikes: dict | None = None,
    ) -> ControlOutput:

        # --------------------------------------------------
        # Sem estímulo → movimento exploratório basal
        # A mosca real nunca para completamente — quando não
        # há recompensa visível, mantém exploração aleatória.
        # --------------------------------------------------
        total = left_input + center_input + right_input
        if total < self.dead_zone:
            return ControlOutput(x=0.0, y=-1.0, magnitude=0.3)

        # --------------------------------------------------
        # DIREÇÃO X: baseada nos inputs contínuos
        #
        # Se right > left  → vira direita (+x)
        # Se left  > right → vira esquerda (-x)
        # Se center domina → vai reto (x pequeno)
        # --------------------------------------------------
        lateral = left_input + right_input
        if lateral > 0.001:
            # dx normalizado entre -1 e +1
            dx = (right_input - left_input) / lateral
        else:
            dx = 0.0

        # Amplifica para o teclado reagir rápido
        dx = max(-1.0, min(1.0, dx * self.turn_sensitivity))

        # --------------------------------------------------
        # MAGNITUDE: o Katamari sempre vai para frente
        # quando há qualquer estímulo
        # --------------------------------------------------
        magnitude = min(
            (center_input * 0.6 + max(left_input, right_input) * 0.4)
            * self.forward_sensitivity
            * self.dopamine,
            1.0
        )

        if magnitude < self.dead_zone:
            return ControlOutput(x=0.0, y=0.0, magnitude=0.0)

        # Sempre frente (y negativo)
        dy = -1.0

        return ControlOutput(x=dx, y=dy, magnitude=magnitude)