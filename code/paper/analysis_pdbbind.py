#!/usr/bin/env python3
"""Paper analysis 2: PDBbind intersection & affinity association.

READY TO RUN - needs one input file: a PDBbind index file
(e.g. INDEX_refined_data.2020 / INDEX_general_data.2020, downloaded from a
registered pdbbind-plus.org.cn account), or a plain CSV with columns
(pdb_id, neg_log_k).

Usage
    python paper/analysis_pdbbind.py --index <path> [--label refined_2020]

What it does
    1. parses the index (PDB code + -log Kd/Ki per complex)
    2. classifies every PDBbind complex against our screening database:
         hit          - has a metal-aromatic contact (<=6 A)   [results.sqlite]
         no-contact   - has a configured metal but no contact <=6 A
         no-metal     - aromatic ligand but no configured metal [step1-step2]
    3. compares -logK distributions across the groups
       (permutation test, no scipy needed) + box plots
    4. writes paper/output/pdbbind_*.csv and paper/figures/fig_pdbbind.png
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
PAPER_OUT = ROOT / "paper" / "output"
FIG_DIR = ROOT / "figures"
PAPER_OUT.mkdir(parents=True, exist_ok=True)

BRIDGE_PRIORITY = ["bridge-direct", "bridge-near", "ligand-held",
                   "unannotated", "embedded"]


# --------------------------------------------------------------------------
def parse_index(path: Path) -> dict:
    """Parse a PDBbind index (or simple csv) -> {pdb_id: (neg_log_k, measure)}."""
    affinities = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # plain CSV mode: pdb_id,neg_log_k
        if "," in line and len(line.split(",")) == 2:
            parts = [p.strip() for p in line.split(",")]
            if len(parts[0]) == 4:
                try:
                    affinities[parts[0].upper()] = (float(parts[1]), "?")
                    continue
                except ValueError:
                    pass
        tokens = line.split()
        if len(tokens) < 3 or len(tokens[0]) != 4:
            continue
        pdb_id = tokens[0]
        if not pdb_id[0].isdigit():
            continue
        float_idx = []          # (index, value) of numeric columns
        for i, t in enumerate(tokens[1:], start=1):
            try:
                v = float(t)
            except ValueError:
                continue
            if v == int(v) and 1970 <= v <= 2035:   # release year column
                continue
            float_idx.append((i, v))
        if float_idx:
            # last numeric column is -log(Kd/Ki) in all known layouts
            i_k, neg_k = float_idx[-1]
            measure = "?"
            if i_k + 1 < len(tokens):
                measure = tokens[i_k + 1].split("=")[0]
            affinities[pdb_id.upper()] = (neg_k, measure)
    return affinities


def load_groups() -> dict:
    """Group every relevant PDB entry: hit / no-contact / no-metal / outside."""
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    conn.row_factory = sqlite3.Row
    hits = {}
    for r in conn.execute(
            "SELECT * FROM hits WHERE geometry_class != 'excluded'"):
        pid = r["pdb_id"]
        coord = r["coordination"] or ""
        protein = any(aa in coord for aa in (
            "HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
            "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
            "GLY", "PRO"))
        if r["metal_embedded"]:
            cls = "embedded"
        elif protein and r["min_dist"] <= 2.8:
            cls = "bridge-direct"
        elif protein:
            cls = "bridge-near"
        elif coord.strip():
            cls = "ligand-held"
        else:
            cls = "unannotated"
        cur = hits.get(pid)
        if cur is None or BRIDGE_PRIORITY.index(cls) < BRIDGE_PRIORITY.index(cur[0]):
            hits[pid] = (cls, r["metal_element"], r["ligand_comp_id"])
    no_contact = {r[0] for r in conn.execute(
        "SELECT pdb_id FROM excluded WHERE reason = 'no_contact'")}
    # entries whose ONLY contacts are porphyrin-excluded: treat as
    # no-contact (metal present, no qualifying non-porphyrin contact)
    no_contact |= ({r[0] for r in conn.execute(
        "SELECT DISTINCT pdb_id FROM hits")} - set(hits))
    conn.close()

    candidates = set(json.loads(
        (ROOT / "data" / "candidates.json").read_text()).keys())
    aromatic = set().union(*json.loads(
        (ROOT / "data" / "aromatic_entries.json").read_text()).values())
    no_metal = aromatic - candidates

    return {"hits": hits, "no_contact": no_contact, "no_metal": no_metal,
            "aromatic": aromatic}


def permutation_test(a, b, n=20_000, seed=1):
    """Two-sided permutation test on the difference of medians."""
    if not a or not b:
        return float("nan"), float("nan")
    obs = abs(sorted(a)[len(a) // 2] - sorted(b)[len(b) // 2])
    rng = random.Random(seed)
    combined = list(a) + list(b)
    na = len(a)
    count = 0
    for _ in range(n):
        rng.shuffle(combined)
        sa, sb = combined[:na], combined[na:]
        sa.sort(); sb.sort()
        d = abs(sa[len(sa) // 2] - sb[len(sb) // 2])
        if d >= obs - 1e-12:
            count += 1
    return obs, count / n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True, help="PDBbind index file or CSV")
    ap.add_argument("--label", default="pdbbind")
    args = ap.parse_args()

    aff = parse_index(Path(args.index))
    print(f"[pdbbind] parsed {len(aff):,} complexes with affinity "
          f"from {args.index}")
    if not aff:
        raise SystemExit("no rows parsed - check the index format")

    groups = load_groups()
    rows = []
    for pid, (neglogk, measure) in sorted(aff.items()):
        if pid in groups["hits"]:
            cls, el, lig = groups["hits"][pid]
            grp = cls
        elif pid in groups["no_contact"]:
            grp, el, lig = "no-contact", "", ""
        elif pid in groups["no_metal"]:
            grp, el, lig = "no-metal", "", ""
        else:
            grp, el, lig = "outside", "", ""
        rows.append({"pdb_id": pid, "neg_log_k": neglogk, "measure": measure,
                     "group": grp, "element": el, "ligand": lig})

    # ---- summary ----------------------------------------------------------
    from collections import Counter
    cnt = Counter(r["group"] for r in rows)
    print("\n[pdbbind] complex classification:")
    for g, n in cnt.most_common():
        vals = [r["neg_log_k"] for r in rows if r["group"] == g]
        med = sorted(vals)[len(vals) // 2] if vals else float("nan")
        print(f"  {g:<14s} n={n:>5,d}   median -logK = {med:.2f}")
    meas = Counter(r["measure"] for r in rows)
    print("[pdbbind] affinity measures:", dict(meas.most_common()))

    import csv
    with open(PAPER_OUT / f"pdbbind_{args.label}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pdb_id", "neg_log_k", "measure",
                                          "group", "element", "ligand"])
        w.writeheader()
        w.writerows(rows)

    # ---- group comparisons -------------------------------------------------
    def vals(g):
        return [r["neg_log_k"] for r in rows if r["group"] == g]

    comparisons = []
    for g1, g2 in [("bridge-direct", "no-contact"),
                   ("bridge-direct", "no-metal"),
                   ("bridge-near", "no-contact"),
                   ("embedded", "no-metal"),
                   ("no-contact", "no-metal")]:
        a, b = vals(g1), vals(g2)
        if len(a) >= 5 and len(b) >= 5:
            diff, p = permutation_test(a, b)
            comparisons.append((g1, g2, len(a), len(b), diff, p))
    with open(PAPER_OUT / f"pdbbind_{args.label}_tests.csv", "w",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["group1", "group2", "n1", "n2",
                    "median_diff", "perm_p"])
        w.writerows(comparisons)
    print("\n[pdbbind] permutation tests (median difference):")
    for g1, g2, n1, n2, d, p in comparisons:
        print(f"  {g1:<14s} vs {g2:<12s} n={n1:>4,d}/{n2:>4,d}  "
              f"diff={d:+.2f}  p={p:.4f}")

    # ---- box plot ------------------------------------------------------------
    order = [g for g in ["bridge-direct", "bridge-near", "ligand-held",
                         "embedded", "unannotated", "no-contact", "no-metal",
                         "outside"] if vals(g)]
    fig, ax = plt.subplots(figsize=(8, 5))
    data = [vals(g) for g in order]
    ax.boxplot(data, showfliers=True)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(order, rotation=30, ha="right")
    ax.set_ylabel(r"$-\log(K_d/K_i)$")
    ax.set_title(f"PDBbind complexes vs metal-contact classification "
                 f"({args.label})")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    out = FIG_DIR / f"fig_pdbbind_{args.label}.png"
    fig.savefig(out, dpi=200)
    print(f"\n[pdbbind] figure -> {out}")


if __name__ == "__main__":
    main()
