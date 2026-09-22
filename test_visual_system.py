import pandas as pd, numpy as np

ann  = pd.read_csv("data/neuron_annotations.tsv", sep="\t", low_memory=False)
conn = pd.read_parquet("data/2025_Connectivity_783.parquet")
conn = conn[conn["Connectivity"] >= 3]
ann["root_id"] = ann["root_id"].astype(np.int64)

def get_ids(pattern):
    return set(ann.loc[ann['cell_type'].astype(str).str.contains(pattern, na=False), 'root_id'].values)

r16   = set(ann.loc[ann['cell_type'].astype(str).str.contains('R1-6|R7|R8', na=False), 'root_id'].values)
l12   = get_ids(r'^L[125]$')
tm    = get_ids(r'^Tm[0-9]|^T4|^T5')
lplc2 = get_ids('LPLC2')
all_ids = r16 | l12 | tm | lplc2

sub = conn[conn['Presynaptic_ID'].isin(all_ids) & conn['Postsynaptic_ID'].isin(all_ids)]
print(f"Neurônios: {len(all_ids):,}")
print(f"Sinapses no subgrafo: {len(sub):,}")
print(f"R1-6/7/8: {len(r16):,}")
print(f"L1/L2/L5: {len(l12):,}")
print(f"T4/T5/Tm: {len(tm):,}")
print(f"LPLC2: {len(lplc2):,}")