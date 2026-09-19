import os

import cv2

from vision.capture import ScreenCapture
from vision.perception import detect_candidates


os.makedirs("debug", exist_ok=True)

capture = ScreenCapture()

print("=== PERCEPTION TEST ===")
print()

try:
    frame = capture.capture()

    candidates, debug = detect_candidates(frame)

    print(f"Candidates: {len(candidates)}")
    print()

    output = frame.copy()

    for index, candidate in enumerate(candidates):

        x = candidate.x
        y = candidate.y
        w = candidate.width
        h = candidate.height

        cv2.rectangle(
            output,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            output,
            f"#{index} S={candidate.score:.2f}",
            (x, max(y - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )

    cv2.imwrite(
        "debug/perception.png",
        output
    )

    cv2.imwrite(
        "debug/perception_edges.png",
        debug
    )

    print("Saved:")
    print("  debug/perception.png")
    print("  debug/perception_edges.png")

finally:
    capture.close()

print()
print("=== TEST FINISHED ===")