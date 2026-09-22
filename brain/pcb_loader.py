"""
Carrega o circuito Protocerebral Bridge (PCB).

O protocérebro é a região anterior do cérebro da mosca que integra
informações de múltiplas modalidades sensoriais e coordena os dois
hemisférios. Inclui SMP, SLP, SIP, FB, LAL e outros neuropils.

3.776 neurônios, 85.536 sinapses internas, 7.263 sinapses para DNs
de 1.399 neurônios — circuito bem conectado motoramente.

Função no projeto: integração bilateral — recebe L/C/R do sensory encoder
e produz assimetria motora coordenada entre os dois hemisférios.
"""

import numpy as np
import pandas as pd
from scipy import sparse
import os
import logging

logger = logging.getLogger(__name__)


class PCBLoader:

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

    def load_pcb_circuit(self):
        from brain.flywire_loader import ConnectomeCircuit

        self._load()
        ann  = self._ann
        conn = self._conn
        ann_idx = ann.set_index("root_id")

        logger.info("Construindo subgrafo Protocerebral Bridge...")

        def get_ids(pattern):
            mask = ann["cell_type"].astype(str).str.contains(pattern, na=False)
            return set(ann.loc[mask, "root_id"].values)

        # Neurônios protocerebrais
        smp_ids = get_ids(r"^SMP")
        slp_ids = get_ids(r"^SLP")
        sip_ids = get_ids(r"^SIP")
        fb_ids  = get_ids(r"^FB[0-9]")
        lal_ids = get_ids(r"^LAL")
        dn_ids  = get_ids(r"^DN")

        pcb_ids = smp_ids | slp_ids | sip_ids | fb_ids | lal_ids

        logger.info(f"  SMP: {len(smp_ids)}  SLP: {len(slp_ids)}  SIP: {len(sip_ids)}")
        logger.info(f"  FB: {len(fb_ids)}  LAL: {len(lal_ids)}")
        logger.info(f"  Total PCB: {len(pcb_ids)}  DNs alvo: {len(dn_ids)}")

        # Subgrafo: PCB interno + PCB→DNs
        all_ids = pcb_ids | dn_ids
        mask = (
            conn["Presynaptic_ID"].isin(pcb_ids) &
            conn["Postsynaptic_ID"].isin(all_ids)
        )
        sub = conn[mask].copy()
        logger.info(f"  Sinapses no subgrafo: {len(sub):,}")

        # Indexação local
        # Só inclui neurônios que realmente aparecem no subgrafo
        active_ids = set(sub["Presynaptic_ID"].values) | set(sub["Postsynaptic_ID"].values)
        neuron_ids = np.array(sorted(active_ids), dtype=np.int64)
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

        # Entradas: LAL e SMP (recebem sinal sensorial)
        # LAL = Lateral Accessory Lobe, gateway motor principal
        input_idx  = local_idx(lal_ids | smp_ids)
        output_idx = local_idx(dn_ids)

        circuit = ConnectomeCircuit(
            name       = "protocerebral_bridge",
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

        logger.info(f"  PCB: {N:,} neurônios, {W.nnz:,} sinapses")
        logger.info(f"  Entradas (LAL+SMP): {len(input_idx)}  Saídas (DNs): {len(output_idx)}")
        return circuit