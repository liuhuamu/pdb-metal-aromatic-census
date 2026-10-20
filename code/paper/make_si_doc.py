#!/usr/bin/env python3
"""Generate the Supporting Information Word document.

paper/manuscript/JCIM_SI.docx
  SI Methods (classification criteria, porphyrin keywords, curated
  lists, attribution)
  SI Figures S1-S5
  SI Tables S1-S8
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
sys.path.insert(0, str(ROOT))
from config import AROMATIC_SMILES  # noqa: E402
FIG = ROOT / "paper" / "figures"
SRC = FIG / "source_data"
OUTDIR = ROOT / "paper" / "manuscript"
OUTDIR.mkdir(parents=True, exist_ok=True)

REFS = json.loads(
    (ROOT / "paper" / "data" / "references_verified.json")
    .read_text(encoding="utf-8"))

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)

t = doc.add_paragraph()
t.alignment = 1
run = t.add_run("Supporting Information\nHow Metal Ions Engage Aromatic "
                "Ligands: A Geometry-Resolved PDB Census")
run.bold = True
run.font.size = Pt(13)


def H(text, level=1):
    doc.add_heading(text, level=level)


def P(text, italic=False, size=None, new=False):
    par = doc.add_paragraph()
    r = par.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if new:  # text added in the v3 revision is printed in blue
        from docx.shared import RGBColor
        r.font.color.rgb = RGBColor(0x00, 0x00, 0xCC)
    return par


def TABLE_CAP(text, new=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(9.5)
    if new or any(text.startswith(f"Table S{i}.") for i in range(10, 19)):
        # tables S10-S18 were added in the v3 revision: printed in blue
        from docx.shared import RGBColor
        r.font.color.rgb = RGBColor(0x00, 0x00, 0xCC)


def table_from_rows(header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = str(h)
    for row in rows:
        c = t.add_row().cells
        for i, v in enumerate(row):
            c[i].text = str(v)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    return t


def table_from_csv(path, max_rows=None):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    if max_rows:
        rows = rows[:max_rows + 1]
    t = doc.add_table(rows=1, cols=len(rows[0]))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(rows[0]):
        t.rows[0].cells[i].text = h
    for row in rows[1:max_rows + 1 if max_rows else None]:
        c = t.add_row().cells
        for i, v in enumerate(row):
            c[i].text = str(v)
    return t


# ------------------------------------------------------------- SI Methods --
H("S1. Supporting Methods")
H("S1.1. Geometry classification criteria", level=2)
P("Every metal-ring pair with d_centroid <= 6 A was classified by the "
  "lateral projection of the metal onto the ring plane: face-on if the "
  "projection falls within 2.5 A of the ring centre (offset < 2.5 A - "
  "the atomic-envelope radius of an aromatic ring; the para-hydrogen "
  "distance across a benzene ring is ~5.0 A), edge-on otherwise. "
  "Contacts involving "
  "porphyrin-family ligands (tetrapyrrole, corrin, and phthalocyanine "
  "macrocycles - heme A/B/C/O, siroheme, chlorophyll a/b/c/d/f and "
  "bacteriochlorophylls, cobalamins, and related variants; keyword list "
  "in S1.2) or with a metal embedded in the ligand itself (including "
  "Ru-polypyridyl complexes) were excluded from the two-class census "
  "and archived separately (44,347 contacts in 3,012 entries).")
H("S1.2. Porphyrin-family exclusion keywords", level=2)
P("A contact was excluded if the ligand name (RCSB chem_comp name, "
  "lowercased) contains any of the following substrings, or if the "
  "metal is embedded in the ligand itself (metal_embedded = 1, which "
  "also captures organometallic ligand fragments such as "
  "ruthenium-polypyridyl complexes):")
kw = ("porphyrin; porphine; chlorophyll; chlorin; corrin; siroheme; "
      "sirohaem; phthalocyanine; cobalamin; pheophorbide; heme")
P(kw)
H("S1.3. Bridging classes and their parameters", level=2)
P("The bridging class of a contact describes where the metal is held. "
  "Coordination partners were taken from the deposited struct_conn records "
  "of type metalc; a partner counts as protein if its residue name is one "
  "of the 20 standard amino-acid codes (HIS, CYS, ASP, GLU, LYS, ARG, SER, "
  "THR, TYR, MET, ASN, GLN, TRP, PHE, VAL, LEU, ILE, ALA, GLY, PRO). "
  "Water, nucleic-acid residues and other ligands were not counted as "
  "protein. Classes are assigned in the order below (first match wins), and "
  "all four use the same contact definition d_centroid <= 6.0 A; metals "
  "embedded in the ligand (metal_embedded = 1) are removed before the "
  "ladder is applied.", new=True)
P("(i) bridge-direct: at least one protein partner AND the closest approach "
  "of the metal to any atom of the contacted ring (min_dist) is <= 2.8 A - "
  "the upper bound of a metal-ligand coordination bond for the elements "
  "considered. (ii) bridge-near: at least one protein partner AND "
  "min_dist > 2.8 A. (iii) ligand-held: at least one deposited partner, "
  "none of them a protein residue, i.e. the ion is held by the ligand "
  "itself, by water or by another ion. (iv) unannotated: no metalc record "
  "in struct_conn. The classification is therefore fully specified by "
  "d_centroid (6.0 A, contact cutoff), min_dist (2.8 A, ring-atom bond) and "
  "the deposited struct_conn partner list.", new=True)
H("S1.4. Curated cofactor and additive lists", level=2)
P("Cofactor list (59 comps): nucleotides and analogues (ATP, ADP, AMP, "
  "GTP, GDP, GNP, GSP, ANP, ACP, APC, CTP/CDP/CMP, UTP/UDP/UMP, "
  "TTP/TDP/TMP, methylated variants 2MG/1MG/A2M/6MZ/2MA/OMG/1MA, QBQ, "
  "NAI), nicotinamide dinucleotides (NAD, NAP, NAJ, NDP, NCD, NDD), "
  "flavins (FAD, FMN, RFL), tetrapyrroles (HEM, HEC, HEA, HAS, HDD, "
  "SRM, CLA, CHL, CL7, F6C, KC1, KC2, BCB, BCL, 07D, A1LZM, CL0, FEC, "
  "BPH), cobalamins (B12, CNC), PQQ, TPP/THM, PLP/PMP, FOL/FA8, "
  "SAH/SAM/MTA, CoA/ACO/DCO.")
P("Additive list (11 comps): IMD, BEZ, BEN, BNZ, IPH, MES, EPE, PFB, "
  "DHB, 3TR, BM0, MBO, BE7.")
P("Cofactor and additive labels take priority over DrugBank drug "
  "groups, because ATP, NAD, and imidazole carry DrugBank identifiers "
  "but are not therapeutic drugs. The lists were curated from the "
  "top-contact ligands of the census and are provided as "
  "machine-readable data (SI_Tables.xlsx, sheet S11).")
H("S1.5. Target attribution", level=2)
P("Each contact was attributed to the UniProt accession of the protein "
  "chain that coordinates the metal, as recorded in struct_conn "
  "(conn_type_id = metalc); e.g. a contact with coordination string "
  "'HIS95(A)=2.10;HIS97(A)=2.03;HIS120(A)=1.98' is attributed to the "
  "UniProt of chain A. Contacts whose metal is not protein-coordinated "
  "are attributed to all UniProt accessions of the entry if the entry "
  "has at most three polymer entities, and to the placeholder "
  "'(multi-chain complex)' otherwise - this avoids counting a single "
  "ribosomal contact once per subunit. Entries without any UniProt "
  "mapping (mostly fully synthetic constructs) are labeled "
  "'(no UniProt)'.")
H("S1.6. Protein-type classification", level=2)
P("Pfam protein-family annotations (families per polymer entity, with "
  "chain identifiers) were retrieved for all hit entries from the RCSB "
  "Data API (GraphQL, batched queries of 100 entries). Each "
  "metal-coordinating chain was assigned to one of 41 broad protein "
  "types by keyword rules over its Pfam family names: the rule list is "
  "ordered (specific families before generic functions) and matches "
  "lowercased Pfam names, e.g. 'Carb_anhydrase' -> Carbonic anhydrase, "
  "'7tm' -> GPCR, 'metallo-beta-lactamase' -> Metallo-beta-lactamase, "
  "'ribosomal' -> Ribosome, 'photosystem'/'chlorophyll' -> Photosynthetic "
  "apparatus, 'pkinase' -> Protein kinase. Chains without a matching "
  "rule fall into 'Other'; contacts without protein coordination "
  "inherit the Pfam types of their entry. The complete rule list is "
  "provided in the analysis script make_fig_classes.py (submission "
  "package). Table S9 lists the protein-type x metal-ion contact "
  "distribution underlying main-text Figure 5.")
H("S1.7. Software", level=2)
P("Python 3.12; requests 2.34; gemmi 0.7.5; networkx 3.7; numpy 2.3; "
  "pandas 3.0; matplotlib 3.10 (figures); python-docx (this "
  "document). The RCSB chemical search backend uses the OpenEye "
  "OEChem toolkit (https://www.eyesopen.com). All scripts are "
  "provided in the submission package.")

# ------------------------------------------------------------- SI Figures --
H("S2. Supporting Figures")
si_figs = [
    ("dist_hist_A.png",
     "Figure S1. Bucket A (d10 ions) - distributions of d_centroid, "
     "d_plane, offset, and theta (angle to ring normal; dashed line = "
     "2.5 A offset face-on boundary in the offset panel)."),
    ("dist_hist_B.png",
     "Figure S2. Bucket B (alkali/alkaline-earth) - as Figure S1."),
    ("dist_hist_C.png",
     "Figure S3. Bucket C (other transition metals) - as Figure S1."),
    ("dist_hist_D.png",
     "Figure S4. Bucket D (noble/platinum-group metals) - as Figure S1."),
     ("fig_pdbbind_general_PL_2020.png",
      "Figure S5. Binding affinity of PDBbind v2020 general PL-set "
      "complexes (n = 19,443) grouped by metal-contact classification "
      "(main-text Figure 7 shows the refined set)."),
]
for fname, cap in si_figs:
    p = doc.add_paragraph()
    p.alignment = 1
    p.add_run().add_picture(str(FIG / fname), width=Inches(6.3))
    cap_p = doc.add_paragraph()
    r = cap_p.add_run(cap)
    r.font.size = Pt(9)

# ------------------------------------------------------------- SI Tables --
H("S3. Supporting Tables")
TABLE_CAP("Table S1. Screening funnel and quality-control statistics.")
f1 = list(csv.reader(open(SRC / "fig1_funnel_data.csv")))
table_from_rows(f1[0], f1[1:])

TABLE_CAP("Table S2. Metal elements, buckets, and component charges. "
          "Rows of type 'element summary' declare the bucket membership "
          "of an element; their comp_id and charge are empty by design "
          "(a bucket is defined per element, not per oxidation state). "
          "Rows of type 'component' list a PDB metal component and its "
          "curated formal charge.")
import sys as _sys
_sys.path.insert(0, str(ROOT))
from config import AROMATIC_SMILES, METAL_BUCKETS, METAL_COMPS  # noqa: E402
s2_rows = []
for el, bucket in sorted(METAL_BUCKETS.items()):
    s2_rows.append(["element summary", el, bucket, "", ""])
for comp, (el, chg) in sorted(METAL_COMPS.items()):
    s2_rows.append(["component", el, METAL_BUCKETS.get(el, ""), comp, chg])
table_from_rows(["row_type", "element", "bucket", "comp_id",
                 "formal_charge"], s2_rows)

TABLE_CAP("Table S3. Aromatic ring SMILES patterns and per-pattern counts "
          "(entries / ligand components).")
import json as _json
entries = _json.loads((ROOT / "data" / "aromatic_entries.json").read_text())
ligands = _json.loads((ROOT / "data" / "aromatic_ligands.json").read_text())
pat_rows = [[name, smi, len(entries[name]), len(ligands[name])]
            for name, smi in AROMATIC_SMILES.items()]
table_from_rows(["pattern", "SMILES", "entries", "ligand_comps"], pat_rows)

TABLE_CAP("Table S4. Ligand functional classification - top 60 ligands by "
          "contacts (complete machine-readable list: SI_Tables.xlsx, "
          "sheet S4; 37,877 comps).")
conn = sqlite3.connect(ROOT / "data" / "results.sqlite")
names = json.loads((ROOT / "paper" / "data" / "ligand_names_all.json").read_text())
lig_class = {}
for row in csv.DictReader(open(ROOT / "paper" / "output" /
                               "ligand_classification.csv")):
    lig_class[row["comp_id"]] = row["category"]
rows = conn.execute(
    "SELECT ligand_comp_id, COUNT(*) n, COUNT(DISTINCT pdb_id) e "
    "FROM hits GROUP BY ligand_comp_id ORDER BY n DESC LIMIT 60").fetchall()
table_from_rows(
    ["comp_id", "category", "name", "contacts", "entries"],
    [[r[0], lig_class.get(r[0], "other"), names.get(r[0], ""), r[1], r[2]]
     for r in rows])
conn.close()

TABLE_CAP("Table S5. UniProt target clustering - top 30 targets "
          "(complete list: fig7_targets_data.csv, 1,296 targets).")
table_from_csv(str(SRC / "fig7_targets_data.csv"), max_rows=30)

TABLE_CAP("Table S6a. PDBbind v2020 permutation tests - general PL set.")
table_from_csv(str(SRC / "pdbbind_general_PL_2020_tests.csv"))
TABLE_CAP("Table S6b. PDBbind v2020 permutation tests - refined set.")
table_from_csv(str(SRC / "pdbbind_refined_2020_tests.csv"))

TABLE_CAP("Table S7. Top approved-drug (DrugBank) ligands by contacts.")
table_from_csv(str(SRC / "fig5_approved_by_ligand.csv"), max_rows=20)

TABLE_CAP("Table S8. Approved-drug contacts by metal.")
table_from_csv(str(SRC / "fig5_approved_by_metal.csv"))

TABLE_CAP("Table S9. Protein-type distribution of metal-aromatic "
          "contacts (contacts per broad protein type and metal ion; "
          "underlying data of main-text Figure 5).")
table_from_csv(str(SRC / "fig_classes_data.csv"))

# ---- v3 deep-analysis tables ---------------------------------------------
OUTP = ROOT / "paper" / "output"


def _orientation(landscape: bool):
    """Start a new page-oriented section (wide tables)."""
    from docx.enum.section import WD_ORIENT, WD_SECTION
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    w, h = sec.page_width, sec.page_height
    if landscape and w < h:
        sec.page_width, sec.page_height = h, w
    if not landscape and w > h:
        sec.page_width, sec.page_height = h, w
    sec.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sec.left_margin = Inches(0.7)
    sec.right_margin = Inches(0.7)
    return sec


def shrink(t, size=7.5):
    for row in t.rows:
        for cell in row.cells:
            for par in cell.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(size)


_orientation(True)
TABLE_CAP("Table S10. Sensitivity of the face-on classification to the "
          "offset cutoff (1.5-3.0 A) and to an additional angular gate "
          "(theta <= 45 or 30 deg). Columns fo_K ... fo_Mn give the "
          "face-on percentage of the respective metal under that "
          "definition.")
shrink(table_from_csv(str(OUTP / "SI_S12_criterion.csv")))

TABLE_CAP("Table S11. Face-on fraction by ring chemistry. Levels: all "
          "contacts; ring size (5- vs 6-membered); individual metals; "
          "ligand functional categories; single substructure patterns "
          "(ligands matching only one of the nine aromatic SMARTS "
          "patterns; n >= 15).")
shrink(table_from_csv(str(OUTP / "SI_S13_ring_chemistry.csv")))

TABLE_CAP("Table S12. Face-on fraction by the metal's coordination "
          "sphere, parsed from the deposited struct_conn metalc records: "
          "coordination number (CN), binned CN, the chemical class of the "
          "protein donor set, and - for the six most frequent metals - "
          "donor class within a single metal species.")
shrink(table_from_csv(str(OUTP / "SI_S14_coordination.csv")))

TABLE_CAP("Table S13. Target-matched (stratified) PDBbind affinity "
          "contrasts. Within every UniProt target (or Pfam-derived "
          "protein type) containing at least three complexes per group, "
          "the difference of group medians was computed; the statistic is "
          "the median of these within-target differences, and p is from "
          "5,000 permutations of group labels within the target "
          "(two-sided).")
shrink(table_from_csv(str(OUTP / "SI_S15_pdbbind_matched.csv")))

TABLE_CAP("Table S14. Face-on fraction by protein type of the "
          "metal-coordinating chain (types with at least 100 non-excluded "
          "contacts). CI: entry-clustered bootstrap 95% confidence "
          "interval (2,000 resamples of entries). This is the full "
          "version of main-text Table 4.")
shrink(table_from_csv(str(OUTP / "SI_S16_target_class.csv")))

TABLE_CAP("Table S15. Rank-normalized, within-target PDBbind affinity "
          "contrasts. Affinities were converted to percentile ranks within "
          "each target (>= 4 complexes) and group means were compared with "
          "a permutation test that shuffles group labels within the target "
          "(20,000 permutations, two-sided).")
shrink(table_from_csv(str(OUTP / "SI_S17_pdbbind_rank.csv")))

TABLE_CAP("Table S16. Matrix metalloproteinase / metzincin subset: "
          "contacts, face-on contacts and face-on fraction per UniProt "
          "target.")
shrink(table_from_csv(str(OUTP / "SI_S18_mmp_isoforms.csv")))

_orientation(False)
from analysis_drug import ADDITIVES, COFACTORS  # noqa: E402
TABLE_CAP("Table S17. Curated cofactor and additive/buffer component "
          "lists used in the ligand priority scheme (Section 2.5).")
shrink(table_from_rows(["list", "comp_id"],
                       [["cofactor", c] for c in sorted(COFACTORS)] +
                       [["additive", a] for a in sorted(ADDITIVES)]))

TABLE_CAP("Table S18. Variables of the per-contact database "
          "(SI_contacts.csv and SI_Tables.xlsx, sheet S5_Contacts).")
table_from_rows(
    ["field", "definition"],
    [["pdb_id", "deposited PDB entry identifier"],
     ["metal_element / metal_comp_id",
      "metal element and deposited component (e.g. ZN, FE2)"],
     ["metal_charge / metal_bucket",
      "curated formal charge (where known) and element-family bucket A-D"],
     ["ligand_comp_id / ligand_category",
      "ligand component identifier and functional category "
      "(cofactor, additive, drug-approved, drug-experimental, other)"],
     ["ring_type / ring_atoms",
      "aromatic substructure pattern(s) matched by the ligand and the "
      "atom names of the contacted ring"],
     ["d_centroid / d_plane / offset / theta_deg / min_dist",
      "geometric descriptors defined in Section 2.2"],
     ["geometry_class",
      "face-on (offset < 2.5 A), edge-on, or excluded (porphyrin-family "
      "or embedded metal)"],
     ["bridging_class",
      "bridge-direct (>= 1 protein partner AND min_dist <= 2.8 A), "
      "bridge-near (>= 1 protein partner, min_dist > 2.8 A), ligand-held "
      "(>= 1 partner, none of them protein: ligand, water or ion), "
      "unannotated (no metalc record); first match wins, all with "
      "d_centroid <= 6.0 A"],
     ["coordination",
      "struct_conn metalc partners of the metal "
      "(residue, chain, distance)"],
     ["ring_class / ring_size",
      "derived: carbocycle, N-heteroarene, or S/O-heteroarene; number of "
      "ring atoms"],
     ["cn / donor_class",
      "derived: coordination number and chemical class of the protein "
      "donor set (N only, N+O, O only, with S)"],
     ["resolution / method / metal_occupancy",
      "deposited data-quality descriptors used for the QC filters"]])

P("")
P("Machine-readable versions of all tables (including the complete "
  "57,578-row contact table with 24 columns) are provided in "
  "SI_Tables.xlsx and SI_contacts.csv.")

out = OUTDIR / "JCIM_SI.docx"
doc.save(out)
print("SI ->", out)





