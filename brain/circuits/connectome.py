"""Data model shared by connectome loaders and neural circuits."""

from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass
class ConnectomeCircuit:
    """Immutable-shape description of a neural connectome subgraph."""

    name: str
    neuron_ids: np.ndarray
    weights: sparse.csr_matrix
    input_idx: np.ndarray
    output_idx: np.ndarray
    sides: np.ndarray
    cell_types: np.ndarray

    @property
    def n_neurons(self) -> int:
        """Return the number of neurons in the subgraph."""
        return len(self.neuron_ids)

    @property
    def n_synapses(self) -> int:
        """Return the number of non-zero synaptic connections."""
        return self.weights.nnz

    def summary(self) -> str:
        """Return a concise human-readable circuit summary."""
        return (
            f"[{self.name}] "
            f"{self.n_neurons} neurônios, "
            f"{self.n_synapses} sinapses, "
            f"{len(self.input_idx)} entradas, "
            f"{len(self.output_idx)} saídas"
        )
