#!/usr/bin/env python3
"""Geometry-classification definitions figure (methods schematic) - v2.

Panel A: 3D schematic of the geometric quantities
         (d_centroid, d_plane, offset, theta)
Panel B: all non-excluded contacts in (offset, d_plane) space with the
         angle-based classification boundary drawn (real data)
Panel C: side-view schematics: face-on / edge-on / excluded (porphyrin)

v2 criteria (2026-10-16):
  face-on : lateral projection of the metal within 2.5 A of the ring
            centre (offset < 2.5 A)
  edge-on : all other contacts with d_centroid <= 6 A
  excluded: porphyrin-family ligands or metal embedded in the ligand
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
FIG = ROOT / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

CLS_COLOR = {"face-on": "#1f77b4", "edge-on": "#d62728"}


def unit(v):
    return v / np.linalg.norm(v)


# ---------------------------------------------------------------- panel A --
def panel_a(ax):
    n = unit(np.array([0.32, 0.28, 0.90]))
    u = unit(np.cross(n, [0, 0, 1]))
    v = np.cross(n, u)
    c0 = np.zeros(3)
    r = 1.4
    angs = np.linspace(0, 2 * np.pi, 7)
    ring = np.array([c0 + r * (np.cos(a) * u + np.sin(a) * v)
                     for a in angs])
    ax.plot(ring[:, 0], ring[:, 1], ring[:, 2], c="#333333", lw=2, zorder=3)
    for p in ring[:-1]:
        ax.scatter(*p, c="#666666", s=35, zorder=4)

    off, h = 2.3, 2.6
    M = c0 + off * u + h * n
    F = c0 + off * u

    ax.quiver(*c0, *(2.0 * n), color="#222222", lw=1.6,
              arrow_length_ratio=0.12)
    ax.text(*(c0 + 2.35 * n - 0.9 * u), "ring normal", fontsize=7.5)

    ax.scatter(*M, c="#aa3377", s=260, edgecolors="black", zorder=6,
               depthshade=False)
    ax.text(*(M + 0.5 * u - 0.05 * n), r"metal $M$", fontsize=9,
            fontweight="bold")

    ax.plot(*zip(M, c0), c="#aa3377", lw=2.2, zorder=5)
    ax.text(*(c0 + 0.42 * (M - c0) + 0.28 * v),
            r"$d_{\mathrm{centroid}}$", fontsize=8.5, color="#aa3377")

    ax.plot(*zip(M, F), c="#1f77b4", lw=1.6, ls="--", zorder=5)
    ax.text(*(F + 0.55 * (M - F) - 0.55 * u), r"$d_{\mathrm{plane}}$",
            fontsize=8.5, color="#1f77b4")

    ax.plot(*zip(F, c0), c="#ff7f0e", lw=1.6, ls="--", zorder=5)
    ax.text(*(c0 + 0.5 * (F - c0) - 0.55 * n), "offset", fontsize=8.5,
            color="#ff7f0e")

    # theta measured from the normal
    tvals = np.linspace(0.0, 0.85, 30)
    arc = np.array([c0 + 1.1 * (np.cos(t) * n + np.sin(t)
                                 * unit(M - c0))
                    for t in tvals])
    ax.plot(arc[:, 0], arc[:, 1], arc[:, 2], c="#444444", lw=1.2)
    ax.text(*(c0 + 1.65 * (n + unit(M - c0)) / 2), r"$\theta$", fontsize=9)

    s = 2.8
    quad = np.array([c0 + s * u + s * v, c0 - s * u + s * v,
                     c0 - s * u - s * v, c0 + s * u - s * v])
    ax.plot_trisurf(*quad.T, color="#dddddd", alpha=0.35, zorder=1)
    ax.scatter(*c0, c="black", s=40, marker="x", zorder=6)

    lim = 3.6
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-0.5, lim)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.set_box_aspect((1, 1, 0.75))
    ax.view_init(elev=14, azim=-58)




# ---------------------------------------------------------------- panel C --
def _ring_side_view(ax, metal_xy, bond_atom=None, cls_note="", big=False):
    xs = np.linspace(-1.25, 1.25, 6)
    ys = np.zeros(6)
    ax.scatter(xs, ys, c="#666666", s=55, zorder=4)
    ax.plot([-1.45, 1.45], [-0.32, -0.32], c="#999999", lw=1.0, ls=":")
    ax.plot([-1.45, 1.45], [0.32, 0.32], c="#999999", lw=1.0, ls=":")
    ax.plot(xs, ys, c="#333333", lw=1.6, zorder=3)
    ax.scatter([0], [0], c="black", s=30, marker="x", zorder=5)
    mx, my = metal_xy
    ax.scatter([mx], [my], c="#aa3377", s=230, edgecolors="black",
               zorder=6)
    ax.plot([0, mx], [0, my], c="#aa3377", lw=1.6, ls="--", zorder=4)
    if bond_atom is not None:
        bx, by = bond_atom
        ax.scatter([bx], [by], c="#cc7722", s=70, zorder=5)
        ax.plot([xs[-1], bx], [0, by], c="#cc7722", lw=1.6, zorder=3)
        ax.plot([bx, mx], [by, my], c="#cc7722", lw=2.0, zorder=4)
    ax.text(0, -1.85, cls_note, fontsize=7.5, ha="center",
            color="#333333")
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-1.8, 2.9)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _porphyrin_view(ax):
    """Top/side sketch: metal inside a tetrapyrrole macrocycle."""
    th = np.linspace(0, 2 * np.pi, 200)
    for r0, r1 in ((0.9, 1.35),):
        ax.plot(np.cos(th) * r1, np.sin(th) * r1 * 0.42 + 1.1,
                c="#666666", lw=1.6)
        ax.plot(np.cos(th) * r0, np.sin(th) * r0 * 0.42 + 1.1,
                c="#999999", lw=1.0, ls=":")
    ax.scatter([0], [1.1], c="#aa3377", s=200, edgecolors="black",
               zorder=6)
    for ang in (45, 135, 225, 315):
        x = np.cos(np.radians(ang)) * 1.1
        y = np.sin(np.radians(ang)) * 1.1 * 0.42 + 1.1
        ax.scatter([x], [y], c="#3355cc", s=45, zorder=5)
        ax.plot([x, 0], [y, 1.1], c="#3355cc", lw=1.4, zorder=4)
    ax.text(0, -0.6, "excluded: porphyrin-family\n(heme, chlorophyll,\n"
                     "cobalamin, ...; metal in\nmacrocycle or embedded)",
            fontsize=8.5, ha="center", color="#555555")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-1.8, 2.6)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def panel_c(axes):
    _ring_side_view(axes[0], (0, 1.7),
                    cls_note="face-on\nproj. < 2.5 $\\mathrm{\\AA}$")
    _ring_side_view(axes[1], (1.8, 1.1), bond_atom=(1.55, 0.55),
                    cls_note="edge-on\nproj. $\\geq$ 2.5 $\\mathrm{\\AA}$")
    _porphyrin_view(axes[2])
    titles = [("face-on", "#1f77b4"), ("edge-on", "#d62728"),
              ("excluded", "#555555")]
    for ax, (t, c) in zip(axes, titles):
        ax.set_title(t, fontsize=10, color=c, fontweight="bold")


def main():
    criteria = """
