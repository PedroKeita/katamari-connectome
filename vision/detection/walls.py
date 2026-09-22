"""
Detecta paredes/obstáculos usando Optical Flow (Lucas-Kanade).

Princípio biológico:
  Os neurônios LPLC2 da mosca respondem a "looming" — objetos ou
  superfícies se expandindo radialmente no campo visual. Quando o
  Katamari se aproxima de uma parede, o fundo expande radialmente
  nas bordas da tela, exatamente o estímulo que os LPLC2 detectam.

Algoritmo:
  1. Detecta pontos-chave (Shi-Tomasi) nas bordas da tela
  2. Rastreia esses pontos entre frames (Lucas-Kanade optical flow)
  3. Calcula vetores de movimento — se apontam para fora do centro
     com magnitude alta = looming = parede se aproximando
  4. Suaviza o sinal com EMA para evitar falsos positivos

Retorna:
  threat_level : float [0.0, 1.0]
  threat_side  : 'left' | 'right' | 'top' | 'bottom' | None
"""

import cv2
import numpy as np


# Zonas de detecção (bordas da tela, excluindo o centro)
ZONES = [
    (0.00, 0.10, 0.18, 0.80, "left"),
    (0.82, 0.10, 0.18, 0.80, "right"),
    (0.10, 0.00, 0.80, 0.15, "top"),
    (0.10, 0.85, 0.80, 0.15, "bottom"),
]

# Parâmetros Shi-Tomasi para detecção de pontos
FEATURE_PARAMS = dict(
    maxCorners    = 80,
    qualityLevel  = 0.2,
    minDistance   = 12,
    blockSize     = 5,
)

# Parâmetros Lucas-Kanade
LK_PARAMS = dict(
    winSize  = (15, 15),
    maxLevel = 2,
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
)


