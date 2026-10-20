#!/usr/bin/env python3
"""L3b - geometry analysis: metal-to-aromatic-ring contacts.

For every candidate structure (cache/cif/<ID>.cif, model 1 = asymmetric unit):

* metals are located as
    (a) free ions   - single-atom non-polymer residues with a metal element
    (b) embedded    - metal atoms inside an aromatic ligand itself
                      (heme/porphyrin/Ru-polypyridyl class)
* aromatic rings are perceived from the entry's own ``_chem_comp_bond``
  table (``pdbx_aromatic_flag == 'y'``) restricted to ligand comps that
  matched an L1 aromatic substructure pattern
* for every metal x ring pair the following are computed:
      d_centroid  metal ... ring centroid distance
      d_plane     perpendicular distance to the least-squares ring plane
      offset      lateral offset = sqrt(d_centroid^2 - d_plane^2)
      theta_deg   angle metal-centroid-vector vs plane normal
      min_dist    closest metal ... ring-atom distance
* classification (projection-based two-class scheme):
      excluded : metal embedded in the ligand OR porphyrin-family ligand
                 (config.PORPHYRIN_KEYWORDS)
      face-on  : d_centroid <= 6 A and lateral projection offset < 2.5 A
                 (the atomic-envelope radius of an aromatic ring)
      edge-on  : d_centroid <= 6 A, otherwise
      (pairs beyond 6 A are not stored)
* entry-level filters: resolution <= 3.0 A; metal occupancy >= 0.5

Output: data/results.sqlite (tables `hits`, `excluded`)

Usage
    python step4_geometry.py [--limit N] [--force] [--only ID1,ID2,...]
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import time
from pathlib import Path

import gemmi
import networkx as nx
import numpy as np

from config import (AROMATIC_LIGANDS_PATH, CANDIDATES_PATH, CIF_DIR,
                    D_CENTROID_MAX, FACE_ON_OFFSET_MAX, METAL_BUCKETS,
                    METAL_COMPS, METAL_MIN_OCCUPANCY, PORPHYRIN_KEYWORDS,
                    RESULTS_DB, RESOLUTION_MAX)

SCHEMA = """
CREATE TABLE IF NOT EXISTS hits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pdb_id          TEXT NOT NULL,
    title           TEXT,
    method          TEXT,
    resolution      REAL,
    n_models        INTEGER,
    metal_comp_id   TEXT,
    metal_element   TEXT,
    metal_charge    INTEGER,
    metal_bucket    TEXT,
    metal_embedded  INTEGER,      -- 1: metal atom inside the ligand (heme-like)
    metal_occupancy REAL,
    metal_subchain  TEXT,
    metal_auth      TEXT,
    ligand_comp_id  TEXT,
    ligand_subchain TEXT,
    ligand_auth     TEXT,
    ring_type       TEXT,         -- matching L1 pattern names, comma separated
    ring_atoms      TEXT,
    d_centroid      REAL,
    d_plane         REAL,
    offset          REAL,
    theta_deg       REAL,
    min_dist        REAL,
    geometry_class  TEXT,         -- chelated / face-on / edge-on / mid
    coordination    TEXT          -- struct_conn `metalc` partners, info only
);
CREATE TABLE IF NOT EXISTS excluded (pdb_id TEXT, reason TEXT);
CREATE INDEX IF NOT EXISTS idx_hits_pdb   ON hits(pdb_id);
CREATE INDEX IF NOT EXISTS idx_hits_elem  ON hits(metal_element);
CREATE INDEX IF NOT EXISTS idx_hits_class ON hits(geometry_class);
"""

INSERT = """INSERT INTO hits (
    pdb_id, title, method, resolution, n_models,
    metal_comp_id, metal_element, metal_charge, metal_bucket, metal_embedded,
    metal_occupancy, metal_subchain, metal_auth,
    ligand_comp_id, ligand_subchain, ligand_auth,
    ring_type, ring_atoms,
    d_centroid, d_plane, offset, theta_deg, min_dist,
    geometry_class, coordination) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


