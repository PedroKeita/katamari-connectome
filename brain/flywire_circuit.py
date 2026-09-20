"""
FlyWireCircuit — LIF sobre subgrafo real do FlyWire.

Parâmetros baseados em Shiu et al. (Nature 2024):
  V_rest = V_reset = -52 mV
  V_thresh = -45 mV
  tau_m = 20 ms, t_ref = 2 ms, dt = 1 ms

Correções vs versão anterior:
  - output_lateralization: usa diferença direta L-R em vez de ratio
    (funciona com apenas 2 neurônios de saída como no escape)
  - stimulate_selective: estimula só uma fração dos ORNs em vez de todos
    (evita saturação no reward com 16900 entradas)
  - limiar de input assimétrico calibrado para o escape (1 passo ≈ suficiente)
"""

import numpy as np
from scipy import sparse
from .flywire_loader import ConnectomeCircuit


class FlyWireCircuit:

    def __init__(
        self,
        circuit:  ConnectomeCircuit,
        tau_m:    float = 20.0,
        V_rest:   float = -52.0,
        V_reset:  float = -52.0,
        V_thresh: float = -45.0,
        t_ref:    float = 2.0,
        dt:       float = 1.0,
        w_scale:  float = 0.05,
    ):
        self.circuit  = circuit
        self.tau_m    = tau_m
        self.V_rest   = V_rest
        self.V_reset  = V_reset
        self.V_thresh = V_thresh
        self.t_ref    = t_ref
        self.dt       = dt
        self.w_scale  = w_scale

        N = circuit.n_neurons
        self.V      = np.full(N, V_rest,  dtype=np.float32)
        self.ref    = np.zeros(N,          dtype=np.float32)
        self.spikes = np.zeros(N,          dtype=bool)

        self.W = circuit.weights.multiply(w_scale).tocsr().astype(np.float32)

    def reset(self):
        self.V[:]      = self.V_rest
        self.ref[:]    = 0.0
        self.spikes[:] = False

    def step(self, external_input: np.ndarray | None = None) -> np.ndarray:
        N = self.circuit.n_neurons

        if self.spikes.any():
            I_syn = np.array(self.W.T.dot(self.spikes.astype(np.float32))).flatten()
        else:
            I_syn = np.zeros(N, dtype=np.float32)

        if external_input is not None and len(self.circuit.input_idx) > 0:
            n = min(len(external_input), len(self.circuit.input_idx))
            I_syn[self.circuit.input_idx[:n]] += external_input[:n]

        active = self.ref <= 0
        dV = ((self.V_rest - self.V) / self.tau_m + I_syn) * self.dt
        self.V[active] += dV[active]
        self.spikes = (self.V >= self.V_thresh)
        self.V[self.spikes]     = self.V_reset
        self.ref[self.spikes]   = self.t_ref
        self.ref[self.ref > 0] -= self.dt

        return self.spikes.copy()

    def stimulate(
        self,
        input_currents: np.ndarray,
        n_steps: int = 30,
    ) -> tuple[np.ndarray, np.ndarray]:
        N = self.circuit.n_neurons
        all_spikes = np.zeros((n_steps, N), dtype=bool)

        n_in = len(self.circuit.input_idx)
        I_ext = np.zeros(n_in, dtype=np.float32)
        I_ext[:min(len(input_currents), n_in)] = input_currents[:min(len(input_currents), n_in)]

        for t in range(n_steps):
            all_spikes[t] = self.step(external_input=I_ext)

        output_rate = all_spikes[:, self.circuit.output_idx].mean(axis=0)
        return output_rate, all_spikes

    def output_lateralization(
        self,
        input_currents: np.ndarray,
        n_steps: int = 30,
    ) -> tuple[float, float, float]:
        """
        Retorna (left, center, right) ∈ [0, 1].

        Usa diferença direta L vs R em vez de ratio sobre total.
        Funciona com qualquer número de neurônios de saída, incluindo
        apenas 2 (como no escape circuit com DNp01 left + right).
        """
        spike_rate, _ = self.stimulate(input_currents, n_steps)

        out_sides = self.circuit.sides[self.circuit.output_idx]

        l_mask = out_sides == "left"
        r_mask = out_sides == "right"

        left_rate  = float(spike_rate[l_mask].mean()) if l_mask.any()  else 0.0
        right_rate = float(spike_rate[r_mask].mean()) if r_mask.any()  else 0.0

        # Centro = média geral (todos os neurônios de saída)
        center_rate = float(spike_rate.mean())

        # Normaliza para [0,1] individualmente, não como proporção do total
        # Isso preserva a assimetria mesmo quando L=0.2 e R=0.0
        max_rate = max(left_rate, right_rate, center_rate, 1e-9)
        return (
            float(np.clip(left_rate   / max_rate, 0, 1)),
            float(np.clip(center_rate / max_rate, 0, 1)),
            float(np.clip(right_rate  / max_rate, 0, 1)),
        )

    def stimulate_lateral(
        self,
        left_strength:  float,
        right_strength: float,
        n_steps: int = 30,
    ) -> tuple[float, float, float]:
        """
        Estimula os neurônios de entrada do lado esquerdo com left_strength
        e do lado direito com right_strength.

        Usa a lateralização anatômica dos neurônios de entrada para
        distribuir o estímulo — biologicamente mais correto do que
        simplesmente dividir o array pela metade.

        Retorna (left, center, right) de atividade nos neurônios de saída.
        """
        self.reset()

        in_sides = self.circuit.sides[self.circuit.input_idx]
        n_in     = len(self.circuit.input_idx)
        I_ext    = np.zeros(n_in, dtype=np.float32)

        l_in = in_sides == "left"
        r_in = in_sides == "right"

        # Neurônios de entrada sem lado anotado recebem média dos dois
        I_ext[l_in]           = left_strength
        I_ext[r_in]           = right_strength
        I_ext[~l_in & ~r_in] = (left_strength + right_strength) / 2.0

        return self.output_lateralization(I_ext, n_steps=n_steps)