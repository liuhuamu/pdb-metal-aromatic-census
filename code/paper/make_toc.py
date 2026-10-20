#!/usr/bin/env python3
"""Graphical table of contents (TOC) for the JCIM submission.

ACS specification: 3.25 in x 1.75 in (8.25 cm x 4.45 cm), >= 300 dpi,
self-contained image, minimal wording. Palette follows the manuscript
figures (face-on blue, edge-on grey, red accent).
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 3.25, 1.75
FACE = "#0F4D92"
EDGE_DARK = "#8A8A8A"
ACCENT = "#B64342"
INK = "#272727"
GREY = "#5F5F5F"

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


def ring(cx, cy, r, color=INK, lw=0.9):
    pts = [(cx + r * math.cos(math.radians(60 * k + 30)),
            cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
    ax.add_patch(Polygon(pts, closed=True, fill=True, facecolor="white",
                         edgecolor=color, linewidth=lw, zorder=3))
    ax.add_patch(Circle((cx, cy), r * 0.50, fill=False, edgecolor=color,
                        linewidth=lw * 0.7, zorder=4))


def ion(cx, cy, r, color, z=5):
    ax.add_patch(Circle((cx, cy), r, facecolor=color, edgecolor="white",
                        linewidth=0.7, zorder=z))
    ax.add_patch(Circle((cx - r * 0.28, cy + r * 0.30), r * 0.30,
                        facecolor="white", edgecolor="none", alpha=0.5,
                        zorder=z + 1))


# ------------------------------------------------------------- panel A: icons
ring(0.40, 1.20, 0.155)
ax.plot([0.40, 0.40], [1.36, 1.45], color=FACE, lw=0.55, ls=(0, (1.3, 1.3)),
        zorder=2)
ion(0.40, 1.50, 0.072, FACE)

ring(0.40, 0.46, 0.155)
ion(0.615, 0.46, 0.072, EDGE_DARK)

ax.text(0.72, 1.36, "face-on", fontsize=6.0, color=FACE, fontweight="bold",
        va="center", ha="left")
ax.text(0.72, 1.20, "7.4%", fontsize=13.0, color=FACE, fontweight="bold",
        va="center", ha="left")

ax.text(0.72, 0.54, "edge-on", fontsize=6.0, color=EDGE_DARK,
        fontweight="bold", va="center", ha="left")
ax.text(0.72, 0.38, "92.6%", fontsize=13.0, color=EDGE_DARK,
        fontweight="bold", va="center", ha="left")

# -------------------------------------------------- panel B: target contrast
ax.text(1.58, 1.50, "the target, not the ion", fontsize=6.6, color=INK,
        fontweight="bold", va="center", ha="left")
ax.text(1.58, 1.34, "face-on contacts (%)", fontsize=5.2, color=GREY,
        va="center", ha="left")

rows = [("metalloproteinases", "60.5%", FACE, 1.14),
        ("carbonic anhydrases", "0.3%", EDGE_DARK, 0.90)]
for name, val, color, y in rows:
    ax.scatter([1.63], [y], s=18, color=color, zorder=6, edgecolor="white",
               linewidth=0.5)
    ax.text(1.73, y, name, fontsize=5.6, color=color, va="center", ha="left")
    ax.text(3.06, y, val, fontsize=7.4, color=color, fontweight="bold",
            va="center", ha="right")

ax.plot([1.63, 3.06], [0.74, 0.74], color="#D6D6D6", lw=0.5, zorder=1)
ax.text(1.58, 0.58, "same Zn(II) and 3xHis donor set", fontsize=5.1,
        color=ACCENT, va="center", ha="left")

# ------------------------------------------------------------------- footer
ax.text(0.06, 0.10, "13,231 contacts in 5,107 PDB entries", fontsize=4.8,
        color="#6E6E6E", ha="left", va="center")

fig.savefig(OUT / "toc_graphic.png", dpi=600, facecolor="white")
fig.savefig(OUT / "toc_graphic.pdf", facecolor="white")
fig.savefig(OUT / "toc_graphic.svg", facecolor="white")
plt.close(fig)
print("TOC ->", OUT / "toc_graphic.png")
