"""
brain/cx_loader.py

Carrega o subgrafo do Complexo Central (CX) do FlyWire v783.

Neurônios incluídos:
  EPG   — bússola interna (codifica direção de cabeça)
  PEN   — atualiza a bússola com sinal de velocidade angular
  PFL3  — traduz direção em assimetria motora L/R
  hDelta/vDelta — interneurônios do fan-shaped body
  FC    — fan-shaped body columns

Saída: DNs motores (conectados pelos PFL3)

1.529 neurônios, ~26k sinapses internas, 3.931 sinapses para DNs
"""

import numpy as np
import pandas as pd
from scipy import sparse
import os
import logging

logger = logging.getLogger(__name__)


class CXLoader:

    CONNECTIVITY_FILE = "2025_Connectivity_783.parquet"
    ANNOTATIONS_FILE  = "neuron_annotations.tsv"

    def __init__(self, data_dir: str = "data", min_weight: int = 3):
        self.data_dir   = data_dir
        self.min_weight = min_weight
        self._ann  = None
        self._conn = None

    def _load(self):
        if self._ann is None:
            path = os.path.join(self.data_dir, self.ANNOTATIONS_FILE)
            self._ann = pd.read_csv(path, sep="\t", low_memory=False)
            self._ann["root_id"] = self._ann["root_id"].astype(np.int64)

        if self._conn is None:
            path = os.path.join(self.data_dir, self.CONNECTIVITY_FILE)
            conn = pd.read_parquet(path)
            self._conn = conn[conn["Connectivity"] >= self.min_weight].copy()

    def load_cx_circuit(self):
        """
        Carrega o Complexo Central completo.

        Retorna um ConnectomeCircuit compatível com FlyWireCircuit.
        Entradas: EPG + PEN (recebem sinal de direção/velocidade)
        Saídas:   DNs conectados pelos PFL3 (assimetria L/R)
        """
        from brain.flywire_loader import ConnectomeCircuit

        self._load()
        ann  = self._ann
        conn = self._conn
        ann_idx = ann.set_index("root_id")

        logger.info("Construindo subgrafo do Complexo Central...")

        def get_ids(pattern):
            mask = ann["cell_type"].astype(str).str.contains(pattern, na=False)
            return set(ann.loc[mask, "root_id"].values)

        # Neurônios do CX
        epg_ids    = get_ids(r"^EPG")
        pen_ids    = get_ids(r"^PEN")
        pfl_ids    = get_ids(r"^PFL")
        hdelta_ids = get_ids(r"^hDelta")
        vdelta_ids = get_ids(r"^vDelta")
        fc_ids     = get_ids(r"^FC[0-9]")

        cx_ids = epg_ids | pen_ids | pfl_ids | hdelta_ids | vdelta_ids | fc_ids

        # DNs motores (saída do CX)
        dn_ids = get_ids(r"^DN")

        logger.info(f"  EPG: {len(epg_ids)}  PEN: {len(pen_ids)}  PFL: {len(pfl_ids)}")
        logger.info(f"  hDelta: {len(hdelta_ids)}  vDelta: {len(vdelta_ids)}  FC: {len(fc_ids)}")
        logger.info(f"  DNs alvo: {len(dn_ids)}")

        # Subgrafo: sinapses internas + CX→DN
        all_ids = cx_ids | dn_ids
        mask = (
            conn["Presynaptic_ID"].isin(cx_ids) &
            conn["Postsynaptic_ID"].isin(all_ids)
        )
        sub = conn[mask].copy()
        logger.info(f"  Sinapses no subgrafo: {len(sub):,}")

        # Indexação local
        neuron_ids = np.array(sorted(all_ids), dtype=np.int64)
        id_to_idx  = {nid: i for i, nid in enumerate(neuron_ids)}
        N = len(neuron_ids)

        pre_idx  = sub["Presynaptic_ID"].map(id_to_idx).values
        post_idx = sub["Postsynaptic_ID"].map(id_to_idx).values
        weights  = sub["Connectivity"].values.astype(np.float32)
        excit    = sub.get("Excitatory", pd.Series([True]*len(sub))).values.astype(bool)
        signed   = np.where(excit, weights, -weights)

        W = sparse.csr_matrix(
            (signed, (pre_idx, post_idx)),
            shape=(N, N), dtype=np.float32
        )

        # Índices locais
        def local_idx(ids):
            return np.array(
                [id_to_idx[i] for i in ids if i in id_to_idx],
                dtype=np.int32
            )

        # Metadados
        sides = np.array([
            ann_idx.loc[nid, "side"] if nid in ann_idx.index else "unknown"
            for nid in neuron_ids
        ])

        # Entradas: EPG + PEN (recebem sinal sensorial)
        input_idx  = local_idx(epg_ids | pen_ids)
        # Saídas: DNs (assimetria motora)
        output_idx = local_idx(dn_ids)

        circuit = ConnectomeCircuit(
            name       = "central_complex",
            neuron_ids = neuron_ids,
            weights    = W,
            input_idx  = input_idx,
            output_idx = output_idx,
            sides      = sides,
            cell_types = np.array([
                ann_idx.loc[nid, "cell_type"] if nid in ann_idx.index else ""
                for nid in neuron_ids
            ]),
        )

        logger.info(f"  CX: {N:,} neurônios, {W.nnz:,} sinapses")
        logger.info(f"  Entradas (EPG+PEN): {len(input_idx)}  Saídas (DNs): {len(output_idx)}")

        return circuit