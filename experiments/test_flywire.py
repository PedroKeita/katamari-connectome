import sys, os, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.loaders.flywire import FlyWireLoader
from brain.circuits.flywire import FlyWireCircuit


def test_circuit(name, circuit, n_steps=30):
    print(f"\n{'='*55}")
    print(f"CIRCUITO: {name.upper()}")
    print('='*55)
    print(circuit.summary())
    left  = np.sum(circuit.sides == "left")
    right = np.sum(circuit.sides == "right")
    print(f"  Lateralização total: {left} esq / {right} dir")

    in_sides = circuit.sides[circuit.input_idx]
    print(f"  Entradas: {np.sum(in_sides=='left')} esq / {np.sum(in_sides=='right')} dir")

    out_sides = circuit.sides[circuit.output_idx]
    print(f"  Saídas:   {np.sum(out_sides=='left')} esq / {np.sum(out_sides=='right')} dir")

    sim = FlyWireCircuit(circuit)

    # --- Estímulo uniforme (mesma força em todos os lados) ---
    n_in = len(circuit.input_idx)
    I_uni = np.ones(n_in, dtype=np.float32) * 2.0
    t0 = time.time()
    rate, spk = sim.stimulate(I_uni, n_steps=n_steps)
    ms = (time.time() - t0) * 1000

    print(f"\n  Uniforme ({n_steps} passos, {ms:.0f}ms):")
    print(f"    Ativos: {spk.any(axis=0).sum()}/{circuit.n_neurons}")
    print(f"    Taxa saída média/máx: {rate.mean():.4f} / {rate.max():.4f}")
    sim.reset()
    L, C, R = sim.output_lateralization(I_uni, n_steps=n_steps)
    print(f"    L/C/R: {L:.3f} / {C:.3f} / {R:.3f}")

    # --- Estímulo lateral (usa lateralização anatômica real) ---
    print(f"\n  Lateral (esq=3.0, dir=0.5):")
    L2, C2, R2 = sim.stimulate_lateral(3.0, 0.5, n_steps=n_steps)
    diff = L2 - R2
    print(f"    L/C/R: {L2:.3f} / {C2:.3f} / {R2:.3f}  Δ={diff:+.3f}")
    print(f"    {'✓ assimetria detectada' if abs(diff) > 0.05 else '✗ sem assimetria'}")

    print(f"\n  Lateral (esq=0.5, dir=3.0):")
    L3, C3, R3 = sim.stimulate_lateral(0.5, 3.0, n_steps=n_steps)
    diff2 = R3 - L3
    print(f"    L/C/R: {L3:.3f} / {C3:.3f} / {R3:.3f}  Δ={diff2:+.3f}")
    print(f"    {'✓ assimetria detectada' if abs(diff2) > 0.05 else '✗ sem assimetria'}")


if __name__ == "__main__":
    print("=== TEST FLYWIRE CIRCUITS ===")
    loader = FlyWireLoader(data_dir="data", min_weight=3)

    for name, fn in [
        ("reward",      loader.load_reward_circuit),
        ("escape",      loader.load_escape_circuit),
        ("orientation", loader.load_orientation_circuit),
    ]:
        print(f"\nCarregando {name}...")
        try:
            test_circuit(name, fn())
        except Exception as e:
            import traceback; traceback.print_exc()

    print("\n=== CONCLUÍDO ===")