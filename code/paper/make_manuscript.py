#!/usr/bin/env python3
"""Generate the JCIM manuscript as a Word document (v2 numbers).

paper/manuscript/JCIM_manuscript.docx
- full main text with superscript citations (numbered by first appearance)
- 8 embedded figures with captions
- 3 inline tables built from the analysis data
- reference list with DOI hyperlinks (every entry verified via Crossref /
  PubMed on 2026-10-16)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
FIG = ROOT / "paper" / "figures"
SRC = FIG / "source_data"
OUTDIR = ROOT / "paper" / "manuscript"
OUTDIR.mkdir(parents=True, exist_ok=True)

REFS = json.loads(
    (ROOT / "paper" / "data" / "references_verified.json")
    .read_text(encoding="utf-8"))

# --- v3 revision bookkeeping: language fixes + blue marks -------------------
from revision_marks import (END, FULL_PARAS, MARKS, NEW_HEADINGS,  # noqa: E402
                            NEW_KEYS, START, TEXT_FIXES)


def _fix(text: str) -> str:
    for old, new in TEXT_FIXES:
        if old in text and new not in text:
            text = text.replace(old, new)
    return text


def _mark(text: str) -> str:
    for marker, frags in MARKS:
        if marker in text:
            for frag in frags:
                if frag in text:
                    text = text.replace(frag, START + frag + END)
    for fp in FULL_PARAS:
        if text.startswith(fp) and not text.startswith(START):
            text = START + text + END
    return text


# ---------------------------------------------------------------- figures --
FIGURES = [
    ("fig1_funnel.png",
     "Figure 1. Screening funnel, geometry classes, and classification "
     "criteria. (a) Number of PDB entries at each screening stage (log "
     "scale): entries with a non-polymeric aromatic ligand (92,487), "
     "entries containing one of 25 configured metal ions (37,337), and "
     "entries with at least one metal...aromatic-ring contact within 6 A "
     "involving a non-porphyrin ligand (5,107). (b) The 13,231 qualifying "
     "contacts are classified as face-on (981; 7.4%) or edge-on (12,250; "
     "92.6%) by the lateral projection of the metal onto the ring plane. "
     "(c) Geometric quantities: d_centroid (metal...ring centroid "
     "distance), d_plane (perpendicular distance to the least-squares "
     "ring plane), offset (lateral displacement of the projection from "
     "the ring center), and theta (angle between the metal...centroid "
     "vector and the ring normal). (d) Side-view schematics: face-on "
     "(projection < 2.5 A, the atomic-envelope radius of the ring), "
     "edge-on (projection >= 2.5 A), and the excluded porphyrin-family "
     "contacts (metal coordinated inside the macrocycle or embedded in "
     "the ligand)."),
    ("fig3_bridging.png",
     "Figure 2. Metal-mediated binding configurations per metal. Stacked "
     "counts of the three bridging classes among non-embedded contacts "
     "(metals with >= 20 contacts): bridge-direct (metal coordinated by "
     "protein residues AND bonded to a ligand ring atom), bridge-near "
     "(metal coordinated by protein residues, ligand ring within 6 A), "
     "ligand-held (metal held by the ligand or water/ions), and "
     "unannotated (no struct_conn coordination record). Approximately 75% "
     "of contacts involve a protein-coordinated metal."),
    ("fig7_targets.png",
     "Figure 3. UniProt target-level clustering of the contacts, with each "
     "contact attributed to the protein chain that coordinates the metal. "
     "(A) Top targets by total non-embedded contacts. (B) Top targets "
     "restricted to DrugBank-annotated ligands. Carbonic anhydrase II "
     "dominates both panels; metallo-beta-lactamases, lysine demethylases, "
     "autotaxin, and tubulin complete the top group - all established "
     "metal-enzyme drug targets."),
    ("fig_classes.png",
     "Figure 4. Protein-type distribution of metal-aromatic contacts. "
     "(A) Heatmap of contact counts for the top protein types (Pfam-"
     "derived, chains classified by the Pfam families of the metal-"
     "coordinating chain) and the top 10 metal ions; only types with >= 20 "
     "contacts are shown. (B) Metal-bucket composition (A d10, B alkali/"
     "alkaline-earth, C other transition, D noble) per protein type. "
     "Carbonic anhydrases are almost exclusively Zn; the photosynthetic "
     "apparatus is dominated by Mg of chlorophylls; ribosomal contacts "
     "are almost entirely Mg."),
    ("fig4_geomclass.png",
     "Figure 5. Metal specificity of the geometry classes. Fraction of "
     "face-on and edge-on contacts per metal, for the 12 metals with at "
     "least 50 non-excluded contacts; the number of contacts is given in "
     "parentheses and the rows are ordered by face-on fraction. K, Zn, and "
     "Na show the highest face-on fractions (12.8%, 10.9%, and 10.8%), "
     "consistent with classical cation–π chemistry, whereas Co (0.3%), Au "
     "(0.0%), Mn (1.7%), and Cu (2.0%) are effectively edge-on only. Copper "
     "sits near the bottom of the ranking: its apparent face-on enrichment "
     "in an unfiltered analysis originates exclusively from copper "
     "coordinated inside porphyrin macrocycles. Rarer metals, such as Ru "
     "(39.1% of only 23 contacts), are too sparsely sampled to rank."),
    ("fig5_drugs.png",
     "Figure 6. Ligand functional categories and approved drugs. (A) "
     "Contacts by ligand category (log scale) after DrugBank annotation "
     "and curation of cofactors/additives. (B) Approved-drug contacts by "
     "metal: Mg (bisphosphonate complexes) and Zn dominate. (C) Top "
     "approved-drug ligands by contact count: zoledronic acid (ZOL) and "
     "risedronate (RIS) are Mg-coordinating bisphosphonates of farnesyl "
     "diphosphate synthase."),
    ("fig_pdbbind_refined_2020.png",
     "Figure 7. Binding affinity of PDBbind v2020 complexes grouped by "
     "metal-contact classification (refined set, n = 5,316; all "
     "Kd/Ki-derived). Box plots of -log(Kd/Ki). In the uncorrected "
     "comparison, complexes whose ligand makes a protein-bridged metal "
     "contact (bridge-near, n = 379) have a higher median affinity than "
     "metal-free controls (median difference +1.16 log units, "
     "permutation p < 0.0001); the general-set analysis (n = 19,443) "
     "reproduces that difference. As shown in Section 3.7, most of this "
     "global difference is target composition: after matching within "
     "target the bridge-near advantage survives against metal-present "
     "contact-free complexes but not against metal-free complexes (see "
     "Table 3 and Source Data)."),
    ("fig6_cases.png",
     "Figure 8. Case studies spanning the geometry continuum (rendered "
     "from deposited coordinates; PyMOL selection commands in the "
     "Supporting Information), ordered from electrostatic to covalent. "
     "(a) Lysozyme (PDB 9GOG): Na+ cation–π (d_centroid 3.68 A). (b) "
     "ARH3 + NAD (PDB 7ARW): Mg face-on over the adenine ring "
     "(d_centroid 3.29 A). (c) 3-hydroxyanthranilate dioxygenase + "
     "picolinate (PDB 4HSJ): Fe face-on (d_centroid 2.57 A) with a "
     "DrugBank-annotated ligand. (d) Nicking endonuclease + imidazole "
     "(PDB 9QGV): Zn essentially stacked on the imidazole face "
     "(d_centroid 2.06 A). (e) Carbonic anhydrase II + "
     "benzeneselenol (PDB 6HWZ): the Se coordinates Zn (2.47 A) and the "
     "ring hangs edge-on (theta_plane = 34.2 deg). (f) Cupin protein + "
     "Ru(eta6-p-cymene) (PDB 9XS9): the extreme face-on case "
     "(d_centroid 1.68 A, eta6-arene coordination). The six cases sample "
     "the tight tail of the face-on distribution: the median face-on "
     "contact of the full census lies at 4.83 A, and 67.6% of face-on "
     "contacts are beyond 4.5 A (Figure 9b)."),
    ("fig9_determinants.png",
     "Figure 9. What sets the odds of face-on engagement. (a) Face-on "
     "fraction per Pfam-derived protein type (types with >= 100 "
     "non-excluded contacts; number of contacts in brackets) with "
     "entry-clustered bootstrap 95% confidence intervals; deaminases, "
     "proteases (dominated by the matrix metalloproteinases) and "
     "phosphodiesterases are face-on-rich, whereas carbonic anhydrases, "
     "dehydrogenases, histone demethylases, tubulins and "
     "dehydratases/lyases are essentially edge-on-only. (b) Distance "
     "spectrum of the 981 face-on contacts, resolved into an inner "
     "(< 3.7 A, n = 115), a stacked (3.7-4.5 A, n = 203) and an outer "
     "(> 4.5 A, n = 663) regime. (c) Face-on fraction by the coordination "
     "number of the metal (left) and by the chemical class of its protein "
     "donor set (N, N+O, O, S; right). (d) Face-on fraction by ring "
     "chemistry (carbocyclic vs N-heteroaromatic ring) for the five most "
     "frequent metals."),
]
FIGURES = [(name, _fix(cap)) for name, cap in FIGURES]

TABLE1_CAPTION = ("Table 1. Screening funnel and classification summary.")
TABLE2_CAPTION = ("Table 2. Bridging configuration of the 13,231 "
                  "non-porphyrin metal-aromatic contacts. Classes are "
                  "assigned in the order listed (first match wins); all four "
                  "require d_centroid <= 6.0 A, and metals embedded in the "
                  "ligand are excluded beforehand. min_dist is the closest "
                  "metal...ring-atom distance of the contacted ring; a "
                  "'protein partner' is a struct_conn metalc partner whose "
                  "residue name is one of the 20 standard amino acids.")
TABLE3_CAPTION = ("Table 3. Binding affinity (median -log(Kd/Ki)) of "
                  "PDBbind v2020 complexes grouped by metal-contact "
                  "classification.")
TABLE4_CAPTION = ("Table 4. Face-on fraction by protein type of the "
                  "metal-coordinating chain (types with >= 100 "
                  "non-excluded contacts). Percentages carry "
                  "entry-clustered bootstrap 95% confidence intervals "
                  "(2,000 resamples of entries). Full table in Table S14.")
TABLE1_CAPTION, TABLE2_CAPTION, TABLE3_CAPTION, TABLE4_CAPTION = (
    _fix(TABLE1_CAPTION), _fix(TABLE2_CAPTION), _fix(TABLE3_CAPTION),
    _fix(TABLE4_CAPTION))

# ---------------------------------------------------------------- text -----
# Citation tokens are written as {c:key1+key2}; the builder converts them
# into superscript reference numbers ordered by first appearance.

PARAGRAPHS = [
    ("H1", "1. Introduction"),
    ("P", "Metal ions are integral components of an estimated one third of "
          "all proteins and act as catalytic, structural and regulatory "
          "cofactors across every branch of life,{c:andreini_metals_2008} "
          "and cells must sense and deliver the correct metal to each "
          "site.{c:waldron_nature_2009!} "
          "A large fraction of established drug targets are "
          "metalloenzymes{c:moianos_2023!} "
          "- carbonic anhydrases,{c:supuran_ca_2016} matrix "
          "metalloproteinases, histone deacetylases, metallo-beta-"
          "lactamases,{c:king_aspergillomarasmine_2014} and the many "
          "purine- and NAD-dependent enzymes whose active sites are built "
          "around Zn2+, Mg2+ or Fe - and at these sites the metal is often "
          "the anchor to which the inhibitor binds. Metals also act where "
          "no catalytic ion is present: the allosteric Na+ site of G "
          "protein-coupled receptors stabilizes the inactive state and "
          "modulates ligand binding allosterically.{c:zou_gpcr_2021} "
          "Aromatic rings, meanwhile, are among the most frequent "
          "structural motifs of small-molecule ligands,{c:lovering_2009} "
          "so a metal ion and an aromatic ring repeatedly share the same "
          "binding pocket."),
    ("P", "The contact that results is not a minor one. Gas-phase "
          "measurements place the binding energies of Na+ and K+ to "
          "benzene in the same range as their ion-water "
          "interactions,{c:mecozzzi} and the strength of the contact "
          "follows the charge density of the cation. What has not been "
          "established is how often, and in which geometry, a metal ion "
          "actually engages the aromatic ring of a bound ligand. For the "
          "aromatic side chains of proteins the picture is comparatively "
          "complete: the cation-π interaction was established as a general "
          "binding force in protein chemistry,{c:dougherty_science_1996!} "
          "reviewed in full three decades on,{c:dougherty_chemrev_2025!} "
          "with solvent effects now accessible to first-principles "
          "calculation,{c:mu_molecules_2024!} quantified thermodynamically "
          "and shown to be strong in water,{c:dougherty_cationpi_2013} and "
          "surveyed across "
          "the Protein Data Bank (PDB),{c:gallivan_cationpi_1999} a "
          "resource that a dedicated databank of cation-π geometries now "
          "extends,{c:cipdb_2023!} and "
          "aromatic-aromatic interactions were analyzed earlier "
          "still.{c:burley_petsko_1985} For the aromatic rings of "
          "ligands, the resources that exist - MetalPDB among them - "
          "catalog metal sites in biological "
          "macromolecules{c:metalpdb} but were not designed "
          "to answer how a metal engages the ring of a bound ligand, in "
          "which geometry, and with what consequence for binding affinity. "
          "We refer to this family of geometries throughout as metal–π "
          "contacts, and we define the term precisely in Section 3.2."),
    ("P", "The answer matters for modeling, not merely for bookkeeping. "
          "Scoring functions, docking engines and classical force fields "
          "treat a metal site as an anchor for a donor atom and carry no "
          "explicit "
          "metal–π term;{c:li_merz_review_2017} explicit metal-ion handling "
          "reached mainstream docking engines only recently,{c:vina_2021!} "
          "and dedicated geometric treatments of metalloprotein docking have "
          "only recently appeared,{c:wang_gpdock_2023!} while backbone-based "
          "predictors now locate metal sites even in structures that lack a "
          "deposited ion.{c:biometall_2021!} Whether such a term is "
          "warranted, and how it should be parameterized, depends on how "
          "often a ring face - rather than a lone pair - approaches the "
          "ion. Building a census that can answer this is harder than it "
          "looks, for three reasons. First, an entry-level chemical search "
          "of the PDB also indexes polymer residues, so that "
          "phenylalanine, tyrosine and tryptophan side chains inflate an "
          "'aromatic ligand' query by roughly a factor of five (255,847 "
          "entries unfiltered against 52,638 restricted to ligand "
          "entities). Second, a fixed distance window confuses the close, "
          "ionic edge contacts of alkali and alkaline-earth ions with "
          "genuine chelation. Third, metal-coordinating macrocycles must "
          "be excluded explicitly: without that filter, copper appears to "
          "be the most face-on metal in the archive, a signal that comes "
          "entirely from the CuB site of cytochrome c oxidase sitting "
          "above a heme macrocycle."),
    ("P", "Here we report a geometry-resolved census of metal ion contacts "
          "to the aromatic rings of non-polymeric ligands across the "
          "entire PDB. Non-polymeric ligands were screened with nine "
          "aromatic substructure patterns, crossed with exact-formula "
          "queries for 25 metals, and every qualifying structure was "
          "downloaded and analyzed geometrically: 37,337 candidate entries "
          "yield 13,231 non-porphyrin metal-aromatic contacts in 5,107 "
          "entries. Three results frame the paper. Edge contacts dominate "
          "(92.6%), and the face-on minority is bimodal in distance, "
          "splitting into a tight coordination-like regime and a much "
          "larger second-shell regime. About three quarters of all "
          "contacts are mediated by a protein-bound metal, so the metal is "
          "part of the binding site rather than a spectator. And face-on "
          "engagement is a property of particular targets rather than of "
          "particular ions, ranging from 60.5% of contacts in the matrix "
          "metalloproteinases to 0.3% in carbonic anhydrase II. The "
          "annotated database, the structure library and the analysis code "
          "are released as a benchmark for metal–π scoring terms and "
          "force-field development."),
    ("H1", "2. Methods"),
    ("H2", "2.1. Screening the PDB Archive"),
    ("P", "All queries were executed against the RCSB PDB Search API "
          "v2.{c:rose_rcsb_2021} The PDB archive itself and the mmCIF "
          "dictionary have been described "
          "elsewhere.{c:berman_pdb_2000}{c:westbrook_mmcif_2000} The "
          "archive was accessed on 16 October 2026; the PDB grows "
          "continuously, and all archive-level counts reported in this "
          "study - including the 261,301-entry experimental universe that "
          "defines the starting point of the census (Figure 1a) - reflect "
          "this snapshot date and will differ for later retrievals. "
          "Aromatic "
          "ligands were identified by SMILES substructure search of "
          "non-polymeric components (OpenEye OEChem graph matching on the "
          "RCSB chemical-index backend) using nine ring patterns: benzene "
          "(c1ccccc1), pyridine, pyrrole, imidazole, furan, thiophene, "
          "thiazole, oxazole, and triazole (Table S3). Because the "
          "entry-level chemical index also indexes polymer residues, all "
          "aromatic queries used the API's non_polymer_entity return "
          "type - which restricts results to ligand entities and thereby "
          "excludes polymer residues - and were reduced to entry "
          "identifiers. Metal-containing entries "
          "were selected by exact molecular-formula queries for 25 "
          "elements grouped into four element-family 'buckets' that serve "
          "as reporting categories throughout this study (A, d10 ions: "
          "Zn, Cd, Hg, Cu, Ag, Au; "
          "B, alkali and alkaline-earth: Li, Na, K, Rb, Cs, Mg, Ca, Sr, "
          "Ba; C, other transition metals: Fe, Mn, Co, Ni, Cr, Mo, W, V, "
          "Ti; D, noble metals: Pt, Pd, Ir, Rh, Ru, Os); a formula query "
          "automatically covers oxidation-state variants (Fe matches both "
          "the FE and FE2 components). Formal charges of the metal sites "
          "were taken from the RCSB component dictionary (metal list, "
          "buckets, and charges in Table S2). Throughout, census statistics refer to metals by bare element symbol (the deposited components span multiple oxidation states for Fe, Mn, Cu, and Au); ionic notation (e.g. Na+, Zn2+) is reserved for statements about the specific cations. The intersection "
          "of the aromatic "
          "and metal sets yielded 37,337 candidate entries."),
    ("H2", "2.2. Structure Set and Geometric Analysis"),
    ("P", "All 37,336 available mmCIF files (the macromolecular Crystallographic Information File, the PDB archive format) were downloaded (16 parallel "
          "threads; gzip transfer) and parsed with gemmi "
          "0.7.5.{c:wojdyr_gemmi_2022} For every structure we considered "
          "model 1 (the asymmetric unit), located all metal sites as "
          "single-atom non-polymeric residues with a metal element (or "
          "metal atoms embedded in an aromatic ligand, such as the Fe of "
          "heme), and perceived aromatic rings of every aromatic ligand "
          "instance from the deposited chem_comp_bond table "
          "(pdbx_aromatic_flag; the mmCIF category listing chemical bonds and aromaticity flags), splitting fused ring systems into a "
          "cycle basis - the minimal set of independent rings that covers a fused polycyclic system, e.g. the six- and five-membered rings of adenine rather than their combined perimeter - as computed with the NetworkX graph library.{c:hagberg_networkx_2008} For every metal x ring pair we "
          "computed the metal...centroid distance (d_centroid), the "
          "perpendicular distance to the least-squares ring plane "
          "(d_plane; the plane is obtained by singular value "
          "decomposition, SVD, of the ring-atom coordinates), the lateral "
          "offset, the angle theta between "
          "the metal...centroid vector and the ring normal, and the "
          "closest metal...ring-atom distance (min_dist). Formally, for a "
          "metal at position m and a ring R of N aromatic atoms with "
          "centroid c = (1/N)SUM r_i and unit normal n (the right "
          "singular vector of the centered ring-atom coordinate matrix, "
          "i.e. the best-fit plane through ring atoms that are not "
          "exactly coplanar because of coordinate uncertainty and ring "
          "puckering), "
          "d_centroid = |m - c|, d_plane = |(m - c) . n|, offset = "
          "(d_centroid^2 - d_plane^2)^(1/2), theta_plane = arcsin(d_plane "
          "/ d_centroid) (the angle between the metal...centroid line and "
          "the ring plane; theta_plane = 90 deg - theta), and min_dist = "
          "min_i |m - r_i|. All five quantities are reported per contact "
          "in the deposited database and are purely descriptive; the "
          "classification (Section 2.3) uses only d_centroid and offset. "
          "Two further annotations were derived for the analyses of "
          "Sections 3.6 and 3.9. First, the chemical composition of each "
          "contacted ring was reconstructed by mapping its atom names to "
          "the elements deposited in atom_site (type_symbol) of the same "
          "ligand component, which classifies a ring as carbocyclic, "
          "N-heteroaromatic, or S/O-heteroaromatic and yields its size. "
          "Second, the coordination sphere of the metal was reconstructed "
          "from the struct_conn metalc records: the number of partners "
          "(coordination number, CN), the number of protein, water, "
          "self-ligand and other-ligand partners, and the elements of the "
          "protein donor atoms inferred from residue identity (HIS/LYS/ARG "
          "and Trp N; Asp/Glu/Ser/Thr/Tyr/Asn/Gln O; Cys/Met S). "
          "Coordination geometry itself was not assigned to an idealized "
          "polyhedron - classifiers such as MetalHawk now perform that "
          "assignment from the same descriptors{c:metalhawk_2024!} - so the "
          "sphere is carried through the analysis as its donor set and CN."),
    ("H2", "2.3. Geometry Classification"),
    ("P", "A 'contact' is defined throughout as any metal-ring pair with "
          "d_centroid <= 6 A, and an 'entry' is a single deposited PDB "
          "structure record (one coordinate file, which may contain "
          "several metal sites and several ligands). Contacts were "
          "classified by a projection-based two-class scheme: "
          "face-on if the lateral projection of the metal onto the ring "
          "plane falls within 2.5 A of the "
          "ring center (offset < 2.5 A - the atomic-envelope radius of an "
          "aromatic ring; the para-hydrogen distance across a benzene "
          "ring is ~5.0 A), edge-on otherwise, with d_centroid <= 6 A as the overall "
          "cutoff. Contacts involving porphyrin-family ligands - "
          "tetrapyrrole, corrin, and phthalocyanine macrocycles "
          "(protoporphyrin, heme A/B/C/O, siroheme, chlorophyll a/b/c/d/f "
          "and bacteriochlorophylls, cobalamins, and related variants; "
          "keyword list in SI Section S1.2) - or with a metal embedded in the "
          "ligand itself (including Ru-polypyridyl complexes) were "
          "excluded from the two-class census and archived separately "
          "(44,347 contacts in 3,012 entries). Because a projection "
          "criterion could in principle admit contacts in which the metal "
          "lies inside the ring radius but almost in the ring plane, we "
          "report a sensitivity analysis over the offset cutoff "
          "(1.5, 2.0, 2.5 and 3.0 A), with and without an additional "
          "angular gate (theta <= 45 deg or <= 30 deg), and we resolve the "
          "face-on class into three distance regimes: inner (< 3.7 A, the "
          "range in which the metal reaches the ring atoms), stacked "
          "(3.7-4.5 A) and outer (> 4.5 A) (Table S10, Figure 9b)."),
    ("H2", "2.4. Bridging Configurations and Target Annotation"),
    ("P", "For every non-excluded contact, the metal coordination "
          "partners deposited in struct_conn (conn_type_id = metalc; the mmCIF category that records metal-coordination links) were"
          "parsed, and each contact was assigned a bridging class: "
          "bridge-direct if the metal is coordinated by protein residues "
          "and additionally forms a coordination contact with a ligand "
          "ring atom (min_dist <= 2.8 A), "
          "bridge-near if the metal is protein-coordinated with the "
          "ligand ring within 6 A, ligand-held if the metal is held by "
          "the ligand itself or by water/other ions, and unannotated if "
          "no coordination record exists. Entries whose only contacts are "
          "porphyrin-excluded were treated as metal-present but "
          "contact-free controls. UniProt accessions (stable protein "
          "identifiers in the UniProt knowledgebase"
          "{c:uniprot_2023}) were retrieved for "
          "all hit entries via the RCSB Data API (GraphQL, a structured "
          "query interface; batches of "
          "100 entries), and each contact was attributed to the UniProt "
          "of the protein chain that coordinates the metal; contacts "
          "without protein coordination in multi-chain complexes were "
          "labeled '(multi-chain complex)' to avoid inflation of "
          "multi-subunit assemblies."),
    ("H2", "2.5. Ligand Functional Annotation"),
    ("P", "All 37,877 aromatic ligand components were classified by a "
          "priority scheme: (i) a curated cofactor list (nucleotides, "
          "NAD(P)(H), flavins, tetrapyrroles, cobalamins, PQQ, TPP, PLP, "
          "folate, CoA, SAM and close analogues), (ii) a curated "
          "additive/buffer list (imidazole, benzoic acid, benzamidine, "
          "MES, HEPES, and related crystallization aromatics), and (iii) "
          "DrugBank drug_groups annotations retrieved through the RCSB "
          "Data API{c:wishart_drugbank_2018} (approved, withdrawn, "
          "investigational, vet_approved, nutraceutical, experimental). "
          "Cofactors take priority over DrugBank labels because ATP, NAD, "
          "and imidazole carry DrugBank identifiers but are not drugs in "
          "the therapeutic sense. Ligand names were retrieved for every "
          "hit ligand (2,758 components) and for all DrugBank-annotated "
          "components (4,201 additional) from the RCSB Data API."),
    ("H2", "2.6. Affinity Association (PDBbind)"),
    ("P", "The PDBbind v2020 index files (general PL set, 19,443 "
          "complexes; refined set, 5,316 "
          "complexes){c:wang_pdbbind_2004}{c:wang_pdbbind_2005} were "
          "joined with our classification. Every indexed complex was "
          "assigned to one of four groups: (i) a metal-aromatic contact "
          "of a given bridging class, (ii) metal present but no contact "
          "within 6 A (no-contact), (iii) aromatic ligand without any "
          "configured metal (no-metal), or (iv) outside the aromatic "
          "census. Group differences in -log(Kd/Ki) were tested with a "
          "two-sided permutation test (20,000 permutations) on the "
          "difference of medians, stratified by affinity measure type "
          "(Kd, Ki, IC50) as a robustness check. Target-family "
          "composition is a strong confounder of this comparison, so we "
          "repeated it in two target-matched designs. (a) Stratified "
          "comparison: within every UniProt target (and, separately, "
          "every Pfam-derived protein type) that contains at least three "
          "complexes of each group, the difference of group medians was "
          "computed, and significance was obtained by permuting group "
          "labels within the target (5,000 permutations); the reported "
          "statistic is the median of the within-target differences. "
          "(b) Rank-normalized comparison: for every target with at "
          "least four complexes the affinities were converted to "
          "within-target percentile ranks, and group means of these ranks "
          "were compared with a permutation test that shuffles labels "
          "within target (20,000 permutations), which keeps all complexes "
          "rather than only the matched strata. Both UniProt and Pfam-"
          "type strata are reported (Tables S13 and S15)."),
    ("H2", "2.7. Quality Control and Software"),
    ("P", "Entries with resolution worse than 3.0 A (3,724) or without a "
          "resolution (NMR; 167) were excluded from the census, as were "
          "metal sites with occupancy < 0.5 (326) and ligand instances "
          "whose ring coordinates or bond tables were incomplete (319). "
          "In total, 24,676 of the 37,337 candidates contain a metal and "
          "an aromatic ligand but no contact within 6 A; a further 2,846 "
          "candidates have only porphyrin-excluded contacts. Together "
          "(27,522 entries) these form the primary no-contact control "
          "group. The full exclusion statistics are given in Table S1. "
          "Because contacts are clustered within entries (up to 48 per "
          "entry) and within targets (up to 662 for carbonic anhydrase "
          "II), all percentages in the target-level analyses of Sections "
          "3.6 and 3.9 carry 95% confidence intervals from an "
          "entry-clustered bootstrap (2,000 resamples of entries), and "
          "contingency-style comparisons are reported as "
          "Mantel-Haenszel odds ratios stratified over metals. "
          "All analyses used Python 3.12 with gemmi 0.7.5, networkx 3.7, "
          "numpy 2.3, pandas 3.0, and matplotlib 3.10; the complete "
          "pipeline and analysis scripts are provided (see Data "
          "Availability)."),
    ("H1", "3. Results and Discussion"),
    ("H2", "3.1. A Geometry-Resolved Census of 13,231 Contacts"),
    ("P", "The screen (Figure 1a) starts from the full archive of "
          "261,301 experimental PDB entries (all methods; accessed "
          "16 October 2026). "
          "Of these, 92,487 contain a non-polymeric ligand with at least "
          "one aromatic ring (37,877 distinct ligand components; Table "
          "S4), of which 37,337 also contain one of the 25 configured "
          "metals. Geometric analysis of all downloaded structures "
          "identified 57,578 metal-aromatic contacts within 6 A, of which "
          "44,347 involve porphyrin-family macrocycles or embedded metals "
          "and are excluded from the two-class census. The qualifying set "
          "comprises 13,231 non-porphyrin contacts in 5,107 entries "
          "(Figure 1b): 981 face-on (7.4%) and 12,250 edge-on (92.6%). Contacts and entries are different units: the 13,231 contacts are unevenly distributed over the 5,107 entries (median 2, mean 2.6, and maximum 48 contacts per entry; 2,345 entries contain exactly one contact). "
          "The 44,347 excluded contacts are dominated by chlorophylls "
          "(CLA, CHL, CL7, BCB, and related; 26,496 contacts, mostly to "
          "Mg2+ of the photosynthetic apparatus) and hemes (HEM, HEC, "
          "HEA, SRM, and related; 14,535 contacts, mostly to the embedded "
          "Fe). They are archived with the same geometric annotations so "
          "that macrocycle specialists can reuse them (Table 1). The "
          "archived set has the signature of covalent chelation rather "
          "than of a contact: the median metal...centroid distance is "
          "3.24 A, the median closest metal...ring-atom distance is "
          "2.04 A, and 43,906 of the 44,347 contacts (99.0%) involve a "
          "metal embedded in the ligand itself, with Mg (28,229, "
          "chlorophylls) and Fe (14,310, hemes) accounting for 96% of the "
          "contacts."),
    ("FIG", "fig1_funnel.png"),
    ("TABLE", 1),
    ("H2", "3.2. A Projection-Based Classification Separates Two Physical "
           "Regimes"),
    ("P", "Throughout, metal–π denotes the continuum of contacts between a "
          "metal ion and the π-electron system of an aromatic ring: at one "
          "end covalent eta6-arene coordination bonds, as in organometallic "
          "arene complexes and their anticancer "
          "scaffolds,{c:yan_ruarene_2005} at the other the purely "
          "electrostatic cation–π interaction of a solvated alkali cation "
          "above a ring face.{c:dougherty_cationpi_2013} The 13,231 "
          "contacts analyzed here sample this whole continuum, which is why "
          "we resolve them by geometry rather than by energy. Figure 1c "
          "defines the geometric quantities and Figure 1d "
          "schematizes the two classes and the porphyrin exclusion; the "
          "underlying (offset, d_plane) positions of all 13,231 contacts "
          "are provided as Source Data. In "
          "the (offset, "
          "d_plane) plane the face-on class corresponds to the region "
          "left of the 2.5 A offset line, and "
          "the 6 A cutoff bounds the point cloud along a quarter circle. "
          "The two classes separate cleanly: edge-on contacts populate "
          "the large-offset region (coordination-driven, e.g. a metal "
          "held by attached donor atoms with the ring hanging to the "
          "side), whereas face-on contacts occupy the region with "
          "projections inside the ring radius. The face-on class is "
          "therefore geometrically homogeneous but energetically not: its "
          "981 members are spread over the whole 6 A window (median "
          "d_centroid 4.83 A, range 1.68-6.00 A) and split into three "
          "regimes (Figure 9b). Only 115 contacts (11.7%) fall below "
          "3.7 A, where the metal approaches the ring atoms closely enough "
          "to overlap with the pi system - 12 lie at or below 2.5 A, in "
          "eta-coordination range, and 45 of the 115 are simultaneously "
          "classified as "
          "bridge-direct, i.e. the metal is also bonded to a ring atom; "
          "203 contacts (20.7%) lie at 3.7-4.5 A, and 663 (67.6%) are "
          "longer than 4.5 A, with a median closest metal...ring-atom "
          "distance of 4.81 A. The short contacts are the chemically "
          "decisive ones - eta6-arene coordination at one end and "
          "classical cation–π contacts at the other, whose energetics has "
          "been examined by free-energy calculations of protein-ligand "
          "cation–π interactions{c:cationpi_ddg} - whereas the majority "
          "are ring-over-metal stacks at van der Waals separation, "
          "relevant to scoring functions but not to covalent "
          "metal–π bonding. Two remarks concern the reliability of very "
          "short contacts. First, a short d_centroid does not imply "
          "penetration of the ring: d_centroid = 1.7 A corresponds to "
          "metal...carbon distances of ~2.2 A, i.e. normal eta6 "
          "coordination-bond lengths (Fe...C = 2.04 A in ferrocene), so "
          "the shortest contacts in the census are established "
          "organometallic geometries rather than anomalies. Second, the "
          "genuine crystallographic risks are metal misassignment - the "
          "classic Mg2+/water confusion{c:leonarski_mg_2017} - and density "
          "misplacement at low resolution; both are addressed by "
          "established metal-site validation practice{c:zheng_cmm_2024} "
          "and mitigated here by our QC criteria (resolution <= 3.0 A, "
          "occupancy >= 0.5), by consistency of the deposited metal "
          "geometries with PDB-wide metal-ligand distance statistics for "
          "the relevant elements,{c:harding_nak_2002} and by the fact that "
          "the six case structures are refined at 1.09-1.64 A, where "
          "coordinate uncertainty is far smaller than the contacts "
          "discussed. The projection-based criterion treats"
          "alkali and alkaline-earth ions on the same footing as "
          "transition metals (their close ring-atom approaches are ionic "
          "edge contacts, not chelation). The per-bucket "
          "distance, offset, and angle distributions are shown in "
          "Figures S1-S4."),
    ("P", "Because the classification rests on a single geometric "
          "threshold, we tested how much of the census depends on it "
          "(Table S10). The angular coordinate is largely redundant with "
          "the projection: the median theta of the 981 face-on contacts is "
          "22.6 deg, 90% are below 34.3 deg and only 18 (1.8%) exceed "
          "45 deg, so adding a theta <= 45 deg gate removes 18 contacts "
          "and moves the face-on fraction from 7.4% to 7.3%. Only three "
          "face-on contacts tilt beyond 60 deg, all with imidazole rings, "
          "and one of them - a Zn whose closest ring atom is 1.24 A away "
          "(PDB 2VZ5, theta 87.5 deg) - is a clear model error rather "
          "than a face contact; we flag such outliers in the database "
          "instead of removing them. Moving the offset cutoff over the "
          "1.5-3.0 A range changes the size of the face-on class by a "
          "factor of five (321 to 1,569 contacts) but leaves K, Zn and Na "
          "in the top three metals at every cutoff, although their "
          "internal order changes (Zn leads below 2.0 A, K above 2.5 A). "
          "Restricting the census to high-quality data (resolution <= "
          "2.0 A and metal occupancy >= 0.9; 5,344 contacts) gives a "
          "face-on fraction of 7.3% (entry-clustered 95% CI 6.2-8.4), "
          "indistinguishable from the archive-wide value. The face-on "
          "fraction does rise with worsening resolution across the "
          "archive (4.3% below 1.5 A, 8.2% at 2.6-3.0 A), but that trend "
          "is between targets and not within them: across 44 targets with "
          "at least 15 contacts and at least four distinct resolution "
          "values, the median within-target correlation between "
          "resolution and face-on status is r = 0.01 (19% positive). The "
          "face-on population is therefore not a low-resolution "
          "artifact; it is a property of particular binding sites, which "
          "Section 3.9 dissects."),
    ("H2", "3.3. Most Contacts Are Protein-Bridged"),
    ("P", "Classifying the non-porphyrin contacts by the coordination "
          "environment of the metal shows that metal-mediated binding is "
          "the dominant configuration (Figure 2): 7,854 contacts (59.4%) "
          "involve a metal that is coordinated by protein residues with "
          "the ligand ring nearby (bridge-near; 3,614 structures), and "
          "2,034 contacts (15.4%) are bridge-direct, i.e. the metal "
          "simultaneously coordinates a protein residue and a ligand ring "
          "atom (950 structures). Only 3,001 contacts (22.7%) are "
          "ligand-held (the metal belongs to the ligand or is coordinated "
          "by water/ions, e.g. the Mg2+ of Mg-ATP complexes; 964 "
          "structures), and 342 (2.6%) lack a coordination annotation. "
          "Bridge-direct contacts concentrate in "
          "metalloenzyme-inhibitor complexes - the carbonic "
          "anhydrase/benzenesulfonamide{c:supuran_ca_2016}, farnesyl "
          "diphosphate synthase/bisphosphonate"
          "{c:ebetino_bisphosphonates_2011}, and HDAC/hydroxamate "
          "families - and "
          "constitute the chemically unambiguous 'metal anchors the drug' "
          "configuration (Table 2); the zinc-binding group is likewise the "
          "pharmacophore around which inhibitors of zinc "
          "enzymes are most often designed.{c:geurs_zbg_2023!} For "
          "medicinal chemistry this defines "
          "a concrete design grammar: the metal-binding group fixes the "
          "inhibitor pose, and the metal-to-ring geometry then determines "
          "which subpockets the aromatic decoration can reach (Figure "
          "8A). Conversely, the promiscuity of metal sites as ligand "
          "anchors makes off-target metal binding a selectivity "
          "liability, so the protein environment around the metal must "
          "supply the selectivity filter."),
    ("FIG", "fig3_bridging.png"),
    ("TABLE", 2),
    ("H2", "3.4. Targets: Metal-Aromatic Contacts Enrich in Metalloenzyme "
           "Drug Targets"),
    ("P", "Attributing every contact to the protein chain that "
          "coordinates the metal and clustering at the UniProt level "
          "(1,296 targets, of which 1,225 carry at least one "
          "protein-coordinated contact; Figure 3a, Table S5) shows that "
          "the census is "
          "dominated "
          "by established drug targets rather than incidental metal "
          "sites. "
          "Carbonic anhydrase II alone contributes 674 contacts in 631 "
          "entries (123 of them with DrugBank-annotated ligands); "
          "lysine-specific demethylase 4A (252 contacts), the "
          "metallo-beta-lactamases VIM-1 and VIM-2 (404 contacts "
          "combined; antimicrobial resistance targets), autotaxin (171), "
          "tubulin (166), and cytochrome c oxidase subunit 1 (165) "
          "complete the top group. 304 hit entries (3.8%) lack a UniProt "
          "mapping, and metal sites of multi-chain complexes that are "
          "not protein-coordinated (e.g. ribosomal Mg2+) are labeled "
          "'(multi-chain complex)' and excluded from target ranking to "
          "avoid subunit inflation. For protein-type analysis, "
          "protein-family annotations from Pfam{c:mistry_pfam_2021} - a "
          "curated database of protein families represented by profile "
          "hidden Markov models - were retrieved for all hit entries "
          "(families per polymer entity, with chain identifiers) from "
          "the RCSB Data API (GraphQL), and each metal-coordinating chain was "
          "assigned to one of 41 broad protein types by keyword rules "
          "over its Pfam family names (e.g. 'Carb_anhydrase' to Carbonic "
          "anhydrase, '7tm' to GPCR; the complete rule list is provided "
          "in the analysis code). Contacts were attributed to the "
          "protein type of the coordinating chain, and contacts without "
          "protein coordination inherited the Pfam types of their entry. "
          "The same clustering restricted to "
          "DrugBank-annotated ligands is shown in Figure 3b. The target "
          "list also extends beyond classical metalloenzymes into "
          "signaling receptors: 42 entries with G-protein-coupled-"
          "receptor-related titles contain metal contacts, a context "
          "recently reviewed by Zou et al., who document how Na+ and "
          "other ions allosterically modulate GPCR ligand "
          "binding.{c:zou_gpcr_2021} At the protein-type level, the "
          "contacts span 940 Pfam families, which collapse into 41 broad "
          "types; "
          "carbonic anhydrases are almost exclusively Zn-bound, the "
          "photosynthetic apparatus is dominated by the Mg of "
          "chlorophylls, ribosomal contacts are almost entirely Mg, and "
          "proteases and dehydrogenases are Zn-rich (Figure 4, Table "
          "S9). This class-level metal specificity turns metal identity "
          "into a target-class signature rather than a random property: "
          "Zn classes coordinate inhibitors through their catalytic "
          "metal, Mg classes bind cofactor or structural metals near "
          "ligand rings, and Mn classes form their own cohort - exactly "
          "the feature a metal-aware machine-learning model should "
          "exploit when featurizing binding sites."),
    ("FIG", "fig7_targets.png"),
    ("FIG", "fig_classes.png"),
    ("H2", "3.5. Metal Specificity: K, Na, and Zn Enrich the Face-On "
           "Class; Cu Does Not"),
    ("P", "The face-on fraction varies strongly between metals (Figure "
          "5). Among metals with at least 20 contacts, K (12.8%), Zn "
          "(10.9%), and Na (10.8%) show the highest face-on fractions, "
          "followed by Fe (8.0%), Ni (7.1%), Mg (4.5%), and Mn (1.7%), "
          "while Co, Cu, Au, Mo, Sr, Rb, Cr, V, W, and Os have none or "
          "almost none. This ordering is chemically coherent: soft, "
          "fully coordinated d10 cations (Zn2+, Cd2+) and hard, "
          "hydrated alkali cations (K+, Na+) engage aromatic π systems "
          "as cations - a preference consistent with the cation–π "
          "binding-energy ordering of simple "
          "cations.{c:mecozzzi} K+ and Na+ cation–π "
          "contacts are also reminiscent of the aromatic residues that "
          "line potassium-selective channels{c:doyle_kchannel_1998} - "
          "whereas open-shell transition metals approach "
          "aromatic rings through attached donor atoms (edge-on). The "
          "most instructive observation concerns copper: in an analysis "
          "without the porphyrin exclusion, Cu appears as the dominant "
          "face-on metal (57.7% of its contacts under the projection "
          "criterion); the entire signal "
          "originates from the CuB site of cytochrome c oxidase, where "
          "Cu+ sits 4.5 A above the porphyrin macrocycle of heme a3. "
          "Once porphyrin-family ligands are excluded, the Cu face-on "
          "fraction drops to 2.0% (3 of 149 contacts, all with projections "
          "just inside the ring radius and modest tilts of 34-49 deg). "
          "Geometry-resolved censuses of metal-aromatic interactions "
          "therefore need to treat metal-coordinating macrocycles "
          "explicitly. For inhibitor design, the practical consequence "
          "is that face-on metal–π engagement is a realistic option "
          "mainly at alkali and d10 cation sites, whereas open-shell "
          "metal sites will usually require a coordinating anchor - a "
          "distinction that determines which scaffolds can exploit a "
          "given metal site. The metal is nevertheless a coarse "
          "predictor: within a single metal species the face-on fraction "
          "of individual targets ranges from 0 to 73% (Section 3.9)."),
    ("FIG", "fig4_geomclass.png"),
    ("H2", "3.6. Drug Subset: 235 Structures with Approved Drugs"),
    ("P", "DrugBank annotation{c:wishart_drugbank_2018} of all aromatic "
          "ligand components (Table S4) shows that 468 contacts in 235 "
          "structures involve approved drugs, with Mg (225 contacts, 120 "
          "structures) and Zn (128 contacts in 66 structures) dominating (Figure 6b, "
          "Table S8). The "
          "category census and the top approved-drug ligands are shown "
          "in Figure 6a and Figure 6c (Table S7). The "
          "top approved-drug ligands are the bisphosphonates zoledronic "
          "acid (66 contacts) and risedronate (27), both anchored to the "
          "Mg2+/Mn2+ pair of farnesyl diphosphate synthase by their "
          "phosphonate groups while the imidazole/pyridine rings hang "
          "nearby{c:ebetino_bisphosphonates_2011}; tetracycline-class "
          "and other antibiotics, adenine, and tacrine complete the top "
          "group. Drug-experimental ligands contribute 1,392 contacts in "
          "653 structures, including metalloporphyrin therapeutics and "
          "catechol/phenanthroline metal-binding scaffolds. Geometry adds "
          "a distinction that the ligand census alone does not make: 36 "
          "of the 468 approved-drug contacts (7.7%) are face-on, and "
          "they are contributed by only 11 of the 73 approved drugs (22 "
          "structures) - face-on engagement is the exception even within "
          "the drug subset. The face-on contacts concentrate on Zn (25 of "
          "128 contacts, 19.5%) rather than on Mg (9 of 225, 4.0%), and "
          "the individual cases are instructive: roflumilast stacks its "
          "dichloropyridine ring over the catalytic Zn2+ of "
          "phosphodiesterase 4 (d_centroid 5.26 A, theta 19-21 deg), "
          "pentostatin (2'-deoxycoformycin) lies 3.7-4.0 A above Zn in "
          "adenosine deaminase (theta 32-34 deg), and risedronate "
          "presents the face of its pyridine ring to the Mg2+ of "
          "farnesyl diphosphate synthase (4.8-5.0 A, theta 29 deg) while "
          "its phosphonates anchor the metal pair. The cofactor subset "
          "shows the same selectivity: ATP (14.4% of 382 contacts), FAD "
          "(15.2% of 33) and NADP (14.4% of 132) place an adenine or "
          "flavin face over a metal in a substantial minority of their "
          "complexes, whereas ADP (0 of 82) and GDP (1.7% of 230) do "
          "not, i.e. the geometry depends on which nucleotide and which "
          "metal site rather than on the nucleotide class. These subsets "
          "provide directly reusable starting points for metal-mediated "
          "drug design, and computational tools for predicting the binding "
          "pose of metal-binding pharmacophores are beginning to "
          "appear.{c:karges_2022!}"),
    ("FIG", "fig5_drugs.png"),
    ("H2", "3.7. Affinity Association: A Large Apparent Effect That Is "
           "Mostly Target Composition"),
    ("P", "Joining the PDBbind v2020 indexes with our classification "
          "yields affinity data for 19,443 general-set and 5,316 "
          "refined-set complexes (Table 3, Figure 7; the general-set box "
          "plots are shown in Figure S5, and the permutation tests in "
          "Table S6). In the refined set "
          "(all Kd/Ki-derived), complexes whose ligand makes a "
          "bridge-near metal contact have the highest median affinity "
          "(-log Kd/Ki = 7.52, n = 379), significantly above both the "
          "metal-free control (6.74, n = 2,400; median difference +1.16, "
          "permutation p < 0.0001) and the metal-present but "
          "contact-free control (6.36, +1.16 log units as well, p < "
          "0.0001). Bridge-direct complexes (n = 55) are also above the "
          "metal-free control (+0.70, p = 0.0496). The association is "
          "reproduced in the general set (+0.4 to +1.2 log units) and "
          "within the Kd- and IC50-only strata, although the strongest "
          "subgroup switches between bridge-near and bridge-direct, and "
          "the Ki-only stratum shows near-equal medians (7.46 vs 7.42). "
          "These differences most likely reflect target-family "
          "composition across measure strata rather than absence of the "
          "association, and we therefore tested the association with the "
          "target held fixed (Section 2.6). Affinities were converted to "
          "within-target percentile ranks (985 UniProt targets with at "
          "least four complexes in the general set, 36 protein types) and "
          "group labels were permuted within target. The bridge-near "
          "advantage over the metal-present but contact-free control "
          "survives this matching in both sets and at both levels of "
          "stratification (general set: +0.053 percentile units, "
          "p < 0.0001; refined set: +0.062, p < 0.0001; protein-type "
          "strata: +0.075 and +0.115, both p < 0.0001), and the stricter "
          "paired analysis - only targets with at least three complexes "
          "per group, median of within-target median differences - agrees "
          "(general set +0.37 log units over 25 targets, permutation "
          "p = 0.010; refined set +0.75 over 5 targets, p = 0.005). The "
          "advantage over metal-free complexes, by contrast, collapses "
          "once the target is matched (+0.036 percentile, p = 0.014 in "
          "the general set but +0.029, p = 0.43 in the refined set), and "
          "the bridge-direct group becomes indistinguishable from both "
          "controls in the general set (+0.034, p = 0.30; +0.043, "
          "p = 0.14). We therefore "
          "revise the interpretation of the uncorrected comparison: the "
          "large global difference (+1.16 log units) is largely a "
          "target-composition effect, and the part that survives matching "
          "is a modest association between affinity and a protein-bound "
          "metal that holds a ligand ring nearby. A geometry-resolved "
          "exploratory contrast points in the same direction but is "
          "underpowered: entry-level complexes containing at least one "
          "face-on contact have a higher median affinity than those with "
          "only edge-on contacts in the general set (+0.48 log units, "
          "n = 160 vs 1,003, p = 0.009) but not in the refined set "
          "(+0.25, n = 36 vs 398, p = 0.40). We report the matched "
          "contrasts as the appropriate null model for any claim that "
          "metal-mediated contacts enhance affinity, and provide them in "
          "Tables S13 and S15. The classified "
          "complexes are also immediate training material for machine "
          "learning: metal identity, coordination sphere, ligand ring "
          "type, and the geometric descriptors reported here provide "
          "structural features that complement the descriptors used by "
          "current affinity models."),
    ("FIG", "fig_pdbbind_refined_2020.png"),
    ("TABLE", 3),
    ("H2", "3.8. Case Studies Across the Metal–π Continuum"),
    ("P", "Six high-resolution structures (1.09-1.64 A) span the observed "
          "geometry space (Figure 8). {b:We walk down the d_centroid "
          "scale from electrostatic to covalent.} At the classical "
          "cation–π end, Na+ lies {b:3.68} A above an aromatic ring of "
          "lysozyme {b:(PDB 9GOG)} (Figure 8a) and the Mg2+ of "
          "ADP-ribose glycohydrolase ARH3 sits {b:3.29} A above the "
          "adenine ring of a bound NAD analogue {b:(PDB 7ARW)} "
          "(Figure 8b) - both drug-target systems. 3-"
          "hydroxyanthranilate dioxygenase with a DrugBank-annotated "
          "picolinate ligand {b:(PDB 4HSJ; d_centroid 2.57 A; Figure "
          "8c)} extends the series to Fe, {b:and the} nicking "
          "endonuclease/imidazole complex {b:(PDB 9QGV; 1.55 A, "
          "d_centroid 2.06 A; Figure 8d)} shows the tightest "
          "non-organometallic Zn–π contact of the census{b: - already "
          "within coordination-bonding range of the ring.} At the "
          "edge-on end, carbonic anhydrase II with benzeneselenol "
          "{b:(PDB 6HWZ; 1.64 A; Figure 8e)} shows the canonical "
          "bridge-direct configuration: the selenolate coordinates Zn2+ "
          "{b:(2.47 A)} with the ring hanging to the side {b:(d_centroid "
          "4.29 A).} The extreme face-on {b:case} is a cupin protein (a "
          "small beta-barrel metalloprotein family) metallocated with a "
          "Ru(eta6-p-cymene) fragment {b:(PDB 9XS9)} (Figure 8f), in "
          "which the Ru sits 1.68 A above the arene centroid - an eta6 "
          "coordination bond (all six arene carbons coordinated to the "
          "metal), i.e. the covalent end of the metal–π continuum; "
          "organoruthenium arene fragments are themselves pharmacophores "
          "of anticancer drug candidates.{c:yan_ruarene_2005} {b:Read "
          "together, the six cases show that contact geometry is "
          "dictated by the coordination chemistry of the metal: a "
          "back-bonding organometallic fragment forms an eta6 bond, a "
          "tetrahedrally saturated Zn2+ site forces an edge-on approach, "
          "and a hydrated alkali cation stacks electrostatically - so "
          "d_centroid is not a free parameter but a direct readout of "
          "the metal's coordination state, which is what makes it an "
          "informative feature for classifying metal sites in "
          "structure-based drug design. It should be kept in mind that "
          "all six cases were chosen at the tight end of the distribution "
          "(1.68-3.68 A): the median face-on contact of the census lies at "
          "4.83 A, and two thirds of the face-on population are beyond "
          "4.5 A (Section 3.2, Figure 9b), so the cases illustrate the "
          "chemistry of the inner regime rather than the bulk of the "
          "class.}"),
    ("FIG", "fig6_cases.png"),
    ("H2", "3.9. Target Class, Coordination Sphere and Ring Chemistry Set "
           "the Odds of Face-On Engagement"),
    ("P", "Metal identity explains only part of the variation in "
          "Section 3.5, so we asked which other properties of a contact "
          "predict its geometry. Stratification by the Pfam-derived "
          "protein type of the coordinating chain (Table 4, Figure 9a) "
          "shows that the face-on fraction spans two orders of magnitude "
          "between target classes: highest in deaminases (37.8% of 254 "
          "contacts), proteases (24.5% of 805), phosphodiesterases (18.5% "
          "of 422) and 2OG-Fe oxygenases (11.0% of 154); lowest or absent "
          "in dehydrogenases (0.5% of 594), carbonic anhydrases (0.2% of "
          "975), histone demethylases, tubulins and dehydratases (0). The "
          "protease signal is entirely due to matrix metalloproteinases "
          "(6.4% without them). Target-level stratification is starker: "
          "of 1,225 targets with protein-coordinated contacts, 1,046 "
          "(85.4%) have no face-on contact, and 72 of the 112 targets "
          "with >= 20 contacts have none; the equal-target-weighted mean "
          "face-on fraction (7.5%) matches the contact-weighted one "
          "(7.4%), so the census value is not driven by over-represented "
          "targets - face-on engagement is a property of particular "
          "binding sites, not of metal-ligand complexes in general."),
    ("P", "The cleanest contrast is a pair of zinc families (Table 4). "
          "Matrix metalloproteinases present inhibitor aryl substituents "
          "to the catalytic zinc in the majority of contacts - 60.5% "
          "overall (164 of 271; entry-clustered 95% CI 52.2-69.1), "
          "ranging from 57.7% (MMP-12) to 73.3% (MMP-3) across five "
          "isoforms with >= 18 contacts each (Table S16) - whereas "
          "carbonic anhydrase II, the most frequently represented target "
          "in the census (620 entries, 662 contacts), almost never does "
          "(0.3%, 2 of 662; CI 0.0-0.8). "
          "Both bind Zn2+ through three histidines, so the difference "
          "reflects the shape of the pocket through which a ring must "
          "pass, not the ion, its charge or its donor set; it is visible "
          "at atomic resolution in the batimastat complex of MMP-12 (PDB "
          "1JK3, 1.09 A), where the thiophene ring sits 4.90 A above the "
          "Zn2+ (offset 1.50 A, theta 17.8 deg) while both hydroxamate "
          "oxygens remain bonded to the same zinc. A metal–π term "
          "calibrated on one zinc enzyme will therefore be systematically "
          "wrong for the other, and the aryl-over-metal pose is a "
          "concrete objective for metal-aware docking, because it is "
          "populated by DrugBank-annotated inhibitor series."),
    ("P", "Parsing the deposited coordination spheres (Figure 9c) "
          "identifies two determinants. A free coordination site favors "
          "face-on approach: 8.8% at coordination number <= 4 vs 4.8% at "
          "CN >= 6 (entry-clustered 95% CI 7.7-9.9 vs 3.8-5.7; "
          "Mantel-Haenszel OR 1.21 over 11 metal strata, p = 0.005) - "
          "strong for open-shell Fe (17.1% vs 3.0%) and absent for "
          "closed-shell Zn (10.2% vs 10.4%), which can stack over a ring "
          "without a vacancy. Donor chemistry matters more than donor "
          "number: N-only ligation 16.0% vs O-only 3.6% (N+O 8.2%, "
          "S-containing 4.4%; OR 2.23 over 10 metal strata, p < 0.0001; "
          "within Zn 16.4% vs 1.5%). O-only sites are largely Mg2+/Ca2+ "
          "carboxylate-water centers (64% of O-only contacts are Mg) "
          "approached edge-on between hydration shells; N-only sites are "
          "buried histidine clusters presenting a hydrophobic face - a "
          "distinction a purely distance-based scoring term cannot "
          "capture."),
    ("P", "Ring chemistry adds a third, weaker axis (Figure 9d): "
          "carbocycles 9.4% vs N-heteroarenes 6.1% (OR 1.22 after "
          "stratification over metals, p = 0.005), widest in the "
          "cation–π regime (K 18.7% vs 7.8%; Na 17.4% vs 5.9%) and "
          "closing for Zn (12.0% vs 10.3%) - an N-heteroarene carries a "
          "sigma-donating lone pair that engages the metal in the ring "
          "plane, and its limiting case, direct ring-atom bonding, is "
          "essentially incompatible with a face contact (45 of 2,034 "
          "bridge-direct contacts, 2.2%; 20 of the 45 are eta-type with "
          "metal...ring-atom distances below 2.3 A). A scaffold needing "
          "both features must anchor through a substituent, as the "
          "hydroxamates and bisphosphonates of Section 3.6 do. Read "
          "together, the three axes explain why the census-wide 7.4% "
          "describes no individual site well and why the metal-level "
          "ordering of Section 3.5, although robust to reclassification, "
          "is a coarse predictor: the largest face-on-rich class "
          "(proteases) and the largest face-on-free class (carbonic "
          "anhydrases) are both almost exclusively zinc. Metal–π terms "
          "should therefore be conditioned on coordination environment "
          "and pocket shape rather than on the element alone, and matter "
          "most in matrix metalloproteinase, deaminase and "
          "phosphodiesterase inhibitor complexes and in the 115 "
          "inner-sphere contacts - the only ones in which the metal "
          "genuinely penetrates the ring's electronic envelope."),
    ("FIG", "fig9_determinants.png"),
    ("TABLE", 4),
    ("H1", "4. Conclusions"),
    ("P", "We present the first geometry-resolved census of metal ions "
          "contacting the aromatic rings of non-polymeric ligands across "
          "the PDB. Four results stand out. (i) Among 13,231 "
          "non-porphyrin contacts, 92.6% are edge-on (coordination-"
          "driven or ionic edge contacts) and only 7.4% are face-on "
          "metal–π interactions; the face-on class is bimodal in "
          "distance, with 115 contacts below 3.7 A - eta6 coordination "
          "and tight cation–π contacts - and 663 beyond 4.5 A, where the "
          "ring simply stacks over the metal at van der Waals "
          "separation. (ii) Approximately 75% "
          "of contacts involve a protein-coordinated metal - metal "
          "mediation of ligand binding is a dominant configuration, not "
          "an edge case - and 15.4% are direct protein-metal-ligand "
          "bridges. (iii) Face-on contacts are enriched for K, Na, and "
          "Zn, whereas the apparent face-on enrichment of Cu in "
          "unfiltered analyses is entirely a porphyrin-macrocycle "
          "artifact; but the metal is a weak predictor compared with the "
          "binding site: 85% of the 1,225 protein targets that bind a "
          "metal through protein residues have no "
          "face-on contact at all, and two zinc families, the matrix "
          "metalloproteinases (60.5%) and the carbonic anhydrases (0.3%), "
          "sit at opposite extremes. (iv) The apparent affinity advantage "
          "of metal-contacted complexes is largely target composition; a "
          "target-matched analysis retains only a modest association "
          "between affinity and a protein-bound metal holding a ligand "
          "ring nearby (+0.05 to +0.06 within-target percentile, "
          "p < 0.0001). The census, the classified structure library, and "
          "the per-contact database are released as machine-readable "
          "supporting material and constitute ready-made benchmark sets "
          "for scoring functions and force fields, whose metal–π terms "
          "can now be fitted against, and validated on, experimentally "
          "observed geometry distributions. Concretely, the 981 face-on "
          "and 12,250 edge-on contacts provide the target geometry "
          "distributions against which metal-center parameterization "
          "schemes (e.g. MCPB.py{c:li_merz_mcpb_2016}), bonded or "
          "dummy-atom models, and pair-specific Lennard-Jones extensions "
          "such as the 12-6-4 potential{c:li_1264_2013} - all embedded "
          "in the broader framework of classical metal-ion "
          "modeling{c:li_merz_review_2017} - can be fitted and validated "
          "by MD simulation. Because the distribution is stratified by "
          "target class and coordination environment (Section 3.9), such "
          "terms should be parameterized against the relevant subset "
          "rather than against the pooled census."),
    ("P", "Beyond force fields, the census supports machine-learning "
          "approaches to metal-mediated drug discovery at three levels. "
          "First, the 24-field database - metal identity, coordination "
          "sphere, ligand ring type, geometry descriptors, and bridging "
          "configuration - is a labeled structural dataset for models "
          "that predict whether a metal site will engage a ligand ring, "
          "and for metal-aware featurization of binding pockets in "
          "affinity and selectivity prediction. The target-class "
          "structure of Section 3.9 sets a concrete performance target "
          "for such models: a classifier that predicts face-on versus "
          "edge-on from the pocket alone would have to reproduce a "
          "0-73% range across protein families, and the four features "
          "that carry most of that signal - coordination number, donor "
          "chemistry, ring class and pocket class - are all available "
          "from deposited coordinates. Second, the target "
          "clustering shows that these features span pharmacologically "
          "diverse families, from metalloenzymes to signaling "
          "receptors, providing the target-structural characteristics "
          "needed to generalize metal-aware models across families "
          "rather than fitting one metalloenzyme at a time. Third, "
          "metal ions modulate ligand binding even in targets without "
          "catalytic metals - most prominently in G protein-coupled "
          "receptors, the family targeted by roughly one third of "
          "marketed drugs{c:zou_gpcr_2021} - implying that the design "
          "grammar extracted here can support novel drug-discovery "
          "efforts wherever a metal site borders a ligand-binding "
          "pocket. The porphyrin-artifact lesson of Section 3.5 is "
          "directly relevant to this agenda: curation of the training "
          "data, not only the model, determines whether metal–π "
          "signals are real."),
    ("H1", "Supporting Information Available"),
    ("P_SI", "Supporting Information (Word): SI Methods (classification "
              "criteria, porphyrin keyword list, curated "
              "cofactor/additive lists, target-attribution and protein-"
              "type algorithms); SI "
              "Tables S1-S18 (screening and QC statistics; metal list; "
              "aromatic patterns; curated lists; top targets; top drug "
              "ligands; PDBbind permutation tests; protein-type metal "
              "distribution; criterion sensitivity; ring chemistry; "
              "coordination spheres; target-matched affinity contrasts; "
              "target-class face-on summary; rank-normalized affinity "
              "contrasts; MMP isoforms); "
              "SI Figures S1-S5 (distance histograms per metal bucket). "
              "Machine-readable data: SI_Tables.xlsx (19 sheets, including "
              "all 57,578 contacts with 24 columns and the complete "
              "ligand/target/PDBbind tables), per-figure source data "
              "(CSV), the core SQLite database, and the complete "
              "pipeline code."),
]

PARAGRAPHS = [(k, _mark(_fix(c)) if isinstance(c, str) else c)
              for k, c in PARAGRAPHS]

# ---- v4 paragraph splits in the Methods (long monoliths) -------------------
_SPLIT_AT = ["Formally, for a metal at position m",
             "Entries whose only contacts are porphyrin-excluded"]


def _split_paras(paras, marks):
    out = []
    for kind, content in paras:
        if isinstance(content, str):
            hit = next((m for m in marks if m in content), None)
            if hit:
                head, tail = content.split(hit, 1)
                out.append((kind, head.rstrip()))
                out.append((kind, hit + tail))
                continue
        out.append((kind, content))
    return out


PARAGRAPHS = _split_paras(PARAGRAPHS, _SPLIT_AT)

# ---- v4 rewrite of Results and Conclusions (sections_v4.py) ----------------
from sections_v4 import SECTIONS  # noqa: E402

_i = next(i for i, (k, c) in enumerate(PARAGRAPHS)
          if k == "H1" and str(c).startswith("3. Results"))
_j = next(i for i, (k, c) in enumerate(PARAGRAPHS)
          if k == "H1" and str(c).startswith("Supporting Information Available"))
PARAGRAPHS = PARAGRAPHS[:_i] + list(SECTIONS) + PARAGRAPHS[_j:]

ASSOCIATED = [
    ("H1", "Associated Content"),
    ("H2", "Supporting Information"),
    ("P_SI", "The Supporting Information is available free of charge at "
             "https://pubs.acs.org/journal/jcimd (placeholder link) and "
             "comprises: JCIM_SI.docx (SI Methods, SI Tables S1-S18, and "
             "SI Figures S1-S5), SI_Tables.xlsx (machine-readable "
             "supporting tables; 19 sheets), SI_contacts.csv (the full "
             "57,578-row contact table), and per-figure source data "
             "(CSV)."),
    ("H2", "Data Availability"),
    ("P_SI", "The classified contact database (SQLite, a single-file "
             "relational database; 57,578 contacts x "
             "24 columns), the complete analysis pipeline, all analysis "
             "scripts, and the classified structure library are provided "
             "in the submission package and will be deposited in a "
             "public repository (Zenodo, https://zenodo.org) with a DOI "
             "upon acceptance. Structure coordinates were retrieved from "
             "the RCSB PDB (https://www.rcsb.org). The PDBbind v2020 "
             "index data are not redistributed (license; "
             "https://www.pdbbind-plus.org.cn); only derived per-complex "
             "classifications and affinity values are included."),
    ("H1", "Author Information"),
    ("P_SI", "Corresponding Author: [to be completed by the authors]."),
    ("P_SI", "Author Contributions: [to be completed by the authors]."),
    ("H1", "Acknowledgments"),
    ("P_SI", "The authors thank the RCSB PDB for maintaining the archive "
             "and the open Search/Data APIs. [Funding information to be "
             "completed by the authors.]"),
]

ASSOCIATED = [(k, _mark(_fix(c)) if isinstance(c, str) else c)
              for k, c in ASSOCIATED]

# ---------------------------------------------------------------- builder --
doc = Document()
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)


def add_hyperlink(paragraph, url, text):
    from docx.oxml import OxmlElement
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/"
        "relationships/hyperlink", is_external=True)
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), r_id)
    r_el = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    r_el.append(rPr)
    t_el = OxmlElement("w:t")
    t_el.text = text
    r_el.append(t_el)
    hl.append(r_el)
    paragraph._p.append(hl)


REV_BLUE = RGBColor(0x00, 0x00, 0xCC)


def add_text_with_citations(par, text, cite_map):
    """Split {c:...} and {b:...} tokens and revision markers.

    \\x01 / \\x02 toggle blue revision colouring (see revision_marks.py).
    """
    import re
    parts = re.split(r"(\{c:[^}]+\}|\{b:[^}]+\})", text)
    blue = False
    for p in parts:
        if not p:
            continue
        if p.startswith("{c:") and p.endswith("}"):
            keys = p[3:-1].split("+")
            # a trailing "!" marks a citation added in this revision (blue)
            new_cite = any(k.endswith("!") for k in keys)
            keys = [k.rstrip("!") for k in keys]
            nums = sorted(cite_map[k] for k in keys)
            # compress consecutive ranges
            runs_s = str(nums[0])
            for a, b in zip(nums, nums[1:]):
                if b == a + 1:
                    continue
                runs_s += f",{a}"
            runs_s += f",{nums[-1]}" if len(nums) > 1 else ""
            run = par.add_run(" " + runs_s)
            run.font.superscript = True
            if blue or new_cite:
                run.font.color.rgb = REV_BLUE
        elif p.startswith("{b:") and p.endswith("}"):
            for seg in re.split(f"([{START}{END}])", p[3:-1]):
                if not seg:
                    continue
                if seg == START:
                    blue = True
                    continue
                if seg == END:
                    blue = False
                    continue
                run = par.add_run(seg)
                run.bold = True
                if blue:
                    run.font.color.rgb = REV_BLUE
        else:
            for seg in re.split(f"([{START}{END}])", p):
                if not seg:
                    continue
                if seg == START:
                    blue = True
                    continue
                if seg == END:
                    blue = False
                    continue
                run = par.add_run(seg)
                if blue:
                    run.font.color.rgb = REV_BLUE


# build citation map by scanning the text in order
import re
order = []
for kind, content in PARAGRAPHS:
    if not isinstance(content, str):
        continue
    for m in re.finditer(r"\{c:([^}]+)\}", content):
        for k in m.group(1).split("+"):
            k = k.rstrip("!")   # trailing ! = citation added in v3
            if k not in order:
                order.append(k)
for k in order:
    if k not in REFS:
        raise SystemExit(f"unverified reference key: {k}")
cite_map = {k: i + 1 for i, k in enumerate(order)}

# ---- title block ----
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = t.add_run("How Metal Ions Engage Aromatic Ligands: "
                "A Geometry-Resolved PDB Census")
run.bold = True
run.font.size = Pt(14)
run.font.color.rgb = REV_BLUE  # revised title, marked for the revision draft

a = doc.add_paragraph()
a.alignment = WD_ALIGN_PARAGRAPH.CENTER
a.add_run("[Author list to be completed]").italic = True

note = doc.add_paragraph()
note_run = note.add_run(
    "[Draft revision v3: language-polished; text that was added or revised in "
    "this revision is printed in blue.]")
note_run.italic = True
note_run.font.size = Pt(9)
note_run.font.color.rgb = REV_BLUE

h = doc.add_paragraph()
h.add_run("ABSTRACT: ").bold = True
# JCIM guidelines (Manuscript Text Components): "An abstract of 3-4
# sentences is required". Four sentences, ~170 words.
abstract = (
    "We report a geometry-resolved census of metal-ion contacts to the "
    "aromatic rings of non-polymeric ligands across the Protein Data Bank: "
    "aromatic substructure and exact-formula metal queries identified "
    "37,337 candidate structures and 13,231 non-porphyrin contacts "
    "(981 face-on, 7.4%; 12,250 edge-on, 92.6%), with 44,347 macrocycle or "
    "metal-embedded contacts archived separately. About 75% of the contacts "
    "involve a protein-coordinated metal, including 2,034 direct "
    "protein-metal-ring bridges, and face-on contacts are enriched for K, "
    "Zn and Na, whereas the apparent copper enrichment of unfiltered "
    "analyses comes entirely from the CuB site of cytochrome c oxidase. "
    "Face-on contacts are bimodal in distance (115 below 3.7 A, 663 beyond "
    "4.5 A) and reflect the binding site rather than the ion: 85% of "
    "1,225 targets have none, and matrix metalloproteinases (60.5%) and "
    "carbonic anhydrases (0.3%) sit at opposite extremes. A target-matched "
    "analysis of PDBbind shows that the apparent affinity advantage of "
    "metal-contacted complexes is mostly target composition, with a modest "
    "within-target effect; the contact database, geometry descriptors and "
    "analysis code are released as a benchmark for metal–π scoring terms "
    "and force-field development.")
h2 = doc.add_paragraph()
add_text_with_citations(h2, START + _fix(abstract) + END, cite_map)

# ---- main text ----
for kind, content in PARAGRAPHS:
    if kind == "H1":
        doc.add_heading(content, level=1)
    elif kind == "H2":
        head = doc.add_heading(content, level=2)
        if any(h in content for h in NEW_HEADINGS):
            for run in head.runs:
                run.font.color.rgb = REV_BLUE
    elif kind == "P":
        par = doc.add_paragraph()
        add_text_with_citations(par, content, cite_map)
    elif kind == "P_SI":
        par = doc.add_paragraph()
        add_text_with_citations(par, content, cite_map)
    elif kind == "FIG":
        stem = content[:-4]
        cap = dict(FIGURES)[content]
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(FIG / content), width=Inches(6.3))
        cap_p = doc.add_paragraph()
        r = cap_p.add_run(cap)
        r.font.size = Pt(9)
        if content == "fig9_determinants.png":
            r.font.color.rgb = REV_BLUE
    elif kind == "TABLE":
        pass  # tables added after text assembly

# ---- tables (inserted at end of Results; referenced as Table 1-3) ----
doc.add_heading("Tables", level=1)
cap_p = doc.add_paragraph()
cap_p.add_run(TABLE1_CAPTION).bold = True
t1 = doc.add_table(rows=1, cols=2)
t1.style = "Light Grid Accent 1"
t1.rows[0].cells[0].text = "Item"
t1.rows[0].cells[1].text = "Value"
for k, v in [("entries_with_aromatic_ligand", "92,487"),
             ("entries_with_configured_metal", "37,337"),
             ("entries with a non-porphyrin contact <= 6 A", "5,107"),
             ("total contacts (all)", "57,578"),
             ("contacts excluded (porphyrin-family/embedded)", "44,347"),
             ("contacts face-on", "981 (7.4%)"),
             ("contacts edge-on", "12,250 (92.6%)"),
             ("bridge-direct", "2,034 (15.4% of non-excluded)"),
             ("bridge-near", "7,854 (59.4%)"),
             ("ligand-held", "3,001 (22.7%)"),
             ("unannotated", "342 (2.6%)")]:
    t1.add_row().cells[0].text, t1.add_row
# simpler: rebuild rows
data1 = [("PDB archive (experimental entries)", "261,301"),
         ("entries_with_aromatic_ligand", "92,487"),
         ("entries_with_configured_metal", "37,337"),
         ("entries with a non-porphyrin contact <= 6 A", "5,107"),
         ("total contacts (all)", "57,578"),
         ("contacts excluded (porphyrin-family/embedded)", "44,347"),
         ("contacts face-on", "981 (7.4%)"),
         ("   face-on, inner regime (< 3.7 A)", "115 (11.7% of face-on)"),
         ("   face-on, stacked regime (3.7-4.5 A)", "203 (20.7%)"),
         ("   face-on, outer regime (> 4.5 A)", "663 (67.6%)"),
         ("contacts edge-on", "12,250 (92.6%)"),
         ("bridge-direct", "2,034 (15.4%)"),
         ("bridge-near", "7,854 (59.4%)"),
         ("ligand-held", "3,001 (22.7%)"),
         ("unannotated", "342 (2.6%)"),
         ("face-on at CN <= 4", "8.8% (vs 4.8% at CN >= 6)"),
         ("face-on, carbocyclic rings", "9.4% (vs 6.1% N-heteroarenes)")]
t1._tbl.getparent().remove(t1._tbl)
t1 = doc.add_table(rows=1, cols=2)
t1.style = "Light Grid Accent 1"
t1.alignment = WD_TABLE_ALIGNMENT.CENTER
t1.rows[0].cells[0].text = "Item"
t1.rows[0].cells[1].text = "Count"
for k, v in data1:
    c = t1.add_row().cells
    c[0].text, c[1].text = k, v
    if k.strip().startswith("face-on at CN") or \
            k.strip().startswith("face-on, carbocyclic") or \
            k.strip().startswith("face-on, inner") or \
            k.strip().startswith("face-on, stacked") or \
            k.strip().startswith("face-on, outer"):
        for cell in c:
            for par in cell.paragraphs:
                for run in par.runs:
                    run.font.color.rgb = REV_BLUE

cap_p = doc.add_paragraph()
_c2 = cap_p.add_run(TABLE2_CAPTION)
_c2.bold = True
_c2.font.color.rgb = REV_BLUE
t2 = doc.add_table(rows=1, cols=4)
t2.style = "Light Grid Accent 1"
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
t2.autofit = False
for i, h in enumerate(["Bridging class", "Decision rule (parameters)",
                       "Contacts", "Entries"]):
    t2.rows[0].cells[i].text = h
for cls, rule, n, e in [
        ("bridge-direct",
         ">= 1 protein partner AND min_dist <= 2.8 A (the metal also "
         "touches an atom of the contacted ring)", "2,034", "950"),
        ("bridge-near",
         ">= 1 protein partner AND min_dist > 2.8 A (ring within "
         "d_centroid <= 6.0 A)", "7,854", "3,614"),
        ("ligand-held",
         ">= 1 deposited partner, none of them protein (held by the "
         "ligand, water or ions); d_centroid <= 6.0 A", "3,001", "964"),
        ("unannotated", "no struct_conn metalc record; "
                        "d_centroid <= 6.0 A", "342", "194")]:
    c = t2.add_row().cells
    c[0].text, c[1].text, c[2].text, c[3].text = cls, rule, n, e
    for cell in c:
        for par in cell.paragraphs:
            for run in par.runs:
                run.font.color.rgb = REV_BLUE
for i, w in enumerate([Inches(1.0), Inches(3.3), Inches(0.85), Inches(0.75)]):
    for cell in t2.columns[i].cells:
        cell.width = w
    t2._tbl.tblGrid.findall(qn("w:gridCol"))[i].set(qn("w:w"), str(int(w.twips)))
_layout2 = OxmlElement("w:tblLayout")
_layout2.set(qn("w:type"), "fixed")
t2._tbl.tblPr.append(_layout2)

cap_p = doc.add_paragraph()
_c4 = cap_p.add_run(TABLE3_CAPTION)
_c4.bold = True
t3 = doc.add_table(rows=1, cols=3)
t3.style = "Light Grid Accent 1"
t3.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, h in enumerate(["Group", "general PL n (median -logK)",
                       "refined n (median -logK)"]):
    t3.rows[0].cells[i].text = h
for g, gn, gm, rn, rm in [
        ("bridge-near", 930, 7.22, 379, 7.52),
        ("bridge-direct", 233, 6.33, 55, 6.05),
        ("no-contact", 3394, 6.46, 1042, 6.36),
        ("no-metal", 9367, 6.79, 2400, 6.74)]:
    c = t3.add_row().cells
    c[0].text = g
    c[1].text = f"{gn:,} ({gm:.2f})"
    c[2].text = f"{rn:,} ({rm:.2f})"

cap_p = doc.add_paragraph()
_c4 = cap_p.add_run(TABLE4_CAPTION)
_c4.bold = True
_c4.font.color.rgb = REV_BLUE
data4 = [("Deaminase", "254", "96", "37.8 (28.6-47.3)", "Zn"),
         ("Protease (MMP-dominated)", "805", "197", "24.5 (19.6-30.0)", "Zn"),
         ("Phosphodiesterase", "422", "78", "18.5 (12.7-24.3)", "Zn"),
         ("Hydrolase", "206", "26", "12.6 (3.8-23.0)", "Zn"),
         ("2OG-Fe(II) oxygenase", "154", "17", "11.0 (2.7-18.8)", "Fe"),
         ("Protein kinase", "108", "4", "3.7 (0.0-9.3)", "Mg"),
         ("Histone deacetylase", "177", "4", "2.3 (0.0-6.4)", "Zn"),
         ("Dehydrogenase", "594", "3", "0.5 (0.0-1.4)", "Zn"),
         ("Carbonic anhydrase", "975", "2", "0.2 (0.0-0.5)", "Zn"),
         ("Tubulin", "189", "0", "0 (0-0)", "Mg"),
         ("Histone demethylase", "412", "0", "0 (0-0)", "Zn"),
         ("Dehydratase/lyase", "273", "0", "0 (0-0)", "Mn")]
t4 = doc.add_table(rows=1, cols=5)
t4.style = "Light Grid Accent 1"
t4.alignment = WD_TABLE_ALIGNMENT.CENTER
t4.autofit = False
for i, h in enumerate(["Protein type", "Contacts", "Face-on",
                       "Face-on % (95% CI)", "Main metal"]):
    t4.rows[0].cells[i].text = h
for row in data4:
    c = t4.add_row().cells
    for i, v in enumerate(row):
        c[i].text = v
        for par in c[i].paragraphs:
            for run in par.runs:
                run.font.color.rgb = REV_BLUE
for i, w in enumerate([Inches(1.85), Inches(0.8), Inches(0.8),
                       Inches(1.5), Inches(0.85)]):
    for cell in t4.columns[i].cells:
        cell.width = w
    grid_col = t4._tbl.tblGrid.findall(qn("w:gridCol"))[i]
    grid_col.set(qn("w:w"), str(int(w.twips)))
from docx.oxml import OxmlElement
_layout = OxmlElement("w:tblLayout")
_layout.set(qn("w:type"), "fixed")
t4._tbl.tblPr.append(_layout)

# ---- Associated content / author info / acknowledgments ----
for kind, content in ASSOCIATED:
    if kind == "H1":
        doc.add_heading(content, level=1)
    elif kind == "H2":
        doc.add_heading(content, level=2)
    else:
        par = doc.add_paragraph()
        add_text_with_citations(par, content, cite_map)

# ---- references ----
from refs_acs import reference_runs  # noqa: E402

doc.add_heading("References", level=1)
for i, key in enumerate(order, 1):
    ref = REFS[key]
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.35)
    par.paragraph_format.first_line_indent = Inches(-0.35)
    for text, style in reference_runs(ref, i):
        r = par.add_run(text)
        r.font.size = Pt(10)
        if "italic" in style:
            r.italic = True
        if "bold" in style:
            r.bold = True
        if key in NEW_KEYS:  # reference added or corrected in this revision
            r.font.color.rgb = REV_BLUE
    url = ref.get("url") or (f"https://doi.org/{ref['doi']}"
                             if ref.get("doi") else
                             f"https://pubmed.ncbi.nlm.nih.gov/"
                             f"{ref.get('pmid')}/")
    add_hyperlink(par, url, url)
    par.paragraph_format.space_after = Pt(4)

out = OUTDIR / "JCIM_manuscript.docx"
doc.save(out)
print("manuscript ->", out)
print("references cited:", len(order))











