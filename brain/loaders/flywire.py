"""
Carrega subgrafos dos circuitos biológicos reais do FlyWire v783.

Cadeia de recompensa descoberta empiricamente neste conectoma:
  ORNs (afferent, ~2277) → PNs (intrinsic, ~276) → KCs (~5177) → PAMs (~331)

Circuito de escape:
  LPLC2 (optic, ~210) → DNp01 / Giant Fiber (descending, 2)

Circuito de orientação:
  Descending neurons lateralizados (L vs R)
"""

import numpy as np
import pandas as pd
from scipy import sparse
import os

from brain.circuits.connectome import ConnectomeCircuit


class FlyWireLoader:
    """
    Carrega e mantém em cache os dados do FlyWire v783.

    min_weight : peso mínimo de sinapses físicas para incluir uma conexão.
                 O paper Shiu et al. usa 5. Usar 3 para capturar mais
                 conexões no circuito de recompensa.
    """

    CONNECTIVITY_FILE = "2025_Connectivity_783.parquet"
    ANNOTATIONS_FILE  = "neuron_annotations.tsv"

    def __init__(self, data_dir: str = "data", min_weight: int = 3):
        self.data_dir   = data_dir
        self.min_weight = min_weight
        self._conn = None
        self._ann  = None

    def _load_annotations(self) -> pd.DataFrame:
        if self._ann is None:
            path = os.path.join(self.data_dir, self.ANNOTATIONS_FILE)
            print(f"  Carregando anotações: {path}")
            self._ann = pd.read_csv(path, sep="\t", low_memory=False)
            self._ann["root_id"] = self._ann["root_id"].astype(np.int64)
        return self._ann

    def _load_connectivity(self) -> pd.DataFrame:
        if self._conn is None:
            path = os.path.join(self.data_dir, self.CONNECTIVITY_FILE)
            print(f"  Carregando conectividade (pode demorar ~10s)...")
            conn = pd.read_parquet(path)
            conn = conn[conn["Connectivity"] >= self.min_weight].copy()
            print(f"  Sinapses após filtro (>={self.min_weight}): {len(conn):,}")
            self._conn = conn
        return self._conn

    def _get_ids(self, pattern: str) -> set:
        ann = self._load_annotations()
        mask = ann["cell_type"].astype(str).str.contains(pattern, na=False, case=False)
        return set(ann.loc[mask, "root_id"].values)

    def _build_circuit(
        self,
        name: str,
        input_ids:  set,
        hidden_ids: set,
        output_ids: set,
    ) -> ConnectomeCircuit:
        conn = self._load_connectivity()
        ann  = self._load_annotations()
        ann_idx = ann.set_index("root_id")

        all_ids = input_ids | hidden_ids | output_ids

        mask = (
            conn["Presynaptic_ID"].isin(all_ids) &
            conn["Postsynaptic_ID"].isin(all_ids)
        )
        sub = conn[mask].copy()

        print(f"  [{name}] entrada={len(input_ids)}  "
              f"oculto={len(hidden_ids)}  saída={len(output_ids)}")
        print(f"  [{name}] sinapses no subgrafo: {len(sub):,}")

        if len(sub) == 0:
            raise ValueError(f"Nenhuma sinapse para '{name}'.")

        neuron_ids = np.array(sorted(all_ids), dtype=np.int64)
        id_to_idx  = {nid: i for i, nid in enumerate(neuron_ids)}
        N = len(neuron_ids)

        pre_idx  = sub["Presynaptic_ID"].map(id_to_idx).values
        post_idx = sub["Postsynaptic_ID"].map(id_to_idx).values
        weights  = sub["Connectivity"].values.astype(np.float32)
        excit    = sub["Excitatory"].values.astype(bool)
        signed   = np.where(excit, weights, -weights)

        W = sparse.csr_matrix(
            (signed, (pre_idx, post_idx)),
            shape=(N, N), dtype=np.float32,
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
        cell_types = np.array([
            ann_idx.loc[nid, "cell_type"] if nid in ann_idx.index else ""
            for nid in neuron_ids
        ])

        return ConnectomeCircuit(
            name       = name,
            neuron_ids = neuron_ids,
            weights    = W,
            input_idx  = local_idx(input_ids),
            output_idx = local_idx(output_ids),
            sides      = sides,
            cell_types = cell_types,
        )

    # ------------------------------------------------------------------
    # Circuitos públicos
    # ------------------------------------------------------------------

    def load_reward_circuit(self) -> ConnectomeCircuit:
        """
        ORNs → PNs → Kenyon Cells → PAMs

        Cadeia de recompensa olfativa do Mushroom Body.
        No contexto do Katamari: objetos coloridos disparam o sistema
        visual/olfativo, que via PNs ativa os KCs e modula os PAMs.
        """
        ann = self._load_annotations()
        ann_idx = ann.set_index("root_id")

        # ORNs: flow=afferent, super_class=sensory
        orn_mask = (
            (ann["flow"] == "afferent") &
            (ann["super_class"] == "sensory")
        )
        orn_ids = set(ann.loc[orn_mask, "root_id"].values)

        # PNs: cell_type contém 'PN' e conectam para KCs
        kc_ids = self._get_ids(r"^KC")
        conn   = self._load_connectivity()
        kc_in  = conn[conn["Postsynaptic_ID"].isin(kc_ids)]
        pn_ids = set(
            pid for pid in kc_in["Presynaptic_ID"].unique()
            if pid in ann_idx.index and "PN" in str(ann_idx.loc[pid, "cell_type"])
        )

        # PAMs: dopaminérgicos do Mushroom Body
        pam_ids = self._get_ids(r"^PAM")

        return self._build_circuit(
            name       = "reward",
            input_ids  = orn_ids,
            hidden_ids = pn_ids | kc_ids,
            output_ids = pam_ids,
        )

    def load_escape_circuit(self) -> ConnectomeCircuit:
        """
        LPLC2 (looming visual) → DNp01 (Giant Fiber)

        Circuito de fuga mais rápido do cérebro da mosca.
        Detecta objetos se aproximando e gera resposta reflexa.
        """
        return self._build_circuit(
            name       = "escape",
            input_ids  = self._get_ids("LPLC2"),
            hidden_ids = set(),
            output_ids = self._get_ids("DNp01"),
        )

    def load_orientation_circuit(self) -> ConnectomeCircuit:
        """
        Descending neurons lateralizados para viés direcional.

        DNs com anotação left/right como proxy de orientação.
        Os tipos mais conectados de cada lado são incluídos.
        """
        ann = self._load_annotations()
        dn  = ann[ann["super_class"] == "descending"].copy()

        # Top 20 tipos por frequência
        top_types = dn["cell_type"].value_counts().head(20).index.tolist()

        input_ids  = self._get_ids("|".join(top_types[:10]))
        output_ids = self._get_ids("|".join(top_types[10:20]))

        return self._build_circuit(
            name       = "orientation",
            input_ids  = input_ids,
            hidden_ids = set(),
            output_ids = output_ids,
        )

    def load_all(self) -> dict:
        print("=== FlyWire Loader ===")
        circuits = {}
        for name, fn in [
            ("reward",      self.load_reward_circuit),
            ("escape",      self.load_escape_circuit),
            ("orientation", self.load_orientation_circuit),
        ]:
            print(f"\nCircuito: {name}")
            try:
                c = fn()
                circuits[name] = c
                print(f"  {c.summary()}")
            except Exception as e:
                print(f"  ERRO: {e}")
        print("\n=== Concluído ===")
        return circuits


if __name__ == "__main__":
    loader = FlyWireLoader(data_dir="data", min_weight=3)
    loader.load_all()