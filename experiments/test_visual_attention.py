import os

import cv2

from vision.capture import ScreenCapture
from vision.detection.attention import (
    detect_attention_candidates,
    draw_attention
)


print("=== FLY VISUAL ATTENTION TEST ===")
print()

capture = ScreenCapture()

try:
    frame = capture.capture()

    candidates = detect_attention_candidates(frame)

    print(f"Candidates: {len(candidates)}")
    print()

    print("ATTENTION:")

    for index, candidate in enumerate(candidates):

        print(
            f"[{index:02d}] "
            f"x={candidate.center_x / frame.shape[1]:.3f} "
            f"y={candidate.center_y / frame.shape[0]:.3f} "
            f"width={candidate.width} "
            f"height={candidate.height} "
            f"attention={candidate.score:.3f}"
        )

    print()

    if candidates:

        focus = candidates[0]

        print("FOCUS:")
        print(
            f"x={focus.center_x / frame.shape[1]:.3f}"
        )
        print(
            f"y={focus.center_y / frame.shape[0]:.3f}"
        )
        print(
            f"attention={focus.score:.3f}"
        )

    result = draw_attention(
        frame,
        candidates
    )

    os.makedirs("debug", exist_ok=True)

    output = "debug/visual_attention.png"

    cv2.imwrite(
        output,
        result
    )

    print()
    print(f"Saved: {output}")

finally:
    capture.close()

print()
print("=== TEST FINISHED ===")