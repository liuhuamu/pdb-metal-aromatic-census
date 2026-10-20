#!/usr/bin/env python3
"""Export every figure as PNG + PDF and collect source data (v2 scheme).

- monkey-patches Figure.savefig so every figure is written in both PNG and
  vector PDF
- re-runs all figure-producing scripts (make_figures, make_fig_definitions,
  analysis_pdbbind x2, step6_stats, make_fig_targets)
- copies the figures that live outside paper/figures into paper/figures
- writes per-figure source-data CSVs into paper/figures/source_data/

v2 (2026-10-16): angle-based two-class geometry scheme, porphyrin-family
contacts excluded (see paper/reclassify_v2.py).
"""
from __future__ import annotations

import csv
import json
import runpy
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.figure

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
FIG = ROOT / "paper" / "figures"
SRC = FIG / "source_data"
SRC.mkdir(parents=True, exist_ok=True)

AA = ("HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
      "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
      "GLY", "PRO")


# ------------------------------------------------ dual PNG+PDF output ------
_orig_savefig = matplotlib.figure.Figure.savefig


def _savefig_both(self, fname, *args, **kwargs):
    _orig_savefig(self, fname, *args, **kwargs)
    fname = str(fname)
    if fname.lower().endswith(".png"):
        _orig_savefig(self, fname[:-4] + ".pdf")


matplotlib.figure.Figure.savefig = _savefig_both


def run(script: str, argv: list | None = None) -> None:
    print(f"\n===== running {script} =====", flush=True)
    script_path = ROOT / script
    for d in (script_path.parent, ROOT):
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
    old_argv = sys.argv
    try:
        sys.argv = [str(script_path)] + (argv or [])
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = old_argv


