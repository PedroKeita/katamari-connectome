"""Minimal reward circuit composed of three independent LIF neurons."""

from typing import TypedDict

from brain.domain.neurons import LIFNeuron


class RewardSpikes(TypedDict):
    """Spike state for the left, center and right sensory channels."""

    left: bool
    center: bool
    right: bool


class RewardCircuit:
    """Convert three continuous sensory channels into spike events."""

    def __init__(self) -> None:
        self.left = LIFNeuron()
        self.center = LIFNeuron()
        self.right = LIFNeuron()

    def step(
        self,
        left_input: float,
        center_input: float,
        right_input: float,
    ) -> RewardSpikes:
        """Advance all channels and return their current spike states."""
        return {
            "left": self.left.step(left_input),
            "center": self.center.step(center_input),
            "right": self.right.step(right_input)
        }