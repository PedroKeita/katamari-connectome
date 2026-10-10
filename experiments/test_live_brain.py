import time

from vision.capture import ScreenCapture
from vision.detection.items import detect_items
from vision.stimuli import Stimulus, StimulusType
from brain.stimulus_to_input import stimulus_to_inputs
from brain.domain.reward import RewardCircuit


capture = ScreenCapture()
circuit = RewardCircuit()

print("=== FLY BRAIN SNAPSHOT TEST ===")
print("Serão feitas 10 capturas.")
print()

try:
    for snapshot in range(10):

        frame = capture.capture()

        items, _ = detect_items(frame)

        height, width = frame.shape[:2]

        stimuli = []

        for item in items:
            stimulus = Stimulus(
                type=StimulusType.REWARD,
                x=item["x"] / width,
                y=item["y"] / height,
                intensity=min(item["area"] / 5000, 1.0)
            )

            stimuli.append(stimulus)

        left, center, right = stimulus_to_inputs(stimuli)

        spikes = circuit.step(
            left_input=left,
            center_input=center,
            right_input=right
        )

        print("=" * 60)
        print(f"SNAPSHOT {snapshot + 1}/10")
        print("=" * 60)

        print(f"Frame: {width}x{height}")
        print(f"Items detected: {len(items)}")

        print()
        print("STIMULI:")

        for index, stimulus in enumerate(stimuli):
            print(
                f"  [{index:02d}] "
                f"x={stimulus.x:.3f} "
                f"y={stimulus.y:.3f} "
                f"intensity={stimulus.intensity:.3f}"
            )

        print()
        print("BRAIN INPUT:")

        print(f"  LEFT   = {left:.3f}")
        print(f"  CENTER = {center:.3f}")
        print(f"  RIGHT  = {right:.3f}")

        print()
        print("SPIKES:")

        print(f"  LEFT   = {spikes['left']}")
        print(f"  CENTER = {spikes['center']}")
        print(f"  RIGHT  = {spikes['right']}")

        print()

        if snapshot < 9:
            time.sleep(1)

finally:
    capture.close()

print("=== TEST FINISHED ===")