# --------------------------------------------------------------------------
# mmCIF parsing helpers
# --------------------------------------------------------------------------
def read_block(path: Path):
    doc = gemmi.cif.read(str(path))
    return doc.sole_block()


def get_resolution(block) -> float | None:
    for tag in ("_refine.ls_d_res_high",
                "_em_3d_reconstruction.resolution"):
        try:
            val = block.find_value(tag)
        except Exception:
            val = None
        if val:
            try:
                return float(gemmi.cif.as_number(val))
            except (TypeError, ValueError):
                continue
    return None


def get_first_value(block, tag: str) -> str | None:
    try:
        for val in block.find_values(tag):
            return gemmi.cif.as_string(val)
    except Exception:
        pass
    return None


def get_aromatic_bonds(block) -> dict:
    """comp_id -> {(atom1, atom2)} for bonds flagged aromatic."""
    out: dict = {}
    try:
        table = block.find("_chem_comp_bond.",
                           ["comp_id", "atom_id_1", "atom_id_2",
                            "pdbx_aromatic_flag"])
        for row in table:
            try:
                if row.str(3).lower() == "y":
                    out.setdefault(row.str(0), set()).add(
                        (row.str(1), row.str(2)))
            except (IndexError, ValueError):
                continue
    except Exception:
        pass
    return out


def get_metalc_records(block) -> list:
    """struct_conn rows of type `metalc` (metal coordination)."""
    records = []
    tags = ["conn_type_id",
            "ptnr1_label_asym_id", "ptnr1_label_comp_id",
            "ptnr1_label_atom_id", "ptnr1_auth_asym_id", "ptnr1_auth_seq_id",
            "ptnr2_label_asym_id", "ptnr2_label_comp_id",
            "ptnr2_label_atom_id", "ptnr2_auth_asym_id", "ptnr2_auth_seq_id",
            "pdbx_dist_value"]
    try:
        for row in block.find("_struct_conn.", tags):
            try:
                if row.str(0).lower() != "metalc":
                    continue
                records.append({
                    "asym1": row.str(1), "comp1": row.str(2),
                    "auth_asym1": row.str(4), "auth_seq1": row.str(5),
                    "asym2": row.str(6), "comp2": row.str(7),
                    "auth_asym2": row.str(9), "auth_seq2": row.str(10),
                    "dist": row.str(11),
                })
            except (IndexError, ValueError):
                continue
    except Exception:
        pass
    return records


def coordination_string(metalc: list, metal_subchain: str) -> str:
    """Partners of the metal ion from struct_conn `metalc` rows."""
    partners = []
    for rec in metalc:
        if rec["asym1"] == metal_subchain:
            partners.append(f"{rec['comp2']}{rec['auth_seq2']}"
                            f"({rec['auth_asym2']})={rec['dist']}")
        elif rec["asym2"] == metal_subchain:
            partners.append(f"{rec['comp1']}{rec['auth_seq1']}"
                            f"({rec['auth_asym1']})={rec['dist']}")
    return ";".join(partners)


# --------------------------------------------------------------------------
# structure analysis
# --------------------------------------------------------------------------
def best_atoms(residue) -> dict:
    """atom_name -> gemmi.Atom, resolving altlocs by highest occupancy."""
    chosen: dict = {}
    for atom in residue:
        if atom.name not in chosen or atom.occ > chosen[atom.name].occ:
            chosen[atom.name] = atom
    return chosen


def seqid_str(res) -> str:
    """Auth sequence number + insertion code as display string."""
    icode = getattr(res.seqid, "icode", " ") or " "
    icode = "" if icode.strip() == "" else icode.strip()
    return f"{res.seqid.num}{icode}"


