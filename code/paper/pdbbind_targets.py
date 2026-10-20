#!/usr/bin/env python3
"""Parallel fetch of UniProt / Pfam annotations for PDBbind v2020 complexes."""
from __future__ import annotations

import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
PAPER = ROOT / "paper"
OUT = PAPER / "data" / "pdbbind_targets.json"

QUERY = """
query($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    polymer_entities {
      rcsb_polymer_entity_container_identifiers {
        auth_asym_ids
        reference_sequence_identifiers { database_name database_accession }
      }
      rcsb_polymer_entity_annotation { type name }
    }
  }
}
"""


def post(ids, tries=4):
    body = json.dumps({"query": QUERY, "variables": {"ids": ids}}).encode()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                "https://data.rcsb.org/graphql", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as fh:
                return json.loads(fh.read().decode()).get(
                    "data", {}).get("entries", []) or []
        except Exception:  # noqa: BLE001
            time.sleep(3 * (attempt + 1))
    return []


def parse(entries):
    out = {}
    for e in entries:
        pfam, chain_uni, unis = {}, {}, []
        for pe in e.get("polymer_entities", []):
            ident = pe.get("rcsb_polymer_entity_container_identifiers", {})
            refs = ident.get("reference_sequence_identifiers") or []
            accs = [x["database_accession"] for x in refs
                    if x.get("database_name") == "UniProt"]
            fams = [a.get("name") for a in
                    (pe.get("rcsb_polymer_entity_annotation") or [])
                    if a.get("type") == "Pfam" and a.get("name")]
            for acc in accs:
                if acc not in unis:
                    unis.append(acc)
            for ch in ident.get("auth_asym_ids") or []:
                if accs:
                    chain_uni[ch] = accs[0]
                if fams:
                    pfam[ch] = fams
        out[e["rcsb_id"]] = {"uniprots": unis, "chains": chain_uni,
                             "pfam": pfam}
    return out


def main():
    xl = pd.ExcelFile(PAPER / "SI_Tables.xlsx")
    ids = set()
    for sh in ("S8_PDBbind_general", "S9_PDBbind_refined"):
        ids |= set(xl.parse(sh).pdb_id.astype(str))
    ids = sorted(ids)
    anno = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [i for i in ids if i not in anno]
    print(f"[pdbbind] {len(ids):,} ids, cached {len(anno):,}, "
          f"fetching {len(todo):,}", flush=True)

    batches = [todo[i:i + 100] for i in range(0, len(todo), 100)]
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for part in ex.map(post, batches):
            anno.update(parse(part))
            done += 1
            if done % 20 == 0:
                OUT.write_text(json.dumps(anno))
                print(f"   {done}/{len(batches)} batches "
                      f"({len(anno):,} entries)", flush=True)
    OUT.write_text(json.dumps(anno))
    n_uni = sum(1 for v in anno.values() if v["uniprots"])
    print(f"[pdbbind] done: {len(anno):,} entries, {n_uni:,} with UniProt")


if __name__ == "__main__":
    main()
