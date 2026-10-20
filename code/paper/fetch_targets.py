#!/usr/bin/env python3
"""Fetch UniProt target annotations for all hit entries (batched GraphQL).

Output: paper/data/target_annotations.json
    {pdb_id: [{"uniprot": acc, "name": description}, ...]}
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import requests

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
OUT = ROOT / "paper" / "data" / "target_annotations.json"

QUERY = """
query($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    polymer_entities {
      rcsb_polymer_entity_container_identifiers {
        auth_asym_ids
        reference_sequence_identifiers { database_name database_accession }
      }
      rcsb_polymer_entity { pdbx_description }
      rcsb_polymer_entity_annotation { type name }
    }
  }
}
"""


def fetch_batch(ids, sess):
    r = sess.post("https://data.rcsb.org/graphql",
                  json={"query": QUERY, "variables": {"ids": ids}},
                  timeout=120)
    r.raise_for_status()
    return r.json().get("data", {}).get("entries", [])


def main() -> None:
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    pdb_ids = sorted({r[0] for r in conn.execute("SELECT DISTINCT pdb_id FROM hits")})
    conn.close()
    print(f"[targets] {len(pdb_ids):,} hit entries to annotate")

    anno = {}
    if OUT.exists():
        anno = json.loads(OUT.read_text())
        print(f"[targets] cached: {len(anno):,}")

    todo = [p for p in pdb_ids if p not in anno]
    sess = requests.Session()
    BATCH = 100
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        for attempt in range(4):
            try:
                entries = fetch_batch(batch, sess)
                break
            except Exception as exc:
                wait = 5 * (attempt + 1)
                print(f"  [warn] {type(exc).__name__}: {exc}; "
                      f"retry in {wait}s", flush=True)
                time.sleep(wait)
        else:
            print(f"  [err] batch failed, skipping: {batch[:3]}...", flush=True)
            continue
        for e in entries:
            targets = []
            chain_map = {}
            pfam_map = {}
            for pe in e.get("polymer_entities", []):
                ids_obj = pe.get(
                    "rcsb_polymer_entity_container_identifiers", {})
                refs = ids_obj.get("reference_sequence_identifiers") or []
                accs = [x["database_accession"] for x in refs
                        if x.get("database_name") == "UniProt"]
                desc = pe.get("rcsb_polymer_entity", {}).get(
                    "pdbx_description", "")
                anns = pe.get("rcsb_polymer_entity_annotation") or []
                pfams = [a.get("name") for a in anns
                         if a.get("type") == "Pfam" and a.get("name")]
                for acc in accs:
                    targets.append({"uniprot": acc, "name": desc})
                for chain in ids_obj.get("auth_asym_ids") or []:
                    if accs:
                        chain_map[chain] = accs[0]
                    if pfams:
                        pfam_map[chain] = pfams
            # de-duplicate UniProt accessions, keep first description
            seen = {}
            for t in targets:
                seen.setdefault(t["uniprot"], t["name"])
            anno[e["rcsb_id"]] = {
                "uniprots": [{"uniprot": k, "name": v}
                             for k, v in seen.items()],
                "chains": chain_map,
                "pfam": pfam_map,
            }
        if (i // BATCH) % 10 == 0 or i + BATCH >= len(todo):
            OUT.write_text(json.dumps(anno))
            print(f"[targets] {i + len(batch):,}/{len(todo):,} "
                  f"(total {len(anno):,})", flush=True)
        time.sleep(0.15)

    OUT.write_text(json.dumps(anno))
    n_with = sum(1 for v in anno.values() if v.get("uniprots"))
    print(f"[targets] done: {len(anno):,} entries annotated, "
          f"{n_with:,} with >=1 UniProt")


if __name__ == "__main__":
    main()
