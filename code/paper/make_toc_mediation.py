#!/usr/bin/env python3
"""TOC graphic: metal-ion-mediated ligand-protein binding (ACS TOC size).

3.25 in x 1.75 in. Three bridging configurations are drawn as compact
schematics in the manuscript's Figure 2 colours: bridge-direct (red),
bridge-near (blue), ligand-held (grey).
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 3.25, 1.75
DIRECT = "#B64342"
NEAR = "#3775BA"
HELD = "#8C8C8C"
METAL = "#3A3A3A"
WALL = "#E7E2D6"
DONOR = "#A79F90"
RING = "#272727"
INK = "#272727"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "figure.dpi": 600,
    "savefig.dpi": 600,
})

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


def hexagon(cx, cy, r, lw=0.9):
    pts = [(cx + r * math.cos(math.radians(60 * k + 30)),
            cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
    ax.add_patch(Polygon(pts, closed=True, fill=True, facecolor="white",
                         edgecolor=RING, linewidth=lw, zorder=5))
    ax.add_patch(Circle((cx, cy), r * 0.48, fill=False, edgecolor=RING,
                        linewidth=lw * 0.7, zorder=6))


def metal(cx, cy, r=0.047):
    ax.add_patch(Circle((cx, cy), r, facecolor=METAL, edgecolor="white",
                        linewidth=0.55, zorder=8))
    ax.add_patch(Circle((cx - r * 0.30, cy + r * 0.30), r * 0.30,
                        facecolor="white", edgecolor="none", alpha=0.45,
                        zorder=9))


def protein(x, y, w=0.34, h=0.34, ghost=False):
    if ghost:
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.07",
            facecolor="none", edgecolor="#CFCAC0", linewidth=0.7,
            linestyle=(0, (1.2, 1.6)), zorder=2))
        return
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.07",
        facecolor=WALL, edgecolor="none", zorder=2))


CY = 0.96
cells = [(0.50, "bridge-direct", "15.4%", DIRECT),
         (1.57, "bridge-near", "59.4%", NEAR),
         (2.62, "ligand-held", "22.7%", HELD)]

for cx, label, pct, color in cells:
    ghost = label == "ligand-held"
    protein(cx - 0.36, CY - 0.17, ghost=ghost)

    if ghost:
        mx = cx + 0.005
        metal(mx, CY)
        hexagon(cx + 0.195, CY, 0.085)
        root = cx + 0.105                      # substituent root on the ring
        ax.plot([cx + 0.125, root], [CY, CY], color=RING, lw=0.9, zorder=6)
        for dy in (-0.021, 0.021):
            ax.plot([root, mx + 0.030], [CY, CY + dy * 2.6], color=color,
                    lw=1.05, zorder=6, solid_capstyle="round")
            ax.scatter([mx + 0.036], [CY + dy * 2.9], s=7, color=RING,
                       zorder=7)
    else:
        mx = cx + 0.02
        metal(mx, CY)
        for dy in (-0.058, 0.058):
            ax.add_patch(Circle((cx - 0.215, CY + dy), 0.0145, facecolor=DONOR,
                                edgecolor="none", zorder=6))
            ax.plot([cx - 0.198, mx - 0.042], [CY + dy, CY + dy * 0.42],
                    color="#BDB6A8", lw=0.7, zorder=4)
        if label == "bridge-direct":
            hexagon(mx + 0.158, CY, 0.085)     # ring vertex just outside the ion
            ax.plot([mx + 0.032, mx + 0.078], [CY, CY], color=color, lw=1.3,
                    zorder=7, solid_capstyle="round")
        else:
            hexagon(cx + 0.205, CY, 0.085)     # clear gap: no bond
            ax.plot([mx + 0.038, cx + 0.126], [CY, CY], color=color, lw=0.95,
                    linestyle=(0, (1.4, 1.5)), zorder=7)

    ax.text(cx - 0.03, 0.52, label, fontsize=5.2, color=color,
            fontweight="bold", ha="center", va="center")
    ax.text(cx - 0.03, 0.34, pct, fontsize=7.8, color=color,
            fontweight="bold", ha="center", va="center")

# ---------------------------------------------------------------- headlines
ax.text(1.625, 1.555, "metal ions bridge ligands and proteins",
        fontsize=6.3, color=INK, fontweight="bold", ha="center", va="center")
ax.text(0.06, 0.10, "13,231 contacts  |  5,107 PDB entries", fontsize=4.7,
        color="#6E6E6E", ha="left", va="center")
ax.text(3.19, 0.10, "75% protein-bridged", fontsize=5.1, color=INK,
        fontweight="bold", ha="right", va="center")

fig.savefig(OUT / "toc_mediation.png", dpi=600, facecolor="white")
fig.savefig(OUT / "toc_mediation.pdf", facecolor="white")
fig.savefig(OUT / "toc_mediation.svg", facecolor="white")
plt.close(fig)
print("TOC (mediation) ->", OUT / "toc_mediation.png")
