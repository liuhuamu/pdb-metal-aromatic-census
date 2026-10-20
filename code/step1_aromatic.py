#!/usr/bin/env python3
"""L1 - find PDB entries containing aromatic-ring LIGANDS (non-polymer).

Important implementation note (validated live):
the entry-level chemical search also indexes polymer residues, so a benzene
substructure query at ``return_type="entry"`` returns 255,847 entries (nearly
every protein, because of Phe/Tyr/Trp side chains).  Using
``return_type="non_polymer_entity"`` instead returns only genuine ligand
entities, e.g. ``181L_4`` (55,521 entity pairs for benzene), which we reduce
to entry IDs by stripping the entity suffix.

For every ring pattern in ``config.AROMATIC_SMILES``:
  * ``return_type="non_polymer_entity"`` -> PDB IDs with a matching ligand
  * ``return_type="mol_definition"``     -> matching ligand comp IDs
    (used later for ring-type annotation; may include polymer-residue comps
    like PHE - harmless, step4 only considers non-polymer entities)

Outputs
    data/aromatic_entries.json   {pattern_name: [pdb_id, ...]}
    data/aromatic_ligands.json   {pattern_name: [comp_id, ...]}
"""
from __future__ import annotations

import json
import time

from config import AROMATIC_ENTRIES_PATH, AROMATIC_LIGANDS_PATH, AROMATIC_SMILES
from rcsb import PAUSE_S, chem_descriptor, search_ids


def main() -> None:
    entries: dict = {}
    ligands: dict = {}

    for name, smiles in AROMATIC_SMILES.items():
        print(f"[L1] {name:10s} {smiles} ...", flush=True)
        q = chem_descriptor(smiles)

        pairs = search_ids(q, return_type="non_polymer_entity")
        ent = {p.split("_")[0] for p in pairs}
        time.sleep(PAUSE_S)
        lig = search_ids(q, return_type="mol_definition")

        entries[name] = sorted(ent)
        ligands[name] = sorted(set(lig))
        print(f"[L1] {name:10s} entries={len(entries[name]):>7,d}   "
              f"ligand_comps={len(ligands[name]):>6,d}", flush=True)

    AROMATIC_ENTRIES_PATH.write_text(json.dumps(entries, indent=1))
    AROMATIC_LIGANDS_PATH.write_text(json.dumps(ligands, indent=1))

    union_entries = set().union(*entries.values())
    union_ligands = set().union(*ligands.values())
    print("\n[L1] summary")
    print(f"     unique entries with aromatic LIGANDS : {len(union_entries):,}")
    print(f"     unique aromatic ligand comp IDs      : {len(union_ligands):,}")
    print(f"     saved -> {AROMATIC_ENTRIES_PATH}")
    print(f"           -> {AROMATIC_LIGANDS_PATH}")


if __name__ == "__main__":
    main()
