"""
Carrega o circuito PPL (Protocerebral Posterior Lateral) dopaminérgico.

PPL são neurônios dopaminérgicos aversivos — na mosca real sinalizam
punição, perigo, e resultados negativos. Complementam os PAMs (recompensa).

Circuito:
  PPL (24 neurônios, 12 tipos) → KCs (mushroom body) → MBONs → saída

Quando o Katamari fica preso, os PPLs são estimulados, inibindo os KCs
e sinalizando via MBONs que a direção atual é ruim.

Sinapses: PPL→KCs: 1.274 | PPL→MBONs: 145 | PPL→DNs: 6
"""

import numpy as np
import pandas as pd
from scipy import sparse
import os
import logging

logger = logging.getLogger(__name__)


class PPLLoader:

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

    def load_ppl_circuit(self):
        from brain.flywire_loader import ConnectomeCircuit

        self._load()
        ann  = self._ann
        conn = self._conn
        ann_idx = ann.set_index("root_id")

        logger.info("Construindo subgrafo PPL dopaminérgico...")

        def get_ids(pattern):
            mask = ann["cell_type"].astype(str).str.contains(pattern, na=False)
            return set(ann.loc[mask, "root_id"].values)

        ppl_ids  = get_ids(r"^PPL")
        kc_ids   = get_ids(r"^KC")
        mbon_ids = get_ids(r"^MBON")
        dn_ids   = get_ids(r"^DN")

        logger.info(f"  PPL: {len(ppl_ids)}  KCs: {len(kc_ids)}  MBONs: {len(mbon_ids)}")

        # Subgrafo: PPL + targets diretos (KCs que PPL conecta + MBONs + DNs)
        ppl_targets = conn[conn["Presynaptic_ID"].isin(ppl_ids)]
        target_ids  = set(ppl_targets["Postsynaptic_ID"].values)

        # KCs que recebem de PPL → seus MBONs downstream
        kc_reached = target_ids & kc_ids
        kc_to_mbon = conn[
            conn["Presynaptic_ID"].isin(kc_reached) &
            conn["Postsynaptic_ID"].isin(mbon_ids)
        ]
        mbon_reached = set(kc_to_mbon["Postsynaptic_ID"].values)

        all_ids = ppl_ids | kc_reached | mbon_reached | (target_ids & dn_ids)

        mask = (
            conn["Presynaptic_ID"].isin(all_ids) &
            conn["Postsynaptic_ID"].isin(all_ids)
        )
        sub = conn[mask].copy()

        logger.info(f"  Subgrafo: {len(all_ids)} neurônios, {len(sub):,} sinapses")
        logger.info(f"  KCs alcançados: {len(kc_reached)}  MBONs: {len(mbon_reached)}")

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

        def local_idx(ids):
            return np.array(
                [id_to_idx[i] for i in ids if i in id_to_idx],
                dtype=np.int32
            )

        sides = np.array([
            ann_idx.loc[nid, "side"] if nid in ann_idx.index else "unknown"
            for nid in neuron_ids
        ])

        input_idx  = local_idx(ppl_ids)           # Entrada: PPL
        output_idx = local_idx(mbon_reached | (target_ids & dn_ids))  # Saída: MBONs + DNs

        circuit = ConnectomeCircuit(
            name       = "ppl_aversive",
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

        logger.info(f"  PPL circuit: {N} neurônios, {W.nnz:,} sinapses")
        logger.info(f"  Entradas (PPL): {len(input_idx)}  Saídas (MBON+DN): {len(output_idx)}")
        return circuit