# fallback residue set in case entity metadata is missing from the file
STD_RESIDUES = {
    # amino acids
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    "MSE", "SEC", "PYL", "UNK",
    # nucleotides
    "A", "C", "G", "I", "U", "DA", "DC", "DG", "DI", "DT", "DU", "N",
}


def is_nonpolymer(st, res) -> bool:
    """True if the residue belongs to a non-polymer entity (a ligand)."""
    try:
        if res.subchain:
            ent = st.get_entity_of_subchain(res.subchain)
            if ent is not None:
                return ent.entity_type == gemmi.EntityType.NonPolymer
    except Exception:
        pass
    return res.name not in STD_RESIDUES  # heuristic fallback


def ligand_rings(residue, atoms: dict, aromatic_bonds: dict) -> list:
    """Perceive aromatic rings of one ligand instance.

    Returns a list of atom-name tuples.  Single 5/6-rings are returned
    directly; fused systems are split into a cycle basis (networkx).
    """
    bonds = aromatic_bonds.get(residue.name)
    if not bonds:
        return []
    graph = nx.Graph()
    for a1, a2 in bonds:
        if a1 in atoms and a2 in atoms:
            graph.add_edge(a1, a2)

    rings = []
    for component in nx.connected_components(graph):
        sub = graph.subgraph(component)
        if all(deg == 2 for _, deg in sub.degree()) and len(component) in (5, 6):
            rings.append(tuple(sorted(component)))
        else:
            for cycle in nx.cycle_basis(sub):
                if 4 <= len(cycle) <= 8:
                    rings.append(tuple(sorted(cycle)))
    return rings


def ring_frame(coords: np.ndarray):
    """centroid + unit normal of the least-squares plane (SVD)."""
    centroid = coords.mean(axis=0)
    _, _, vt = np.linalg.svd(coords - centroid)
    normal = vt[2]
    norm = np.linalg.norm(normal)
    if norm > 0:
        normal = normal / norm
    return centroid, normal


def classify(offset, d_centroid, metal_embedded, ligand_comp,
             ligand_names) -> str | None:
    """Projection-based two-class scheme (final, matches the manuscript)."""
    if d_centroid > D_CENTROID_MAX:
        return None
    if metal_embedded:
        return "excluded"
    nm = (ligand_names.get(ligand_comp) or "").lower()
    if any(k in nm for k in PORPHYRIN_KEYWORDS):
        return "excluded"
    return "face-on" if offset < FACE_ON_OFFSET_MAX else "edge-on"


