from vision.stimuli import Stimulus, StimulusType
from brain.stimulus_to_input import stimulus_to_inputs
from brain.reward import RewardCircuit


stimuli = [
    Stimulus(
        type=StimulusType.REWARD,
        x=0.15,
        y=0.50,
        intensity=0.8
    ),
    Stimulus(
        type=StimulusType.REWARD,
        x=0.80,
        y=0.40,
        intensity=0.6
    )
]


left, center, right = stimulus_to_inputs(stimuli)

print("=== STIMULUS → BRAIN ===")
print()
print(f"left   = {left:.3f}")
print(f"center = {center:.3f}")
print(f"right  = {right:.3f}")

print()
print("=== REWARD CIRCUIT ===")

circuit = RewardCircuit()

for step in range(30):
    result = circuit.step(
        left_input=left,
        center_input=center,
        right_input=right
    )

    if any(result.values()):
        print(
            f"step={step:02d} "
            f"left={result['left']} "
            f"center={result['center']} "
            f"right={result['right']}"
        )