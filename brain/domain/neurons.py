"""Modelos neuronais pequenos usados pelos circuitos locais."""


class LIFNeuron:
    """Leaky Integrate-and-Fire neuron with one-step state updates."""

    def __init__(
        self,
        threshold: float = 1.0,
        resting_potential: float = 0.0,
        reset_potential: float = 0.0,
        tau: float = 20.0,
    ) -> None:
        self.threshold = threshold
        self.resting_potential = resting_potential
        self.reset_potential = reset_potential
        self.tau = tau

        self.potential = resting_potential
        self.spike = False

    def step(self, input_current: float, dt: float = 1.0) -> bool:
        """Integrate ``input_current`` and return whether the neuron spiked."""
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