Geometry classification criteria (2026-10-16, all distances in Angstrom):

  quantities:
    d_centroid : metal ... ring centroid distance
    d_plane    : perpendicular distance from metal to the least-squares
                 ring plane (SVD)
    offset     : lateral offset = sqrt(d_centroid^2 - d_plane^2)
    theta      : angle between (metal - centroid) and the plane normal
    theta_plane: angle between (metal - centroid) and the ring plane
                 (= 90 deg - theta)
    min_dist   : closest metal ... ring-atom distance

  classes:
    face-on  : lateral projection offset < 2.5 A from the ring centre
               (the atomic-envelope radius of an aromatic ring)
    edge-on  : offset >= 2.5 A, with d_centroid <= 6 A
    excluded : contacts with porphyrin-family ligands (tetrapyrrole /
               corrin / phthalocyanine macrocycles: heme, chlorophyll,
               cobalamin, siroheme, ...) or with a metal embedded in the
               ligand itself (incl. Ru-polypyridyl complexes)
    contacts with d_centroid > 6 A are not stored

  rationale:
    - Alkali/alkaline-earth metals (Na, Ca) close to ring atoms are ionic
      edge contacts, not chelation; they are classified by the same angle
      criterion as all other metals (no separate 'chelated' class).
    - Porphyrin-type macrocycles bind their metal through directed
      covalent coordination by ring nitrogens - a fundamentally different
      interaction from metal-aromatic contacts of ordinary ligands, hence
      excluded from the census.
"""
    (ROOT / "paper" / "geometry_criteria.txt").write_text(criteria)
    print("criteria -> paper/geometry_criteria.txt")


if __name__ == "__main__":
    main()
