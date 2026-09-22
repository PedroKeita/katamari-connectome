from dataclasses import dataclass, field

from .stimuli import Stimulus


@dataclass
class StimulusMap:

    stimuli: list[Stimulus] = field(
        default_factory=list
    )

    def add(self, stimulus):
        self.stimuli.append(stimulus)

    @property
    def rewards(self):

        return [
            stimulus
            for stimulus in self.stimuli
            if stimulus.type.value == "reward"
        ]