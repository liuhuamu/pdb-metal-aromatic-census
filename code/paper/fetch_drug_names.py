#!/usr/bin/env python3
"""Fetch names for drug-category aromatic comps (for the SI table)."""
import csv
import json
import time
from pathlib import Path

import requests

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
CACHE = ROOT / "paper" / "data" / "ligand_names_all.json"
OUT = ROOT / "paper" / "data" / "ligand_names_drug.json"

names = json.loads(CACHE.read_text())
need = []
for row in csv.DictReader(
        open(ROOT / "paper" / "output" / "ligand_classification.csv")):
    if row["category"].startswith("drug-") and row["comp_id"] not in names:
        need.append(row["comp_id"])
print(f"[names] fetching {len(need):,} drug-comp names", flush=True)

sess = requests.Session()
out = {}
for i, comp in enumerate(need):
    for attempt in range(3):
        try:
            d = sess.get(
                f"https://data.rcsb.org/rest/v1/core/chemcomp/{comp}",
                timeout=30).json()
            out[comp] = d.get("chem_comp", {}).get("name", "?")
            names[comp] = out[comp]
            break
        except Exception:
            time.sleep(2)
    else:
        out[comp] = "?"
    if (i + 1) % 500 == 0:
        CACHE.write_text(json.dumps(names))
        OUT.write_text(json.dumps(out))
        print(f"  {i+1:,}/{len(need):,}", flush=True)
    time.sleep(0.05)

CACHE.write_text(json.dumps(names))
OUT.write_text(json.dumps(out))
print(f"[names] done: {len(out):,} fetched")
