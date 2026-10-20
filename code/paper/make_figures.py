#!/usr/bin/env python3
"""Paper figures (v2 classification), styled with the nature-figure rules.

Journal-final sizes (double column 7.2 in / single column 5.0 in), 7 pt
base font, Arial, spines top/right off, frameless legends, unified
palette (blue hero / neutral family / red accent).
"""
from __future__ import annotations

import json
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
from nature_style import (  # noqa: E402
    BRIDGE_COLORS, CLASS_COLORS, DOUBLE_COL, ONE_HALF_COL, PALETTE,
    add_panel_label, apply_publication_style, save_pub)

FIG = ROOT / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

AA = ("HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
      "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
      "GLY", "PRO")


def bridging_class(row) -> str:
    if row["metal_embedded"]:
        return "embedded"
    coord = row["coordination"] or ""
    protein = any(aa in coord for aa in AA)
    if protein and row["min_dist"] <= 2.8:
        return "bridge-direct"
    if protein:
        return "bridge-near"
    if coord.strip():
        return "ligand-held"
    return "unannotated"


def load_hits():
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    conn.row_factory = sqlite3.Row
    hits = list(conn.execute("SELECT * FROM hits"))
    conn.close()
    return hits


HITS = load_hits()
HITS_INCL = [r for r in HITS if r["geometry_class"] != "excluded"]


# ---------------------------------------------------------------- Fig 1 ----
def fig1_funnel():
    import make_fig_definitions as mfd

    pdb_total = 261301   # experimental entries in the archive (2026-10-16,
                         # RCSB Search API, query omitted = match all)
    aromatic = set().union(*json.loads(
        (ROOT / "data" / "aromatic_entries.json").read_text()).values())
    candidates = set(json.loads(
        (ROOT / "data" / "candidates.json").read_text()).keys())
    hit_entries = {r["pdb_id"] for r in HITS_INCL}

    apply_publication_style(font_size=7, axes_linewidth=0.8)
    fig = plt.figure(figsize=(DOUBLE_COL, 5.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.15],
                          width_ratios=[1.25, 1])

    # ---- row 1: funnel + donut ------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    stages = [
        "PDB archive\n(experimental entries)",
        "+ non-polymeric\naromatic ligand",
        "+ configured metal ion",
        "+ non-porphyrin\ncontact \u2264 6 \u00c5",
    ]
    vals = [pdb_total, len(aromatic), len(candidates), len(hit_entries)]
    ys = np.arange(len(stages))[::-1]
    ax1.barh(ys, vals, color=[PALETTE["neutral_light"],
                              PALETTE["blue_main"],
                              PALETTE["blue_secondary"],
                              PALETTE["red_strong"]], height=0.62)
    for y, v in zip(ys, vals):
        ax1.text(v * 1.06, y, f"{v:,}", va="center", fontsize=7,
                 fontweight="bold")
    ax1.set_yticks(ys)
    ax1.set_yticklabels(stages, fontsize=6.5)
    ax1.set_xscale("log")
    ax1.set_xlim(1e3, 2e6)
    ax1.set_xlabel("PDB entries (log scale)")
    add_panel_label(ax1, "a")

    # donut of the geometry classes (non-excluded)
    cls = Counter(r["geometry_class"] for r in HITS_INCL)
    order = ["edge-on", "face-on"]
    sizes = [cls[c] for c in order]
    colors = [CLASS_COLORS[c] for c in order]
    wedges, _ = ax2.pie(sizes, colors=colors, startangle=90,
                        counterclock=False,
                        wedgeprops=dict(width=0.42, edgecolor="white"))
    ax2.text(0, 0.08, f"{sum(sizes):,}", ha="center", fontsize=9,
             fontweight="bold")
    ax2.text(0, -0.16, "contacts", ha="center", fontsize=6.5,
             color=PALETTE["neutral_dark"])
    for w, c, v in zip(wedges, order, sizes):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        x, y = np.cos(ang) * 0.8, np.sin(ang) * 0.8
        ax2.annotate(f"{c}\n{v:,} ({100*v/sum(sizes):.1f}%)",
                     xy=(x * 1.02, y * 1.02),
                     xytext=(x * 1.32, y * 1.32),
                     ha="center", va="center", fontsize=6.5,
                     arrowprops=dict(arrowstyle="-", lw=0.6,
                                     color=PALETTE["neutral_mid"]))
    add_panel_label(ax2, "b")
    ax2.set_title("", fontsize=7)

    # ---- row 2: geometric quantities (c) + class schematics (d) ---------
    axA = fig.add_subplot(gs[1, 0], projection="3d")
    gs_bot = gs[1, 1].subgridspec(1, 3)
    axes_c = [fig.add_subplot(gs_bot[0, i]) for i in range(3)]
    mfd.panel_a(axA)
    mfd.panel_c(axes_c)
    # 3-D axes have no 2-D text(); use text2D for the panel label
    axA.text2D(-0.05, 1.02, "c", transform=axA.transAxes,
               fontsize=8, fontweight="bold", va="bottom")
    add_panel_label(axes_c[0], "d")

    fig.tight_layout(pad=1.5)
    save_pub(fig, FIG / "fig1_funnel")
    print("fig1 done")


