#!/usr/bin/env python3
"""Paper analysis 1: ligand functional classification (drug annotation).

Classification priority (per ligand comp):
  1. cofactor   - curated list (nucleotides, NAD/FAD, tetrapyrroles, cobalamin,
                  PQQ, TPP/PLP/folate/CoA/SAM and close analogues); curated
                  FIRST because DrugBank also assigns IDs to ATP/NAD/IMD etc.
  2. additive   - curated list (imidazole, benzoic acid, benzamidine, buffers,
                  crystallization/reagent aromatics)
  3. drug-<group> - RCSB/DrugBank drug_groups annotation
                    (approved > withdrawn > investigational > vet_approved >
                     nutraceutical > experimental)

Outputs (paper/data, paper/output):
    drugbank_groups.json      comp lists per DrugBank group (raw API result)
    top100_names.json         names + drugbank ids for top-100 contact ligands
    ligand_classification.csv every aromatic comp -> category
    drug_stats_*.csv          category cross-tabulations
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import requests

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
PAPER = ROOT / "paper"
PAPER_DATA = PAPER / "data"
PAPER_OUT = PAPER / "output"
for d in (PAPER_DATA, PAPER_OUT):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- curated ---
COFACTORS = {
    # purine / pyrimidine nucleotides and analogues
    "ATP", "ADP", "AMP", "GTP", "GDP", "GNP", "GSP", "ANP", "ACP", "APC",
    "APP", "GPP", "CPP", "CTP", "CDP", "CMP", "UTP", "UDP", "UMP",
    "TTP", "TDP", "TMP", "2MG", "1MG", "A2M", "6MZ", "2MA", "OMG", "1MA",
    "QBQ", "NAI",
    # nicotinamide dinucleotides
    "NAD", "NAP", "NAJ", "NDP", "NCD", "NDD",
    # flavins
    "FAD", "FMN", "RFL",
    # tetrapyrroles (heme/chlorophyll/siroheme/porphyrin models)
    "HEM", "HEC", "HEA", "HAS", "HDD", "SRM", "CLA", "CHL", "CL7", "F6C",
    "KC1", "KC2", "BCB", "BCL", "07D", "A1LZM", "CL0", "FEC", "BPH",
    # cobalamin
    "B12", "CNC",
    # quinone / thiamine / pyridoxal / folate / CoA / SAM
    "PQQ", "TPP", "THM", "PLP", "PMP", "FOL", "FA8", "SAH", "SAM", "MTA",
    "COA", "ACO", "DCO",
}
ADDITIVES = {
    # buffers / crystallization additives / common reagent aromatics
    "IMD", "BEZ", "BEN", "BNZ", "IPH", "MES", "EPE", "PFB", "DHB", "3TR",
    "BM0", "MBO", "BE7",
}

DRUG_GROUPS = ["approved", "withdrawn", "investigational",
               "vet_approved", "nutraceutical", "experimental"]
GROUP_PRIORITY = ["approved", "withdrawn", "investigational",
                  "vet_approved", "nutraceutical", "experimental"]

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
PAGE = 10_000


def fetch_group(group: str) -> list:
    ids, start = [], 0
    while True:
        body = {
            "query": {"type": "terminal", "service": "text_chem",
                      "parameters": {"attribute": "drugbank_info.drug_groups",
                                     "operator": "exact_match", "value": group}},
            "return_type": "mol_definition",
            "request_options": {"paginate": {"start": start, "rows": PAGE},
                                "results_content_type": ["experimental"]}}
        r = requests.post(SEARCH_URL, json=body, timeout=300)
        if r.status_code == 204:
            break
        r.raise_for_status()
        d = r.json()
        batch = [h["identifier"] for h in d.get("result_set", [])]
        ids.extend(batch)
        start += PAGE
        if not batch or start >= d.get("total_count", 0):
            break
        time.sleep(0.4)
    return sorted(set(ids))


def classify(comp: str, group_sets: dict) -> str:
    if comp in COFACTORS:
        return "cofactor"
    if comp in ADDITIVES:
        return "additive"
    for g in GROUP_PRIORITY:
        if comp in group_sets.get(g, ()):
            return f"drug-{g}"
    return "other"


def main() -> None:
    # ---- 1. DrugBank group comp lists -----------------------------------
    groups_path = PAPER_DATA / "drugbank_groups.json"
    if groups_path.exists():
        group_sets = json.loads(groups_path.read_text())
    else:
        group_sets = {}
        for g in DRUG_GROUPS:
            print(f"[drug] fetching DrugBank group: {g} ...", flush=True)
            group_sets[g] = fetch_group(g)
            print(f"[drug] {g}: {len(group_sets[g]):,} comps")
        groups_path.write_text(json.dumps(group_sets, indent=1))

    # ---- 2. names for top-100 contact ligands ---------------------------
    conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
    top = [r[0] for r in conn.execute(
        "SELECT ligand_comp_id FROM hits GROUP BY ligand_comp_id "
        "ORDER BY COUNT(*) DESC LIMIT 100")]
    names_path = PAPER_DATA / "top100_names.json"
    if names_path.exists():
        names = json.loads(names_path.read_text())
    else:
        names = {}
        sess = requests.Session()
        for comp in top:
            d = sess.get(f"https://data.rcsb.org/rest/v1/core/chemcomp/{comp}",
                         timeout=30).json()
            names[comp] = {
                "name": d.get("chem_comp", {}).get("name", "?"),
                "drugbank": d.get("rcsb_chem_comp_container_identifiers",
                                  {}).get("drugbank_id", ""),
            }
        names_path.write_text(json.dumps(names, indent=1))

    # ---- 3. classify every aromatic ligand ------------------------------
    aromatic = json.loads((ROOT / "data" / "aromatic_ligands.json").read_text())
    all_comps = sorted(set().union(*aromatic.values()))
    lig_class = {c: classify(c, group_sets) for c in all_comps}

    import csv
    with open(PAPER_OUT / "ligand_classification.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["comp_id", "category", "name"])
        for c in all_comps:
            w.writerow([c, lig_class[c], names.get(c, {}).get("name", "")])

    # ---- 4. classify hits ------------------------------------------------
    def bridging_class(row) -> str:
        if row["metal_embedded"]:
            return "embedded"
        coord = row["coordination"] or ""
        protein = any(aa in coord for aa in (
            "HIS", "CYS", "ASP", "GLU", "LYS", "ARG", "SER", "THR", "TYR",
            "MET", "ASN", "GLN", "TRP", "PHE", "VAL", "LEU", "ILE", "ALA",
            "GLY", "PRO"))
        if protein and row["min_dist"] <= 2.8:
            return "bridge-direct"
        if protein:
            return "bridge-near"
        if coord.strip():
            return "ligand-held"
        return "unannotated"

    conn.row_factory = sqlite3.Row
    hits = conn.execute("SELECT * FROM hits").fetchall()
    conn.close()

    rows = []
    for r in hits:
        cat = lig_class.get(r["ligand_comp_id"], "other")
        rows.append({
            "pdb_id": r["pdb_id"], "element": r["metal_element"],
            "cat": cat, "bridge": bridging_class(r),
            "geom": r["geometry_class"],
        })

    def dump(name, keyfields):
        from collections import Counter, defaultdict
        contacts = Counter()
        ents = defaultdict(set)
        for r in rows:
            k = tuple(r[f] for f in keyfields)
            contacts[k] += 1
            ents[k].add(r["pdb_id"])
        with open(PAPER_OUT / f"drug_stats_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(keyfields) + ["entries", "contacts"])
            for k in sorted(contacts, key=lambda k: -contacts[k]):
                w.writerow(list(k) + [len(ents[k]), contacts[k]])

    dump("category", ["cat"])
    dump("cat_x_metal", ["cat", "element"])
    dump("cat_x_bridge", ["cat", "bridge"])
    dump("cat_x_geom", ["cat", "geom"])
    dump("cat_x_metal_x_bridge", ["cat", "element", "bridge"])

    # ---- 5. console summary ---------------------------------------------
    from collections import Counter, defaultdict
    cat_contacts = Counter(r["cat"] for r in rows)
    cat_entries = defaultdict(set)
    for r in rows:
        cat_entries[r["cat"]].add(r["pdb_id"])
    print("\n=== ligand category (contacts / entries) ===")
    for c, n in cat_contacts.most_common():
        print(f"  {c:<22s} {n:>7,d} contacts  {len(cat_entries[c]):>6,d} entries")

    print("\n=== top approved-drug ligands ===")
    drug_rows = [r for r in rows if r["cat"].startswith("drug-")]
    per_comp = Counter(r["pdb_id"] for r in drug_rows)
    top_drug = Counter()
    for r in drug_rows:
        top_drug[r["cat"]] += 1
    for c, n in top_drug.most_common():
        print(f"  {c:<22s} {n:>7,d} contacts")
    conn2 = sqlite3.connect(ROOT / "data" / "results.sqlite")
    comp_counts = Counter()
    comp_cat = {}
    for r in conn2.execute("SELECT ligand_comp_id FROM hits"):
        comp_counts[r[0]] += 1
    conn2.close()
    shown = 0
    print("  --- individual drug ligands by contacts ---")
    for comp, n in comp_counts.most_common():
        cat = lig_class.get(comp, "other")
        if cat.startswith("drug-"):
            print(f"  {comp:>6s} {cat:<18s} {n:>5,d}  "
                  f"{names.get(comp, {}).get('name', '')[:45]}")
            shown += 1
            if shown >= 25:
                break


if __name__ == "__main__":
    main()
