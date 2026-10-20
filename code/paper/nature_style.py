#!/usr/bin/env python3
"""Shared Nature-style figure settings (learned from Yuan1z0825/nature-skills,
skill `nature-figure` v2.8: static/core/contract.md, stance.md,
fragments/backend/python.md, references/design-theory.md and api.md).

Adapted for the metal-aromatic census figures (matplotlib backend,
journal-final sizes: double column 7.2 in, single column 5.0 in; base
font 7 pt, every glyph >= 5 pt after export).
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- palette --
PALETTE = {
    "blue_main":      "#0F4D92",   # hero (face-on class, approved drugs)
    "blue_secondary": "#3775BA",
    "green_3":        "#8BCF8B",
    "red_strong":     "#B64342",   # accent (bridge-direct)
    "red_1":          "#F6CFCB",
    "neutral_light":  "#CFCECE",
    "neutral_mid":    "#767676",
    "neutral_dark":   "#4D4D4D",
    "neutral_black":  "#272727",
    "teal":           "#42949E",
    "violet":         "#9A4D8E",
}

# semantic colors for the geometry classes
CLASS_COLORS = {
    "face-on": "#0F4D92",          # hero (rare, key class)
    "edge-on": "#CFCECE",          # dominant neutral family
}

# semantic colors for the bridging configurations
BRIDGE_COLORS = {
    "bridge-direct": "#B64342",    # accent (direct drug anchoring)
    "bridge-near":   "#3775BA",    # blue secondary
    "ligand-held":   "#CFCECE",    # neutral
    "unannotated":   "#E5E5E5",
}

DEFAULT_COLORS = [
    PALETTE["blue_main"],
    PALETTE["green_3"],
    PALETTE["red_strong"],
    PALETTE["teal"],
    PALETTE["violet"],
    PALETTE["neutral_light"],
]

DOUBLE_COL = 7.2     # inches (~183 mm)
ONE_HALF_COL = 5.0   # inches (~127 mm)
SINGLE_COL = 3.5     # inches (~89 mm)


def apply_publication_style(font_size: float = 7.0,
                            axes_linewidth: float = 0.8) -> None:
    """Nature-style rcParams (dense journal-final preset)."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans",
                            "Liberation Sans"],
        "svg.fonttype": "none",          # editable text in SVG
        "pdf.fonttype": 42,              # editable TrueType text in PDF
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 0.5,
        "ytick.labelsize": font_size - 0.5,
        "legend.fontsize": font_size - 0.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": axes_linewidth,
        "xtick.major.width": axes_linewidth,
        "ytick.major.width": axes_linewidth,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "legend.frameon": False,
        "axes.grid": False,
        "lines.linewidth": 1.2,
    })


def add_panel_label(ax, label, x=0, y=1, x_offset_pt=-2, y_offset_pt=3,
                    fontsize=8, color="black", fontweight="bold",
                    va="bottom"):
    """Panel label with fixed physical offset from an axes anchor."""
    from matplotlib.transforms import ScaledTranslation
    offset = ScaledTranslation(
        x_offset_pt / 72, y_offset_pt / 72, ax.figure.dpi_scale_trans)
    ax.text(x, y, label, transform=ax.transAxes + offset,
            fontsize=fontsize, fontweight=fontweight, color=color,
            ha="left", va=va)


def save_pub(fig, base_path, formats=("svg", "png", "pdf"), dpi=600):
    """Export a figure: SVG primary (editable text) + PNG (300/600 dpi)
    + PDF. base_path without extension."""
    base = str(base_path)
    if "svg" in formats:
        fig.savefig(base + ".svg", bbox_inches="tight")
    if "png" in formats:
        fig.savefig(base + ".png", dpi=dpi, bbox_inches="tight")
    if "pdf" in formats:
        fig.savefig(base + ".pdf", bbox_inches="tight")
    plt.close(fig)
