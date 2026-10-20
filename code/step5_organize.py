#!/usr/bin/env python3
"""L4 - organise final hit structures into bucket / metal / geometry folders.

Layout (angle-based two-class scheme, porphyrins excluded):

    output/structures/
        A_d10_metpi/Zn/face-on/    <- .cif + .pdb + index.csv (face-on contacts)
        A_d10_metpi/Zn/edge-on/
        B_alkali_cationpi/Na/edge-on/ ...

Contacts with porphyrin-family ligands (heme/chlorophyll/corrin/
phthalocyanine macrocycles) or embedded metals are EXCLUDED.

An entry with contacts of both classes appears in EACH corresponding
class subfolder; every index.csv lists exactly the contacts of that class.

Usage
    python step5_organize.py            # copy files + write indices
    python step5_organize.py --dry-run  # only report planned layout
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3

from config import BUCKET_FOLDERS, CIF_DIR, PDB_DIR, RESULTS_DB, STRUCTURES_DIR

INDEX_COLUMNS = [
    "pdb_id", "geometry_class", "metal_comp_id", "metal_element",
    "metal_charge", "metal_bucket", "metal_embedded",
    "ligand_comp_id", "ring_type", "ring_atoms",
    "d_centroid", "d_plane", "offset", "theta_deg", "min_dist",
    "coordination", "resolution", "method", "title",
]

GEOMETRY_CLASSES = ("face-on", "edge-on")

FOLDER_README = """Structures containing a metal-aromatic-ring contact
=================================================

Folder layout (2026-10-16)
    <bucket>/<Metal element>/<geometry class>/   <PDBID>.cif + <PDBID>.pdb + index.csv

Buckets
    A_d10_metpi       d10 ions (Zn, Cd, Hg, Cu, Ag, Au)
    B_alkali_cationpi alkali/alkaline-earth (K, Na, Mg, Ca, ...)
    C_transition      other transition metals (Fe, Mn, Co, Ni, ...)
    D_noble           noble / platinum-group metals (Pt, Pd, ...)

Geometry classes (angle-based)
    face-on   angle(metal-centroid line, ring plane) >= 60 deg
              (equivalently: angle to the ring normal <= 30 deg)
    edge-on   all other contacts with d_centroid <= 6 A
    Contacts with porphyrin-family ligands (tetrapyrrole/corrin/
    phthalocyanine macrocycles: heme, chlorophyll, cobalamin, ...) or
    with a metal embedded in the ligand itself are EXCLUDED from this
    library (special metal-coordinating macrocycles, not typical
    aromatic ligands).

Note: an entry with contacts of both classes appears in each corresponding
class subfolder. index.csv lists exactly the contacts of that class.
Files are copies of cache/cif and cache/pdb (entries without a PDB-format
file at RCSB have .cif only).
"""


def _copy_entry_files(folder, pdb_id: str) -> int:
    """Copy cif+pdb of one entry into folder. Returns 1 if cif copied."""
    copied_cif = 0
    for src_dir, ext in ((CIF_DIR, "cif"), (PDB_DIR, "pdb")):
        src = src_dir / f"{pdb_id}.{ext}"
        if not src.exists():
            continue  # pdb optional (large entries lack it)
        dst = folder / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
        if ext == "cif":
            copied_cif = 1
    return copied_cif


def _write_index(folder, rows: list) -> None:
    with open(folder / "index.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=INDEX_COLUMNS,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="report planned layout without copying files")
    args = ap.parse_args()

    conn = sqlite3.connect(RESULTS_DB)
    conn.row_factory = sqlite3.Row

    summary_rows = []

    combos = [tuple(r) for r in conn.execute(
        """SELECT DISTINCT metal_bucket, metal_element FROM hits
           WHERE geometry_class IN ('face-on', 'edge-on')
           ORDER BY metal_bucket, metal_element""")]

    print(f"[L4] {len(combos)} (bucket, metal) metal folders, "
          "each with face-on / edge-on subfolders")

    for bucket, element in combos:
        rows_all = [dict(r) for r in conn.execute(
            """SELECT * FROM hits
               WHERE geometry_class IN ('face-on', 'edge-on')
                 AND metal_bucket = ? AND metal_element = ?
               ORDER BY pdb_id""", (bucket, element))]

        for cls in GEOMETRY_CLASSES:
            rows = [r for r in rows_all if r["geometry_class"] == cls]
            if not rows:
                continue
            folder = (STRUCTURES_DIR / BUCKET_FOLDERS[bucket]
                      / element / cls)
            if not args.dry_run:
                folder.mkdir(parents=True, exist_ok=True)

            copied = 0
            for pdb_id in sorted({r["pdb_id"] for r in rows}):
                if args.dry_run:
                    copied += 1
                else:
                    copied += _copy_entry_files(folder, pdb_id)
            if not args.dry_run:
                _write_index(folder, rows)

            n_entries = len({r["pdb_id"] for r in rows})
            print(f"     {BUCKET_FOLDERS[bucket]}/{element}/{cls:<8s} "
                  f"{n_entries:>5,d} entries, {len(rows):>6,d} contacts")
            summary_rows.append({
                "folder": f"{BUCKET_FOLDERS[bucket]}/{element}/{cls}",
                "entries": n_entries, "contacts": len(rows), "class": cls,
            })

    if not args.dry_run:
        with open(STRUCTURES_DIR / "summary.csv", "w", newline="",
                  encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                "folder", "entries", "contacts", "class"])
            writer.writeheader()
            writer.writerows(summary_rows)
        (STRUCTURES_DIR / "README.txt").write_text(FOLDER_README,
                                                   encoding="utf-8")
        print(f"\n[L4] done -> {STRUCTURES_DIR} "
              "(summary.csv, README.txt written)")
    else:
        print("\n[L4] dry run - nothing copied")

    conn.close()


if __name__ == "__main__":
    main()
