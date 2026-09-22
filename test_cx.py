# test_cx.py — roda na raiz do projeto
import pandas as pd, numpy as np

ann  = pd.read_csv("data/neuron_annotations.tsv", sep="\t", low_memory=False)
conn = pd.read_parquet("data/2025_Connectivity_783.parquet")
conn = conn[conn["Connectivity"] >= 3]
ann["root_id"] = ann["root_id"].astype(np.int64)

# Complexo Central
cx = ann[ann["super_class"].astype(str).str.contains("central_complex", na=False)]
print(f"super_class=central_complex: {len(cx)}")

cx2 = ann[ann["cell_type"].astype(str).str.contains(
    r"^EPG|^PEN|^PEG|^FC[1-9]|^hDelta|^vDelta|^PFL|^LAL", na=False)]
print(f"Tipos CX: {len(cx2)}")
print(cx2["cell_type"].value_counts().head(20).to_string())

dn_ids  = set(ann.loc[ann["cell_type"].astype(str).str.contains(r"^DN", na=False), "root_id"])
cx_ids  = set(cx2["root_id"].values)
cx_sub  = conn[conn["Presynaptic_ID"].isin(cx_ids) & conn["Postsynaptic_ID"].isin(cx_ids)]
cx_2_dn = conn[conn["Presynaptic_ID"].isin(cx_ids) & conn["Postsynaptic_ID"].isin(dn_ids)]
print(f"\nSinapses internas CX: {len(cx_sub):,}")
print(f"CX → DNs (saída motora): {len(cx_2_dn):,}  de {cx_2_dn['Presynaptic_ID'].nunique()} neurônios")