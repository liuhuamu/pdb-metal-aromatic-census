#!/usr/bin/env python3
"""Figure 5: protein-type distribution of metal-aromatic contacts.

Chains are classified into broad protein types from their Pfam families
(RCSB polymer-entity annotations; keyword rules below, documented in the
SI). Contacts are attributed to the protein type of the chain that
coordinates the metal.

Panel a: heatmap of contact counts, protein type (rows) x metal element
          (columns).
Panel b: metal-bucket composition per protein type (100% stacked).

Source data -> paper/figures/source_data/fig_classes_data.csv
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
sys.path.insert(0, str(ROOT / "paper"))
from nature_style import PALETTE, add_panel_label, apply_publication_style  # noqa: E402

FIG = ROOT / "paper" / "figures"
SRC = FIG / "source_data"
FIG.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)

AA = ("HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
      "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
      "GLY", "PRO")

# Pfam name/description keyword rules -> broad protein type.
# Ordered: first match wins (specific families before generic functions).
CLASS_RULES = [
    ("Carbonic anhydrase", ("carbonic anhydrase", "carb_anhydrase")),
    ("Metallo-beta-lactamase",
     ("metallo-beta-lactamase", "beta-lactamase", "lactamase_b")),
    ("Protein kinase", ("pkinase", "protein kinase", "tyrosine kinase",
                        "pk_tyr_ser-thr", "kinase domain")),
    ("Photosynthetic apparatus",
     ("photosystem", "chlorophyll", "light-harvesting", "reaction center",
      "peridinin", "fcp", "kranz", "psb", "psa")),
    ("GPCR", ("7tm", "gpcr")),
    ("Ribosome", ("ribosomal", "ribosome")),
    ("Cytochrome", ("cytochrome",)),
    ("Ferritin", ("ferritin",)),
    ("Histone deacetylase", ("hist_deacetyl", "histone deacetylase")),
    ("Histone demethylase", ("jmj", "histone demethylase", "jmjd")),
    ("Tubulin", ("tubulin",)),
    ("Protease", ("peptidase", "protease", "thermolysin", "trypsin",
                  "neprilysin")),
    ("Phosphodiesterase", ("phosphodiesterase", "pdease")),
    ("Deaminase", ("deaminase",)),
    ("Nuclease", ("endonuclease", "exonuclease", "nuclease")),
    ("Polyprenyl synthase", ("polyprenyl",)),
    ("tRNA synthetase", ("trna-synt", "trna synthetase")),
    ("Integrase", ("integrase", "rve")),
    ("NO synthase", ("no_synthase", "nitric oxide")),
    ("2OG-Fe oxygenase", ("2og-fe", "ring_hydroxyl")),
    ("Biopterin hydroxylase", ("biopterin",)),
    ("Periplasmic binding protein", ("peripla", "sbp_bac")),
    ("Dehydratase/lyase", ("imidazoleglycerol", "dehydratase")),
    ("Lipocalin", ("lipocalin",)),
    ("Somatomedin", ("somatomedin",)),
    ("CRISPR protein", ("cas_ne0113", "crispr")),
    ("Dehydrogenase", ("dehydrogenase",)),
    ("Hydrolase", ("hydrolase",)),
    ("Transferase", ("transferase",)),
    ("Oxidoreductase", ("oxidoreductase", "monooxygenase")),
    ("Zinc finger", ("zinc finger", "znf")),
    ("Cupin", ("cupin",)),
    ("Glyoxalase", ("glyoxalase",)),
    ("HPPK", ("hppk",)),
    ("Phytanoyl dioxygenase", ("phyh", "phytano")),
    ("TonB-dependent receptor", ("tonb",)),
    ("RNase H", ("rnase_h", "rnase")),
    ("Malic enzyme", ("malic",)),
    ("Ion channel", ("ion_trans", "ion transport")),
    ("Phospholipase", ("phospholip",)),
]


def classify_pfam(pfam_names):
    """Map Pfam families of one chain to a broad protein type."""
    blob = " ".join(pfam_names).lower()
    for type_name, keys in CLASS_RULES:
        if any(k in blob for k in keys):
            return type_name
    return "Other"


def main() -> None:
    anno = json.loads(
        (ROOT / "paper" / "data" / "target_annotations.json").read_text())

    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    conn.row_factory = sqlite3.Row
    hits = list(conn.execute(
        "SELECT * FROM hits WHERE geometry_class != 'excluded'"))
    conn.close()

    # ---- attribute contacts to protein types -----------------------------
    # contact -> coordinating chains -> Pfam -> protein type
    type_metal = defaultdict(Counter)      # (ptype, element) -> contacts
    type_bucket = defaultdict(Counter)     # (ptype, bucket) -> contacts
    type_entries = defaultdict(set)
    type_names = {}

    unclassified_chains = Counter()

    for r in hits:
        anno_e = anno.get(r["pdb_id"]) or {}
        chains = anno_e.get("chains", {})
        pfam_map = anno_e.get("pfam", {})
        coord = r["coordination"] or ""
        coord_chains = set(re.findall(r"\(([A-Za-z0-9]+)\)", coord))
        all_chains = set(coord_chains)

        # resolve protein type per coordinating chain
        ptypes = set()
        for ch in coord_chains:
            pf = pfam_map.get(ch)
            if pf:
                pt = classify_pfam(pf)
                ptypes.add(pt)
                type_names.setdefault(pt, "; ".join(pf)[:60])
            elif ch in chains:
                # chain has UniProt but no Pfam -> Other
                ptypes.add("Other")
        if not ptypes:
            # ligand-held / unannotated: use entry-level Pfam if the entry
            # has few entities, else placeholder
            entry_pfams = set()
            for ch, pf in pfam_map.items():
                entry_pfams.update(pf)
            if entry_pfams:
                pt = classify_pfam(sorted(entry_pfams))
                ptypes.add(pt)
            else:
                ptypes.add("Other")
                type_names.setdefault("Other", "Pfam not annotated")

        for pt in ptypes:
            type_metal[pt][r["metal_element"]] += 1
            type_bucket[pt][r["metal_bucket"]] += 1
            type_entries[pt].add(r["pdb_id"])

    # ---- panel a: heatmap -------------------------------------------------
    top_types = sorted(type_metal, key=lambda t: -sum(type_metal[t].values()))
    top_types = [t for t in top_types if sum(type_metal[t].values()) >= 20]
    top_types = top_types[:16]
    metals = sorted({m for t in top_types
                     for m in type_metal[t]},
                    key=lambda m: -sum(type_metal[t][m] for t in top_types))
    metals = metals[:10]

    mat = np.zeros((len(top_types), len(metals)))
    for i, t in enumerate(top_types):
        for j, m in enumerate(metals):
            mat[i, j] = type_metal[t].get(m, 0)

    apply_publication_style(font_size=7, axes_linewidth=0.8)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(7.2, 3.6), gridspec_kw={"width_ratios": [1.8, 1]})

    im = ax1.imshow(np.log10(mat + 1), cmap="Blues", aspect="auto")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = int(mat[i, j])
            if v >= 5:
                col = "white" if np.log10(v + 1) > 0.55 * np.log10(
                    mat.max() + 1) else "#272727"
                ax1.text(j, i, str(v), ha="center", va="center",
                         fontsize=5.5, color=col)
    ax1.set_xticks(range(len(metals)))
    ax1.set_xticklabels(metals, rotation=45, ha="right")
    ax1.set_yticks(range(len(top_types)))
    ax1.set_yticklabels(top_types)
    ax1.set_title("a  Contacts per protein type and metal", loc="left",
                  fontsize=7)
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    cax = make_axes_locatable(ax1).append_axes("right", size="4%",
                                               pad=0.08)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("log10(contacts + 1)", fontsize=6)
    cbar.ax.tick_params(labelsize=5.5)

    # ---- panel b: metal-bucket composition per type -----------------------
    buckets = ["A", "B", "C", "D"]
    bucket_colors = {"A": "#0F4D92", "B": "#8BCF8B", "C": "#B64342",
                     "D": "#9A4D8E"}
    ys = np.arange(len(top_types))[::-1]
    left = np.zeros(len(top_types))
    for b in buckets:
        vals = np.array(
            [100 * type_bucket[t].get(b, 0) / max(sum(type_bucket[t].values()), 1)
             for t in top_types])
        ax2.barh(ys, vals, left=left, color=bucket_colors[b],
                 label=f"bucket {b}", height=0.7)
        left += vals
    ax2.set_yticks(ys)
    ax2.set_yticklabels([])
    ax2.set_xlabel("% of contacts")
    ax2.set_xlim(0, 100)
    ax2.set_title("b  Metal-bucket composition", loc="left", fontsize=7)
    ax2.legend(fontsize=5.5, loc="lower right")

    fig.tight_layout(pad=1.2)
    fig.savefig(FIG / "fig_classes.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig_classes.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"[classes] figure -> FIG/fig_classes.png (top {len(top_types)} "
          f"types x {len(metals)} metals)")

    # ---- source data -------------------------------------------------------
    import csv
    rows = []
    for t in top_types:
        for m in metals:
            rows.append([t, m, type_metal[t].get(m, 0)])
    with open(SRC / "fig_classes_data.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["protein_type", "metal_element", "contacts"])
        w.writerows(rows)

    rows2 = []
    for t in top_types:
        total = sum(type_bucket[t].values())
        for b in buckets:
            rows2.append([t, b, type_bucket[t].get(b, 0),
                          round(100 * type_bucket[t].get(b, 0)
                                / max(total, 1), 2)])
    with open(SRC / "fig_classes_buckets.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["protein_type", "metal_bucket", "contacts", "pct"])
        w.writerows(rows2)
    print("[classes] source data -> fig_classes_data.csv, "
          "fig_classes_buckets.csv")

    # console preview
    print("\n[classes] top protein types (non-excluded contacts):")
    for t in top_types[:12]:
        tot = sum(type_metal[t].values())
        top_metals = ", ".join(
            f"{m}={c}" for m, c in
            sorted(type_metal[t].items(), key=lambda x: -x[1])[:4])
        print(f"  {t:<26s} {tot:>6,}  ({top_metals})")


if __name__ == "__main__":
    main()
