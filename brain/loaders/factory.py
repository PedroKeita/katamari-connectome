"""
brain/loaders.py — Funções de carregamento dos circuitos neurais

Cada função tenta carregar um circuito do conectoma FlyWire v783.
Retorna None silenciosamente se os dados não existirem ou ocorrer erro.
"""

import logging
import os

logger = logging.getLogger(__name__)

_ANNOTATIONS = "neuron_annotations.tsv"


def _data_ok(data_dir: str) -> bool:
    return os.path.exists(os.path.join(data_dir, _ANNOTATIONS))


def load_flywire(data_dir: str) -> dict | None:
    """Carrega circuitos reward, escape e orient do FlyWire v783."""
    try:
        from brain.loaders.flywire import FlyWireLoader
        from brain.circuits.flywire import FlyWireCircuit

        if not _data_ok(data_dir):
            return None

        logger.info("Carregando circuitos FlyWire v783...")
        loader   = FlyWireLoader(data_dir=data_dir, min_weight=3)
        reward_c = loader.load_reward_circuit()
        escape_c = loader.load_escape_circuit()
        orient_c = loader.load_orientation_circuit()
        logger.info(f"  {reward_c.summary()}")
        logger.info(f"  {escape_c.summary()}")
        logger.info(f"  {orient_c.summary()}")

        return {
            "reward": FlyWireCircuit(reward_c),
            "escape": FlyWireCircuit(escape_c),
            "orient": FlyWireCircuit(orient_c),
        }
    except Exception as e:
        logger.warning(f"FlyWire não carregou: {e}")
        return None


def load_ppl(data_dir: str):
    """Carrega neurônios PPL dopaminérgicos aversivos (PPL→KCs→MBONs)."""
    try:
        from brain.loaders.ppl import PPLLoader
        from brain.runners.ppl import PPLRunner

        if not _data_ok(data_dir):
            return None

        logger.info("Carregando PPL dopaminérgicos (aversivo)...")
        loader  = PPLLoader(data_dir=data_dir, min_weight=3)
        circuit = loader.load_ppl_circuit()
        return PPLRunner(circuit)
    except Exception as e:
        logger.warning(f"PPL não carregou: {e}")
        return None


def load_pcb(data_dir: str):
    """Carrega o Protocerebral Bridge (integração bilateral SMP/SLP→DNs)."""
    try:
        from brain.loaders.pcb import PCBLoader
        from brain.runners.pcb import PCBRunner

        if not _data_ok(data_dir):
            return None

        logger.info("Carregando Protocerebral Bridge (integração bilateral)...")
        loader  = PCBLoader(data_dir=data_dir, min_weight=3)
        circuit = loader.load_pcb_circuit()
        return PCBRunner(circuit)
    except Exception as e:
        logger.warning(f"PCB não carregou: {e}")
        return None


def load_cx(data_dir: str):
    """Carrega o Complexo Central (EPG → PFL3 → DNs — bússola interna)."""
    try:
        from brain.loaders.cx import CXLoader
        from brain.runners.cx import CXRunner

        if not _data_ok(data_dir):
            return None

        logger.info("Carregando Complexo Central (EPG → PFL3 → DNs)...")
        loader  = CXLoader(data_dir=data_dir, min_weight=3)
        circuit = loader.load_cx_circuit()
        return CXRunner(circuit)
    except Exception as e:
        logger.warning(f"Complexo Central não carregou: {e}")
        return None


def load_visual_circuit(data_dir: str):
    """Carrega o sistema visual completo (R1-6 → L → T4/T5 → LPLC2 → DNp01)."""
    try:
        from brain.loaders.visual import VisualLoader
        from brain.circuits.visual import VisualCircuit

        if not _data_ok(data_dir):
            return None

        logger.info("Carregando sistema visual FlyWire (R1-6 → L → T4/T5 → LPLC2 → DNp01)...")
        loader  = VisualLoader(data_dir=data_dir, min_weight=3)
        circuit = loader.load_visual_circuit()

        vc = VisualCircuit(circuit)
        if hasattr(circuit, '_r_positions'):
            vc._r_positions = circuit._r_positions

        return vc
    except Exception as e:
        logger.warning(f"Sistema visual não carregou: {e}")
        return None