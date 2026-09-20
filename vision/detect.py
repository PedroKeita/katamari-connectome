"""

CollectionDetector reescrito com sinal dual confiável:
  dark_ratio  > 0.004  → círculo escuro de overlay presente
  bright_ratio > 0.005 → item 3D branco/claro visível dentro
  AMBOS necessários    → elimina falsos positivos
"""

import cv2
import numpy as np

# ------------------------------------------------------------------
# CONFIGURAÇÃO DE DETECÇÃO
# ------------------------------------------------------------------
CANNY_LOW  = 25
CANNY_HIGH = 75
MORPH_KERNEL = 3

AREA_MIN       = 100
AREA_MAX_RATIO = 0.035
ASPECT_MAX = 4.5
ASPECT_MIN = 0.22
COMPACTNESS_MIN = 0.10
NMS_OVERLAP = 0.30

W_PROXIMITY   = 0.60
W_COMPACTNESS = 0.25
W_SIZE        = 0.15

KATAMARI_CX = 0.50
KATAMARI_CY = 0.58
KATAMARI_RX = 0.13
KATAMARI_RY = 0.20

# ------------------------------------------------------------------
# ZONAS DE EXCLUSÃO DO HUD
# ------------------------------------------------------------------
HUD_ZONES = [
    (0.00, 0.00, 0.22, 0.26),   # flor de tamanho
    (0.70, 0.00, 1.00, 0.24),   # timer + dial
    (0.58, 0.58, 1.00, 1.00),   # primo verde + parede azul
]


# ------------------------------------------------------------------
# COLLECTION DETECTOR  (reescrito v2)
# ------------------------------------------------------------------

class CollectionDetector:
    """
    Detecta quando o jogo confirma uma coleta via notificação
    no canto inferior esquerdo.

    Sinal dual (ambos necessários):
      1. dark_ratio  > DARK_THRESH
         → círculo escuro de overlay presente na zona
      2. bright_ratio > BRIGHT_THRESH
         → item 3D branco/claro visível dentro do círculo

    Isso elimina:
      - Papéis/objetos brancos do cenário (sem círculo escuro)
      - Menus escuros (sem item brilhante)
      - Chão uniforme (nenhum dos dois)
    """

    # Zona de monitoramento (proporções do frame)
    ZONE = (0.02, 0.60, 0.22, 0.95)   # x1, y1, x2, y2

    # Thresholds validados empiricamente
    DARK_THRESH   = 0.004   # fração de pixels com V < 80
    BRIGHT_THRESH = 0.005   # fração de pixels com V > 200 e S < 50

    # Frames estáveis para confirmar (evita ruído de 1 frame)
    CONFIRM_FRAMES = 3

    # Cooldown após disparo (evita contar a mesma notificação várias vezes)
    COOLDOWN_FRAMES = 25   # ~0.8s a 30fps

    def __init__(self):
        self._active_frames = 0
        self._cooldown      = 0
        self.is_active      = False

    def check(self, frame: np.ndarray) -> bool:
        """
        Retorna True UMA VEZ no início de cada notificação.
        Atualiza self.is_active durante toda a notificação.
        """
        if self._cooldown > 0:
            self._cooldown -= 1
            self.is_active = False
            return False

        h, w = frame.shape[:2]
        x1 = int(w * self.ZONE[0]); y1 = int(h * self.ZONE[1])
        x2 = int(w * self.ZONE[2]); y2 = int(h * self.ZONE[3])

        zone = frame[y1:y2, x1:x2]
        total = zone.shape[0] * zone.shape[1]
        if total == 0:
            return False

        hsv = cv2.cvtColor(zone, cv2.COLOR_BGR2HSV)
        v   = hsv[:, :, 2]
        s   = hsv[:, :, 1]

        dark_ratio   = np.count_nonzero(v < 80)          / total
        bright_ratio = np.count_nonzero((v > 200) & (s < 50)) / total

        signal = dark_ratio > self.DARK_THRESH and bright_ratio > self.BRIGHT_THRESH

        if signal:
            self._active_frames += 1
        else:
            self._active_frames = 0

        self.is_active = signal

        if self._active_frames == self.CONFIRM_FRAMES:
            self._cooldown      = self.COOLDOWN_FRAMES
            self._active_frames = 0
            return True

        return False

    def reset(self):
        self._active_frames = 0
        self._cooldown      = 0
        self.is_active      = False


# ------------------------------------------------------------------
# DETECÇÃO DE ITENS
# ------------------------------------------------------------------

def _build_valid_mask(h, w):
    mask = np.ones((h, w), dtype=np.uint8) * 255
    for (nx1, ny1, nx2, ny2) in HUD_ZONES:
        x1 = int(w * nx1); y1 = int(h * ny1)
        x2 = int(w * nx2); y2 = int(h * ny2)
        mask[y1:y2, x1:x2] = 0
    kx  = int(w * KATAMARI_CX); ky  = int(h * KATAMARI_CY)
    krx = int(w * KATAMARI_RX); kry = int(h * KATAMARI_RY)
    cv2.ellipse(mask, (kx, ky), (krx, kry), 0, 0, 360, 0, -1)
    return mask


