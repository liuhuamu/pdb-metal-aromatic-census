# Metal–aromatic contacts in the Protein Data Bank

A geometry-resolved census of metal-ion contacts to the aromatic rings of
non-polymeric ligands across the experimental PDB archive.

**13,231 non-porphyrin metal–aromatic contacts in 5,107 PDB entries**
(261,301 structures screened; snapshot 16 October 2026), plus 44,347
porphyrin-family or metal-embedded contacts archived separately.

Companion manuscript: *How Metal Ions Engage Aromatic Ligands: A
Geometry-Resolved PDB Census*.

---

## Contents

| Path | Size | What it is |
|---|---|---|
| `data/results.sqlite` | 21.4 MB | **Core database**: `hits` (57,578 contacts × 26 columns, all contacts including porphyrin), `excluded` (29,384 excluded candidate contacts with reason) |
| `data/SI_Tables.xlsx` | 9.0 MB | Supporting Tables S1–S18 (screening, metal list, target annotations, top targets, drug subsets, criterion sensitivity, coordination spheres, target-matched affinity tests) |
| `data/source_data/*.csv` | 19 MB | Per-figure and per-table source data (`SI_contacts.csv`, `fig1_contacts_data.csv`, `pdbbind_general_PL_2020.csv`, `dist_hist_data.csv`, …) |
| `code/` | 17.8 MB | Complete analysis pipeline (`step1`–`step6`), paper scripts (figures, tables, statistics), and cached intermediate JSON/CSV files needed to rerun the figure code offline |
| `figures/` | 10.4 MB | Publication figures, each as PNG (600 dpi) and vector PDF |
| `structures/` | 5.4 MB | The six case-study structures (CIF/PDB) |
| `requirements.txt` | — | Python dependencies |

---

## Quick start

```bash
pip install -r requirements.txt

# the census, in one query
sqlite3 data/results.sqlite "SELECT geometry_class, COUNT(*) FROM hits \
  WHERE geometry_class IN ('face-on','edge-on') GROUP BY 1;"

# per-target face-on fractions (Table 4)
sqlite3 data/results.sqlite "SELECT coordination, COUNT(*) FROM hits GROUP BY 1;"

# reproduce a figure (from the code directory)
cd code/paper && python make_figures.py
```

The SQLite file is self-describing: `PRAGMA table_info(hits);` lists every
column.

---

## Data dictionary — table `hits`

**Entry and quality**

| Column | Meaning |
|---|---|
| `id` | internal contact id |
| `pdb_id` | 4-character PDB entry code |
| `title`, `method`, `resolution`, `n_models` | entry metadata from the deposited file |

**Metal**

| Column | Meaning |
|---|---|
| `metal_comp_id`, `metal_element`, `metal_charge` | component id, element, formal charge used in the query |
| `metal_bucket` | A (d10), B (alkali/alkaline earth), C (other transition), D (noble) |
| `metal_embedded` | 1 if the metal is part of the ligand entity itself (porphyrins, etc.) |
| `metal_occupancy`, `metal_subchain`, `metal_auth` | deposited atom attributes |

**Ligand ring**

| Column | Meaning |
|---|---|
| `ligand_comp_id`, `ligand_subchain`, `ligand_auth` | ligand component and chain |
| `ring_type` | carbocycle / N-heteroarene / S,O-heteroarene |
| `ring_atoms` | atom names of the aromatic ring |

**Geometry** (all distances in Å, angles in degrees)

| Column | Meaning |
|---|---|
| `d_centroid` | metal → ring-centroid distance |
| `d_plane` | perpendicular distance to the least-squares ring plane |
| `offset` | lateral displacement of the metal projection from the ring centre |
| `theta_deg` | angle between the metal–centroid vector and the ring normal |
| `min_dist` | shortest metal → ring-atom distance |

**Classification**

| Column | Meaning |
|---|---|
| `geometry_class` | `face-on` (offset ≤ 2.5 Å), `edge-on` (offset > 2.5 Å), or `excluded-porphyrin` |
| `coordination` | `bridge-direct` (protein partner **and** `min_dist` ≤ 2.8 Å), `bridge-near` (protein partner, `min_dist` > 2.8 Å), `ligand-held` (partners present, none protein), `unannotated` (no `struct_conn` record) |

All contacts satisfy `d_centroid ≤ 6.0 Å` and involve a non-polymeric
aromatic ligand.

---

## Provenance and licensing of inputs

* Structure coordinates come from the RCSB PDB (<https://www.rcsb.org>),
  snapshot of 16 October 2026. PDB structures are distributed under CC0;
  please cite the originating entries.
* The PDBbind v2020 index data are **not redistributed** (licence,
  <https://www.pdbbind-plus.org.cn>). Only derived per-complex
  classifications and affinity values are included
  (`data/source_data/pdbbind_general_PL_2020.csv`).

## Licence

* **Code** (`code/`): MIT — see `LICENSE-CODE`.
* **Data** (`data/`, `figures/`): CC BY 4.0 — see `LICENSE-DATA`.

## Citation

If you use these data, please cite the manuscript and this repository:

```
Liuhua Mu. How Metal Ions Engage Aromatic Ligands: A
Geometry-Resolved PDB Census. J. Chem. Inf. Model. (submitted).
Database and code: https://github.com/liuhuamu/pdb-metal-aromatic-census (v1.0.0)
```

## Contact

Liuhua Mu
muliuhua@nbu.edu.cn

