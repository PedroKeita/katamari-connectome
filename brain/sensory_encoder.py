"""
SensoryEncoder — única camada que traduz o campo visual em
sinais neurais L/C/R para os circuitos.

É aqui que mora a "opinião" sobre o que o cérebro deve notar.
Não no sistema de visão (que é cego a significados) e não
nos circuitos (que só integram carga elétrica).

O encoder atual implementa uma heurística simples mas biologicamente
plausível: objetos mais próximos (maior tamanho aparente) e mais
baixos na tela (mais perto do Katamari) geram sinal mais forte.

Isso pode ser refinado futuramente com:
- Pesos por frequência de coleta (dopamina real)
- Supressão de objetos já visitados sem coleta (memória de curto prazo)
- Boost para objetos em movimento (atenção seletiva)
"""

from vision.visual_field import VisualStimulus


class SensoryEncoder:
    """
    Converte uma lista de VisualStimulus em três valores escalares:
      left, center, right  ∈ [0, 1]

    Foco em TOP-N estímulos mais salientes para evitar saturação.
    Quando todos os canais saturam em 1.0, dx=0 e o Katamari vai reto.
    Processar só os N mais relevantes preserva o sinal direcional.

    Parâmetros
    ----------
    top_n           : quantos estímulos processar (os mais salientes)
    size_weight     : peso do tamanho aparente
    proximity_weight: peso da posição vertical (mais baixo = mais perto)
    contrast_weight : peso do contraste/definição do objeto
    velocity_weight : peso do movimento
    vertical_bias   : boost máximo para objetos no fundo da tela
    attention_decay : peso decrescente por ranking (1º=1.0, 2º*decay, ...)
    """

    def __init__(
        self,
        top_n:            int   = 5,
        size_weight:      float = 0.40,
        proximity_weight: float = 0.35,
        contrast_weight:  float = 0.15,
        velocity_weight:  float = 0.10,
        vertical_bias:    float = 0.60,
        size_scale:       float = 80.0,
        attention_decay:  float = 0.55,  # cada item seguinte vale 55% do anterior
    ):
        total = size_weight + proximity_weight + contrast_weight + velocity_weight
        self.w_size         = size_weight      / total
        self.w_proximity    = proximity_weight / total
        self.w_contrast     = contrast_weight  / total
        self.w_velocity     = velocity_weight  / total
        self.vertical_bias  = vertical_bias
        self.size_scale     = size_scale
        self.top_n          = top_n
        self.attention_decay = attention_decay

    def _saliency(self, s: VisualStimulus) -> float:
        """Score de saliência — decide quais objetos entram no top-N."""
        size_signal = min(s.apparent_size * self.size_scale, 1.0)
        return (
            0.50 * (1.0 + self.vertical_bias * s.y) / (1.0 + self.vertical_bias) +
            0.30 * size_signal +
            0.20 * s.contrast
        )

    def encode(self, stimuli: list[VisualStimulus]) -> tuple[float, float, float]:
        """
        Retorna (left, center, right) ∈ [0, 1].

        Processa apenas os top-N estímulos mais salientes, com
        peso decrescente por ranking (atenção seletiva).
        """
        if not stimuli:
            return 0.0, 0.0, 0.0

        # Ordena por saliência e pega top-N
        ranked = sorted(stimuli, key=self._saliency, reverse=True)
        focused = ranked[: self.top_n]

        left = center = right = 0.0
        norm = 1.0 + self.vertical_bias * self.w_proximity

        for rank, s in enumerate(focused):
            # Peso de atenção decai por ranking
            attention = self.attention_decay ** rank

            size_signal     = min(s.apparent_size * self.size_scale, 1.0)
            prox_signal     = 1.0 + self.vertical_bias * s.y
            contrast_signal = s.contrast
            vel_signal      = min(abs(s.velocity_x) + abs(s.velocity_y), 1.0)

            intensity = (
                self.w_size      * size_signal     +
                self.w_proximity * prox_signal     +
                self.w_contrast  * contrast_signal +
                self.w_velocity  * vel_signal
            ) / norm

            intensity = max(0.0, min(intensity, 1.0)) * attention

            x = s.x
            if x < 0.5:
                left   += intensity * (0.5 - x) / 0.5
            if x > 0.5:
                right  += intensity * (x - 0.5) / 0.5
            center_dist = abs(x - 0.5)
            center += intensity * max(0.0, 1.0 - center_dist / 0.5)

        left   = min(left,   1.0)
        center = min(center, 1.0)
        right  = min(right,  1.0)

        return left, center, right