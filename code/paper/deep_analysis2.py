#!/usr/bin/env python3
"""Second-stage deep analysis: distance regimes, robustness of the metal
ranking, entry-clustered confidence intervals, target-family contrasts and
stratified (Mantel-Haenszel) tests for the ring-chemistry / coordination
contrasts.

Writes paper/output/deep_results2.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
P = ROOT / "paper"
sys.path.insert(0, str(P))
from make_fig_classes import classify_pfam  # noqa: E402

OUT = P / "output"
rng = np.random.default_rng(20261016)
ne = pd.read_csv(OUT / "contacts_derived.csv")
ne["is_fo"] = ne.is_fo.astype(int)
R = {}


def boot_pct(df, mask_col="is_fo", reps=2000):
    """Entry-clustered bootstrap CI for a percentage."""
    g = df.groupby("pdb_id")[mask_col].agg(["sum", "count"])
    ids = g.index.to_numpy()
    s = g["sum"].to_numpy(float)
    n = g["count"].to_numpy(float)
    out = np.empty(reps)
    for i in range(reps):
        idx = rng.integers(0, len(ids), len(ids))
        out[i] = 100 * s[idx].sum() / n[idx].sum()
    return dict(pct=round(100 * df[mask_col].mean(), 1),
                lo=round(float(np.percentile(out, 2.5)), 1),
                hi=round(float(np.percentile(out, 97.5)), 1),
                entries=int(len(ids)))


def mh_odds(df, exposure, outcome="is_fo", strat="metal_element", min_n=30):
    """Mantel-Haenszel OR + test for a binary exposure within strata."""
    num = den = var = delta = 0.0
    used = 0
    for _, s in df.groupby(strat):
        if len(s) < min_n:
            continue
        a = int(((s[exposure]) & (s[outcome] == 1)).sum())
        b = int(((s[exposure]) & (s[outcome] == 0)).sum())
        c = int(((~s[exposure]) & (s[outcome] == 1)).sum())
        d = int(((~s[exposure]) & (s[outcome] == 0)).sum())
        n = a + b + c + d
        if min(a + b, c + d, a + c, b + d) == 0:
            continue
        used += 1
        num += a * d / n
        den += b * c / n
        e = (a + b) * (a + c) / n
        v = (a + b) * (c + d) * (a + c) * (b + d) / (n * n * (n - 1))
        delta += a - e
        var += v
    stat = delta ** 2 / var if var else float("nan")
    from math import erf, sqrt
    p = 1 - erf(sqrt(stat) / sqrt(2)) if var else float("nan")
    return dict(or_mh=round(num / den, 2) if den else None,
                chi2=round(stat, 1), p=p, strata=used)


# ------------------------------------------------------------------ 1. regimes
edges = [0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.01]
fo = ne[ne.is_fo == 1].copy()
fo["bin"] = pd.cut(fo.d_centroid, edges, right=False)
R["faceon_distance"] = (fo.groupby("bin", observed=True)
                        .agg(n=("is_fo", "size"),
                             median_min_dist=("min_dist", "median"),
                             median_theta=("theta_deg", "median"))
                        .reset_index().astype(str).to_dict("records"))
R["faceon_short"] = dict(
    n_total=int(len(fo)),
    le25=int((fo.d_centroid <= 2.5).sum()),
    le30=int((fo.d_centroid <= 3.0).sum()),
    le35=int((fo.d_centroid <= 3.5).sum()),
    le37=int((fo.d_centroid <= 3.7).sum()),
    le40=int((fo.d_centroid <= 4.0).sum()),
    gt45=int((fo.d_centroid > 4.5).sum()),
    pct_le37=round(100 * (fo.d_centroid <= 3.7).mean(), 1),
    pct_gt45=round(100 * (fo.d_centroid > 4.5).mean(), 1),
    median=round(float(fo.d_centroid.median()), 2))
# metal composition of the short vs long face-on subsets
short = fo[fo.d_centroid <= 3.7]
long_ = fo[fo.d_centroid > 4.5]
R["faceon_short_metals"] = short.metal_element.value_counts().head(8).to_dict()
R["faceon_long_metals"] = long_.metal_element.value_counts().head(8).to_dict()
R["faceon_regimes"] = {}
for lo, hi, name in [(0, 3.7, "inner"), (3.7, 4.5, "stacked"),
                     (4.5, 6.01, "outer")]:
    s = fo[(fo.d_centroid >= lo) & (fo.d_centroid < hi)]
    R["faceon_regimes"][name] = dict(
        n=int(len(s)), pct=round(100 * len(s) / len(fo), 1),
        median_d=round(float(s.d_centroid.median()), 2),
        median_mindist=round(float(s.min_dist.median()), 2),
        top_metals=s.metal_element.value_counts().head(5).to_dict(),
        top_rings=s.ring_class.value_counts().to_dict(),
        top_bridge=s.bridging_class.value_counts().to_dict())

# --------------------------------------------------- 2. clustered CIs / tests
R["overall_boot"] = boot_pct(ne)
R["faceon_by_metal_boot"] = {
    el: boot_pct(ne[ne.metal_element == el])
    for el in ["Zn", "Mg", "Fe", "Mn", "Ca", "Ni", "K", "Na", "Cu"]}

# ring chemistry contrast, stratified by metal
ne["is_carbocycle"] = ne.ring_class == "carbocycle"
R["ring_mh"] = mh_odds(ne, "is_carbocycle")
R["ring_mh_excl_additive"] = mh_odds(ne[ne.ligand_category != "additive"],
                                     "is_carbocycle")
R["ring_boot"] = {
    "carbocycle": boot_pct(ne[ne.is_carbocycle]),
    "N-heteroarene": boot_pct(ne[ne.ring_class == "N-heteroarene"])}
ne["low_cn"] = ne.cn <= 4
R["cn_mh"] = mh_odds(ne, "low_cn")
R["cn_boot"] = {"low": boot_pct(ne[ne.low_cn]),
                "high": boot_pct(ne[ne.cn >= 6])}
ne["is_N_only"] = ne.donor_class.isin(["N only"])
R["donor_boot"] = {"N only": boot_pct(ne[ne.donor_class == "N only"]),
                   "O only": boot_pct(ne[ne.donor_class == "O only"]),
                   "none": boot_pct(ne[ne.donor_class == "none"])}
R["donor_mh"] = mh_odds(ne, "is_N_only")

# ------------------------------------------------- 3. strict-QC robustness
strict = ne[(ne.resolution <= 2.0) & (ne.metal_occupancy >= 0.9)]
R["strict_qc"] = dict(n=int(len(strict)), pct=round(100 * strict.is_fo.mean(), 1),
                      boot=boot_pct(strict),
                      metals={el: dict(n=int((strict.metal_element == el).sum()),
                                       pct=round(100 * strict[
                                           strict.metal_element == el].is_fo
                                                 .mean(), 1))
                              for el in ["Zn", "K", "Na", "Mg", "Fe"]})
ultra = ne[(ne.resolution <= 1.5)]
R["ultra_high_res"] = dict(boot=boot_pct(ultra), n_entries=int(ultra.pdb_id.nunique()))

# --------------------------------------------------- 4. target-family contrast
anno = json.loads((P / "data" / "target_annotations.json")
                  .read_text(encoding="utf-8"))
ch2uni, ch2pfam, uname = {}, {}, {}
for pid, a in anno.items():
    for ch, acc in (a.get("chains") or {}).items():
        ch2uni[(pid, ch)] = acc
    for ch, fams in (a.get("pfam") or {}).items():
        ch2pfam[(pid, ch)] = fams
    for u in a.get("uniprots") or []:
        uname.setdefault(u["uniprot"], u["name"])


def chains(row):
    co = row.coordination if isinstance(row.coordination, str) else ""
    return set(re.findall(r"\(([A-Za-z0-9]+)\)", co))


def uni_of(row):
    for ch in chains(row):
        acc = ch2uni.get((row.pdb_id, ch))
        if acc:
            return acc
    return None


def ptype(row):
    for ch in chains(row):
        fams = ch2pfam.get((row.pdb_id, ch))
        if fams:
            return classify_pfam(fams)
    return None


ne["uniprot"] = ne.apply(uni_of, axis=1)
ne["ptype"] = ne.apply(ptype, axis=1)
ne["uname"] = ne.uniprot.map(uname)
R["ptype"] = (ne.dropna(subset=["ptype"]).groupby("ptype")
              .agg(n=("is_fo", "size"), fo=("is_fo", "sum"),
                   entries=("pdb_id", "nunique"))
              .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
              .sort_values("n", ascending=False).head(15)
              .reset_index().to_dict("records"))
R["ptype_boot"] = {k: boot_pct(ne[ne.ptype == k])
                   for k in ["Protease", "Carbonic anhydrase",
                             "Phosphodiesterase", "Nuclease", "Deaminase",
                             "Protein kinase", "Dehydrogenase"]}

mmp = ne[ne.uname.astype(str).str.contains("matrix metallo|Stromelysin|"
                                           "Collagenase|Gelatinase|elastase",
                                           case=False, na=False)]
R["mmp"] = dict(
    targets=int(mmp.uniprot.nunique()), contacts=int(len(mmp)),
    entries=int(mmp.pdb_id.nunique()), fo=int(mmp.is_fo.sum()),
    pct=round(100 * mmp.is_fo.mean(), 1), boot=boot_pct(mmp),
    median_d=round(float(mmp[mmp.is_fo == 1].d_centroid.median()), 2),
    by_target=(mmp.groupby(["uniprot", "uname"])
               .agg(n=("is_fo", "size"), fo=("is_fo", "sum"),
                    entries=("pdb_id", "nunique"))
               .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
               .reset_index().sort_values("n", ascending=False)
               .head(10).astype(str).to_dict("records")),
    ligands=mmp[mmp.is_fo == 1].ligand_comp_id.value_counts().head(10).to_dict(),
    cn=mmp.cn.value_counts().head(6).to_dict(),
    donor=mmp.donor_class.value_counts().head(5).to_dict(),
    short_faceon=int((mmp.is_fo == 1).sum() and
                     ((mmp.is_fo == 1) & (mmp.d_centroid <= 4.5)).sum()))
ca = ne[ne.uniprot == "P00918"]
R["ca2"] = dict(contacts=int(len(ca)), entries=int(ca.pdb_id.nunique()),
                fo=int(ca.is_fo.sum()), pct=round(100 * ca.is_fo.mean(), 1),
                median_d=round(float(ca.d_centroid.median()), 2),
                boot=boot_pct(ca))

# target-level table (min 20 contacts) with bootstrap-free CIs via Wilson
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


tg = ne.dropna(subset=["uniprot"]).groupby("uniprot").agg(
    n=("is_fo", "size"), fo=("is_fo", "sum"),
    entries=("pdb_id", "nunique"), uname=("uname", "first"))
tg["pct"] = (100 * tg.fo / tg.n).round(1)
tg[["lo", "hi"]] = pd.DataFrame(
    [wilson(k, n) for k, n in zip(tg.fo, tg.n)], index=tg.index)
tg["lo"] = (100 * tg.lo).round(1)
tg["hi"] = (100 * tg.hi).round(1)
R["targets_min20"] = (tg[tg.n >= 20].sort_values(["pct", "n"], ascending=False)
                      .head(25).reset_index().astype(str).to_dict("records"))
R["target_planes"] = dict(
    n_targets=int(len(tg)),
    n_min20=int((tg.n >= 20).sum()),
    equal_weight_pct=round(float(tg.pct.mean()), 1),
    median_weight_pct=round(float(tg.pct.median()), 1))

# ------------------------------------------------------------ 5. cofactor set
def ribose_style(sub, label):
    s = ne[ne.ligand_comp_id == sub]
    return dict(ligand=label, n=int(len(s)), fo=int(s.is_fo.sum()),
                pct=round(100 * s.is_fo.mean(), 1) if len(s) else None,
                median_d=round(float(s.d_centroid.median()), 2) if len(s) else None)


R["nucleotides"] = [ribose_style(c, l) for c, l in
                    [("ATP", "ATP"), ("ANP", "AMP-PNP"), ("ADP", "ADP"),
                     ("AMP", "AMP"), ("GTP", "GTP"), ("GDP", "GDP"),
                     ("NAD", "NAD"), ("NAP", "NADP"), ("FAD", "FAD")]]

(OUT / "deep_results2.json").write_text(json.dumps(R, indent=1, default=str))
print(json.dumps({k: R[k] for k in ["faceon_short", "faceon_regimes",
                                    "ring_mh", "cn_mh", "donor_mh",
                                    "strict_qc", "mmp", "ca2",
                                    "target_planes", "overall_boot"]},
                 indent=1, default=str)[:6000])
print("[done] -> deep_results2.json")
