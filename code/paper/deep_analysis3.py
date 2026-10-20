#!/usr/bin/env python3
"""Third-stage tables: archived porphyrin set, cleaned MMP family, target-class
summary (Table 4), and drug / cofactor details for the new text."""
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
rng = np.random.default_rng(7)
R = {}


def boot(df, reps=2000, col="is_fo"):
    g = df.groupby("pdb_id")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    if len(s) == 0:
        return None
    v = np.empty(reps)
    for i in range(reps):
        idx = rng.integers(0, len(s), len(s))
        v[i] = 100 * s[idx].sum() / n[idx].sum()
    return dict(pct=round(100 * df[col].mean(), 1),
                lo=round(float(np.percentile(v, 2.5)), 1),
                hi=round(float(np.percentile(v, 97.5)), 1))


# ------------------------------------------------------- archived porphyrins
allc = pd.read_excel(P / "SI_Tables.xlsx", sheet_name="S5_Contacts")
ex = allc[allc.geometry_class == "excluded"].copy()
R["excluded"] = dict(
    contacts=int(len(ex)), entries=int(ex.pdb_id.nunique()),
    metals=ex.metal_element.value_counts().head(8).to_dict(),
    ligands=ex.ligand_comp_id.value_counts().head(10).to_dict(),
    median_d=round(float(ex.d_centroid.median()), 2),
    median_min=round(float(ex.min_dist.median()), 2),
    embedded=int((ex.metal_embedded == 1).sum()),
    by_ligfam=dict(chlorophyll=int(ex.ligand_comp_id.isin(
        ["CLA", "CHL", "CL7", "BCB", "BCL", "CLA", "KC1", "CL0", "CH0",
         "6CH", "CL1", "CL2"]).sum()),
        heme=int(ex.ligand_comp_id.isin(
            ["HEM", "HEC", "HEA", "SRM", "HEB", "HAS", "HNI", "HEM"]).sum())))
# per metal distance/angle summary for the archived set
g = ex.groupby("metal_element").agg(
    n=("d_centroid", "size"), med_d=("d_centroid", "median"),
    med_min=("min_dist", "median"), med_theta=("theta_deg", "median"),
    entries=("pdb_id", "nunique"))
R["excluded_by_metal"] = (g[g.n >= 100].sort_values("n", ascending=False)
                          .round(2).reset_index().to_dict("records"))

# ------------------------------------------------------------------- MMP set
ne = pd.read_csv(OUT / "contacts_derived.csv")
anno = json.loads((P / "data" / "target_annotations.json")
                  .read_text(encoding="utf-8"))
ch2uni, ch2pf, uname = {}, {}, {}
for pid, a in anno.items():
    for ch, acc in (a.get("chains") or {}).items():
        ch2uni[(pid, ch)] = acc
    for ch, fams in (a.get("pfam") or {}).items():
        ch2pf[(pid, ch)] = fams
    for u in a.get("uniprots") or []:
        uname.setdefault(u["uniprot"], u["name"])


def chains(row):
    co = row.coordination if isinstance(row.coordination, str) else ""
    return set(re.findall(r"\(([A-Za-z0-9]+)\)", co))


def uni(row):
    for ch in chains(row):
        if (row.pdb_id, ch) in ch2uni:
            return ch2uni[(row.pdb_id, ch)]
    return None


def ptype(row):
    for ch in chains(row):
        f = ch2pf.get((row.pdb_id, ch))
        if f:
            return classify_pfam(f)
    return None


ne["uniprot"] = ne.apply(uni, axis=1)
ne["ptype"] = ne.apply(ptype, axis=1)
ne["uname"] = ne.uniprot.map(uname)

MMP = {"P39900", "P45452", "P14780", "P08254", "P22894", "P09238", "P08253",
       "P33435", "Q9X721", "Q90611", "P51512", "P15167", "Q9UHI8", "P78325",
       "P03956"}
mmp = ne[ne.uniprot.isin(MMP)]
R["mmp"] = dict(targets=int(mmp.uniprot.nunique()), contacts=int(len(mmp)),
                entries=int(mmp.pdb_id.nunique()), fo=int(mmp.is_fo.sum()),
                pct=round(100 * mmp.is_fo.mean(), 1), boot=boot(mmp),
                median_d_faceon=round(float(
                    mmp[mmp.is_fo == 1].d_centroid.median()), 2),
                by_target=(mmp.groupby(["uniprot", "uname"])
                           .agg(n=("is_fo", "size"), fo=("is_fo", "sum"),
                                entries=("pdb_id", "nunique"))
                           .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                           .reset_index().sort_values("n", ascending=False)
                           .astype(str).to_dict("records")))
ca = ne[ne.uniprot == "P00918"]
R["ca2"] = dict(contacts=int(len(ca)), entries=int(ca.pdb_id.nunique()),
                fo=int(ca.is_fo.sum()),
                pct=round(100 * ca.is_fo.mean(), 1), boot=boot(ca))
# same-metal, same-donor comparison: MMP vs CA-II both Zn / 3xN donors
R["zn_protease_vs_ca"] = dict(
    mmp_zn=int((mmp.metal_element == "Zn").sum()),
    mmp_zn_pct=round(100 * mmp[mmp.metal_element == "Zn"].is_fo.mean(), 1),
    ca_zn_pct=round(100 * ca[ca.metal_element == "Zn"].is_fo.mean(), 1))