# ---------------------------------------------------------------- Fig 3 ----
def fig3_bridging():
    per_metal = defaultdict(Counter)
    for r in HITS_INCL:
        b = bridging_class(r)
        if b == "embedded":
            continue
        per_metal[r["metal_element"]][b] += 1
    metals = sorted(per_metal, key=lambda m: -sum(per_metal[m].values()))
    metals = [m for m in metals if sum(per_metal[m].values()) >= 20][:12]

    apply_publication_style(font_size=7, axes_linewidth=0.8)
    fig, ax = plt.subplots(figsize=(ONE_HALF_COL, 3.4))
    cats = ["bridge-direct", "bridge-near", "ligand-held", "unannotated"]
    ys = np.arange(len(metals))[::-1]
    left = np.zeros(len(metals))
    for c in cats:
        vals = np.array([per_metal[m][c] for m in metals], dtype=float)
        ax.barh(ys, vals, left=left, color=BRIDGE_COLORS[c], label=c,
                height=0.7)
        left += vals
    for y, m in zip(ys, metals):
        total = sum(per_metal[m].values())
        ax.text(total * 1.03, y, f"{int(total):,}", va="center",
                fontsize=6)
    ax.set_yticks(ys)
    ax.set_yticklabels(metals)
    ax.set_xlabel("metal\u2013ligand contacts (porphyrin-family excluded)")
    ax.legend(loc="lower right", fontsize=5.5)
    add_panel_label(ax, "")
    fig.tight_layout(pad=1.2)
    save_pub(fig, FIG / "fig3_bridging")
    print("fig3 done")


# ---------------------------------------------------------------- Fig 4 ----
def fig4_geomclass():
    """Per-metal geometry mix.

    Only metals with >= 50 non-excluded contacts are ranked (sparse metals
    such as Ru, 23 contacts, are noted in the caption/text instead), the rows
    are ordered by face-on fraction, and every segment carries its value with
    one decimal place.
    """
    MIN_CONTACTS = 50

    per_metal = defaultdict(Counter)
    for r in HITS_INCL:
        per_metal[r["metal_element"]][r["geometry_class"]] += 1
    totals = {m: sum(c.values()) for m, c in per_metal.items()}
    metals = [m for m in per_metal if totals[m] >= MIN_CONTACTS]
    frac = {m: 100 * per_metal[m].get("face-on", 0) / totals[m]
            for m in metals}
    metals.sort(key=lambda m: frac[m])          # smallest fraction at bottom

    apply_publication_style(font_size=7, axes_linewidth=0.8)
    fig, ax = plt.subplots(figsize=(6.3, 0.285 * len(metals) + 1.05))
    ys = np.arange(len(metals))
    for i, m in enumerate(metals):
        p = frac[m]
        q = 100 - p
        ax.barh(ys[i], p, color=CLASS_COLORS["face-on"], height=0.70,
                label="face-on" if i == 0 else None, zorder=3)
        ax.barh(ys[i], q, left=p, color=CLASS_COLORS["edge-on"], height=0.70,
                label="edge-on" if i == 0 else None, zorder=3)
        # face-on value: inside the segment when it is wide enough, otherwise
        # immediately to its right (still inside the bar)
        if p >= 7:
            ax.text(p / 2, ys[i], f"{p:.1f}%", va="center", ha="center",
                    fontsize=6, color="white", fontweight="bold", zorder=4)
        else:
            ax.text(p + 1.4, ys[i], f"{p:.1f}%", va="center", ha="left",
                    fontsize=5.8, color=CLASS_COLORS["face-on"],
                    fontweight="bold", zorder=4)
        ax.text(97.5, ys[i], f"{q:.1f}%", va="center", ha="right",
                fontsize=6, color=PALETTE["neutral_dark"], fontweight="bold",
                zorder=4)

    ax.set_yticks(ys)
    ax.set_yticklabels([f"{m} ({totals[m]})" for m in metals], fontsize=6.5)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("% of contacts")
    ax.xaxis.grid(True, ls=":", lw=0.4, color="#D9D9D9", zorder=0)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.115), ncol=2,
              frameon=False, fontsize=6.5, handlelength=1.1,
              handleheight=0.7, columnspacing=1.4)
    fig.tight_layout(pad=0.45)
    save_pub(fig, FIG / "fig4_geomclass")
    plt.close(fig)
    print("fig4 done:", ", ".join(f"{m} {frac[m]:.1f}%" for m in metals[::-1]))