def analyze_entry(pdb_id: str, path: Path, ligand_patterns: dict,
                  aromatic_comps: set, ligand_names: dict):
    """Returns (hits_rows, exclusion_reason_or_None)."""
    block = read_block(path)

    resolution = get_resolution(block)
    method = get_first_value(block, "_exptl.method")
    title = get_first_value(block, "_struct.title")

    if resolution is None:
        return [], "no_resolution"
    if resolution > RESOLUTION_MAX:
        return [], "low_resolution"

    aromatic_bonds = get_aromatic_bonds(block)
    metalc = get_metalc_records(block)

    st = gemmi.make_structure_from_block(block)
    st.setup_entities()
    model = st[0]
    n_models = len(st)

    # --- collect residues by entity type -------------------------------
    free_metals = []        # dicts describing free metal ions
    aromatic_residues = []  # (residue, atoms)
    for chain in model:
        for res in chain:
            if not is_nonpolymer(st, res):
                continue
            subchain = res.subchain
            if res.name == "HOH" or res.name == "DOD":
                continue
            atoms = best_atoms(res)
            heavy = [a for a in atoms.values()
                     if a.element not in (gemmi.Element("H"),
                                          gemmi.Element("D"))]
            if len(heavy) == 1 and heavy[0].element.is_metal:
                atom = heavy[0]
                free_metals.append({
                    "comp_id": res.name,
                    "element": atom.element.name,
                    "charge": METAL_COMPS.get(res.name, (None, None))[1],
                    "pos": np.array([atom.pos.x, atom.pos.y, atom.pos.z]),
                    "occ": atom.occ,
                    "subchain": subchain,
                    "auth": f"{res.name}{seqid_str(res)}({chain.name})",
                    "embedded": 0,
                })
            elif res.name in aromatic_comps:
                aromatic_residues.append((res, atoms))

    if not aromatic_residues:
        return [], "no_aromatic_ligand"
    if not free_metals and not any(
            a.element.is_metal
            for _, atoms in aromatic_residues for a in atoms.values()):
        return [], "no_metal"

    # --- ring inventory --------------------------------------------------
    # rings: list of dicts with ligand info + coords
    rings = []
    embedded_metals = []
    for res, atoms in aromatic_residues:
        subchain = res.subchain
        auth = f"{res.name}{seqid_str(res)}"
        for ring_names in ligand_rings(res, atoms, aromatic_bonds):
            coords = []
            ok = True
            for name in ring_names:
                atom = atoms.get(name)
                if atom is None:
                    ok = False
                    break
                coords.append([atom.pos.x, atom.pos.y, atom.pos.z])
            if ok and len(coords) >= 4:
                rings.append({
                    "ligand_comp": res.name,
                    "ligand_subchain": subchain,
                    "ligand_auth": auth,
                    "atom_names": ",".join(ring_names),
                    "coords": np.array(coords),
                })
        # metals embedded in this aromatic ligand (heme/porphyrin class)
        for atom in atoms.values():
            if atom.element.is_metal:
                embedded_metals.append({
                    "comp_id": res.name,          # e.g. HEM
                    "element": atom.element.name,
                    "charge": None,
                    "pos": np.array([atom.pos.x, atom.pos.y, atom.pos.z]),
                    "occ": atom.occ,
                    "subchain": subchain,
                    "auth": f"{res.name}:{atom.name}",
                    "embedded": 1,
                    "own_ligand_comp": res.name,
                })

    if not rings:
        return [], "no_ring_coordinates"

    # --- metal x ring geometry -------------------------------------------
    rows = []
    all_metal_centers = free_metals + embedded_metals
    if not any(METAL_BUCKETS.get(m["element"]) for m in all_metal_centers):
        return [], "no_configured_metal"
    # only metals from the configured bucket list are analysed
    metals = [m for m in all_metal_centers
              if METAL_BUCKETS.get(m["element"])
              and m["occ"] >= METAL_MIN_OCCUPANCY]
    if not metals:
        return [], "low_metal_occupancy"

    for metal in metals:
        bucket = METAL_BUCKETS.get(metal["element"])
        for ring in rings:
            if metal["embedded"] and ring["ligand_comp"] != metal["own_ligand_comp"]:
                # embedded metal only pairs with rings of its own ligand
                continue
            centroid, normal = ring_frame(ring["coords"])
            vec = metal["pos"] - centroid
            d_centroid = float(np.linalg.norm(vec))
            d_plane = float(abs(np.dot(vec, normal)))
            offset = float(math.sqrt(max(d_centroid ** 2 - d_plane ** 2, 0.0)))
            cos_t = abs(np.dot(vec, normal)) / max(d_centroid, 1e-9)
            theta = float(math.degrees(math.acos(min(1.0, cos_t))))
            min_dist = float(np.linalg.norm(ring["coords"] - metal["pos"],
                                            axis=1).min())

            geom_class = classify(offset, d_centroid, metal["embedded"],
                                  ring["ligand_comp"], ligand_names)
            if geom_class is None:
                continue

            rows.append((
                pdb_id, title, method, resolution, n_models,
                metal["comp_id"], metal["element"], metal["charge"], bucket,
                metal["embedded"], metal["occ"], metal["subchain"],
                metal["auth"],
                ring["ligand_comp"], ring["ligand_subchain"], ring["ligand_auth"],
                ligand_patterns.get(ring["ligand_comp"], "?"),
                ring["atom_names"],
                round(d_centroid, 3), round(d_plane, 3), round(offset, 3),
                round(theta, 1), round(min_dist, 3),
                geom_class,
                ("" if metal["embedded"]
                 else coordination_string(metalc, metal["subchain"])),
            ))

    if not rows:
        return [], "no_contact"
    return rows, None


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None,
                    help="only analyse the first N candidates (testing)")
    ap.add_argument("--only", type=str, default=None,
                    help="comma-separated list of PDB IDs to (re)analyse")
    ap.add_argument("--force", action="store_true",
                    help="reanalyse entries already present in the database")
    args = ap.parse_args()

    # ligand comp -> matched pattern names (ring-type annotation)
    ligand_sets = json.loads(AROMATIC_LIGANDS_PATH.read_text())
    ligand_patterns: dict = {}
    for pattern, comps in ligand_sets.items():
        for comp in comps:
            ligand_patterns.setdefault(comp, []).append(pattern)
    ligand_patterns = {k: ",".join(v) for k, v in ligand_patterns.items()}
    aromatic_comps = set(ligand_patterns)

    # ligand names for the porphyrin-family exclusion rule
    names_path = Path(__file__).resolve().parent / "paper" / "data" / \
        "ligand_names_all.json"
    ligand_names = json.loads(names_path.read_text(encoding="utf-8"))

    candidates = json.loads(CANDIDATES_PATH.read_text())
    all_ids = sorted(candidates)

    conn = sqlite3.connect(RESULTS_DB)
    conn.executescript(SCHEMA)

    if args.only:
        todo = [i.strip().upper() for i in args.only.split(",") if i.strip()]
    else:
        todo = all_ids
        if not args.force:
            done = {r[0] for r in conn.execute(
                "SELECT pdb_id FROM hits UNION SELECT pdb_id FROM excluded")}
            todo = [i for i in todo if i not in done]
    if args.limit:
        todo = todo[:args.limit]

    print(f"[L3b] {len(todo):,} entries to analyse "
          f"(cache: {CIF_DIR}), db: {RESULTS_DB}")

    t0 = time.time()
    counts: dict = {}
    for n, pdb_id in enumerate(todo, 1):
        path = CIF_DIR / f"{pdb_id}.cif"
        try:
            if not path.exists():
                reason = "no_cif"
                rows = []
            else:
                rows, reason = analyze_entry(pdb_id, path, ligand_patterns,
                                             aromatic_comps, ligand_names)
        except Exception as exc:  # noqa: BLE001 - log and continue
            rows, reason = [], f"parse_error:{type(exc).__name__}:{exc}"[:200]
            print(f"  [err] {pdb_id}: {reason}", file=sys.stderr)

        if rows:
            conn.executemany(INSERT, rows)
        else:
            reason = reason or "no_contact"
            conn.execute("INSERT INTO excluded VALUES (?,?)",
                         (pdb_id, reason))
            counts[reason] = counts.get(reason, 0) + 1

        if n % 200 == 0 or n == len(todo):
            conn.commit()
            rate = n / max(time.time() - t0, 1e-9)
            eta_min = (len(todo) - n) / max(rate, 1e-9) / 60
            n_hits = conn.execute("SELECT COUNT(*) FROM hits").fetchone()[0]
            print(f"[L3b] {n:,}/{len(todo):,}  hits={n_hits:,}  "
                  f"({rate:.1f}/s, eta {eta_min:.0f} min)", flush=True)

    conn.commit()
    n_hits = conn.execute("SELECT COUNT(*) FROM hits").fetchone()[0]
    n_excl = conn.execute("SELECT COUNT(*) FROM excluded").fetchone()[0]
    print(f"\n[L3b] done: {n_hits:,} metal-ring contacts stored, "
          f"{n_excl:,} entries excluded")
    if counts:
        print("[L3b] exclusion reasons:")
        for reason, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"     {reason:25s} {cnt:,}")
    conn.close()


if __name__ == "__main__":
    main()
