from brain.domain.reward import RewardCircuit


circuit = RewardCircuit()

print("=== REWARD CIRCUIT TEST ===")

for step in range(30):
    result = circuit.step(
        left_input=0.08,
        center_input=0.03,
        right_input=0.12
    )

    print(
        f"step={step:02d} "
        f"left={result['left']} "
        f"center={result['center']} "
        f"right={result['right']}"
    )