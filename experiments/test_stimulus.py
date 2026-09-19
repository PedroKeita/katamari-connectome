import cv2

from vision.capture import ScreenCapture
from vision.detect import detect_items
from vision.stimuli import Stimulus, StimulusType


capture = ScreenCapture()

frame = capture.capture()

items, mask = detect_items(frame)

height, width = frame.shape[:2]

print()
print("=== FLY VISUAL SYSTEM ===")
print(f"Detected regions: {len(items)}")
print()

for item in items:

    x = item["x"] / width
    y = item["y"] / height

    intensity = min(
        item["area"] / 5000,
        1.0
    )

    stimulus = Stimulus(
        type=StimulusType.REWARD,
        x=x,
        y=y,
        intensity=intensity
    )

    print(stimulus)

    cv2.circle(
        frame,
        (item["x"], item["y"]),
        8,
        (0, 255, 0),
        2
    )

cv2.imwrite(
    "test_stimulus_result.png",
    frame
)

capture.close()

print()
print("Saved: test_stimulus_result.png")
