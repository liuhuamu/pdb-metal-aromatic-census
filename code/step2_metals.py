#!/usr/bin/env python3
"""L2 - intersect aromatic-ligand entries with per-metal entry lists.

Strategy (light on the search API):
  1. one *formula-only* query per metal element (fast, exact; a formula query
     automatically covers oxidation-state comp variants, e.g. "Fe" -> FE+FE2);
  2. intersect locally with the L1 aromatic entry union.

Outputs
    data/metals/<Element>.json   per-metal candidate lists
    data/candidates.json         {pdb_id: [elements present]}

Validated reference number (2026-10-15): aromatic-ligand AND Zn -> 11,716
entries (aromatic entries from non_polymer_entity queries; the entry-level
chemical search would inflate this to 27,995 by counting Phe/Tyr/Trp
polymer residues).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from config import (AROMATIC_ENTRIES_PATH, CANDIDATES_PATH, DATA_DIR,
                    METAL_BUCKETS)
from rcsb import PAUSE_S, chem_formula, search_ids

METALS_DIR = DATA_DIR / "metals"


def main() -> None:
    METALS_DIR.mkdir(parents=True, exist_ok=True)

    aromatic_sets = json.loads(AROMATIC_ENTRIES_PATH.read_text())
    aromatic_union = set().union(*aromatic_sets.values())
    print(f"[L2] aromatic union from L1: {len(aromatic_union):,} entries")

    candidates: dict = {}
    summary = []

    for element, bucket in METAL_BUCKETS.items():
        print(f"[L2] {element} (bucket {bucket}) ...", flush=True)
        with_metal = set(search_ids(chem_formula(element), return_type="entry"))
        time.sleep(PAUSE_S)

        hits = with_metal & aromatic_union
        print(f"[L2] {element}: entries with metal={len(with_metal):,}  "
              f"aromatic∧metal={len(hits):,}", flush=True)

        METALS_DIR.joinpath(f"{element}.json").write_text(json.dumps({
            "element": element,
            "bucket": bucket,
            "n_entries_with_metal": len(with_metal),
            "n_candidates": len(hits),
            "entries": sorted(hits),
        }, indent=1))

        for pdb_id in hits:
            candidates.setdefault(pdb_id, []).append(element)
        summary.append((bucket, element, len(with_metal), len(hits)))

    CANDIDATES_PATH.write_text(json.dumps(candidates, indent=1))

    print("\n[L2] summary  (bucket  element  n_metal  n_candidates)")
    for bucket, element, n_metal, n_cand in sorted(summary):
        print(f"     {bucket}  {element:>3s}  {n_metal:>8,d}  {n_cand:>8,d}")
    print(f"\n[L2] unique candidate entries: {len(candidates):,}")
    print(f"     saved -> {CANDIDATES_PATH}")


if __name__ == "__main__":
    main()
