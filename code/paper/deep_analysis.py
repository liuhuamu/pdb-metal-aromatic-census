#!/usr/bin/env python3
"""Deep excavation of the classified contact table (paper v3 additions).

Reads the released contact table (SI_Tables.xlsx, sheet S5_Contacts) and adds
per-contact annotations that the v2 manuscript did not exploit:

  * ring chemistry  - element composition and size of the contacted ring,
                      reconstructed from the deposited coordinates
  * coordination     - number and chemical type of the metal's other ligands
                      (parsed from the struct_conn `metalc` string)
  * criterion        - sensitivity of the face-on class to the offset and
                      angle definitions
  * data quality     - resolution / method / occupancy dependence
  * subsets          - approved drugs, cofactors, targets

Writes
  paper/data/ring_elements.json         {(comp,atom): element}
  paper/output/contacts_derived.csv     per-contact derived table
  paper/output/deep_results.json        every number quoted in the new text
  paper/output/S12_ring_chemistry.csv
  paper/output/S13_coordination.csv
  paper/output/S14_criterion.csv
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
PAPER = ROOT / "paper"
OUT = PAPER / "output"
OUT.mkdir(exist_ok=True)

CIF = ROOT / "cache" / "cif"

STANDARD = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    "MSE", "SEC", "PYL", "UNK", "HID", "HIE", "HIP", "CYX", "ASH", "GLH",
    "LYN", "HOH", "DOD",
}
RES_ELEM = {"HIS": "N", "ASP": "O", "GLU": "O", "CYS": "S", "MET": "S",
            "SER": "O", "THR": "O", "TYR": "O", "ASN": "O", "GLN": "O",
            "LYS": "N", "ARG": "N", "TRP": "N", "HOH": "O", "DOD": "O"}
METAL_COMP = {"NA", "K", "CL", "MG", "CA", "ZN", "CU", "FE", "MN", "CD", "NI",
              "CO", "BR", "IOD", "CS", "RB", "SR", "BA", "HG", "AG", "AU",
              "PT", "PD", "IR", "RH", "RU", "OS", "MO", "W", "V", "CR", "LI"}
COORD_RE = re.compile(r"^([A-Za-z0-9]+?)(-?\d+[A-Za-z]?)\(([^)]+)\)=([\d.]+)$")


# --------------------------------------------------------------- ring map --
def scan_one(pdb_id: str) -> dict:
    """{(comp_id, atom_name): element} for every ligand atom of one entry."""
    import gemmi
    out = {}
    try:
        st = gemmi.read_structure(str(CIF / f"{pdb_id}.cif"))
    except Exception:
        return out
    st.setup_entities()
    try:
        for chain in st[0]:
            for res in chain:
                if res.name in STANDARD:
                    continue
                for at in res:
                    out[f"{res.name}|{at.name}"] = at.element.name
    except Exception:
        pass
    return out


def build_ring_map(pdb_ids, cache=OUT.parent / "data" / "ring_elements.json"):
    cache = PAPER / "data" / "ring_elements.json"
    if cache.exists():
        return json.loads(cache.read_text())
    print(f"[ring] scanning {len(pdb_ids):,} structures for atom elements ...")
    merged = {}
    with ProcessPoolExecutor(max_workers=12) as ex:
        for i, part in enumerate(ex.map(scan_one, pdb_ids, chunksize=20), 1):
            merged.update(part)
            if i % 1000 == 0:
                print(f"   {i:,}/{len(pdb_ids):,}", flush=True)
    cache.write_text(json.dumps(merged))
    return merged


def ring_class(elems):
    s = set(elems)
    if s <= {"C", "H"}:
        return "carbocycle"
    if s & {"S", "O"}:
        return "S/O-heteroarene"
    return "N-heteroarene"


# ------------------------------------------------------------ coordination --
def parse_coord(s, self_comp):
    prot = wat = selflig = other = metal = 0
    donors = set()
    dists = []
    if not isinstance(s, str) or not s.strip():
        return dict(cn_prot=0, cn_water=0, cn_self=0, cn_other=0, cn_metal=0,
                    cn=0, donors="", cn_prot_dist=np.nan)
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        m = COORD_RE.match(part)
        comp = (m.group(1) if m else part.split("(")[0]).upper()
        if m:
            dists.append(float(m.group(4)))
        if comp in STANDARD:
            if comp in ("HOH", "DOD"):
                wat += 1
                donors.add("O")
            else:
                prot += 1
                donors.add(RES_ELEM.get(comp, "C"))
        elif comp == (self_comp or "").upper():
            selflig += 1
        elif comp in METAL_COMP:
            metal += 1
        else:
            other += 1
    return dict(cn_prot=prot, cn_water=wat, cn_self=selflig, cn_other=other,
                cn_metal=metal, cn=prot + wat + selflig + other + metal,
                donors="".join(sorted(donors)),
                cn_prot_dist=float(np.mean(dists)) if dists else np.nan)


def donor_class(donors):
    if not donors:
        return "none"
    s = set(donors)
    if s == {"N"}:
        return "N only"
    if s == {"O"}:
        return "O only"
    if "S" in s and len(s) == 1:
        return "S only"
    if s == {"N", "O"}:
        return "N+O"
    if "S" in s:
        return "with S"
    return "other"


# ------------------------------------------------------------------- main --
def main():
    df = pd.read_excel(PAPER / "SI_Tables.xlsx", sheet_name="S5_Contacts")
    ne = df[df.geometry_class != "excluded"].copy()
    ne["is_fo"] = (ne.geometry_class == "face-on").astype(int)

    ringmap = build_ring_map(sorted(ne.pdb_id.unique()))
    print(f"[ring] element map: {len(ringmap):,} (comp,atom) pairs")

    def ring_info(row):
        toks = str(row.ring_atoms).split(",")
        els = [ringmap.get(f"{row.ligand_comp_id}|{t}") for t in toks]
        known = [e for e in els if e]
        if len(known) < max(3, len(toks) - 1):
            return "unknown", np.nan, len(toks), ""
        return ring_class(known), len(toks), len(toks), "".join(sorted(set(known)))

    info = ne.apply(ring_info, axis=1, result_type="expand")
    info.columns = ["ring_class", "ring_size", "n_ring_atoms", "ring_elems"]
    ne = pd.concat([ne, info], axis=1)
    ne["ring_size"] = pd.to_numeric(ne.ring_size, errors="coerce")
    print("[ring] class counts:", ne.ring_class.value_counts().to_dict())

    cd = ne.apply(lambda r: parse_coord(r.coordination, r.ligand_comp_id), axis=1,
                  result_type="expand")
    ne = pd.concat([ne, cd], axis=1)
    ne["donor_class"] = ne.donors.map(donor_class)
    ne["cn_bin"] = pd.cut(ne.cn, [-0.1, 2, 4, 5, 6, 7, 20],
                          labels=["0-2", "3-4", "5", "6", "7", "8+"])

    keep = ["pdb_id", "metal_element", "metal_charge", "ligand_comp_id",
            "ligand_category", "ring_type", "ring_class", "ring_size",
            "ring_elems", "d_centroid", "d_plane", "offset", "theta_deg",
            "min_dist", "geometry_class", "bridging_class", "resolution",
            "method", "metal_occupancy", "cn", "cn_prot", "cn_water",
            "cn_self", "cn_other", "cn_metal", "donors", "donor_class",
            "coordination", "is_fo"]
    ne[keep].to_csv(OUT / "contacts_derived.csv", index=False)

    R = {}
    R["n_contacts"] = int(len(ne))
    R["n_entries"] = int(ne.pdb_id.nunique())
    R["n_faceon"] = int(ne.is_fo.sum())
    R["n_edgeon"] = int((1 - ne.is_fo).sum())

    # ---------------- 1. criterion sensitivity ---------------------------------
    sens = []
    for off in [1.5, 2.0, 2.5, 3.0]:
        for th in [None, 45, 30]:
            m = ne.offset < off
            if th is not None:
                m &= ne.theta_deg <= th
            sub = ne[m]
            row = dict(offset_cut=off, theta_cut=th if th else "none",
                       n=int(len(sub)), pct=round(100 * len(sub) / len(ne), 2))
            for el in ["K", "Na", "Zn", "Mg", "Fe", "Mn"]:
                e = ne[ne.metal_element == el]
                mm = e.offset < off
                if th is not None:
                    mm &= e.theta_deg <= th
                row[f"fo_{el}"] = round(100 * mm.mean(), 1)
            sens.append(row)
    S = pd.DataFrame(sens)
    S.to_csv(OUT / "S14_criterion.csv", index=False)
    R["sensitivity"] = sens

    fo = ne[ne.geometry_class == "face-on"]
    R["faceon_theta"] = dict(
        median=round(float(fo.theta_deg.median()), 1),
        q90=round(float(np.percentile(fo.theta_deg, 90)), 1),
        max=round(float(fo.theta_deg.max()), 1),
        n_gt30=int((fo.theta_deg > 30).sum()),
        n_gt45=int((fo.theta_deg > 45).sum()),
        n_gt60=int((fo.theta_deg > 60).sum()),
        pct_gt45=round(100 * (fo.theta_deg > 45).mean(), 1),
        n_theta_gt60=list(fo[fo.theta_deg > 60][
            ["pdb_id", "metal_element", "ligand_comp_id", "d_centroid",
             "offset", "theta_deg", "ring_type"]].astype(str).to_dict("records")))
    eo = ne[ne.geometry_class == "edge-on"]
    R["edgeon_theta"] = dict(median=round(float(eo.theta_deg.median()), 1),
                             min=round(float(eo.theta_deg.min()), 1),
                             n_lt30=int((eo.theta_deg < 30).sum()),
                             pct_lt30=round(100 * (eo.theta_deg < 30).mean(), 1))

    # boundary zone: offset 2.5-3.5 with a flat approach
    bz = ne[(ne.offset >= 2.5) & (ne.offset < 3.5) & (ne.theta_deg < 45)]
    R["boundary"] = dict(n=int(len(bz)), pct=round(100 * len(bz) / len(ne), 1))

    # ---------------- 2. ring chemistry ----------------------------------------
    def fo_table(col, min_n=20):
        g = ne.groupby(col).agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
        g["pct"] = (100 * g.fo / g.n).round(1)
        return g[g.n >= min_n].sort_values("n", ascending=False)

    R["ring_class"] = fo_table("ring_class", 1).reset_index().to_dict("records")
    R["ring_class_by_size"] = (ne.groupby(["ring_class", "ring_size"])
                               .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                               .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                               .reset_index().to_dict("records"))
    # within metal
    rc_metal = {}
    for el in ["Zn", "Mg", "Fe", "Mn", "K", "Na", "Ca", "Ni"]:
        s = ne[ne.metal_element == el]
        g = s.groupby("ring_class").agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
        g["pct"] = (100 * g.fo / g.n).round(1)
        rc_metal[el] = g.reset_index().to_dict("records")
    R["ring_class_by_metal"] = rc_metal
    # within ligand category
    rc_cat = {}
    for cat in ["drug-approved", "cofactor", "other", "additive",
                "drug-experimental"]:
        s = ne[ne.ligand_category == cat]
        g = s.groupby("ring_class").agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
        g["pct"] = (100 * g.fo / g.n).round(1)
        rc_cat[cat] = g.reset_index().to_dict("records")
    R["ring_class_by_category"] = rc_cat
    # top ring_type (single-pattern) face-on fractions
    single = ne[~ne.ring_type.str.contains(",")]
    g = single.groupby("ring_type").agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
    g["pct"] = (100 * g.fo / g.n).round(1)
    R["ring_type_single"] = g[g.n >= 15].sort_values("n", ascending=False
                                                     ).reset_index().to_dict("records")

    # ---------------- 3. coordination environment ------------------------------
    g = ne.groupby(ne.cn.clip(upper=8)).agg(n=("is_fo", "size"),
                                            fo=("is_fo", "sum"))
    g["pct"] = (100 * g.fo / g.n).round(1)
    R["cn_faceon"] = g.reset_index().rename(columns={"index": "cn"}).to_dict("records")
    R["cn_bin"] = (ne.groupby("cn_bin", observed=True)
                   .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                   .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                   .reset_index().astype(str).to_dict("records"))
    g = ne.groupby("donor_class").agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
    g["pct"] = (100 * g.fo / g.n).round(1)
    R["donor_class"] = g.sort_values("n", ascending=False).reset_index(
    ).to_dict("records")
    R["cn_stats"] = dict(
        median=float(ne.cn.median()),
        water_zero_pct=round(100 * (ne.cn_water == 0).mean(), 1),
        selflig_pct=round(100 * (ne.cn_self > 0).mean(), 1))
    # low-CN (<=4) vs high-CN (>=6) contrast, overall and within Zn/Mg
    lowcn = ne[ne.cn <= 4]
    highcn = ne[ne.cn >= 6]
    R["cn_contrast"] = dict(low_n=int(len(lowcn)),
                            low_pct=round(100 * lowcn.is_fo.mean(), 1),
                            high_n=int(len(highcn)),
                            high_pct=round(100 * highcn.is_fo.mean(), 1))
    R["cn_contrast_metal"] = {}
    for el in ["Zn", "Mg", "Fe"]:
        s = ne[ne.metal_element == el]
        R["cn_contrast_metal"][el] = dict(
            low_n=int((s.cn <= 4).sum()),
            low_pct=round(100 * s[s.cn <= 4].is_fo.mean(), 1),
            high_n=int((s.cn >= 6).sum()),
            high_pct=round(100 * s[s.cn >= 6].is_fo.mean(), 1))
    # bridging x geometry
    R["bridge"] = (ne.groupby("bridging_class")
                   .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                   .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                   .reset_index().to_dict("records"))
    # eta / ring-atom-bonded face-on cases
    bd_fo = ne[(ne.bridging_class == "bridge-direct") & (ne.is_fo == 1)]
    R["bridge_direct_faceon"] = dict(
        n=int(len(bd_fo)),
        n_min_dist_lt25=int((bd_fo.min_dist < 2.5).sum()),
        examples=bd_fo[["pdb_id", "metal_element", "ligand_comp_id",
                        "d_centroid", "min_dist", "theta_deg",
                        "ring_class"]].head(8).astype(str).to_dict("records"))

    # ---------------- 4. data quality -----------------------------------------
    r = ne.copy()
    r["resbin"] = pd.cut(r.resolution, [0.8, 1.5, 1.8, 2.0, 2.3, 2.6, 3.01],
                         right=False)
    R["resolution"] = (r.groupby("resbin", observed=True)
                       .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                       .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                       .reset_index().astype(str).to_dict("records"))
    R["resolution_metal"] = {}
    for el in ["Zn", "Mg", "Fe"]:
        s = r[r.metal_element == el]
        R["resolution_metal"][el] = (s.groupby("resbin", observed=True)
                                     .agg(n=("is_fo", "size"),
                                          fo=("is_fo", "sum"))
                                     .assign(pct=lambda x: (100 * x.fo / x.n)
                                             .round(1))
                                     .reset_index().astype(str)
                                     .to_dict("records"))
    R["method"] = (r.groupby("method").agg(n=("is_fo", "size"),
                                           fo=("is_fo", "sum"))
                   .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                   .reset_index().to_dict("records"))
    hi = r[r.resolution < 1.5]
    R["highres"] = dict(n=int(len(hi)), pct=round(100 * hi.is_fo.mean(), 1),
                        n_entries=int(hi.pdb_id.nunique()),
                        metals=hi.metal_element.value_counts().head(5).to_dict())

    # ---------------- 5. drug and cofactor subsets ----------------------------
    dr = ne[ne.ligand_category == "drug-approved"]
    R["drugs"] = dict(
        contacts=int(len(dr)), entries=int(dr.pdb_id.nunique()),
        n_faceon=int(dr.is_fo.sum()),
        pct=round(100 * dr.is_fo.mean(), 1),
        n_drugs_with_faceon=int(dr[dr.is_fo == 1].ligand_comp_id.nunique()),
        n_drugs=int(dr.ligand_comp_id.nunique()),
        by_metal=(dr.groupby("metal_element")
                  .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
                  .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
                  .reset_index().to_dict("records")),
        faceon=dr[dr.is_fo == 1][
            ["pdb_id", "metal_element", "ligand_comp_id", "ligand_name",
             "d_centroid", "theta_deg", "bridging_class", "ring_class"]
        ].astype(str).to_dict("records"),
        top=(dr.groupby(["ligand_comp_id", "ligand_name"])
             .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
             .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
             .reset_index().sort_values("n", ascending=False)
             .head(15).astype(str).to_dict("records")))
    cf = ne[ne.ligand_category == "cofactor"]
    R["cofactors"] = dict(
        contacts=int(len(cf)), pct=round(100 * cf.is_fo.mean(), 1),
        top=(cf.groupby("ligand_comp_id")
             .agg(n=("is_fo", "size"), fo=("is_fo", "sum"))
             .assign(pct=lambda x: (100 * x.fo / x.n).round(1))
             .reset_index().sort_values("n", ascending=False)
             .head(12).to_dict("records")))

    # ---------------- 6. target-level face-on profile -------------------------
    anno = json.loads((PAPER / "data" / "target_annotations.json")
                      .read_text(encoding="utf-8"))
    ch2uni = {}
    for pid, a in anno.items():
        for ch, acc in (a.get("chains") or {}).items():
            ch2uni[(pid, ch)] = acc

    def uniprot_for(row):
        co = row.coordination if isinstance(row.coordination, str) else ""
        chains = set(re.findall(r"\(([A-Za-z0-9]+)\)", co))
        for ch in chains:
            acc = ch2uni.get((row.pdb_id, ch))
            if acc:
                return acc
        return None

    ne["uniprot"] = ne.apply(uniprot_for, axis=1)
    tg = ne.dropna(subset=["uniprot"]).groupby("uniprot").agg(
        n=("is_fo", "size"), fo=("is_fo", "sum"),
        entries=("pdb_id", "nunique"))
    tg["pct"] = (100 * tg.fo / tg.n).round(1)
    R["targets"] = dict(
        n=int(len(tg)),
        top_faceon=tg[tg.n >= 20].sort_values(["pct", "n"], ascending=False)
        .head(12).reset_index().to_dict("records"),
        top_count=tg.sort_values("n", ascending=False).head(10)
        .reset_index().to_dict("records"),
        overall_pct=round(100 * ne.dropna(subset=["uniprot"]).is_fo.mean(), 1),
        n_with=int(ne.uniprot.notna().sum()))

    # equal-target-weighted face-on fraction (removes redundant-target bias)
    per_target = tg.pct
    R["targets"]["equal_weight_pct"] = round(float(per_target.mean()), 1)
    # redundancy
    R["redundancy"] = dict(max_entries=int(tg.entries.max()),
                           top=tg.sort_values("entries", ascending=False)
                           .head(5).reset_index().to_dict("records"))

    (OUT / "deep_results.json").write_text(
        json.dumps(R, indent=1, default=str))
    print("[done] ->", OUT / "deep_results.json")

    # SI tables
    pd.DataFrame(R["ring_class"]).to_csv(OUT / "S12_ring_chemistry.csv",
                                         index=False)
    pd.DataFrame(R["cn_faceon"]).to_csv(OUT / "S13_coordination.csv",
                                        index=False)
    print("keys:", len(R))


if __name__ == "__main__":
    main()
