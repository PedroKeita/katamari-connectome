"""
Detecta paredes/bordas próximas ao Katamari e gera um sinal
de ameaça para o EscapeCircuit (LPLC2 → DNp01).

Estratégia biológica:
  A mosca detecta looming (objeto se aproximando) via LPLC2.
  No Katamari, paredes e bordas escuras das fases simulam isso.
  Detectamos regiões escuras densas nas bordas da tela.

Retorna:
  threat_level : float [0.0, 1.0]
    0.0 = nenhuma parede detectada
    1.0 = parede muito próxima, escape reflexo necessário
  threat_side  : str 'left' | 'right' | 'center' | None
    lado da tela onde a ameaça é maior
"""

import cv2
import numpy as np


# Bordas da tela onde paredes normalmente aparecem
# (exclui o centro onde está o Katamari)
WALL_ZONES = [
    # (x_norm, y_norm, w_norm, h_norm, nome)
    (0.00, 0.10, 0.15, 0.80, "left"),    # borda esquerda
    (0.85, 0.10, 0.15, 0.80, "right"),   # borda direita
    (0.10, 0.00, 0.80, 0.12, "top"),     # borda superior
    (0.10, 0.88, 0.80, 0.12, "bottom"),  # borda inferior
]

# Threshold de escuridão para considerar parede
DARK_THRESHOLD = 40    # valor de brilho (0-255)
WALL_DENSITY   = 0.25  # fração mínima de pixels escuros para disparar


class WallDetector:
    """
    Detecta paredes próximas ao Katamari via análise de regiões escuras
    nas bordas da tela.

    A detecção é inspirada no circuito LPLC2 da mosca — neurônios
    sensíveis a objetos grandes e escuros se aproximando.
    """

    def __init__(
        self,
        dark_threshold: int   = DARK_THRESHOLD,
        wall_density:   float = WALL_DENSITY,
        smoothing:      float = 0.3,   # EMA para suavizar o sinal
    ):
        self.dark_threshold = dark_threshold
        self.wall_density   = wall_density
        self.smoothing      = smoothing
        self._threat_smooth = 0.0

    def detect(self, frame: np.ndarray) -> tuple[float, str | None]:
        """
        Analisa o frame e retorna (threat_level, threat_side).

        Parameters
        ----------
        frame : BGR frame do OpenCV

        Returns
        -------
        threat_level : float [0, 1]
        threat_side  : 'left' | 'right' | 'top' | 'bottom' | None
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        zone_threats = {}

        for (xn, yn, wn, hn, name) in WALL_ZONES:
            x1 = int(xn * w)
            y1 = int(yn * h)
            x2 = int((xn + wn) * w)
            y2 = int((yn + hn) * h)

            region = gray[y1:y2, x1:x2]
            if region.size == 0:
                continue

            dark_pixels = np.sum(region < self.dark_threshold)
            density     = dark_pixels / region.size

            zone_threats[name] = density

        if not zone_threats:
            return 0.0, None

        # Lado com maior ameaça
        max_side  = max(zone_threats, key=zone_threats.get)
        max_density = zone_threats[max_side]

        # Normaliza para [0, 1] baseado no threshold
        raw_threat = min(max_density / self.wall_density, 1.0)

        # Suavização EMA para evitar falsos positivos momentâneos
        self._threat_smooth = (
            self.smoothing * raw_threat
            + (1 - self.smoothing) * self._threat_smooth
        )

        threat_side = max_side if self._threat_smooth > 0.3 else None

        return float(self._threat_smooth), threat_side

    def reset(self):
        self._threat_smooth = 0.0