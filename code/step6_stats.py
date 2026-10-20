#!/usr/bin/env python3
"""L5 - statistics and figures for the metal-aromatic contact database.

Produces (figures/ and output/):
    counts_by_bucket.csv     bucket x geometry_class contact counts
    counts_by_metal.csv      element x geometry_class contact counts
    top_ligands.csv          most frequent ligand comps per element
    dist_hist_<bucket>.png   d_centroid / d_plane / offset histograms
                             split by geometry class
"""
from __future__ import annotations

import sqlite3
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from config import FIG_DIR, OUTPUT_DIR, RESULTS_DB  # noqa: E402

sys.path.insert(0, str(FIG_DIR.parent))
from nature_style import CLASS_COLORS, apply_publication_style  # noqa: E402


def main() -> None:
    conn = sqlite3.connect(RESULTS_DB)
    df = pd.read_sql(
        "SELECT * FROM hits WHERE geometry_class != 'excluded'", conn)
    conn.close()
    if df.empty:
        print("[L5] hits table empty - run step4 first")
        return

    print(f"[L5] {len(df):,} contacts, "
          f"{df.pdb_id.nunique():,} unique entries")

    # ---- counts tables ---------------------------------------------------
    counts_bucket = (df.groupby(["metal_bucket", "geometry_class"])
                       .size().unstack(fill_value=0))
    counts_bucket.to_csv(OUTPUT_DIR / "counts_by_bucket.csv")

    counts_metal = (df.groupby(["metal_element", "geometry_class"])
                      .size().unstack(fill_value=0))
    counts_metal.to_csv(OUTPUT_DIR / "counts_by_metal.csv")

    top = (df.groupby(["metal_element", "ligand_comp_id"])
             .size().rename("n").reset_index()
             .sort_values("n", ascending=False)
             .groupby("metal_element").head(8))
    top.to_csv(OUTPUT_DIR / "top_ligands.csv", index=False)

    print("\n[L5] contacts by bucket x class:")
    print(counts_bucket.to_string())

    # ---- histograms ------------------------------------------------------
    metrics = [("d_centroid", "metal ... ring centroid distance (A)"),
               ("d_plane", "metal ... ring plane distance (A)"),
               ("offset", "lateral offset (A)"),
               ("theta_deg", "angle to ring normal (deg)")]
    groups = {"A": "A d10 (met-pi)", "B": "B alkali (cation-pi)",
              "C": "C transition", "D": "D noble"}
    for key, label in groups.items():
        sub = df[df.metal_bucket == key]
        if sub.empty:
            continue
        fig, axes = plt.subplots(1, len(metrics), figsize=(7.2, 2.0))
        for ax, (metric, xlabel) in zip(axes, metrics):
            for cls, color in CLASS_COLORS.items():
                vals = sub.loc[sub.geometry_class == cls, metric]
                if vals.empty:
                    continue
                vals.hist(ax=ax, bins=40, alpha=0.8, label=cls,
                          color=color)
            if metric == "offset":
                ax.axvline(2.5, c="black", ls="--", lw=0.8)
            ax.set_xlabel(xlabel)
            ax.set_ylabel("count")
        axes[0].legend(fontsize=5.5)
        fig.suptitle(f"bucket {label}  ({len(sub):,} contacts, "
                     f"{sub.pdb_id.nunique():,} entries; porphyrins "
                     f"excluded)", fontsize=7)
        fig.tight_layout(pad=1.0)
        out = FIG_DIR / f"dist_hist_{key}.png"
        fig.savefig(out, dpi=300)
        plt.close(fig)
        print(f"[L5] wrote {out}")

    print(f"\n[L5] CSV tables -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