def main() -> None:
    # ---- 1. regenerate all figures with dual output ----------------------
    run("paper/make_figures.py")
    run("paper/make_fig_definitions.py")
    run("paper/analysis_pdbbind.py",
        ["--index", r"E:\agent\protein\index\INDEX_general_PL_data.2020",
         "--label", "general_PL_2020"])
    run("paper/analysis_pdbbind.py",
        ["--index", r"E:\agent\protein\index\INDEX_refined_data.2020",
         "--label", "refined_2020"])
    run("step6_stats.py")
    run("paper/make_fig_targets.py")

    # ---- 2. gather figures written outside paper/figures ------------------
    for pattern in ("fig_pdbbind_*.png", "fig_pdbbind_*.pdf",
                    "dist_hist_*.png", "dist_hist_*.pdf"):
        for f in (ROOT / "figures").glob(pattern):
            shutil.copy2(f, FIG / f.name)

    # ---- 3. source data ----------------------------------------------------
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    conn.row_factory = sqlite3.Row
    hits = list(conn.execute("SELECT * FROM hits"))
    incl = [r for r in hits if r["geometry_class"] != "excluded"]

    def bridge(r):
        if r["metal_embedded"]:
            return "embedded"
        coord = r["coordination"] or ""
        protein = any(aa in coord for aa in AA)
        if protein and r["min_dist"] <= 2.8:
            return "bridge-direct"
        if protein:
            return "bridge-near"
        if coord.strip():
            return "ligand-held"
        return "unannotated"

    def write_csv(name, header, rows):
        with open(SRC / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        print(f"  source: {name} ({len(rows):,} rows)")

    # fig1 funnel (v2)
    aromatic = set().union(*json.loads(
        (ROOT / "data" / "aromatic_entries.json").read_text()).values())
    candidates = set(json.loads(
        (ROOT / "data" / "candidates.json").read_text()).keys())
    hit_entries = {r["pdb_id"] for r in incl}
    cls_counts = Counter(r["geometry_class"] for r in incl)
    write_csv("fig1_funnel_data.csv",
              ["item", "value"],
              [("entries_in_pdb_archive_experimental", 261301),
               ("entries_with_aromatic_ligand", len(aromatic)),
               ("entries_with_metal", len(candidates)),
               ("entries_with_contact_le_6A_nonporphyrin",
                len(hit_entries)),
               ("total_contacts_all", len(hits)),
               ("total_contacts_nonporphyrin", len(incl)),
               ("contacts_porphyrin_excluded", len(hits) - len(incl))]
              + [(f"contacts_{k}", v) for k, v in cls_counts.most_common()])

    # per-contact source data (Figure 1c/d geometry quantities)
    write_csv("fig1_contacts_data.csv",
              ["pdb_id", "geometry_class", "metal_element", "ligand_comp_id",
               "d_centroid", "d_plane", "offset", "theta_deg", "min_dist"],
              [(r["pdb_id"], r["geometry_class"], r["metal_element"],
                r["ligand_comp_id"], r["d_centroid"], r["d_plane"],
                r["offset"], r["theta_deg"], r["min_dist"]) for r in incl])

    # fig3 bridging per metal
    pm = defaultdict(Counter)
    pe = defaultdict(set)
    for r in incl:
        b = bridge(r)
        if b == "embedded":
            continue
        pm[r["metal_element"]][b] += 1
        pe[(r["metal_element"], b)].add(r["pdb_id"])
    write_csv("fig3_bridging_data.csv",
              ["metal_element", "bridge_class", "contacts", "entries"],
              [(m, b, pm[m][b], len(pe[(m, b)]))
                for m in sorted(pm, key=lambda x: -sum(pm[x].values()))
                for b in ("bridge-direct", "bridge-near", "ligand-held",
                          "unannotated") if pm[m][b]])

    # fig4 geometry class per metal
    gm = defaultdict(Counter)
    ge = defaultdict(set)
    for r in incl:
        gm[r["metal_element"]][r["geometry_class"]] += 1
        ge[(r["metal_element"], r["geometry_class"])].add(r["pdb_id"])
    write_csv("fig4_geomclass_data.csv",
              ["metal_element", "geometry_class", "contacts", "entries",
               "pct_within_metal"],
              [(m, g, gm[m][g], len(ge[(m, g)]),
                round(100 * gm[m][g] / sum(gm[m].values()), 2))
                for m in sorted(gm, key=lambda x: -sum(gm[x].values()))
                for g in ("face-on", "edge-on") if gm[m][g]])

    # fig5 drug categories
    lig_class = {}
    with open(ROOT / "paper" / "output" / "ligand_classification.csv") as f:
        for row in csv.DictReader(f):
            lig_class[row["comp_id"]] = row["category"]
    names = json.loads(
        (ROOT / "paper" / "data" / "ligand_names_all.json").read_text())
    cat_c, cat_e = Counter(), defaultdict(set)
    drug_metal = Counter()
    comp_c = Counter()
    for r in incl:
        c = lig_class.get(r["ligand_comp_id"], "other")
        cat_c[c] += 1
        cat_e[c].add(r["pdb_id"])
        if c == "drug-approved":
            drug_metal[r["metal_element"]] += 1
            comp_c[r["ligand_comp_id"]] += 1
    write_csv("fig5_drugs_data.csv",
              ["category", "contacts", "entries"],
              [(c, n, len(cat_e[c])) for c, n in cat_c.most_common()])
    write_csv("fig5_approved_by_metal.csv",
              ["metal_element", "contacts"], drug_metal.most_common())
    write_csv("fig5_approved_by_ligand.csv",
              ["ligand_comp_id", "ligand_name", "contacts"],
              [(c, names.get(c, ""), n) for c, n in comp_c.most_common()])

    # fig6 cases
    CASE_IDS = ("6HWZ", "9XS9", "9QGV", "4HSJ", "7ARW", "9GOG")
    write_csv("fig6_cases_data.csv",
              ["pdb_id", "metal_comp_id", "metal_element", "ligand_comp_id",
               "geometry_class", "d_centroid", "d_plane", "offset",
               "theta_deg", "min_dist", "coordination", "resolution",
               "title"],
              [(r["pdb_id"], r["metal_comp_id"], r["metal_element"],
                r["ligand_comp_id"], r["geometry_class"], r["d_centroid"],
                r["d_plane"], r["offset"], r["theta_deg"], r["min_dist"],
                r["coordination"], r["resolution"], r["title"])
               for r in hits
               if r["pdb_id"] in CASE_IDS
               and r["geometry_class"] != "excluded"])

    # dist histogram source
    write_csv("dist_hist_data.csv",
              ["metal_bucket", "geometry_class", "d_centroid", "d_plane",
               "offset", "theta_deg"],
              [(r["metal_bucket"], r["geometry_class"], r["d_centroid"],
                r["d_plane"], r["offset"], r["theta_deg"]) for r in incl])

    conn.close()

    # pdbbind source (copy the existing per-complex tables)
    for name in ("pdbbind_general_PL_2020.csv", "pdbbind_refined_2020.csv",
                 "pdbbind_general_PL_2020_tests.csv",
                 "pdbbind_refined_2020_tests.csv"):
        src = ROOT / "paper" / "output" / name
        if src.exists():
            shutil.copy2(src, SRC / name)
            print(f"  source: {name} (copied)")

    # ---- 4. final listing ---------------------------------------------------
    print("\n===== paper/figures contents =====")
    for f in sorted(FIG.iterdir()):
        if f.is_file():
            print(f"  {f.name:<44s} {f.stat().st_size/1024:>8.1f} KB")
    print("  source_data/")
    for f in sorted(SRC.iterdir()):
        print(f"    {f.name:<42s} {f.stat().st_size/1024:>8.1f} KB")


if __name__ == "__main__":
    main()
