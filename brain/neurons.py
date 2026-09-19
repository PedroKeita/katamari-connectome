class LIFNeuron:
    def __init__(
        self,
        threshold=1.0,
        resting_potential=0.0,
        reset_potential=0.0,
        tau=20.0
    ):
        self.threshold = threshold
        self.resting_potential = resting_potential
        self.reset_potential = reset_potential
        self.tau = tau

        self.potential = resting_potential
        self.spike = False

    def step(self, input_current, dt=1.0):
        self.spike = False

        # Leaky integration
        decay = (self.resting_potential - self.potential) / self.tau

        self.potential += (
            decay + input_current
        ) * dt

        # Fire
        if self.potential >= self.threshold:
            self.spike = True
            self.potential = self.reset_potential

        return self.spike