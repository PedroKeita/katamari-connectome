import cv2
import numpy as np
import os

from vision.capture import ScreenCapture


capture = ScreenCapture()

os.makedirs("debug", exist_ok=True)

print("=== OBJECT DETECTION DIAGNOSTIC ===")
print()

try:

    frame = capture.capture()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    saturation = hsv[:, :, 1]
    brightness = hsv[:, :, 2]

    # ==================================================
    # COLOR
    # ==================================================

    color_mask = (
        (saturation > 80) &
        (brightness > 100)
    ).astype(np.uint8) * 255

    # ==================================================
    # NEUTRAL / WHITE
    # ==================================================

    neutral_mask = (
        (saturation < 80) &
        (brightness > 140)
    ).astype(np.uint8) * 255

    # ==================================================
    # EDGES
    # ==================================================

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    # ==================================================
    # CONTORNO COLOR
    # ==================================================

    color_contours, _ = cv2.findContours(
        color_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    color_objects = []

    for contour in color_contours:

        area = cv2.contourArea(contour)

        if 300 <= area <= 30000:
            x, y, w, h = cv2.boundingRect(contour)

            color_objects.append(
                (x, y, w, h, area)
            )

    # ==================================================
    # CONTORNO NEUTRAL
    # ==================================================

    neutral_contours, _ = cv2.findContours(
        neutral_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    neutral_objects = []

    for contour in neutral_contours:

        area = cv2.contourArea(contour)

        if 300 <= area <= 30000:
            x, y, w, h = cv2.boundingRect(contour)

            neutral_objects.append(
                (x, y, w, h, area)
            )

    # ==================================================
    # CONTORNO EDGES
    # ==================================================

    edge_contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    edge_objects = []

    for contour in edge_contours:

        area = cv2.contourArea(contour)

        if 300 <= area <= 30000:
            x, y, w, h = cv2.boundingRect(contour)

            edge_objects.append(
                (x, y, w, h, area)
            )

    print(f"Color candidates:   {len(color_objects)}")
    print(f"Neutral candidates: {len(neutral_objects)}")
    print(f"Edge candidates:    {len(edge_objects)}")
    print()

    # ==================================================
    # IMAGES
    # ==================================================

    color_debug = frame.copy()

    for index, (x, y, w, h, area) in enumerate(color_objects):

        cv2.rectangle(
            color_debug,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            color_debug,
            f"#{index}",
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    neutral_debug = frame.copy()

    for index, (x, y, w, h, area) in enumerate(neutral_objects):

        cv2.rectangle(
            neutral_debug,
            (x, y),
            (x + w, y + h),
            (255, 0, 0),
            2
        )

        cv2.putText(
            neutral_debug,
            f"#{index}",
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1
        )

    edge_debug = frame.copy()

    for index, (x, y, w, h, area) in enumerate(edge_objects):

        cv2.rectangle(
            edge_debug,
            (x, y),
            (x + w, y + h),
            (0, 255, 255),
            2
        )

        cv2.putText(
            edge_debug,
            f"#{index}",
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1
        )

    # ==================================================
    # SAVE
    # ==================================================

    cv2.imwrite(
        "debug/detection_color.png",
        color_debug
    )

    cv2.imwrite(
        "debug/detection_neutral.png",
        neutral_debug
    )

    cv2.imwrite(
        "debug/detection_edges.png",
        edge_debug
    )

    cv2.imwrite(
        "debug/mask_color.png",
        color_mask
    )

    cv2.imwrite(
        "debug/mask_neutral.png",
        neutral_mask
    )

    cv2.imwrite(
        "debug/mask_edges.png",
        edges
    )

    print("Saved:")
    print("  debug/detection_color.png")
    print("  debug/detection_neutral.png")
    print("  debug/detection_edges.png")
    print("  debug/mask_color.png")
    print("  debug/mask_neutral.png")
    print("  debug/mask_edges.png")

finally:

    capture.close()

print()
print("=== TEST FINISHED ===")