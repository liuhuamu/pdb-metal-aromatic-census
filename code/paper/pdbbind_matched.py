#!/usr/bin/env python3
"""Target-matched (stratified) re-analysis of the PDBbind affinity association.

The v2 manuscript reported a global median difference between metal-contacted
complexes and controls and deferred a family-matched analysis to follow-up
work.  This script does it:

  * every PDBbind v2020 complex is annotated with its UniProt target and its
    Pfam-derived protein type (pdbbind_targets.json)
  * within each target with >=3 complexes in both groups we compute the
    difference of median -logK
  * significance comes from a stratified permutation test: group labels are
    permuted *within* target, and the statistic is the mean/most-common
    within-target difference

Writes paper/output/pdbbind_matched.json and S15_pdbbind_matched.csv
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
rng = np.random.default_rng(4242)
NPERM = 5000


def load():
    xl = pd.ExcelFile(P / "SI_Tables.xlsx")
    gen = xl.parse("S8_PDBbind_general")
    ref = xl.parse("S9_PDBbind_refined")
    anno = json.loads((P / "data" / "pdbbind_targets.json").read_text())
    for d in (gen, ref):
        d["uniprot"] = d.pdb_id.map(
            lambda p: (anno.get(p, {}).get("uniprots") or [None])[0])
        d["ptype"] = d.pdb_id.map(
            lambda p: classify_pfam([f for v in
                                     (anno.get(p, {}).get("pfam") or {}).values()
                                     for f in v])
            if anno.get(p, {}).get("pfam") else None)
    return gen, ref, anno


def stratified(df, g1, g2, strat, min_n=3, nperm=NPERM):
    """Within-stratum median differences + stratified permutation test."""
    d = df[df.group.isin([g1, g2]) & df[strat].notna()].copy()
    d["y"] = pd.to_numeric(d.neg_log_k, errors="coerce")
    d = d.dropna(subset=["y"])
    rows, keep = [], []
    for key, s in d.groupby(strat):
        a = s.loc[s.group == g1, "y"].to_numpy()
        b = s.loc[s.group == g2, "y"].to_numpy()
        if len(a) >= min_n and len(b) >= min_n:
            rows.append(dict(stratum=key, n1=len(a), n2=len(b),
                             med1=round(float(np.median(a)), 2),
                             med2=round(float(np.median(b)), 2),
                             delta=round(float(np.median(a) - np.median(b)), 2)))
            keep.append((key, a, b))
    if not rows:
        return None
    tab = pd.DataFrame(rows)
    obs = float(tab.delta.median())
    mean_obs = float(tab.delta.mean())
    n1 = sum(len(a) for _, a, b in keep)
    n2 = sum(len(b) for _, a, b in keep)
    stat = np.empty(nperm)
    stat_mean = np.empty(nperm)
    for i in range(nperm):
        deltas = np.empty(len(keep))
        for j, (_, a, b) in enumerate(keep):
            pool = np.concatenate([a, b])
            rng.shuffle(pool)
            deltas[j] = np.median(pool[:len(a)]) - np.median(pool[len(a):])
        stat[i] = np.median(deltas)
        stat_mean[i] = deltas.mean()
    p_med = float((np.abs(stat) >= abs(obs)).mean())
    p_mean = float((np.abs(stat_mean) >= abs(mean_obs)).mean())
    return dict(group1=g1, group2=g2, strat=strat, n_strata=int(len(tab)),
                n1=int(n1), n2=int(n2), median_delta=obs,
                mean_delta=round(mean_obs, 2),
                n_positive=int((tab.delta > 0).sum()),
                n_negative=int((tab.delta < 0).sum()),
                iqr=[round(float(tab.delta.quantile(.25)), 2),
                     round(float(tab.delta.quantile(.75)), 2)],
                p_perm_median=p_med, p_perm_mean=p_mean,
                table=tab.sort_values("n1", ascending=False)
                .head(20).to_dict("records"),
                sign_test_p=_sign_test(int((tab.delta > 0).sum()), len(tab)))


def _sign_test(k, n):
    from math import comb
    if n == 0:
        return None
    tail = sum(comb(n, i) for i in range(min(k, n - k) + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 4)


def main():
    gen, ref, anno = load()
    print(f"general {len(gen):,}  refined {len(ref):,}  "
          f"annotated {len(anno):,}")
    res = {"n_general": int(len(gen)), "n_refined": int(len(ref)),
           "n_with_uniprot": int(gen.uniprot.notna().sum())}

    for name, d in (("general", gen), ("refined", ref)):
        res[name] = {}
        for strat in ("uniprot", "ptype"):
            for g1, g2 in (("bridge-near", "no-metal"),
                           ("bridge-near", "no-contact"),
                           ("bridge-direct", "no-metal")):
                r = stratified(d, g1, g2, strat)
                res[name][f"{g1}_vs_{g2}__{strat}"] = r
                if r:
                    print(f"[{name}] {g1} vs {g2} by {strat}: "
                          f"strata={r['n_strata']} n={r['n1']}/{r['n2']} "
                          f"median d={r['median_delta']:+.2f} "
                          f"({r['n_positive']}+/{r['n_negative']}-) "
                          f"p_perm={r['p_perm_median']:.4f} "
                          f"sign p={r['sign_test_p']}")
        # face-on vs edge-on (exploratory geometry contrast) at entry level
        sub = d[d.group.isin(["bridge-near", "bridge-direct"])]
        res[name]["faceon_vs_edgeon"] = None

    # ---- entry-level geometry contrast (all contacts of an entry pooled) ----
    ne = pd.read_csv(OUT / "contacts_derived.csv")
    entry = ne.groupby("pdb_id").agg(
        n=("is_fo", "size"), fo=("is_fo", "sum")).reset_index()
    entry["any_faceon"] = entry.fo > 0
    for name, d in (("general", gen), ("refined", ref)):
        dd = d.merge(entry, on="pdb_id", how="inner")
        dd = dd[dd.group.isin(["bridge-near", "bridge-direct"])]
        a = pd.to_numeric(dd.loc[dd.any_faceon, "neg_log_k"], errors="coerce").dropna()
        b = pd.to_numeric(dd.loc[~dd.any_faceon, "neg_log_k"], errors="coerce").dropna()
        obj = dict(n_faceon=len(a), n_edgeon=len(b),
                   med_faceon=round(float(a.median()), 2) if len(a) else None,
                   med_edgeon=round(float(b.median()), 2) if len(b) else None)
        if len(a) >= 10 and len(b) >= 10:
            obs = a.median() - b.median()
            pool = np.concatenate([a.to_numpy(), b.to_numpy()])
            cnt = 0
            for _ in range(5000):
                rng.shuffle(pool)
                dlt = np.median(pool[:len(a)]) - np.median(pool[len(a):])
                if abs(dlt) >= abs(obs):
                    cnt += 1
            obj["delta"] = round(float(obs), 2)
            obj["p_perm"] = round((cnt + 1) / 5001, 4)
        res[name]["faceon_entry_contrast"] = obj
        print(f"[{name}] entry-level face-on vs edge-on: {obj}")

    (OUT / "pdbbind_matched.json").write_text(json.dumps(res, indent=1,
                                                         default=str))
    rows = []
    for name in ("general", "refined"):
        for k, v in res[name].items():
            if isinstance(v, dict) and "median_delta" in v:
                rows.append(dict(dataset=name, comparison=k,
                                 strata=v["n_strata"], n1=v["n1"], n2=v["n2"],
                                 median_delta=v["median_delta"],
                                 mean_delta=v["mean_delta"],
                                 n_pos=v["n_positive"], n_neg=v["n_negative"],
                                 p_perm=v["p_perm_median"]))
    pd.DataFrame(rows).to_csv(OUT / "S15_pdbbind_matched.csv", index=False)
    print("[done]")


if __name__ == "__main__":
    main()

