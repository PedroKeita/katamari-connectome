# test_ppl_pcb.py
import pandas as pd, numpy as np

ann  = pd.read_csv("data/neuron_annotations.tsv", sep="\t", low_memory=False)
conn = pd.read_parquet("data/2025_Connectivity_783.parquet")
conn = conn[conn["Connectivity"] >= 3]
ann["root_id"] = ann["root_id"].astype(np.int64)

print("=== PPL DOPAMINÉRGICOS ===")
ppl = ann[ann["cell_type"].astype(str).str.contains(r"^PPL", na=False)]
print(f"Total PPL: {len(ppl)}")
print(ppl["cell_type"].value_counts().head(15).to_string())

pam_ids  = set(ann.loc[ann["cell_type"].astype(str).str.contains(r"^PAM", na=False), "root_id"])
dn_ids   = set(ann.loc[ann["cell_type"].astype(str).str.contains(r"^DN", na=False), "root_id"])
kc_ids   = set(ann.loc[ann["cell_type"].astype(str).str.contains(r"^KC", na=False), "root_id"])
mbon_ids = set(ann.loc[ann["cell_type"].astype(str).str.contains(r"^MBON", na=False), "root_id"])
ppl_ids  = set(ppl["root_id"].values)

ppl_to_kc    = conn[conn["Presynaptic_ID"].isin(ppl_ids) & conn["Postsynaptic_ID"].isin(kc_ids)]
ppl_to_mbon  = conn[conn["Presynaptic_ID"].isin(ppl_ids) & conn["Postsynaptic_ID"].isin(mbon_ids)]
ppl_to_dn    = conn[conn["Presynaptic_ID"].isin(ppl_ids) & conn["Postsynaptic_ID"].isin(dn_ids)]
ppl_internal = conn[conn["Presynaptic_ID"].isin(ppl_ids) & conn["Postsynaptic_ID"].isin(ppl_ids)]
print(f"\nPPL → KCs:    {len(ppl_to_kc):,}")
print(f"PPL → MBONs:  {len(ppl_to_mbon):,}")
print(f"PPL → DNs:    {len(ppl_to_dn):,}")
print(f"PPL interno:  {len(ppl_internal):,}")

print("\n=== PROTOCEREBRAL BRIDGE ===")
pcb = ann[ann["cell_type"].astype(str).str.contains(r"^PB|^EB|^FB|^NO|^LAL|^SMP|^SIP|^SLP", na=False)]
print(f"Total PCB: {len(pcb)}")
print(pcb["cell_type"].value_counts().head(20).to_string())

pcb_ids      = set(pcb["root_id"].values)
pcb_internal = conn[conn["Presynaptic_ID"].isin(pcb_ids) & conn["Postsynaptic_ID"].isin(pcb_ids)]
pcb_to_dn    = conn[conn["Presynaptic_ID"].isin(pcb_ids) & conn["Postsynaptic_ID"].isin(dn_ids)]
print(f"\nSinapses internas PCB: {len(pcb_internal):,}")
print(f"PCB → DNs: {len(pcb_to_dn):,}  de {pcb_to_dn['Presynaptic_ID'].nunique()} neurônios")
pcb_dn_types = pcb.loc[pcb["root_id"].isin(pcb_to_dn["Presynaptic_ID"]), "cell_type"].value_counts().head(10)
print(f"\nTop tipos PCB → DNs:\n{pcb_dn_types.to_string()}")