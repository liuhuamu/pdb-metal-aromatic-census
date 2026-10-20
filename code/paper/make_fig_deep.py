#!/usr/bin/env python3
"""Figure 9: determinants of face-on metal-aromatic engagement.

(a) face-on fraction per protein type (>=100 contacts) with entry-clustered
    bootstrap 95% CIs
(b) distance spectrum of the 981 face-on contacts, split into inner /
    stacked / outer regimes
(c) face-on fraction by coordination number and by protein-donor class
(d) face-on fraction by ring chemistry for the main metals

Source data -> paper/figures/source_data/fig9_determinants.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
P = ROOT / "paper"
sys.path.insert(0, str(P))
from nature_style import (PALETTE, add_panel_label, apply_publication_style,  # noqa: E402
                          save_pub)

FIG = P / "figures"
SRC = FIG / "source_data"
SRC.mkdir(parents=True, exist_ok=True)

R3 = json.loads((P / "output" / "deep_results3.json").read_text())
R2 = json.loads((P / "output" / "deep_results2.json").read_text())
R1 = json.loads((P / "output" / "deep_results.json").read_text())
ne = pd.read_csv(P / "output" / "contacts_derived.csv")
ne["is_fo"] = ne.is_fo.astype(int)

apply_publication_style(6.8)
fig = plt.figure(figsize=(6.3, 5.0))
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.40,
                      left=0.235, right=0.985, top=0.945, bottom=0.095)

BLUE = PALETTE["blue_main"]
GREY = PALETTE["neutral_light"]
RED = PALETTE["red_strong"]
TEAL = PALETTE["teal"]

# ------------------------------------------------------------------ panel a --
ax = fig.add_subplot(gs[0, 0])
tab = pd.DataFrame(R3["table4"])
tab = tab[~tab.ptype.isin(["Other"])].sort_values("pct")
y = np.arange(len(tab))
colors = [RED if p >= 15 else (BLUE if p >= 5 else GREY) for p in tab.pct]
ax.hlines(y, 0, tab.pct, color=colors, lw=1.0, alpha=.55)
ax.errorbar(tab.pct, y, xerr=[tab.pct - tab.lo, tab.hi - tab.pct],
            fmt="none", ecolor=PALETTE["neutral_mid"], elinewidth=0.7,
            capsize=1.5)
ax.scatter(tab.pct, y, s=16, color=colors, zorder=3, edgecolor="white",
           linewidth=0.3)
ax.set_yticks(y)
ax.set_yticklabels([f"{r.ptype} ({int(r.contacts)})"
                    for r in tab.itertuples()], fontsize=6)
ax.set_xlabel("face-on contacts (%)")
ax.set_xlim(-1, 52)
for spine in ("left",):
    ax.spines[spine].set_visible(False)
ax.tick_params(axis="y", length=0)
add_panel_label(ax, "a", x=-0.30, y=1.02, fontsize=8)
ax.set_title("target class", fontsize=7, pad=3)
# ------------------------------------------------------------------ panel b --
ax = fig.add_subplot(gs[0, 1])
bins = np.arange(1.5, 6.1, 0.25)
fo = ne[ne.is_fo == 1]
ax.axvspan(1.5, 3.7, color=PALETTE["blue_secondary"], alpha=.10, lw=0)
ax.axvspan(3.7, 4.5, color=PALETTE["green_3"], alpha=.16, lw=0)
ax.axvspan(4.5, 6.05, color=PALETTE["neutral_light"], alpha=.30, lw=0)
ax.hist(fo.d_centroid, bins=bins, color=BLUE, edgecolor="white", lw=.35)
for x, lab, col in [(2.6, "inner\n117", PALETTE["blue_main"]),
                    (4.1, "stacked\n203", PALETTE["green_3"]),
                    (5.25, "outer\n663", PALETTE["neutral_mid"])]:
    ax.text(x, ax.get_ylim()[1] * 0.93, lab, ha="center", va="top",
            fontsize=5.6, color=col)
ax.set_xlabel(r"$d_{\mathrm{centroid}}$ of face-on contacts ($\AA$)")
ax.set_ylabel("contacts")
ax.set_xlim(1.5, 6.05)
add_panel_label(ax, "b", x=-0.22, y=1.02, fontsize=8)
ax.set_title("distance regimes (n = 981)", fontsize=7, pad=3)

# ------------------------------------------------------------------ panel c --
ax = fig.add_subplot(gs[1, 0])
cn = pd.DataFrame(R1["cn_faceon"])
cn = cn[(cn.cn >= 1) & (cn.cn <= 6)]
don = pd.DataFrame(R1["donor_class"])
don = don[don.donor_class.isin(["N only", "N+O", "O only", "with S"])]
labels = [str(int(c)) for c in cn.cn] + ["N", "N+O", "O", "S"]
vals = list(cn.pct) + list(don.pct)
ns = list(cn.n) + list(don.n)
x = np.arange(len(vals))
cols = [BLUE] * len(cn) + [RED, PALETTE["blue_secondary"], GREY,
                           PALETTE["neutral_mid"]]
ax.bar(x, vals, color=cols, width=.72, edgecolor="white", lw=.4)
for xi, v, n in zip(x, vals, ns):
    ax.text(xi, v + 0.35, f"{v:.0f}", ha="center", fontsize=5.2,
            color=PALETTE["neutral_dark"])
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=6.0, rotation=0)
ax.set_ylabel("face-on contacts (%)")
ax.set_xlabel("coordination number  |  protein donor set")
ax.axvline(len(cn) - 0.5, color=PALETTE["neutral_mid"], lw=.6, ls=":")
ax.set_ylim(0, 19)
add_panel_label(ax, "c", x=-0.16, y=1.02, fontsize=8)
ax.set_title("metal's own coordination sphere", fontsize=7, pad=3)

# ------------------------------------------------------------------ panel d --
ax = fig.add_subplot(gs[1, 1])
metals = ["K", "Na", "Zn", "Mg", "Fe"]
classes = ["carbocycle", "N-heteroarene"]
w = 0.36
for k, cls in enumerate(classes):
    vals, err, xt = [], [], []
    for i, m in enumerate(metals):
        s = ne[(ne.metal_element == m) & (ne.ring_class == cls)]
        vals.append(100 * s.is_fo.mean() if len(s) else 0)
        xt.append(i + (k - 0.5) * w)
    cols = [BLUE, TEAL]
    ax.bar(xt, vals, width=w, color=cols[k], label=cls, edgecolor="white", lw=.4)
ax.set_xticks(range(len(metals)))
ax.set_xticklabels(metals)
ax.set_xlabel("metal")
ax.set_ylabel("face-on contacts (%)")
ax.legend(fontsize=5.6, handlelength=1.0, borderpad=.1, loc="upper right")
ax.set_ylim(0, 21)
add_panel_label(ax, "d", x=-0.18, y=1.02, fontsize=8)
ax.set_title("ring chemistry", fontsize=7, pad=3)

save_pub(fig, FIG / "fig9_determinants")

# ------------------------------------------------------------ source data ----
rows = []
for r in tab.itertuples():
    rows.append(dict(panel="a", key=r.ptype, n=int(r.contacts),
                     faceon_pct=r.pct, lo=r.lo, hi=r.hi))
for name, d in R2["faceon_regimes"].items():
    rows.append(dict(panel="b", key=name, n=d["n"], faceon_pct=d["pct"],
                     lo="", hi=""))
for r in cn.itertuples():
    rows.append(dict(panel="c", key=f"CN{int(r.cn)}", n=int(r.n),
                     faceon_pct=r.pct, lo="", hi=""))
for r in don.itertuples():
    rows.append(dict(panel="c", key=r.donor_class, n=int(r.n),
                     faceon_pct=r.pct, lo="", hi=""))
for m in metals:
    for cls in classes:
        s = ne[(ne.metal_element == m) & (ne.ring_class == cls)]
        rows.append(dict(panel="d", key=f"{m}|{cls}", n=int(len(s)),
                         faceon_pct=round(100 * s.is_fo.mean(), 1)
                         if len(s) else "", lo="", hi=""))
pd.DataFrame(rows).to_csv(SRC / "fig9_determinants.csv", index=False)
print("figure 9 ->", FIG / "fig9_determinants.png")




