from dataclasses import dataclass
from enum import Enum


class StimulusType(Enum):
    REWARD = "reward"
    THREAT = "threat"
    LIGHT = "light"


@dataclass
class Stimulus:

    type: StimulusType

    x: float
    y: float

    intensity: float

    