# --------------------------------------------------------- target-level stats
tg = ne.dropna(subset=["uniprot"]).groupby("uniprot").agg(
    n=("is_fo", "size"), fo=("is_fo", "sum"),
    entries=("pdb_id", "nunique"), uname=("uname", "first"))
tg["pct"] = 100 * tg.fo / tg.n
big = tg[tg.n >= 20]
R["target_distribution"] = dict(
    n_targets=int(len(tg)), n_big=int(len(big)),
    zero_all=int((tg.fo == 0).sum()), zero_big=int((big.fo == 0).sum()),
    zero_pct_all=round(100 * (tg.fo == 0).mean(), 1),
    zero_pct_big=round(100 * (big.fo == 0).mean(), 1),
    q=[round(float(tg.pct.quantile(q)), 1) for q in (0.25, 0.5, 0.75, 0.9)],
    mean_pct=round(float(tg.pct.mean()), 1),
    median_pct=round(float(tg.pct.median()), 1))

# Table 4: protein types with >= 100 contacts
pt = ne.dropna(subset=["ptype"]).groupby("ptype").agg(
    n=("is_fo", "size"), fo=("is_fo", "sum"), entries=("pdb_id", "nunique"))
pt["pct"] = (100 * pt.fo / pt.n).round(1)
pt = pt[pt.n >= 100].sort_values("pct", ascending=False)
rows = []
for k in pt.index:
    sub = ne[ne.ptype == k]
    b = boot(sub)
    rows.append(dict(ptype=k, contacts=int(pt.loc[k, "n"]),
                     entries=int(pt.loc[k, "entries"]),
                     faceon=int(pt.loc[k, "fo"]), pct=float(pt.loc[k, "pct"]),
                     lo=b["lo"], hi=b["hi"],
                     top_metal=sub.metal_element.value_counts().index[0],
                     top_metal_pct=round(100 * sub.metal_element.value_counts()
                                         .iloc[0] / len(sub), 1),
                     top_ring=sub.ring_class.value_counts().index[0]))
R["table4"] = rows
pd.DataFrame(rows).to_csv(OUT / "S16_target_class.csv", index=False)

# ------------------------------------------------- drug / cofactor highlights
dr = ne[(ne.ligand_category == "drug-approved") & (ne.is_fo == 1)]
leg = pd.read_excel(P / "SI_Tables.xlsx", sheet_name="S4_Ligands").set_index("comp_id")
leg_names = leg.name.to_dict()
rows = []
for (comp, m), s in dr.groupby(["ligand_comp_id", "metal_element"]):
    rows.append(dict(comp=comp, metal=m, contacts=int(len(s)),
                     entries=int(s.pdb_id.nunique()),
                     name=str(leg_names.get(comp))[:70],
                     median_d=round(float(s.d_centroid.median()), 2),
                     median_theta=round(float(s.theta_deg.median()), 1),
                     bridging=s.bridging_class.value_counts().index[0]))
R["drug_faceon_rows"] = sorted(rows, key=lambda r: -r["contacts"])
R["drug_faceon_n_drugs"] = int(dr.ligand_comp_id.nunique())
R["drug_faceon_n_entries"] = int(dr.pdb_id.nunique())

cf = ne[ne.ligand_category == "cofactor"]
R["cofactor_faceon"] = dict(
    n=int(len(cf)), pct=round(100 * cf.is_fo.mean(), 1), boot=boot(cf),
    atp=dict(n=int((cf.ligand_comp_id == "ATP").sum()),
             pct=round(100 * cf[cf.ligand_comp_id == "ATP"].is_fo.mean(), 1)),
    nad=dict(n=int((cf.ligand_comp_id == "NAD").sum()),
             pct=round(100 * cf[cf.ligand_comp_id == "NAD"].is_fo.mean(), 1)),
    fad=dict(n=int((cf.ligand_comp_id == "FAD").sum()),
             pct=round(100 * cf[cf.ligand_comp_id == "FAD"].is_fo.mean(), 1)))

# ------------------------------------------------------- bridging x geometry
R["bridge_faceon"] = (ne.groupby("bridging_class")
                      .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                      .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                      .reset_index().to_dict("records"))
bd = ne[(ne.bridging_class == "bridge-direct") & (ne.is_fo == 1)]
R["bridge_direct_faceon"] = dict(
    n=int(len(bd)), rings=bd.ring_class.value_counts().to_dict(),
    metals=bd.metal_element.value_counts().head(5).to_dict(),
    median_d=round(float(bd.d_centroid.median()), 2),
    median_min=round(float(bd.min_dist.median()), 2),
    n_eta=int((bd.min_dist < 2.3).sum()))

(OUT / "deep_results3.json").write_text(json.dumps(R, indent=1, default=str))
print(json.dumps({k: R[k] for k in ["excluded", "mmp", "ca2", "zn_protease_vs_ca",
                                    "target_distribution", "bridge_direct_faceon",
                                    "cofactor_faceon", "drug_faceon_n_drugs",
                                    "drug_faceon_n_entries"]}, indent=1)[:4000])
print("\nTable 4:")
for r in rows[:0]:
    pass
print(pd.DataFrame(R["table4"]).to_string())
