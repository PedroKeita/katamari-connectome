import cv2
import numpy as np


class PerceptionCandidate:
    def __init__(self, x, y, width, height, score=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.score = score

    @property
    def center_x(self):
        return self.x + self.width / 2

    @property
    def center_y(self):
        return self.y + self.height / 2

    @property
    def area(self):
        return self.width * self.height


def detect_candidates(frame):
    """
    Detecta possíveis objetos próximos ao centro da tela.

    Nesta primeira versão:
    - não tenta reconhecer o objeto;
    - usa bordas/contraste;
    - ignora o HUD;
    - ignora a região central do personagem/Katamari.
    """

    height, width = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detecta bordas.
    edges = cv2.Canny(gray, 60, 140)

    # Fecha pequenos espaços nas bordas.
    kernel = np.ones((5, 5), np.uint8)

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )

    # --------------------------------------------------
    # REGIÃO DE INTERESSE
    # --------------------------------------------------

    roi_mask = np.zeros_like(edges)

    # Região central onde normalmente estão os objetos
    # próximos do Katamari.
    center_x = width // 2
    center_y = int(height * 0.55)

    roi_radius_x = int(width * 0.42)
    roi_radius_y = int(height * 0.38)

    cv2.ellipse(
        roi_mask,
        (center_x, center_y),
        (roi_radius_x, roi_radius_y),
        0,
        0,
        360,
        255,
        -1
    )

    edges = cv2.bitwise_and(edges, roi_mask)

    # --------------------------------------------------
    # IGNORAR CENTRO
    # --------------------------------------------------

    # O centro contém principalmente o Prince/Katamari.
    # Não queremos transformar o personagem em dezenas
    # de candidatos.
    cv2.ellipse(
        edges,
        (center_x, center_y),
        (int(width * 0.10), int(height * 0.16)),
        0,
        0,
        360,
        0,
        -1
    )

    # --------------------------------------------------
    # CONTORNOS
    # --------------------------------------------------

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)

        area = w * h

        # Muito pequeno.
        if area < 300:
            continue

        # Muito grande provavelmente é cenário.
        if area > width * height * 0.12:
            continue

        # Linhas extremamente finas normalmente são
        # cabos, bordas ou detalhes do cenário.
        if w < 12 or h < 12:
            continue

        aspect_ratio = w / max(h, 1)

        if aspect_ratio > 8 or aspect_ratio < 0.125:
            continue

        # Centro do candidato.
        cx = x + w / 2
        cy = y + h / 2

        # Distância normalizada ao centro.
        dx = (cx - center_x) / width
        dy = (cy - center_y) / height

        distance = np.sqrt(dx * dx + dy * dy)

        # Quanto mais perto do Katamari, maior o score.
        proximity = max(
            0.0,
            1.0 - distance * 2.5
        )

        # Objetos com área moderada são interessantes.
        size_score = min(
            area / 10000.0,
            1.0
        )

        score = (
            proximity * 0.65 +
            size_score * 0.35
        )

        candidates.append(
            PerceptionCandidate(
                x=x,
                y=y,
                width=w,
                height=h,
                score=float(score)
            )
        )

    candidates.sort(
        key=lambda candidate: candidate.score,
        reverse=True
    )

    return candidates, edges