class WallDetector:
    """
    Detecta looming (expansão radial) via optical flow.
    Biologicamente análogo aos neurônios LPLC2 da mosca.
    """

    def __init__(
        self,
        looming_threshold: float = 0.35,  # fração de vetores apontando para fora
        min_magnitude:     float = 1.5,   # magnitude mínima do flow (pixels/frame)
        smoothing:         float = 0.35,
        check_every:       int   = 4,     # analisa 1 a cada 4 frames (~7Hz a 30fps)
    ):
        self.looming_threshold = looming_threshold
        self.min_magnitude     = min_magnitude
        self.smoothing         = smoothing
        self.check_every       = check_every

        self._prev_gray  = None
        self._prev_pts   = None
        self._threat     = 0.0
        self._last_side  = None
        self._frame_n    = 0

    def _get_zone_mask(self, h, w, zone_name):
        """Máscara para uma zona de borda específica."""
        mask = np.zeros((h, w), dtype=np.uint8)
        for (xn, yn, wn, hn, name) in ZONES:
            if name == zone_name:
                x1, y1 = int(xn*w), int(yn*h)
                x2, y2 = int((xn+wn)*w), int((yn+hn)*h)
                mask[y1:y2, x1:x2] = 255
        return mask

    def _full_border_mask(self, h, w):
        """Máscara cobrindo todas as zonas de borda."""
        mask = np.zeros((h, w), dtype=np.uint8)
        for (xn, yn, wn, hn, _) in ZONES:
            x1, y1 = int(xn*w), int(yn*h)
            x2, y2 = int((xn+wn)*w), int((yn+hn)*h)
            mask[y1:y2, x1:x2] = 255
        return mask

    def detect(self, frame: np.ndarray) -> tuple[float, str | None]:
        """
        Analisa o frame e retorna (threat_level, threat_side).
        """
        self._frame_n += 1

        # Reduz para acelerar
        small = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)
        h, w  = small.shape[:2]
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # Inicializa no primeiro frame
        if self._prev_gray is None:
            self._prev_gray = gray
            border_mask = self._full_border_mask(h, w)
            self._prev_pts = cv2.goodFeaturesToTrack(
                gray, mask=border_mask, **FEATURE_PARAMS
            )
            return 0.0, None

        # Pula frames intermediários (usa o último resultado)
        if self._frame_n % self.check_every != 0:
            return float(self._threat), self._last_side

        # Precisa de pontos para rastrear
        if self._prev_pts is None or len(self._prev_pts) < 4:
            border_mask = self._full_border_mask(h, w)
            self._prev_pts = cv2.goodFeaturesToTrack(
                gray, mask=border_mask, **FEATURE_PARAMS
            )
            self._prev_gray = gray
            return float(self._threat), self._last_side

        # Optical flow Lucas-Kanade
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            self._prev_gray, gray, self._prev_pts, None, **LK_PARAMS
        )

        if next_pts is None:
            self._prev_gray = gray
            return float(self._threat), self._last_side

        # Filtra só os pontos rastreados com sucesso
        good_prev = self._prev_pts[status == 1]
        good_next = next_pts[status == 1]

        if len(good_prev) < 4:
            self._prev_gray = gray
            self._prev_pts  = cv2.goodFeaturesToTrack(
                gray, mask=self._full_border_mask(h, w), **FEATURE_PARAMS
            )
            return float(self._threat), self._last_side

        # Centro da tela (onde está o Katamari)
        cx, cy = w / 2, h / 2

        # Analisa cada vetor de flow
        zone_scores = {z[4]: [] for z in ZONES}

        for (px, py), (nx, ny) in zip(good_prev, good_next):
            dx = nx - px
            dy = ny - py
            mag = np.sqrt(dx*dx + dy*dy)

            if mag < self.min_magnitude:
                continue

            # Vetor do centro até o ponto
            to_point_x = px - cx
            to_point_y = py - cy
            to_point_len = max(np.sqrt(to_point_x**2 + to_point_y**2), 1e-6)

            # Produto escalar: flow alinhado com "para fora do centro" = looming
            dot = (dx * to_point_x + dy * to_point_y) / to_point_len
            looming_score = dot / max(mag, 1e-6)

            # Classifica em qual zona está o ponto
            pxn, pyn = px/w, py/h
            for (xn, yn, wn, hn, name) in ZONES:
                if xn <= pxn <= xn+wn and yn <= pyn <= yn+hn:
                    zone_scores[name].append(looming_score)
                    break

        # Calcula ameaça por zona
        zone_threats = {}
        for name, scores in zone_scores.items():
            if len(scores) < 3:
                zone_threats[name] = 0.0
                continue
            # Fração de vetores apontando para fora (looming_score > 0)
            looming_frac = np.mean(np.array(scores) > 0.3)
            zone_threats[name] = float(looming_frac)

        # Zona com maior ameaça
        if not zone_threats or max(zone_threats.values()) < 0.01:
            raw_threat = 0.0
            side = None
        else:
            max_side    = max(zone_threats, key=zone_threats.get)
            raw_threat  = min(zone_threats[max_side] / self.looming_threshold, 1.0)
            side        = max_side if raw_threat > 0.3 else None

        # EMA
        self._threat    = self.smoothing * raw_threat + (1-self.smoothing) * self._threat
        self._last_side = side if self._threat > 0.25 else None

        # Atualiza para próximo frame
        self._prev_gray = gray
        # Re-detecta pontos periodicamente
        if self._frame_n % (self.check_every * 8) == 0:
            border_mask = self._full_border_mask(h, w)
            self._prev_pts = cv2.goodFeaturesToTrack(
                gray, mask=border_mask, **FEATURE_PARAMS
            )
        else:
            self._prev_pts = good_next.reshape(-1, 1, 2)

        return float(self._threat), self._last_side

    def reset(self):
        self._prev_gray  = None
        self._prev_pts   = None
        self._threat     = 0.0
        self._last_side  = None
        self._frame_n    = 0