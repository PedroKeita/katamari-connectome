import math
import os
import time

import cv2

from vision.capture import ScreenCapture
from vision.detection.items import detect_items


capture = ScreenCapture()

os.makedirs("debug", exist_ok=True)

print("=== FLY ATTENTION TEST ===")
print()


try:
    for snapshot in range(1, 6):

        frame = capture.capture()

        items, _ = detect_items(frame)

        height, width = frame.shape[:2]

        stimuli = []

        max_distance = math.sqrt(
            (0.5 ** 2) +
            (0.5 ** 2)
        )

        for item in items:

            x = item["x"] / width
            y = item["y"] / height

            intensity = min(
                item["area"] / 5000,
                1.0
            )

            # -----------------------------------------
            # 1. POSIÇÃO
            # -----------------------------------------

            distance = math.sqrt(
                (x - 0.5) ** 2 +
                (y - 0.5) ** 2
            )

            position_score = 1.0 - (
                distance / max_distance
            )

            position_score = max(
                0.0,
                min(position_score, 1.0)
            )

            # -----------------------------------------
            # 2. TAMANHO
            # -----------------------------------------

            size_score = min(
                item["area"] / 5000,
                1.0
            )

            # -----------------------------------------
            # 3. INTENSIDADE
            # -----------------------------------------

            intensity_score = intensity

            # -----------------------------------------
            # ATENÇÃO
            # -----------------------------------------

            attention = (
                position_score * 0.5
                + size_score * 0.3
                + intensity_score * 0.2
            )

            stimuli.append({
                "x": x,
                "y": y,
                "area": item["area"],
                "intensity": intensity,
                "position": position_score,
                "size": size_score,
                "attention": attention,
                "pixel_x": item["x"],
                "pixel_y": item["y"]
            })

        # Maior atenção primeiro
        stimuli.sort(
            key=lambda stimulus: stimulus["attention"],
            reverse=True
        )

        # =============================================
        # TERMINAL
        # =============================================

        print("=" * 70)
        print(f"SNAPSHOT {snapshot}/5")
        print("=" * 70)

        print(f"Items detected: {len(stimuli)}")
        print()

        print("ATTENTION:")
        print()

        for index, stimulus in enumerate(stimuli):

            print(
                f"[{index:02d}] "
                f"x={stimulus['x']:.3f} "
                f"y={stimulus['y']:.3f} "
                f"position={stimulus['position']:.3f} "
                f"size={stimulus['size']:.3f} "
                f"intensity={stimulus['intensity']:.3f} "
                f"attention={stimulus['attention']:.3f}"
            )

        # =============================================
        # DEBUG IMAGE
        # =============================================

        debug_frame = frame.copy()

        center_x = width // 2
        center_y = height // 2

        # Centro da visão
        cv2.drawMarker(
            debug_frame,
            (center_x, center_y),
            (255, 255, 255),
            cv2.MARKER_CROSS,
            30,
            2
        )

        # ---------------------------------------------
        # TODOS OS ESTÍMULOS
        # ---------------------------------------------

        for index, stimulus in enumerate(stimuli):

            px = stimulus["pixel_x"]
            py = stimulus["pixel_y"]

            attention = stimulus["attention"]

            radius = int(
                8 + attention * 25
            )

            cv2.circle(
                debug_frame,
                (px, py),
                radius,
                (0, 255, 0),
                2
            )

            label = (
                f"#{index} "
                f"A={attention:.2f}"
            )

            cv2.putText(
                debug_frame,
                label,
                (px + 8, py - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )

        # ---------------------------------------------
        # FOCUS
        # ---------------------------------------------

        if stimuli:

            focus = stimuli[0]

            focus_x = focus["pixel_x"]
            focus_y = focus["pixel_y"]

            cv2.line(
                debug_frame,
                (center_x, center_y),
                (focus_x, focus_y),
                (0, 0, 255),
                3
            )

            cv2.circle(
                debug_frame,
                (focus_x, focus_y),
                35,
                (0, 0, 255),
                3
            )

            cv2.putText(
                debug_frame,
                "FOCUS",
                (focus_x + 40, focus_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

        # ---------------------------------------------
        # SALVAR
        # ---------------------------------------------

        filename = (
            f"debug/attention_{snapshot:02d}.png"
        )

        cv2.imwrite(
            filename,
            debug_frame
        )

        print()
        print(f"Saved: {filename}")
        print()

        if snapshot < 5:
            time.sleep(1)

finally:

    capture.close()


print("=== TEST FINISHED ===")