# ---------------------------------------------------------------- Fig 5 ----
def fig5_drugs():
    lig_class = {}
    with open(ROOT / "paper" / "output" / "ligand_classification.csv") as f:
        import csv
        for row in csv.DictReader(f):
            lig_class[row["comp_id"]] = row["category"]
    names = json.loads(
        (ROOT / "paper" / "data" / "ligand_names_all.json").read_text())

    cat_contacts = Counter()
    cat_entries = defaultdict(set)
    drug_metal = Counter()
    comp_contacts = Counter()
    for r in HITS_INCL:
        cat = lig_class.get(r["ligand_comp_id"], "other")
        cat_contacts[cat] += 1
        cat_entries[cat].add(r["pdb_id"])
        if cat == "drug-approved":
            drug_metal[r["metal_element"]] += 1
            comp_contacts[r["ligand_comp_id"]] += 1

    apply_publication_style(font_size=7, axes_linewidth=0.8)
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COL, 2.4))

    ax = axes[0]
    order = [c for c, _ in cat_contacts.most_common()]
    xs = np.arange(len(order))[::-1]
    colors = [PALETTE["blue_main"] if c == "drug-approved"
              else PALETTE["neutral_light"] for c in order]
    ax.barh(xs, [cat_contacts[c] for c in order], color=colors)
    ax.set_yticks(xs)
    ax.set_yticklabels([c.replace("drug-", "") for c in order], fontsize=6)
    ax.set_xscale("log")
    ax.set_xlim(1, 3e5)
    ax.set_xlabel("contacts (log)")
    add_panel_label(ax, "a")

    ax = axes[1]
    order2 = [m for m, _ in drug_metal.most_common()][:10]
    ax.bar(range(len(order2)), [drug_metal[m] for m in order2],
           color=PALETTE["blue_main"])
    ax.set_xticks(range(len(order2)))
    ax.set_xticklabels(order2)
    ax.set_ylabel("contacts")
    add_panel_label(ax, "b")

    ax = axes[2]
    top = comp_contacts.most_common(10)
    labels = [f"{c}\n{names.get(c, '')[:16]}" for c, _ in top]
    ax.bar(range(len(top)), [n for _, n in top],
           color=PALETTE["blue_secondary"])
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=5.5)
    ax.set_ylabel("contacts")
    add_panel_label(ax, "c")

    fig.tight_layout(pad=1.2)
    save_pub(fig, FIG / "fig5_drugs")
    print("fig5 done")


# ---------------------------------------------------------------- Fig 6 ----
def fig6_cases():
    import gemmi  # noqa: F401
    cases = [
        ("9GOG", "Na", "A1IOM",
         "a  Lysozyme, Na$^+$ cation$-\pi$\nface-on (77.5\u00b0, 3.68 \u00c5)"),
        ("7ARW", "Mg", "8NA",
         "b  ARH3 + NAD adenine ring\nMg face-on (69.6\u00b0, 3.29 \u00c5)"),
        ("4HSJ", "Fe", "6PC",
         "c  HAA dioxygenase + picolinate\nFe face-on (62.4\u00b0, 2.57 \u00c5)"),
        ("9QGV", "Zn", "IMD",
         "d  Endonuclease + imidazole\nZn face-on (82.3\u00b0, 2.06 \u00c5)"),
        ("6HWZ", "Zn", "GXE",
         "e  CA II + benzeneselenol\nZn edge-on (34.2\u00b0)"),
        ("9XS9", "Ru", "MML",
         "f  Cupin + Ru(\u03b76-p-cymene)\nface-on (86.1\u00b0, 1.68 \u00c5)"),
    ]
    fig = plt.figure(figsize=(DOUBLE_COL, 4.4))
    for i, (pid, el, comp, title) in enumerate(cases, 1):
        ax = fig.add_subplot(2, 3, i, projection="3d")
        try:
            (mpos, mres, lig, lig_atoms, lig_elems, bonds, arom, partners) \
                = _case_data(pid, el, comp)
        except Exception as exc:
            ax.set_title(f"{pid}: {exc}", fontsize=6)
            continue

        for a1, a2 in bonds:
            if a1 in lig_atoms and a2 in lig_atoms:
                p1, p2 = lig_atoms[a1], lig_atoms[a2]
                isarom = (a1, a2) in arom or (a2, a1) in arom
                ax.plot(*zip(p1, p2), c="#333333",
                        lw=1.6 if isarom else 0.9, alpha=0.9)
        for name, p in lig_atoms.items():
            e = lig_elems[name]
            color = {"C": "#666666", "N": "#3355cc", "O": "#cc3333",
                     "S": "#ccaa22", "Se": "#cc7722", "P": "#ff7700",
                     "H": "#cccccc"}.get(e, "#994499")
            big = name in {a for bond in arom for a in bond}
            ax.scatter(*p, c=color, s=50 if big else 25, depthshade=True)

        ax.scatter(*mpos, c="#aa3377", s=180, marker="o",
                   edgecolors="black", linewidths=1.0, depthshade=False)

        for label, aname, p, d in partners:
            ax.scatter(*p, c="#4c72b0", s=20)
            ax.plot(*zip(mpos, p), ls="--", c="#4c72b0", lw=0.8,
                    alpha=0.8)

        ring_atoms = sorted({a for bond in arom for a in bond
                             if a in lig_atoms})
        if ring_atoms:
            coords = np.array([lig_atoms[a] for a in ring_atoms])
            centroid = coords.mean(axis=0)
            d_c = np.linalg.norm(mpos - centroid)
            ax.scatter(*centroid, c="none", s=35, marker="x")
            ax.plot(*zip(centroid, mpos), ls=":", c="#aa3377", lw=1.2)
            ax.text(*(centroid + (mpos - centroid) * 0.45),
                    f"{d_c:.2f} \u00c5", fontsize=6, color="#aa3377",
                    fontweight="bold")

        allpts = list(lig_atoms.values()) + [mpos] + [p for _, _, p, _ in
                                                      partners]
        pts = np.array(allpts)
        c0, r = pts.mean(axis=0), max(6.0, (pts.max(0) - pts.min(0)).max())
        ax.set_xlim(c0[0] - r, c0[0] + r)
        ax.set_ylim(c0[1] - r, c0[1] + r)
        ax.set_zlim(c0[2] - r, c0[2] + r)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        ax.set_box_aspect((1, 1, 1))
        ax.set_title(title, fontsize=6.5)
    fig.tight_layout(pad=0.8)
    save_pub(fig, FIG / "fig6_cases")
    print("fig6 done")


