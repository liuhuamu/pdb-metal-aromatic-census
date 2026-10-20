#!/usr/bin/env python3
"""Assemble the new supporting tables (S12-S18) for SI_Tables.xlsx."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
P = ROOT / "paper"
OUT = P / "output"

R1 = json.loads((OUT / "deep_results.json").read_text())
R2 = json.loads((OUT / "deep_results2.json").read_text())
R3 = json.loads((OUT / "deep_results3.json").read_text())
rank = json.loads((OUT / "pdbbind_rank.json").read_text())
matched = json.loads((OUT / "pdbbind_matched.json").read_text())
ne = pd.read_csv(OUT / "contacts_derived.csv")

def fmt_p(x):
    if x is None or x == "":
        return ""
    x = float(x)
    return "<0.0001" if x < 0.0001 else round(x, 4)


# ---- S12: criterion sensitivity -------------------------------------------
s12 = pd.read_csv(OUT / "S14_criterion.csv")
s12 = s12.rename(columns={"offset_cut": "offset_cutoff_A",
                          "theta_cut": "theta_gate_deg"})
s12.to_csv(OUT / "SI_S12_criterion.csv", index=False)

# ---- S13: ring chemistry ---------------------------------------------------
rows = []
for r in R1["ring_class"]:
    rows.append(dict(level="all contacts", group=r["ring_class"], n=r["n"],
                     faceon=r["fo"], pct=r["pct"]))
for r in R1["ring_class_by_size"]:
    rows.append(dict(level="ring size", group=f'{r["ring_class"]} ({int(r["ring_size"])}-ring)',
                     n=r["n"], faceon=r["fo"], pct=r["pct"]))
for metal, lst in R1["ring_class_by_metal"].items():
    for r in lst:
        rows.append(dict(level=f"metal {metal}", group=r["ring_class"],
                         n=r["n"], faceon=r["fo"], pct=r["pct"]))
for cat, lst in R1["ring_class_by_category"].items():
    for r in lst:
        rows.append(dict(level=f"ligand {cat}", group=r["ring_class"],
                         n=r["n"], faceon=r["fo"], pct=r["pct"]))
for r in R1["ring_type_single"]:
    rows.append(dict(level="substructure pattern", group=r["ring_type"],
                     n=r["n"], faceon=r["fo"], pct=r["pct"]))
s13 = pd.DataFrame(rows)
s13.to_csv(OUT / "SI_S13_ring_chemistry.csv", index=False)

# ---- S14: coordination sphere ---------------------------------------------
rows = []
for r in R1["cn_faceon"]:
    rows.append(dict(level="coordination number", group=f'CN {int(r["cn"])}',
                     n=r["n"], faceon=r["fo"], pct=r["pct"]))
for r in R1["cn_bin"]:
    rows.append(dict(level="coordination number (binned)", group=r["cn_bin"],
                     n=r["n"], faceon=r["fo"], pct=r["pct"]))
for r in R1["donor_class"]:
    rows.append(dict(level="protein donor set", group=r["donor_class"],
                     n=r["n"], faceon=r["fo"], pct=r["pct"]))
for m in ["Zn", "Fe", "Mg", "Ca", "Mn", "Ni"]:
    sub = ne[ne.metal_element == m]
    for dc, g in sub.groupby("donor_class"):
        if len(g) >= 20:
            rows.append(dict(level=f"metal {m}", group=dc, n=len(g),
                             faceon=int(g.is_fo.sum()),
                             pct=round(100 * g.is_fo.mean(), 1)))
s14 = pd.DataFrame(rows)
s14.to_csv(OUT / "SI_S14_coordination.csv", index=False)

# ---- S15: target-matched affinity contrasts --------------------------------
def pretty(key: str) -> str:
    """'bridge-near_vs_no-metal__uniprot' -> 'bridge-near vs no-metal (uniprot)'."""
    if "__" in key:
        base, level = key.split("__", 1)
        return base.replace("_vs_", " vs ") + f" ({level})"
    return key.replace("_vs_", " vs ")


rows = []
for ds in ("general", "refined"):
    for k, v in matched[ds].items():
        if isinstance(v, dict) and "median_delta" in v:
            rows.append(dict(dataset=ds, comparison=pretty(k),
                             strata=v["n_strata"],
                             n_group1=v["n1"], n_group2=v["n2"],
                             median_delta=round(v["median_delta"], 3),
                             mean_delta=round(v["mean_delta"], 3),
                             n_pos=v["n_positive"],
                             n_neg=v["n_negative"],
                             p_permutation=fmt_p(v["p_perm_median"]),
                             p_sign_test=v["sign_test_p"]))
    e = matched[ds].get("faceon_entry_contrast")
    if e:
        rows.append(dict(dataset=ds, comparison="face-on vs edge-on entries",
                         strata="", n_group1=e["n_faceon"],
                         n_group2=e["n_edgeon"],
                         median_delta=e.get("delta"),
                         mean_delta="",
                         n_pos="", n_neg="",
                         p_permutation=(fmt_p(e["p_perm"]) if e.get("p_perm") is not None else ""), p_sign_test=""))
s15 = pd.DataFrame(rows)
for col in ("strata", "n_group1", "n_group2", "n_pos", "n_neg"):
    s15[col] = pd.to_numeric(s15[col], errors="coerce").astype("Int64")
s15.to_csv(OUT / "SI_S15_pdbbind_matched.csv", index=False)

# ---- S16: target-class face-on summary -------------------------------------
s16 = pd.DataFrame(R3["table4"]).rename(columns={
    "ptype": "protein_type", "contacts": "contacts", "entries": "entries",
    "faceon": "faceon_contacts", "pct": "faceon_pct", "lo": "ci_low",
    "hi": "ci_high", "top_metal": "main_metal",
    "top_metal_pct": "main_metal_pct", "top_ring": "main_ring_class"})
s16.to_csv(OUT / "SI_S16_target_class.csv", index=False)

# ---- S17: rank-normalized affinity contrasts -------------------------------
rows = []
for key, v in rank.items():
    ds, strat = key.split("|")
    for t in v["tests"]:
        if not t:
            continue
        rows.append(dict(dataset=ds, stratum_level=strat, comparison=
                         f'{t["group1"]} vs {t["group2"]}',
                         n_group1=t["n1"], n_group2=t["n2"],
                         n_strata=t["n_strata"],
                         mean_rank_group1=t["mean_rank1"],
                         mean_rank_group2=t["mean_rank2"],
                         rank_delta=t["delta"], p_permutation=fmt_p(t["p"])))
s17 = pd.DataFrame(rows)
s17.to_csv(OUT / "SI_S17_pdbbind_rank.csv", index=False)

# ---- S18: MMP isoforms -----------------------------------------------------
s18 = pd.DataFrame(R3["mmp"]["by_target"]).rename(columns={
    "uniprot": "uniprot", "uname": "target_name", "n": "contacts",
    "fo": "faceon_contacts", "entries": "entries", "pct": "faceon_pct"})
s18.insert(0, "family", "matrix metalloproteinase / metzincin")
s18.to_csv(OUT / "SI_S18_mmp_isoforms.csv", index=False)

for name in ["S12", "S13", "S14", "S15", "S16", "S17", "S18"]:
    f = OUT / f"SI_{name}_*.csv"
    for p in sorted(OUT.glob(f"SI_{name}_*.csv")):
        d = pd.read_csv(p)
        print(f"{p.name:<34s} {len(d):>5,} rows x {len(d.columns)} cols")



