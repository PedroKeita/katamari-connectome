from brain.neurons import LIFNeuron


neuron = LIFNeuron()

print("=== LIF NEURON TEST ===")

for step in range(30):
    spike = neuron.step(0.08)

    print(
        f"step={step:02d} "
        f"potential={neuron.potential:.3f} "
        f"spike={spike}"
    )