import cv2
import numpy as np


def detect_items(frame):

    hsv = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2HSV
    )

    saturation = hsv[:, :, 1]
    brightness = hsv[:, :, 2]

    mask = (
        (saturation > 80) &
        (brightness > 100)
    ).astype(np.uint8) * 255

    kernel = np.ones(
        (5, 5),
        np.uint8
    )

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

    items = []

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < 200:
            continue

        moments = cv2.moments(contour)

        if moments["m00"] == 0:
            continue

        cx = int(
            moments["m10"] /
            moments["m00"]
        )

        cy = int(
            moments["m01"] /
            moments["m00"]
        )

        items.append({
            "x": cx,
            "y": cy,
            "area": area
        })

    return items, mask