# ---------------------------------------------------------------- Fig 8 ----
def _case_data(pdb_id, element, lig_comp):
    """Coordinates + bonds for one case: metal, ligand, coordinating atoms."""
    import gemmi
    path = ROOT / "cache" / "cif" / f"{pdb_id}.cif"
    block = gemmi.cif.read(str(path)).sole_block()

    bonds_all, bonds_arom = [], set()
    for row in block.find("_chem_comp_bond.",
                          ["comp_id", "atom_id_1", "atom_id_2"]):
        if row.str(0) == lig_comp:
            bonds_all.append((row.str(1), row.str(2)))
    for row in block.find("_chem_comp_bond.",
                          ["comp_id", "atom_id_1", "atom_id_2",
                           "pdbx_aromatic_flag"]):
        if row.str(0) == lig_comp and row.str(3).lower() == "y":
            bonds_arom.add((row.str(1), row.str(2)))

    st = gemmi.make_structure_from_block(block)
    st.setup_entities()
    model = st[0]

    metal = None
    for chain in model:
        for res in chain:
            for atom in res:
                if atom.element.name == element and (
                        res.name in ("ZN", "MG", "MN", "CU", "CU1", "CU2",
                                     "FE", "FE2", "NI", "CO", "CA", "NA",
                                     "K", "RU", "AG", "LI", "RB", "CS",
                                     "SR", "BA", "CD", "HG")):
                    metal = (np.array([atom.pos.x, atom.pos.y, atom.pos.z]),
                             res, atom, chain.name)
    if metal is None:
        raise RuntimeError(f"metal {element} not found in {pdb_id}")

    mpos, mres, matom, mchain = metal

    best, bestd = None, 1e9
    for chain in model:
        for res in chain:
            if res.name != lig_comp:
                continue
            for atom in res:
                d = np.linalg.norm(
                    mpos - [atom.pos.x, atom.pos.y, atom.pos.z])
                if d < bestd:
                    bestd, best = d, res
    lig = best
    lig_atoms = {a.name: np.array([a.pos.x, a.pos.y, a.pos.z])
                 for a in lig}
    lig_elems = {a.name: a.element.name for a in lig}

    partners = []
    for chain in model:
        for res in chain:
            if res.name == lig_comp:
                continue
            for atom in res:
                d = np.linalg.norm(
                    mpos - [atom.pos.x, atom.pos.y, atom.pos.z])
                if d <= 2.9 and atom.element.name not in ("H", "D"):
                    partners.append((
                        f"{res.name}{res.seqid.num}({chain.name})",
                        atom.name,
                        np.array([atom.pos.x, atom.pos.y, atom.pos.z]), d))
    return mpos, mres, lig, lig_atoms, lig_elems, bonds_all, bonds_arom, \
        partners


if __name__ == "__main__":
    fig1_funnel()
    fig3_bridging()
    fig4_geomclass()
    fig5_drugs()
    fig6_cases()
    print("all figures ->", FIG)
