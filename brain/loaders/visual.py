"""
Carrega o subgrafo do sistema visual completo do FlyWire v783:
  R1-6/R7/R8 → L1/L2/L5 → T4/T5/Tm → LPLC2 → DNp01

46.465 neurônios, ~239k sinapses.
"""

import numpy as np
import pandas as pd
from scipy import sparse
import os
import logging

logger = logging.getLogger(__name__)


class VisualLoader:

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
            logger.info(f"  Anotações: {len(self._ann):,} neurônios")

        if self._conn is None:
            path = os.path.join(self.data_dir, self.CONNECTIVITY_FILE)
            logger.info(f"  Carregando conectividade visual...")
            conn = pd.read_parquet(path)
            self._conn = conn[conn["Connectivity"] >= self.min_weight].copy()
            logger.info(f"  Sinapses (>={self.min_weight}): {len(self._conn):,}")

    def load_visual_circuit(self):
        """
        Carrega o circuito visual completo.
        Retorna um objeto compatível com FlyWireCircuit.
        """
        from brain.circuits.connectome import ConnectomeCircuit

        self._load()
        ann  = self._ann
        conn = self._conn
        ann_idx = ann.set_index("root_id")

        logger.info("Construindo subgrafo visual...")

        def get_ids(pattern):
            mask = ann["cell_type"].astype(str).str.contains(pattern, na=False)
            return set(ann.loc[mask, "root_id"].values)

        # Camadas do sistema visual
        r_ids    = set(ann.loc[
            ann["cell_type"].astype(str).str.contains(r"R1-6|R7|R8", na=False),
            "root_id"
        ].values)
        l_ids    = get_ids(r"^L[125]$")
        tm_ids   = get_ids(r"^Tm\d|^T4[abcd]|^T5[abcd]")
        lplc2_ids = get_ids("LPLC2")
        dnp01_ids = get_ids("DNp01")

        all_ids = r_ids | l_ids | tm_ids | lplc2_ids | dnp01_ids

        logger.info(f"  R1-8: {len(r_ids):,}  L: {len(l_ids):,}  "
                    f"Tm/T4/T5: {len(tm_ids):,}  LPLC2: {len(lplc2_ids):,}  "
                    f"DNp01: {len(dnp01_ids):,}")

        # Filtra sinapses dentro do subgrafo
        mask = (
            conn["Presynaptic_ID"].isin(all_ids) &
            conn["Postsynaptic_ID"].isin(all_ids)
        )
        sub = conn[mask].copy()
        logger.info(f"  Sinapses no subgrafo: {len(sub):,}")

        # Remapeia para índices locais
        neuron_ids = np.array(sorted(all_ids), dtype=np.int64)
        id_to_idx  = {nid: i for i, nid in enumerate(neuron_ids)}
        N = len(neuron_ids)

        pre_idx = sub["Presynaptic_ID"].map(id_to_idx).values
        post_idx = sub["Postsynaptic_ID"].map(id_to_idx).values
        weights  = sub["Connectivity"].values.astype(np.float32)
        excit    = sub["Excitatory"].values.astype(bool)
        signed   = np.where(excit, weights, -weights)

        W = sparse.csr_matrix(
            (signed, (pre_idx, post_idx)),
            shape=(N, N), dtype=np.float32
        )

        def local_idx(ids):
            return np.array(
                [id_to_idx[i] for i in ids if i in id_to_idx],
                dtype=np.int32
            )

        # Metadados por neurônio
        sides = np.array([
            ann_idx.loc[nid, "side"] if nid in ann_idx.index else "unknown"
            for nid in neuron_ids
        ])
        cell_types = np.array([
            ann_idx.loc[nid, "cell_type"] if nid in ann_idx.index else ""
            for nid in neuron_ids
        ])

        # Posições espaciais dos fotorreceptores (para mapeamento visual)
        r_local = local_idx(r_ids)
        r_positions = np.zeros((len(r_local), 2), dtype=np.float32)
        for i, idx in enumerate(r_local):
            nid = neuron_ids[idx]
            if nid in ann_idx.index:
                row = ann_idx.loc[nid]
                px = float(row.get("pos_x", 0) or 0)
                py = float(row.get("pos_y", 0) or 0)
                r_positions[i] = [px, py]

        # Normaliza posições para [0, 1]
        if r_positions.max() > 0:
            r_positions[:, 0] = (r_positions[:, 0] - r_positions[:, 0].min()) / \
                                 max(r_positions[:, 0].max() - r_positions[:, 0].min(), 1)
            r_positions[:, 1] = (r_positions[:, 1] - r_positions[:, 1].min()) / \
                                 max(r_positions[:, 1].max() - r_positions[:, 1].min(), 1)

        circuit = ConnectomeCircuit(
            name       = "visual",
            neuron_ids = neuron_ids,
            weights    = W,
            input_idx  = r_local,
            output_idx = local_idx(dnp01_ids),
            sides      = sides,
            cell_types = cell_types,
        )

        # Armazena posições para uso no VisualCircuit
        circuit._r_positions = r_positions

        logger.info(f"  Circuito visual: {N:,} neurônios, {W.nnz:,} sinapses")
        logger.info(f"  Entradas (R): {len(r_local):,}  Saídas (DNp01): {len(local_idx(dnp01_ids)):,}")

        return circuit