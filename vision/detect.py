"""
vision/detect.py  —  Katamari item detector (v3)

Abordagem: detecção por BORDAS (Canny + contornos fechados).
O filtro HSV puro falhou porque o chão rosa tem quase o mesmo
H/S/V dos objetos colectáveis. Borda + forma fechada funciona
para qualquer cor de objeto.

Retorna:
    items — lista de dicts compatível com o resto do projeto:
            x, y, width, height, center_x, center_y, area, score
    mask  — imagem de debug (bordas fechadas, uint8 grayscale)
"""

import cv2
import numpy as np

# ------------------------------------------------------------------
# CONFIGURAÇÃO — ajuste aqui sem mexer na lógica
# ------------------------------------------------------------------

# Canny thresholds — quanto menor, mais bordas detecta
CANNY_LOW  = 25
CANNY_HIGH = 75

# Tamanho do kernel morfológico para fechar buracos nas bordas
# (3 = conservador; 5 = fecha gaps maiores mas pode fundir objetos)
MORPH_KERNEL = 3

# Filtros de área (pixels)
AREA_MIN       = 100
AREA_MAX_RATIO = 0.035   # até 3.5 % da tela

# Proporção W/H — exclui faixas muito finas
ASPECT_MAX = 4.5
ASPECT_MIN = 0.22

# Compacidade mínima (area_contorno / area_bbox)
COMPACTNESS_MIN = 0.10

# HUD: faixa do topo a ignorar (proporção da altura)
HUD_TOP_RATIO = 0.16

# Zona de exclusão do Katamari+Prince (elipse)
KATAMARI_CX = 0.42   # centro x (normalizado)
KATAMARI_CY = 0.55   # centro y (ligeiramente abaixo do meio)
KATAMARI_RX = 0.14   # raio x
KATAMARI_RY = 0.22   # raio y

# Non-Maximum Suppression — IoU máximo entre dois candidatos
NMS_OVERLAP = 0.30

# Pesos do score
W_PROXIMITY    = 0.60
W_COMPACTNESS  = 0.25
W_SIZE         = 0.15

# ------------------------------------------------------------------


def detect_items(frame):
    """
    Detecta objetos colectáveis por bordas + forma fechada.

    Retorna:
        items  — lista de dicts: x, y, width, height,
                 center_x, center_y, area, score
        mask   — imagem de bordas fechadas (uint8, para debug)
    """
    h, w   = frame.shape[:2]
    screen = h * w

    # --------------------------------------------------
    # 1. DETECÇÃO DE BORDAS
    # --------------------------------------------------
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, CANNY_LOW, CANNY_HIGH)

    # Fecha pequenos buracos para formar contornos fechados
    k      = np.ones((MORPH_KERNEL, MORPH_KERNEL), np.uint8)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, k)

    # --------------------------------------------------
    # 2. CONTORNOS
    # --------------------------------------------------
    contours, _ = cv2.findContours(
        closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Parâmetros de exclusão em pixels
    hud_top = int(h * HUD_TOP_RATIO)
    kx  = int(w * KATAMARI_CX)
    ky  = int(h * KATAMARI_CY)
    krx = int(w * KATAMARI_RX)
    kry = int(h * KATAMARI_RY)

    # Ponto de atenção: ligeiramente à frente do Katamari
    attn_cx = kx
    attn_cy = ky
    max_dist = np.sqrt(w**2 + h**2)

    raw = []

    for c in contours:
        area = cv2.contourArea(c)

        if area < AREA_MIN or area > screen * AREA_MAX_RATIO:
            continue

        x, y, cw, ch = cv2.boundingRect(c)
        cx = x + cw / 2
        cy = y + ch / 2

        # --- Exclusão de HUD ---
        if cy < hud_top:
            continue

        # --- Exclusão da zona do Katamari ---
        ell = ((cx - kx) / krx) ** 2 + ((cy - ky) / kry) ** 2
        if ell < 1.0:
            continue

        # --- Proporção ---
        aspect = cw / max(ch, 1)
        if aspect > ASPECT_MAX or aspect < ASPECT_MIN:
            continue

        # --- Compacidade ---
        compact = area / max(cw * ch, 1)
        if compact < COMPACTNESS_MIN:
            continue

        # --- Score ---
        dist       = np.sqrt((cx - attn_cx)**2 + (cy - attn_cy)**2)
        proximity  = max(0.0, 1.0 - dist / max_dist)
        size_score = min(area / 2000.0, 1.0)
        comp_score = min(compact * 2.0, 1.0)

        score = (
            proximity  * W_PROXIMITY +
            comp_score * W_COMPACTNESS +
            size_score * W_SIZE
        )

        raw.append({
            "x":        x,
            "y":        y,
            "width":    cw,
            "height":   ch,
            "center_x": int(cx),
            "center_y": int(cy),
            "area":     float(area),
            "score":    float(score),
        })

    # --------------------------------------------------
    # 3. NON-MAXIMUM SUPPRESSION
    # --------------------------------------------------
    items = _nms(raw, NMS_OVERLAP)
    items.sort(key=lambda c: c["score"], reverse=True)

    return items, closed


def _nms(candidates, overlap_thresh):
    if not candidates:
        return []

    by_score = sorted(candidates, key=lambda c: c["score"], reverse=True)
    kept = []

    for cand in by_score:
        ax1 = cand["x"]
        ay1 = cand["y"]
        ax2 = ax1 + cand["width"]
        ay2 = ay1 + cand["height"]
        area_a = cand["width"] * cand["height"]

        suppressed = False
        for k in kept:
            bx1 = k["x"]
            by1 = k["y"]
            bx2 = bx1 + k["width"]
            by2 = by1 + k["height"]
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


# ------------------------------------------------------------------
# DEBUG VISUAL
# ------------------------------------------------------------------

def draw_detections(frame, items):
    """Desenha bounding boxes sobre o frame. Retorna cópia."""
    debug = frame.copy()
    h, w  = frame.shape[:2]

    kx = int(w * KATAMARI_CX)
    ky = int(h * KATAMARI_CY)

    # Zona de exclusão (vermelho tracejado)
    cv2.ellipse(debug, (kx, ky),
                (int(w * KATAMARI_RX), int(h * KATAMARI_RY)),
                0, 0, 360, (0, 0, 180), 1)

    # Cruz de atenção
    cv2.drawMarker(debug, (kx, ky), (255, 255, 255),
                   cv2.MARKER_CROSS, 20, 1)

    for idx, item in enumerate(items):
        x  = item["x"]
        y  = item["y"]
        bw = item["width"]
        bh = item["height"]
        sc = item["score"]
        cx = item["center_x"]
        cy = item["center_y"]

        # Cor: verde brilhante para top, amarelo para médio
        green = int(255 * min(sc * 2, 1.0))
        red   = int(255 * max(0, 1 - sc * 2))
        color = (0, green, red)

        cv2.rectangle(debug, (x, y), (x + bw, y + bh), color, 2)

        label = f"#{idx} {sc:.2f}"
        cv2.putText(debug, label,
                    (x, max(y - 4, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(debug, label,
                    (x, max(y - 4, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    color, 1, cv2.LINE_AA)

        # Linha e círculo de FOCUS no item de maior score
        if idx == 0:
            cv2.line(debug, (kx, ky), (cx, cy), (0, 0, 255), 2)
            cv2.circle(debug, (cx, cy), 28, (0, 0, 255), 2)
            cv2.putText(debug, "FOCUS",
                        (cx + 32, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(debug, "FOCUS",
                        (cx + 32, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 0, 255), 2, cv2.LINE_AA)

    return debug