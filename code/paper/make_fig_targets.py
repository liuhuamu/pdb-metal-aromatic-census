#!/usr/bin/env python3
"""Figure 7: target-level clustering of metal-aromatic contacts.

Panel A: top targets by non-embedded contacts (metal-mediated binding
         landscape), stacked by bridging class
Panel B: top targets among DRUG ligand contacts (DrugBank-annotated),
         stacked by bridging class

Source data -> paper/figures/source_data/fig7_targets_data.csv
"""
from __future__ import annotations

import csv
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
from nature_style import (BRIDGE_COLORS, DOUBLE_COL, add_panel_label,
                          apply_publication_style, save_pub)  # noqa: E402

FIG = ROOT / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
SRC = FIG / "source_data"

AA = ("HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
      "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
      "GLY", "PRO")
BRIDGE_COLORS = {"bridge-direct": "#8c564b", "bridge-near": "#1f77b4",
                 "ligand-held": "#ff7f0e", "unannotated": "#c7c7c7"}


def bridging_class(r) -> str:
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


import re


def contact_targets(r, anno_entry):
    """UniProts responsible for one contact.

    Attribution: the coordinating protein chain(s) recorded in struct_conn
    (e.g. 'HIS95(A)=2.10' -> chain A) are mapped to their UniProt.  If no
    protein-coordinating chain can be resolved (ligand-held metals such as
    Mg-ATP), the contact is attributed to all UniProts of the entry when
    the entry has <= 3 polymer entities, otherwise to a '(multi-chain
    complex)' placeholder (avoids ribosome-style inflation).
    """
    if not anno_entry or not anno_entry.get("uniprots"):
        return ["(no UniProt)"], {"(no UniProt)": "entry without UniProt"}
    names = {t["uniprot"]: t["name"] for t in anno_entry["uniprots"]}
    coord = r["coordination"] or ""
    chains = set(re.findall(r"\(([A-Za-z0-9]+)\)", coord))
    chain_map = anno_entry.get("chains", {})
    uniprots = {chain_map[c] for c in chains if c in chain_map}
    uniprots.discard(None)
    if uniprots:
        return sorted(uniprots), names
    all_u = [t["uniprot"] for t in anno_entry["uniprots"]]
    if len(all_u) <= 3:
        return all_u, names
    return ["(multi-chain complex)"], names


def main() -> None:
    anno = json.loads(
        (ROOT / "paper" / "data" / "target_annotations.json").read_text())
    lig_class = {}
    with open(ROOT / "paper" / "output" / "ligand_classification.csv") as f:
        for row in csv.DictReader(f):
            lig_class[row["comp_id"]] = row["category"]

    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    conn.row_factory = sqlite3.Row
    hits = list(conn.execute("SELECT * FROM hits"))
    conn.close()

    # per-target aggregation (chain-of-coordination attribution)
    tgt_contacts = defaultdict(Counter)   # uniprot -> Counter(bridge class)
    tgt_entries = defaultdict(set)
    tgt_name = {"(no UniProt)": "entry without UniProt annotation",
                "(multi-chain complex)": "multi-chain complex "
                                         "(metal not protein-coordinated)"}
    tgt_drug_contacts = defaultdict(Counter)
    tgt_drug_entries = defaultdict(set)

    for r in hits:
        if r["geometry_class"] == "excluded":
            continue  # porphyrin-family / embedded contacts excluded (v2)
        b = bridging_class(r)
        is_drug = lig_class.get(r["ligand_comp_id"], "other").startswith(
            "drug-")
        uniprots, names = contact_targets(r, anno.get(r["pdb_id"]))
        tgt_name.update(names)
        for u in uniprots:
            if b != "embedded":
                tgt_contacts[u][b] += 1
                tgt_entries[u].add(r["pdb_id"])
            if is_drug and b != "embedded":
                tgt_drug_contacts[u][b] += 1
                tgt_drug_entries[u].add(r["pdb_id"])

    # ---- source data table -----------------------------------------------
    rows = []
    for u in sorted(tgt_contacts,
                    key=lambda x: -sum(tgt_contacts[x].values())):
        c = tgt_contacts[u]
        rows.append({
            "uniprot": u, "target_name": tgt_name[u],
            "entries": len(tgt_entries[u]),
            "contacts": sum(c.values()),
            "bridge_direct": c["bridge-direct"],
            "bridge_near": c["bridge-near"],
            "ligand_held": c["ligand-held"],
            "unannotated": c["unannotated"],
            "drug_contacts": sum(tgt_drug_contacts[u].values()),
        })
    with open(SRC / "fig7_targets_data.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[fig7] {len(rows):,} unique targets -> source_data/"
          f"fig7_targets_data.csv")

    # ---- panel helper ------------------------------------------------------
    def draw(ax, agg, entries, title, topn=18):
        top = sorted(agg, key=lambda u: -sum(agg[u].values()))[:topn]
        labels = []
        for u in top:
            nm = tgt_name[u]
            nm = nm[0].upper() + nm[1:] if nm else u
            if len(nm) > 34:
                nm = nm[:32] + ".."
            labels.append(f"{nm}\n{u} (n={len(entries[u])})")
        ys = np.arange(len(top))[::-1]
        left = np.zeros(len(top))
        cats = ["bridge-direct", "bridge-near", "ligand-held", "unannotated"]
        for c in cats:
            vals = np.array([agg[u][c] for u in top], dtype=float)
            ax.barh(ys, vals, left=left, color=BRIDGE_COLORS[c], label=c,
                    height=0.72)
            left += vals
        for y, u in zip(ys, top):
            total = sum(agg[u].values())
            ax.text(total * 1.02, y, f"{int(total):,}", va="center",
                    fontsize=6)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels, fontsize=6)
        ax.set_xlabel("metal\u2013aromatic contacts (non-embedded)")
        ax.set_title(title, fontsize=7, loc="left")
        ax.legend(loc="lower right", fontsize=5.5)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL, 4.6))
    draw(ax1, tgt_contacts, tgt_entries,
         "a  Top targets: all non-embedded contacts")
    draw(ax2, tgt_drug_contacts, tgt_drug_entries,
         "b  Top targets: DrugBank-annotated ligands")
    add_panel_label(ax1, "a")
    add_panel_label(ax2, "b")
    fig.tight_layout(pad=1.2)
    out = FIG / "fig7_targets"
    save_pub(fig, out)
    print(f"[fig7] figure -> {out} (.png/.pdf/.svg)")

    # console top-10 preview
    print("\n[fig7] top 10 targets (non-embedded contacts):")
    for row in rows[:10]:
        print(f"  {row['uniprot']:<10s} {row['target_name'][:40]:<42s} "
              f"contacts={row['contacts']:>6,} entries={row['entries']:>4,} "
              f"drug={row['drug_contacts']:>5,}")


if __name__ == "__main__":
    main()
