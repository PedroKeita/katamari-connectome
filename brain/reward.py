from brain.neurons import LIFNeuron


class RewardCircuit:
    def __init__(self):
        self.left = LIFNeuron()
        self.center = LIFNeuron()
        self.right = LIFNeuron()

    def step(self, left_input, center_input, right_input):
        return {
            "left": self.left.step(left_input),
            "center": self.center.step(center_input),
            "right": self.right.step(right_input)
        }