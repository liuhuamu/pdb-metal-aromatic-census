#!/usr/bin/env python3
"""Build the comprehensive supporting-information workbook.

paper/SI_Tables.xlsx - one workbook, eighteen sheets:

  S0_README            sheet index + classification criteria + definitions
  S1_Screening         funnel counts, QC/exclusion statistics, class counts
  S2_Metals            metal elements, buckets, comp->charge dictionary
  S3_Patterns          aromatic ring SMILES patterns + per-pattern counts
  S4_Ligands           all 37,877 aromatic comps: category + name
  S5_Contacts          all 57,578 metal-aromatic contacts (24 columns)
  S6_Structures        one summary row per hit structure (7,953)
  S7_Targets           UniProt target clustering table (1,336)
  S8_PDBbind_general   PDBbind v2020 general PL set intersection (19,443)
  S9_PDBbind_refined   PDBbind v2020 refined set intersection (5,316)
  S10_PDBbind_tests    permutation-test summaries (both datasets)
  S11_Curated_lists    curated cofactor / additive comp lists
  S12_Criterion        offset / angle sensitivity of the face-on class
  S13_Ring_chemistry   face-on fraction by ring class, size, metal, category
  S14_Coordination     face-on fraction by coordination number / donor set
  S15_PDBbind_matched  target-matched affinity contrasts (stratified)
  S16_Target_class     face-on fraction per protein type (+ bootstrap CI)
  S17_PDBbind_rank     rank-normalized (within-target) affinity contrasts
  S18_MMP_isoforms     matrix metalloproteinase / metzincin subset

Supersedes the earlier SI_Table_structures.xlsx (same contact/structure
sheets, plus everything else).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
PAPER = ROOT / "paper"
sys.path.insert(0, str(PAPER))
sys.path.insert(0, str(ROOT))

from analysis_drug import ADDITIVES, COFACTORS  # noqa: E402
from config import METAL_BUCKETS, METAL_COMPS  # noqa: E402


def sheet_s0():
    rows = [
        ("Title", "Metal-aromatic contacts in PDB protein-ligand structures "
                  "- Supporting Tables"),
        ("Generated", "2026-10-16 (pipeline: pdb-metal-pi)"),
        ("Sheet S1", "Screening funnel + quality-control statistics"),
        ("Sheet S2", "Metal elements, buckets A-D, comp->charge dictionary"),
        ("Sheet S3", "Aromatic ring SMILES substructure patterns"),
        ("Sheet S4", "Ligand functional classification (all aromatic comps)"),
        ("Sheet S5", "ALL metal-aromatic ring contacts (one row per "
                     "contact; filter any classification column)"),
        ("Sheet S6", "One summary row per hit structure"),
        ("Sheet S7", "UniProt target-level clustering"),
        ("Sheet S8/S9", "PDBbind v2020 intersection (general PL / refined)"),
        ("Sheet S10", "Sensitivity of the face-on class to the offset and "
                      "angle criteria"),
        ("Sheet S11", "Face-on fraction by ring chemistry (class, size, "
                      "metal, ligand category, substructure pattern)"),
        ("Sheet S12", "Face-on fraction by the metal's coordination "
                      "number and protein donor set"),
        ("Sheet S13", "Target-matched (stratified) PDBbind affinity "
                      "contrasts"),
        ("Sheet S14", "Face-on fraction per protein type with "
                      "entry-clustered bootstrap 95% CI (= Table 4)"),
        ("Sheet S15", "Rank-normalized within-target PDBbind affinity "
                      "contrasts"),
        ("Sheet S16", "Matrix metalloproteinase / metzincin subset"),
        ("Sheet PDBbind_tests",
         "PDBbind v2020 permutation tests (both datasets)"),
        ("Sheet Curated_lists", "Curated cofactor / additive comp lists"),
        ("", ""),
        ("GEOMETRY CLASS CRITERIA (2026-10-16, distances in Angstrom)",
         ""),
        ("d_centroid", "metal...ring centroid distance"),
        ("d_plane", "perpendicular distance metal...least-squares ring plane"),
        ("offset", "sqrt(d_centroid^2 - d_plane^2)"),
        ("theta_deg", "angle between metal-centroid vector and ring normal "
                      "(theta_plane = 90 - theta_deg is the angle to the "
                      "ring plane)"),
        ("min_dist", "closest metal...ring-atom distance"),
        ("face-on", "lateral projection offset < 2.5 A from the ring "
                    "centre (the atomic-envelope radius of an aromatic "
                    "ring)"),
        ("edge-on", "offset >= 2.5 A, with d_centroid <= 6 A"),
        ("excluded", "contacts with porphyrin-family ligands "
                     "(tetrapyrrole/corrin/phthalocyanine macrocycles: "
                     "heme, chlorophyll, cobalamin, siroheme, ...) or with "
                     "a metal embedded in the ligand itself"),
        ("cutoff", "contacts beyond 6 A were not stored"),
        ("", ""),
        ("BRIDGING CLASSES (metal-mediated binding configuration)", ""),
        ("bridge-direct", "metal coordinated by protein residues AND "
                          "bonded (<=2.8 A) to a ligand ring atom"),
        ("bridge-near", "metal coordinated by protein residues; ligand "
                        "ring within 6 A"),
        ("ligand-held", "metal held by ligand itself or water/ions "
                        "(e.g. Mg-ATP)"),
        ("embedded", "metal is part of the aromatic ligand (heme, "
                     "chlorophyll)"),
        ("unannotated", "no struct_conn coordination annotation"),
        ("", ""),
        ("METAL BUCKETS", "A: d10 (Zn Cd Hg Cu Ag Au) | B: alkali/alkaline-"
                          "earth (Li Na K Rb Cs Mg Ca Sr Ba) | "
                          "C: other transition | D: noble/platinum-group"),
        ("LIGAND CATEGORIES", "DrugBank drug_groups (approved/withdrawn/"
                              "investigational/vet_approved/nutraceutical/"
                              "experimental) take priority after curated "
                              "cofactor and additive lists"),
        ("TARGET ATTRIBUTION", "contacts attributed to the UniProt of the "
                               "protein chain coordinating the metal "
                               "(struct_conn); non-protein-coordinated "
                               "metals in multi-chain complexes are "
                               "labelled '(multi-chain complex)'"),
        ("SOURCE FIGURES", "figure source data in figures/source_data/"),
    ]
    return pd.DataFrame(rows, columns=["item", "description"])


def sheet_s1(contacts: pd.DataFrame) -> pd.DataFrame:
    aromatic = set().union(*json.loads(
        (ROOT / "data" / "aromatic_entries.json").read_text()).values())
    candidates = set(json.loads(
        (ROOT / "data" / "candidates.json").read_text()).keys())
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    excl = conn.execute(
        "SELECT reason, COUNT(*) FROM excluded GROUP BY reason "
        "ORDER BY 2 DESC").fetchall()
    conn.close()

    rows = [("entries_with_aromatic_ligand", len(aromatic)),
            ("entries_with_configured_metal", len(candidates)),
            ("entries_with_contact_le_6A", contacts.pdb_id.nunique()),
            ("total_contacts", len(contacts)),
            ("", ""),
            ("EXCLUSION REASONS (of 37,337 candidates)", "")]
    rows += [(f"  {r}", n) for r, n in excl]
    rows += [("", ""), ("CONTACTS BY GEOMETRY CLASS", "")]
    rows += [(f"  {k}", v) for k, v in
             contacts.geometry_class.value_counts().items()]
    rows += [("", ""), ("CONTACTS BY BRIDGING CLASS", "")]
    rows += [(f"  {k}", v) for k, v in
             contacts.bridging_class.value_counts().items()]
    rows += [("", ""), ("CONTACTS BY METAL BUCKET", "")]
    rows += [(f"  {k}", v) for k, v in
             contacts[contacts.metal_bucket.notna()]
             .metal_bucket.value_counts().items()]
    return pd.DataFrame(rows, columns=["item", "count"])


def sheet_s2() -> pd.DataFrame:
    rows = []
    for comp, (el, chg) in sorted(METAL_COMPS.items()):
        rows.append({"comp_id": comp, "element": el, "charge": chg,
                     "bucket": METAL_BUCKETS.get(el, "")})
    for el, b in sorted(METAL_BUCKETS.items()):
        rows.append({"comp_id": "", "element": el, "charge": "",
                     "bucket": b})
    return pd.DataFrame(rows)


def sheet_s3() -> pd.DataFrame:
    entries = json.loads((ROOT / "data" / "aromatic_entries.json").read_text())
    ligands = json.loads((ROOT / "data" / "aromatic_ligands.json").read_text())
    from config import AROMATIC_SMILES
    return pd.DataFrame([
        {"pattern": name, "smiles": smi,
         "entries_with_ligand": len(entries[name]),
         "ligand_comps": len(ligands[name])}
        for name, smi in AROMATIC_SMILES.items()])


def sheet_s4() -> pd.DataFrame:
    names = json.loads((PAPER / "data" / "ligand_names_all.json").read_text())
    df = pd.read_csv(PAPER / "output" / "ligand_classification.csv")
    df["name"] = df["comp_id"].map(names).fillna("")
    return df[["comp_id", "category", "name"]]


def sheet_s6(contacts: pd.DataFrame) -> pd.DataFrame:
    agg = (contacts.groupby("pdb_id")
           .agg(title=("title", "first"),
                method=("method", "first"),
                resolution=("resolution", "first"),
                n_contacts=("geometry_class", "size"),
                metals=("metal_element", lambda s: ";".join(sorted(set(s)))),
                ligands=("ligand_comp_id",
                         lambda s: ";".join(sorted(set(s)))),
                geometry_classes=("geometry_class",
                                  lambda s: ";".join(sorted(set(s)))),
                ligand_categories=("ligand_category",
                                   lambda s: ";".join(sorted(set(s)))),
                structure_folders=("structure_folder",
                                   lambda s: ";".join(sorted(set(s)))))
           .reset_index())
    return agg


def main() -> None:
    contacts = pd.read_csv(PAPER / "figures" / "source_data" /
                           "SI_contacts.csv")

    s0 = sheet_s0()
    s1 = sheet_s1(contacts)
    s2 = sheet_s2()
    s3 = sheet_s3()
    s4 = sheet_s4()
    s6 = sheet_s6(contacts)
    s7 = pd.read_csv(PAPER / "figures" / "source_data" /
                     "fig7_targets_data.csv")
    s8 = pd.read_csv(PAPER / "output" / "pdbbind_general_PL_2020.csv")
    s9 = pd.read_csv(PAPER / "output" / "pdbbind_refined_2020.csv")
    t1 = pd.read_csv(PAPER / "output" /
                     "pdbbind_general_PL_2020_tests.csv")
    t1.insert(0, "dataset", "general_PL_2020")
    t2 = pd.read_csv(PAPER / "output" / "pdbbind_refined_2020_tests.csv")
    t2.insert(0, "dataset", "refined_2020")
    s10 = pd.concat([t1, t2], ignore_index=True)
    s11 = pd.DataFrame(
        [{"list": "cofactor", "comp_id": c} for c in sorted(COFACTORS)] +
        [{"list": "additive", "comp_id": a} for a in sorted(ADDITIVES)])

    # ---- v3 deep-analysis tables -----------------------------------------
    s12 = pd.read_csv(PAPER / "output" / "SI_S12_criterion.csv")
    s13 = pd.read_csv(PAPER / "output" / "SI_S13_ring_chemistry.csv")
    s14 = pd.read_csv(PAPER / "output" / "SI_S14_coordination.csv")
    s15 = pd.read_csv(PAPER / "output" / "SI_S15_pdbbind_matched.csv")
    s16 = pd.read_csv(PAPER / "output" / "SI_S16_target_class.csv")
    s17 = pd.read_csv(PAPER / "output" / "SI_S17_pdbbind_rank.csv")
    s18 = pd.read_csv(PAPER / "output" / "SI_S18_mmp_isoforms.csv")

    sheets = [
        ("S0_README", s0), ("S1_Screening", s1), ("S2_Metals", s2),
        ("S3_Patterns", s3), ("S4_Ligands", s4),
        ("S5_Contacts", contacts), ("S6_Structures", s6),
        ("S7_Targets", s7), ("S8_PDBbind_general", s8),
        ("S8_PDBbind_general", s8),
        ("S9_PDBbind_refined", s9), ("PDBbind_tests", s10),
        ("Curated_lists", s11),
        ("S10_Criterion", s12), ("S11_Ring_chemistry", s13),
        ("S12_Coordination", s14), ("S13_PDBbind_matched", s15),
        ("S14_Target_class", s16), ("S15_PDBbind_rank", s17),
        ("S16_MMP_isoforms", s18),
    ]

    xlsx = PAPER / "SI_Tables.xlsx"
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for name, df in sheets:
            df.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.book[name]
            sheet.freeze_panes = "A2"
            n_cols = sheet.max_column
            sheet.auto_filter.ref = (
                f"A1:{get_column_letter(n_cols)}{sheet.max_row}")
            for i in range(1, n_cols + 1):
                col = get_column_letter(i)
                h = str(sheet.cell(1, i).value)
                if h in ("description", "title", "coordination", "smiles"):
                    sheet.column_dimensions[col].width = 60
                elif h in ("name", "target_name", "ligands",
                           "geometry_classes", "ligand_categories",
                           "structure_folders", "structure_folder",
                           "ligand_name", "item"):
                    sheet.column_dimensions[col].width = 30
                else:
                    sheet.column_dimensions[col].width = 13
            for cell in sheet[1]:
                cell.font = Font(bold=True)

    print(f"workbook -> {xlsx}")
    for name, df in sheets:
        print(f"  {name:<22s} {len(df):>7,} rows x {len(df.columns)} cols")

    # the comprehensive workbook supersedes the earlier file
    old = PAPER / "SI_Table_structures.xlsx"
    if old.exists():
        old.unlink()
        print("removed superseded SI_Table_structures.xlsx")


if __name__ == "__main__":
    main()