def _nms(candidates, overlap_thresh):
    if not candidates:
        return []
    by_score = sorted(candidates, key=lambda c: c["score"], reverse=True)
    kept = []
    for cand in by_score:
        ax1, ay1 = cand["x"], cand["y"]
        ax2, ay2 = ax1 + cand["width"], ay1 + cand["height"]
        area_a = cand["width"] * cand["height"]
        suppressed = False
        for k in kept:
            bx1, by1 = k["x"], k["y"]
            bx2, by2 = bx1 + k["width"], by1 + k["height"]
            area_b = k["width"] * k["height"]
            ix = max(0, min(ax2, bx2) - max(ax1, bx1))
            iy = max(0, min(ay2, by2) - max(ay1, by1))
            inter = ix * iy
            union = area_a + area_b - inter
            if union > 0 and inter / union > overlap_thresh:
                suppressed = True
                break
        if not suppressed:
            kept.append(cand)
    return kept


def detect_items(frame):
    h, w   = frame.shape[:2]
    screen = h * w

    gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges  = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)
    k      = np.ones((MORPH_KERNEL, MORPH_KERNEL), np.uint8)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, k)
    valid  = _build_valid_mask(h, w)
    closed = cv2.bitwise_and(closed, valid)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    attn_cx  = w * KATAMARI_CX
    attn_cy  = h * KATAMARI_CY
    max_dist = np.sqrt(w**2 + h**2)

    raw = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < AREA_MIN or area > screen * AREA_MAX_RATIO:
            continue
        x, y, cw, ch = cv2.boundingRect(c)
        cx = x + cw / 2; cy = y + ch / 2
        aspect = cw / max(ch, 1)
        if aspect > ASPECT_MAX or aspect < ASPECT_MIN:
            continue
        compact = area / max(cw * ch, 1)
        if compact < COMPACTNESS_MIN:
            continue
        dist      = np.sqrt((cx - attn_cx)**2 + (cy - attn_cy)**2)
        proximity = max(0.0, 1.0 - dist / max_dist)
        size_sc   = min(area / 2000.0, 1.0)
        comp_sc   = min(compact * 2.0, 1.0)
        score = proximity * W_PROXIMITY + comp_sc * W_COMPACTNESS + size_sc * W_SIZE
        raw.append({
            "x": x, "y": y, "width": cw, "height": ch,
            "center_x": int(cx), "center_y": int(cy),
            "area": float(area), "score": float(score),
        })

    items = _nms(raw, NMS_OVERLAP)
    items.sort(key=lambda c: c["score"], reverse=True)
    return items, closed


# ------------------------------------------------------------------
# DEBUG VISUAL
# ------------------------------------------------------------------

def draw_detections(frame, items, col_zone=None):
    debug = frame.copy()
    h, w  = frame.shape[:2]

    overlay = debug.copy()
    for (nx1, ny1, nx2, ny2) in HUD_ZONES:
        x1 = int(w*nx1); y1 = int(h*ny1)
        x2 = int(w*nx2); y2 = int(h*ny2)
        cv2.rectangle(overlay, (x1,y1), (x2,y2), (40,40,40), -1)
    cv2.addWeighted(overlay, 0.25, debug, 0.75, 0, debug)

    # Borda da zona de notificação
    z = CollectionDetector.ZONE
    cv2.rectangle(debug,
                  (int(w*z[0]), int(h*z[1])),
                  (int(w*z[2]), int(h*z[3])),
                  (0, 140, 255), 1)

    kx  = int(w * KATAMARI_CX); ky  = int(h * KATAMARI_CY)
    cv2.ellipse(debug, (kx, ky),
                (int(w*KATAMARI_RX), int(h*KATAMARI_RY)),
                0, 0, 360, (0,0,120), 1)
    cv2.drawMarker(debug, (kx, ky), (255,255,255), cv2.MARKER_CROSS, 20, 1)

    for idx, item in enumerate(items):
        x, y   = item["x"], item["y"]
        bw, bh = item["width"], item["height"]
        sc     = item["score"]
        icx, icy = item["center_x"], item["center_y"]

        green = int(255 * min(sc * 2, 1.0))
        red   = int(255 * max(0, 1 - sc * 2))
        color = (0, green, red)

        cv2.rectangle(debug, (x,y), (x+bw,y+bh), color, 2)
        label = f"#{idx} {sc:.2f}"
        cv2.putText(debug, label, (x, max(y-4,12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,0,0), 3, cv2.LINE_AA)
        cv2.putText(debug, label, (x, max(y-4,12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)

        if idx == 0:
            cv2.line(debug, (kx,ky), (icx,icy), (0,0,255), 2)
            cv2.circle(debug, (icx,icy), 28, (0,0,255), 2)
            cv2.putText(debug, "FOCUS", (icx+32,icy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(debug, "FOCUS", (icx+32,icy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,255), 2, cv2.LINE_AA)

    return debug