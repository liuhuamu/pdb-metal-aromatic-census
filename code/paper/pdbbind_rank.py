#!/usr/bin/env python3
"""Target-adjusted (rank-normalized) affinity analysis.

For every protein target with >= 4 PDBbind complexes, affinities are converted
to within-target percentile ranks; group means are then compared with a
permutation test that shuffles group labels *within* target.  This controls for
target identity without discarding complexes (unlike the strict
"both-groups-present" stratification).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
P = ROOT / "paper"
sys.path.insert(0, str(P))
from make_fig_classes import classify_pfam  # noqa: E402

OUT = P / "output"
rng = np.random.default_rng(99)
NPERM = 20000
GROUPS = ["bridge-near", "bridge-direct", "no-contact", "no-metal"]


def load():
    xl = pd.ExcelFile(P / "SI_Tables.xlsx")
    anno = json.loads((P / "data" / "pdbbind_targets.json").read_text())
    out = {}
    for name, sh in (("general", "S8_PDBbind_general"),
                     ("refined", "S9_PDBbind_refined")):
        d = xl.parse(sh)
        d["uniprot"] = d.pdb_id.map(
            lambda p: (anno.get(p, {}).get("uniprots") or [None])[0])
        d["ptype"] = d.pdb_id.map(
            lambda p: classify_pfam([f for v in
                                     (anno.get(p, {}).get("pfam") or {}).values()
                                     for f in v])
            if anno.get(p, {}).get("pfam") else None)
        d["y"] = pd.to_numeric(d.neg_log_k, errors="coerce")
        out[name] = d.dropna(subset=["y"])
    return out


def rank_within(d, strat, min_n=4):
    d = d[d[strat].notna()].copy()
    sizes = d.groupby(strat).size()
    keep = sizes[sizes >= min_n].index
    d = d[d[strat].isin(keep)].copy()
    d["rank"] = d.groupby(strat)["y"].rank(pct=True)
    return d


def perm_test(d, g1, g2, nperm=NPERM):
    sub = d[d.group.isin([g1, g2])].copy()
    if len(sub) == 0:
        return None
    mask = (sub.group == g1).to_numpy()
    ranks = sub["rank"].to_numpy()
    strata = sub[strat_col].to_numpy()
    obs = ranks[mask].mean() - ranks[~mask].mean()
    idx_by_stratum = [np.where(strata == s)[0] for s in np.unique(strata)]
    cnt = 0
    for _ in range(nperm):
        perm = np.empty(len(ranks), dtype=bool)
        for idx in idx_by_stratum:
            v = np.zeros(len(idx), dtype=bool)
            v[:mask[idx].sum()] = True
            rng.shuffle(v)
            perm[idx] = v
        dlt = ranks[perm].mean() - ranks[~perm].mean()
        if abs(dlt) >= abs(obs):
            cnt += 1
    return dict(group1=g1, group2=g2, n1=int(mask.sum()),
                n2=int((~mask).sum()), n_strata=int(len(idx_by_stratum)),
                mean_rank1=round(float(ranks[mask].mean()), 3),
                mean_rank2=round(float(ranks[~mask].mean()), 3),
                delta=round(float(obs), 3), p=(cnt + 1) / (nperm + 1))


res = {}
for name, d in load().items():
    for strat_col, min_n in (("uniprot", 4), ("ptype", 4)):
        globals()["strat_col"] = strat_col
        dd = rank_within(d, strat_col, min_n)
        res[f"{name}|{strat_col}"] = dict(
            n=len(dd), strata=int(dd[strat_col].nunique()),
            groups=dd.group.value_counts().to_dict(),
            tests=[perm_test(dd, a, b) for a, b in
                   [("bridge-near", "no-contact"),
                    ("bridge-near", "no-metal"),
                    ("bridge-direct", "no-contact")]])

(OUT / "pdbbind_rank.json").write_text(json.dumps(res, indent=1, default=str))
for k, v in res.items():
    print(f"== {k}: n={v['n']} strata={v['strata']}")
    for t in v["tests"]:
        if t:
            print(f"   {t['group1']} vs {t['group2']}: n={t['n1']}/{t['n2']} "
                  f"strata={t['n_strata']} rank {t['mean_rank1']:.3f} vs "
                  f"{t['mean_rank2']:.3f} d={t['delta']:+.3f} p={t['p']:.4f}")
