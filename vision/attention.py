from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass
class AttentionCandidate:
    center_x: int
    center_y: int
    width: int
    height: int
    area: float
    score: float


def detect_attention_candidates(frame):
    height, width = frame.shape[:2]

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    saturation = hsv[:, :, 1]
    brightness = hsv[:, :, 2]

    # --------------------------------------------------
    # 1. REGIÕES COLORIDAS
    # --------------------------------------------------

    mask = (
        (saturation > 70) &
        (brightness > 80)
    ).astype(np.uint8) * 255

    # Junta pequenos fragmentos pertencentes ao mesmo objeto
    kernel = np.ones((7, 7), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    screen_area = width * height

    for contour in contours:

        area = cv2.contourArea(contour)

        # --------------------------------------------------
        # FILTRO DE TAMANHO
        # --------------------------------------------------

        if area < 250:
            continue

        if area > screen_area * 0.08:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        # --------------------------------------------------
        # FILTRO DE PROPORÇÃO
        # --------------------------------------------------

        aspect_ratio = w / max(h, 1)

        if aspect_ratio > 8:
            continue

        if aspect_ratio < 0.12:
            continue

        center_x = x + w // 2
        center_y = y + h // 2

        nx = center_x / width
        ny = center_y / height

        # --------------------------------------------------
        # DISTÂNCIA DO CENTRO
        # --------------------------------------------------

        distance = math.sqrt(
            (nx - 0.5) ** 2 +
            (ny - 0.5) ** 2
        )

        max_distance = math.sqrt(0.5 ** 2 + 0.5 ** 2)

        position_score = 1.0 - (
            distance / max_distance
        )

        position_score = max(
            0.0,
            min(position_score, 1.0)
        )

        # --------------------------------------------------
        # TAMANHO
        # --------------------------------------------------

        size_score = min(
            area / 8000.0,
            1.0
        )

        # --------------------------------------------------
        # COMPACTAÇÃO
        #
        # Objetos mais compactos recebem preferência.
        # --------------------------------------------------

        bounding_area = w * h

        compactness = area / max(
            bounding_area,
            1
        )

        compactness_score = min(
            compactness * 1.5,
            1.0
        )

        # --------------------------------------------------
        # SCORE FINAL
        # --------------------------------------------------

        score = (
            position_score * 0.55
            + size_score * 0.20
            + compactness_score * 0.25
        )

        candidates.append(
            AttentionCandidate(
                center_x=center_x,
                center_y=center_y,
                width=w,
                height=h,
                area=area,
                score=score
            )
        )

    # --------------------------------------------------
    # MAIOR ATENÇÃO PRIMEIRO
    # --------------------------------------------------

    candidates.sort(
        key=lambda candidate: candidate.score,
        reverse=True
    )

    return candidates


def draw_attention(frame, candidates):

    debug = frame.copy()

    height, width = frame.shape[:2]

    center_x = width // 2
    center_y = height // 2

    # --------------------------------------------------
    # CENTRO DA VISÃO
    # --------------------------------------------------

    cv2.drawMarker(
        debug,
        (center_x, center_y),
        (255, 255, 255),
        cv2.MARKER_CROSS,
        30,
        2
    )

    # --------------------------------------------------
    # CANDIDATOS
    # --------------------------------------------------

    for index, candidate in enumerate(candidates):

        x = candidate.center_x
        y = candidate.center_y

        radius = int(
            8 + candidate.score * 35
        )

        cv2.circle(
            debug,
            (x, y),
            radius,
            (0, 255, 0),
            2
        )

        label = (
            f"#{index} "
            f"A={candidate.score:.2f}"
        )

        cv2.putText(
            debug,
            label,
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

    # --------------------------------------------------
    # FOCO
    # --------------------------------------------------

    if candidates:

        focus = candidates[0]

        focus_x = focus.center_x
        focus_y = focus.center_y

        cv2.line(
            debug,
            (center_x, center_y),
            (focus_x, focus_y),
            (0, 0, 255),
            3
        )

        cv2.circle(
            debug,
            (focus_x, focus_y),
            35,
            (0, 0, 255),
            3
        )

        cv2.putText(
            debug,
            "FOCUS",
            (focus_x + 40, focus_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

    return debug