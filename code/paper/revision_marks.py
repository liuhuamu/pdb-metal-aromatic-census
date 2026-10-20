#!/usr/bin/env python3
"""Revision bookkeeping for the v3 manuscript (deep-analysis revision).

TEXT_FIXES  : (old, new) language/logic corrections applied at build time.
MARKS       : (paragraph-identifying substring, [fragments to colour blue]).
FULL_PARAS  : paragraphs that are entirely new (whole paragraph in blue).
NEW_HEADINGS: headings that are new (blue + bold).

The blue markers are the private-use characters U+F8F0 (start) and U+F8F1 (end);
they are consumed by the run builder in make_manuscript.py.
"""
from __future__ import annotations

# reference keys added in the v3 revision (printed in blue in the list)
NEW_KEYS = {
    # added in v3.6 (2022-2023 literature)
    "cipdb_2023", "geurs_zbg_2023", "moianos_2023", "wang_gpdock_2023",
    "augoff_2022", "karges_2022",
    # pre-existing entries whose DOI pointed to the wrong paper (v3.6 repair)
    "metalpdb", "mecozzzi",
    # JCIM references added in v4.3
    "vina_2021", "biometall_2021", "binana2_2022", "metalhawk_2024",
    "oxidstates_2022",
    # flagship-journal references added in v4.5 (Nature / Science / Cell)
    "waldron_nature_2009", "dougherty_science_1996", "cell_nmda_2018",
    # cation-pi references added after ref. 9 in v4.9
    "dougherty_chemrev_2025", "mu_molecules_2024",
}

START = "\uf8f0"
END = "\uf8f1"

# ---------------------------------------------------------------- fixes -----
TEXT_FIXES = [
    ("wereparsed", "were parsed"),
    ("criterion treatsalkali", "criterion treats alkali"),
    ("drug-experimental ligands contribute", "Drug-experimental ligands contribute"),
    ("(Figure 8A)", "(Figure 8e)"),
    ("artefact", "artifact"),
    ("ring centre", "ring center"),
    ("centres surrounded", "centers surrounded"),
    ("signalling", "signaling"),
    ("is favoured where", "is favored where"),
    ("Only 3,001 contacts (22.7%) are ligand-held",
     "A further 3,001 contacts (22.7%) are ligand-held"),
    ("and Zn (128, 66) dominating",
     "and Zn (128 contacts in 66 structures) dominating"),
    ("The projection-based criterion treatsalkali and alkaline-earth ions on "
     "the same footing as transition metals (their close ring-atom approaches "
     "are ionic edge contacts, not chelation).",
     "The projection-based criterion treats alkali and alkaline-earth ions on "
     "the same footing as transition metals, so that their close ring-atom "
     "approaches are scored as ionic edge contacts rather than as chelation."),
    ("which Section 3.9 dissects.", "which Section 3.9 examines."),
    ("Two further annotations were derived for the analyses of Sections 3.6 "
     "and 3.9.", "Two further annotations were derived for the analyses of "
                 "Section 3.9."),
    ("Separates Two Physical Regimes", "Separates Two Geometric Regimes"),
    ("Case Studies: The Face-On Distance Continuum",
     "Case Studies Across the Metal\u2013\u03c0 Continuum"),
    ("3.9. Target Class, Coordination Sphere and Ring Chemistry Set the Odds "
     "of Face-On Engagement",
     "3.9. Determinants of Face-On Engagement: Target Class, Coordination "
     "Sphere and Ring Chemistry"),
    ("These differences most likely reflect target-family composition across "
     "measure strata rather than absence of the association, and we therefore "
     "tested the association with the target held fixed (Section 2.6).",
     "These stratum differences most likely reflect the target composition of "
     "each measure stratum rather than a dependence on the affinity type, and "
     "we therefore repeated the comparison with the target held fixed "
     "(Section 2.6)."),
    ("In the refined set (all Kd/Ki-derived), complexes whose ligand makes a "
     "bridge-near metal contact have the highest median affinity",
     "In the uncorrected comparison in the refined set (all Kd/Ki-"
     "derived), complexes whose ligand makes a bridge-near metal contact have "
     "the highest median affinity"),
    ("(general set: +0.053 percentile units, p < 0.0001; refined set: +0.062, "
     "p < 0.0001; protein-type strata: +0.075 and +0.115, both p < 0.0001)",
     "(general set: +0.053 within-target percentile units, i.e. about five "
     "percentile points, p < 0.0001; refined set: +0.062, p < 0.0001; "
     "protein-type strata: +0.075 and +0.115, both p < 0.0001)"),
    ("whereas Cu shows no face-on contacts at all: its apparent face-on "
     "enrichment in an unfiltered analysis",
     "whereas Cu shows almost none (2.0%): its apparent face-on enrichment in "
     "an unfiltered analysis"),
    ("artifact; but the metal is a weak predictor compared with the binding "
     "site:",
     "artifact. The metal itself is, however, a weak predictor compared with "
     "the binding site:"),
    ("carbonic anhydrase II, the most frequently represented target in the "
     "census (620 entries, 662 contacts), almost never does",
     "carbonic anhydrase II, the most frequently represented target in the "
     "census (620 entries with a protein-coordinated contact, 662 contacts; "
     "entry-level fallback attribution as used in Section 3.4 gives 674 "
     "contacts in 631 entries), almost never does"),
    ("because it is populated by DrugBank-annotated inhibitor series.",
     "because the pose is populated by many independent inhibitor series of "
     "this family."),
]

# ---------------------------------------------------------------- marks -----
_RING = ("The face-on class itself is bimodal in distance: only 115 contacts "
         "(11.7%) lie below 3.7 A, where the metal reaches into the ring's "
         "coordination sphere, while 663 (67.6%) are longer-range "
         "ring-over-metal stacks beyond 4.5 A.")
_CONC = ("Face-on engagement is concentrated rather than uniform: 85% of the "
         "1,225 protein targets that bind a metal through protein residues "
         "have none, and two zinc families sit at opposite extremes (matrix "
         "metalloproteinases 60.5%, carbonic anhydrases 0.3%), so the "
         "geometry reflects the binding site rather than the ion.")
_AFF = ("and a target-matched re-analysis of PDBbind shows that the apparent "
        "affinity advantage of metal-contacted complexes is mostly target "
        "composition, with a modest within-target advantage over "
        "metal-present contact-free controls (p < 0.0001)")
_DRUG = "36 of their 468 contacts are face-on"

# --- explicit, parameterized bridging-class ladder (v3.1) -------------------
_BR_OLD = (
    "were parsed, and each contact was assigned a bridging class: "
    "bridge-direct if the metal is coordinated by protein residues and "
    "additionally forms a coordination contact with a ligand ring atom "
    "(min_dist <= 2.8 A), bridge-near if the metal is protein-coordinated "
    "with the ligand ring within 6 A, ligand-held if the metal is held by the "
    "ligand itself or by water/other ions, and unannotated if no coordination "
    "record exists.")
_BR_LADDER = (
    "(i) bridge-direct - the metal has at least one protein partner and its "
    "closest approach to any atom of the contacted ring is <= 2.8 A (the "
    "parameter min_dist, the upper bound of a metal-ligand coordination bond "
    "for the elements considered); (ii) bridge-near - the metal has at least "
    "one protein partner, but no atom of the contacted ring lies within 2.8 A; "
    "(iii) ligand-held - the metal has at least one deposited partner and none "
    "of them is a protein residue, i.e. the ion is held by the ligand itself, "
    "by water or by another ion; and (iv) unannotated - no metalc record "
    "exists in struct_conn.")
_BR_PARTNER = (
    "A partner counts as protein if its residue name is one of the 20 "
    "standard amino-acid codes; water, nucleic-acid residues and other "
    "ligands do not count.")
_BR_PARAMS = (
    "All four classes share the contact definition d_centroid <= 6.0 A, and "
    "metals embedded in the ligand are removed before the ladder is applied, "
    "so the classification is fully specified by three quantities: "
    "d_centroid (6.0 A, contact cutoff), min_dist (2.8 A, ring-atom bond) and "
    "the deposited struct_conn metalc partner list. Precedence matters: a "
    "metal that both touches an atom of the ring and is protein-bound is "
    "bridge-direct, never bridge-near.")
_BR_NEW = ("were parsed into a partner list, and each contact was assigned to "
           "the first matching class of a four-step ladder (Table 2): "
           + _BR_LADDER + " " + _BR_PARTNER + " " + _BR_PARAMS)

_N3_OLD = ("7,854 contacts (59.4%) involve a metal that is coordinated by "
           "protein residues with the ligand ring nearby (bridge-near; 3,614 "
           "structures), and 2,034 contacts (15.4%) are bridge-direct, i.e. "
           "the metal simultaneously coordinates a protein residue and a "
           "ligand ring atom (950 structures). A further 3,001 contacts "
           "(22.7%) are ligand-held (the metal belongs to the ligand or is "
           "coordinated by water/ions, e.g. the Mg2+ of Mg-ATP complexes; 964 "
           "structures)")
_N3_NEW = ("7,854 contacts (59.4%) involve a metal that is coordinated by at "
           "least one protein residue while the ligand ring lies nearby "
           "(bridge-near: >= 1 protein partner and min_dist > 2.8 A; 3,614 "
           "structures), and 2,034 contacts (15.4%) are bridge-direct, i.e. "
           "the metal coordinates a protein residue and simultaneously "
           "approaches an atom of the contacted ring to within 2.8 A (950 "
           "structures). A further 3,001 contacts (22.7%) are ligand-held "
           "(>= 1 deposited partner, none of them a protein residue - the "
           "metal belongs to the ligand or is coordinated by water/ions, e.g. "
           "the Mg2+ of Mg-ATP complexes; 964 structures)")

TEXT_FIXES += [(_BR_OLD, _BR_NEW), (_N3_OLD, _N3_NEW),
               ("the dominant configuration (Figure 2): 7,854 contacts",
                "the dominant configuration (Figure 2; definitions and "
                "thresholds in Section 2.4 and Table 2): 7,854 contacts")]

# --- figure/table citation order and panel-letter consistency (v3.3) --------
TEXT_FIXES += [
    # Table 1 must be cited before Table 2 (ACS: numbered in citation order)
    ("yielded 37,337 candidate entries.",
     "yielded 37,337 candidate entries (Table 1)."),
    # Figure 9 must not be cited before Figures 2-8: point to Table 1 instead
    ("(Table S10, Figure 9b)", "(Table S10, Table 1)"),
    ("the permutation tests in Table S6)", "the permutation tests in Tables S6a and S6b)"),
    ("and split into three regimes (Figure 9b)",
     "and split into three regimes (Table 1)"),
    # Figure 8 must not be cited before Figures 2-7
    ("(Figure 8e)", "(Section 3.8)"),
    # panel letters in captions: uppercase -> lowercase (matches the panels
    # drawn in the figures and the in-text citations)
    ("(A) Top targets by total non-embedded contacts. (B) Top targets "
     "restricted to DrugBank-annotated ligands.",
     "(a) Top targets by total non-embedded contacts. (b) Top targets "
     "restricted to DrugBank-annotated ligands."),
    ("(A) Heatmap of contact counts for the top protein types",
     "(a) Heatmap of contact counts for the top protein types"),
    ("(B) Metal-bucket composition (A d10, B alkali/alkaline-earth, C other "
     "transition, D noble) per protein type.",
     "(b) Metal-bucket composition (A d10, B alkali/alkaline-earth, C other "
     "transition, D noble) per protein type."),
    ("(A) Contacts by ligand category (log scale)",
     "(a) Contacts by ligand category (log scale)"),
    ("(B) Approved-drug contacts by metal",
     "(b) Approved-drug contacts by metal"),
    ("(C) Top approved-drug ligands by contact count",
     "(c) Top approved-drug ligands by contact count"),
    # SI table enumeration: list the S1-S18 tables in their actual order
    ("SI Tables S1-S18 (screening and QC statistics; metal list; aromatic "
     "patterns; curated lists; top targets; top drug ligands; PDBbind "
     "permutation tests; protein-type metal distribution; criterion "
     "sensitivity; ring chemistry; coordination spheres; target-matched "
     "affinity contrasts; target-class face-on summary; rank-normalized "
     "affinity contrasts; MMP isoforms)",
     "SI Tables S1-S18 (screening and QC statistics; metal list; aromatic "
     "patterns; ligand classification; top targets; PDBbind permutation "
     "tests; top approved-drug ligands; approved-drug contacts by metal; "
     "protein-type metal distribution; criterion sensitivity; ring "
     "chemistry; coordination spheres; target-matched affinity contrasts; "
     "target-class face-on summary; rank-normalized affinity contrasts; MMP "
     "isoforms; curated cofactor/additive lists; database variable "
     "definitions)"),
]

MARKS = [
    # abstract
    ("Metal ions are integral to numerous drug targets", [_RING, _CONC, _DRUG, _AFF]),
    # methods 2.2 / 2.3 / 2.6 / 2.7 additions
    ("All 37,336 available mmCIF files",
     ["Two further annotations were derived for the analyses of Section 3.9.",
      "First, the chemical composition of each contacted ring was "
      "reconstructed by mapping its atom names to the elements deposited in "
      "atom_site (type_symbol) of the same ligand component, which classifies "
      "a ring as carbocyclic, N-heteroaromatic, or S/O-heteroaromatic and "
      "yields its size.",
      "Second, the coordination sphere of the metal was reconstructed from "
      "the struct_conn metalc records: the number of partners (coordination "
      "number, CN), the number of protein, water, self-ligand and "
      "other-ligand partners, and the elements of the protein donor atoms "
      "inferred from residue identity (HIS/LYS/ARG and Trp N; "
      "Asp/Glu/Ser/Thr/Tyr/Asn/Gln O; Cys/Met S)."]),
    ("A 'contact' is defined throughout as any metal-ring pair",
     ["Because a projection criterion could in principle admit contacts in "
      "which the metal lies inside the ring radius but almost in the ring "
      "plane, we report a sensitivity analysis over the offset cutoff (1.5, "
      "2.0, 2.5 and 3.0 A), with and without an additional angular gate "
      "(theta <= 45 deg or <= 30 deg), and we resolve the face-on class into "
      "three distance regimes: inner (< 3.7 A, the range in which the metal "
      "reaches the ring atoms), stacked (3.7-4.5 A) and outer (> 4.5 A) "
      "(Table S10, Figure 9b)."]),
    ("The PDBbind v2020 index files",
     ["Target-family composition is a strong confounder of this comparison, "
      "so we repeated it in two target-matched designs.",
      "(a) Stratified comparison: within every UniProt target (and, "
      "separately, every Pfam-derived protein type) that contains at least "
      "three complexes of each group, the difference of group medians was "
      "computed, and significance was obtained by permuting group labels "
      "within the target (5,000 permutations); the reported statistic is the "
      "median of the within-target differences.",
      "(b) Rank-normalized comparison: for every target with at least four "
      "complexes the affinities were converted to within-target percentile "
      "ranks, and group means of these ranks were compared with a permutation "
      "test that shuffles labels within target (20,000 permutations), which "
      "keeps all complexes rather than only the matched strata. Both UniProt "
      "and Pfam-type strata are reported (Tables S13 and S15)."]),
    ("Entries with resolution worse than 3.0 A",
     ["Because contacts are clustered within entries (up to 48 per entry) and "
      "within targets (up to 662 for carbonic anhydrase II), all percentages "
      "in the target-level analyses of Sections 3.6 and 3.9 carry 95% "
      "confidence intervals from an entry-clustered bootstrap (2,000 "
      "resamples of entries), and contingency-style comparisons are reported "
      "as Mantel-Haenszel odds ratios stratified over metals."]),
    # results 3.1 addition
    ("The screen (Figure 1a) starts from the full archive",
     ["The archived set has the signature of covalent chelation rather than "
      "of a contact: the median metal...centroid distance is 3.24 A, the "
      "median closest metal...ring-atom distance is 2.04 A, and 43,906 of the "
      "44,347 contacts (99.0%) involve a metal embedded in the ligand itself, "
      "with Mg (28,229, chlorophylls) and Fe (14,310, hemes) accounting for "
      "96% of the contacts."]),
    # results 3.2 rewritten span
    ("Figure 1c defines the geometric quantities",
     ["Throughout, metal\u2013\u03c0 denotes the continuum of contacts between "
      "a metal ion and the \u03c0-electron system of an aromatic ring: at one "
      "end covalent eta6-arene coordination bonds, as in organometallic arene "
      "complexes and their anticancer scaffolds,",
      "at the other the purely electrostatic cation\u2013\u03c0 interaction "
      "of a solvated alkali cation above a ring face.",
      "The 13,231 contacts analyzed here sample this whole continuum, which "
      "is why we resolve them by geometry rather than by energy.",
      "three regimes (Table 1)",
      "The face-on class is therefore geometrically homogeneous but "
      "energetically not: its 981 members are spread over the whole 6 A "
      "window (median d_centroid 4.83 A, range 1.68-6.00 A) and split into "
      "three regimes (Figure 9b).",
      "Only 115 contacts (11.7%) fall below 3.7 A, where the metal approaches "
      "the ring atoms closely enough to overlap with the pi system - 12 lie at "
      "or below 2.5 A, in eta-coordination range, and 45 of the 115 are "
      "simultaneously classified as bridge-direct, i.e. the metal is also "
      "bonded to a ring atom; 203 contacts (20.7%) lie at 3.7-4.5 A, and 663 "
      "(67.6%) are longer than 4.5 A, with a median closest metal...ring-atom "
      "distance of 4.81 A.",
      "The short contacts are the chemically decisive ones - eta6-arene "
      "coordination at one end and classical cation\u2013\u03c0 contacts at "
      "the other",
      "whereas the majority are ring-over-metal stacks at van der Waals "
      "separation, relevant to scoring functions but not to covalent "
      "metal\u2013\u03c0 bonding."]),
    # results 3.4 clarification
    ("Attributing every contact to the protein chain",
     ["of which 1,225 carry at least one protein-coordinated contact"]),
    # results 3.5 caveat
    ("The face-on fraction varies strongly between metals",
     ["The metal is nevertheless a coarse predictor: within a single metal "
      "species the face-on fraction of individual targets ranges from 0 to "
      "73% (Section 3.9)."]),
    # results 3.6 additions
    ("DrugBank annotation",
     ["Geometry adds a distinction that the ligand census alone does not "
      "make: 36 of the 468 approved-drug contacts (7.7%) are face-on, and "
      "they are contributed by only 11 of the 73 approved drugs (22 "
      "structures) - face-on engagement is the exception even within the drug "
      "subset.",
      "The face-on contacts concentrate on Zn (25 of 128 contacts, 19.5%) "
      "rather than on Mg (9 of 225, 4.0%), and the individual cases are "
      "instructive: roflumilast stacks its dichloropyridine ring over the "
      "catalytic Zn2+ of phosphodiesterase 4 (d_centroid 5.26 A, theta 19-21 "
      "deg), pentostatin (2'-deoxycoformycin) lies 3.7-4.0 A above Zn in "
      "adenosine deaminase (theta 32-34 deg), and risedronate presents the "
      "face of its pyridine ring to the Mg2+ of farnesyl diphosphate synthase "
      "(4.8-5.0 A, theta 29 deg) while its phosphonates anchor the metal pair.",
      "The cofactor subset shows the same selectivity: ATP (14.4% of 382 "
      "contacts), FAD (15.2% of 33) and NADP (14.4% of 132) place an adenine "
      "or flavin face over a metal in a substantial minority of their "
      "complexes, whereas ADP (0 of 82) and GDP (1.7% of 230) do not, i.e. "
      "the geometry depends on which nucleotide and which metal site rather "
      "than on the nucleotide class."]),
    # results 3.7 revisions
    ("Joining the PDBbind v2020 indexes with our classification",
     ["In the uncorrected comparison in the refined set (all Kd/Ki-"
      "derived), complexes whose ligand makes a bridge-near metal contact "
      "have the highest median affinity",
      "These stratum differences most likely reflect the target composition "
      "of each measure stratum rather than a dependence on the affinity type, "
      "and we therefore repeated the comparison with the target held fixed "
      "(Section 2.6).",
      "Affinities were converted to within-target percentile ranks (985 "
      "UniProt targets with at least four complexes in the general set, 36 "
      "protein types) and group labels were permuted within target.",
      "The bridge-near advantage over the metal-present but contact-free "
      "control survives this matching in both sets and at both levels of "
      "stratification",
      "(general set: +0.053 within-target percentile units, i.e. about five "
      "percentile points, p < 0.0001; refined set: +0.062, p < 0.0001; "
      "protein-type strata: +0.075 and +0.115, both p < 0.0001)",
      "(general set +0.37 log units over 25 targets, permutation p = 0.010; "
      "refined set +0.75 over 5 targets, p = 0.005).",
      "The advantage over metal-free complexes, by contrast, collapses once "
      "the target is matched (+0.036 percentile, p = 0.014 in the general set "
      "but +0.029, p = 0.43 in the refined set), and the bridge-direct group "
      "becomes indistinguishable from both controls in the general set "
      "(+0.034, p = 0.30; +0.043, p = 0.14).",
      "We therefore revise the interpretation of the uncorrected comparison: "
      "the large global difference (+1.16 log units) is largely a "
      "target-composition effect, and the part that survives matching is a "
      "modest association between affinity and a protein-bound metal that "
      "holds a ligand ring nearby.",
      "A geometry-resolved exploratory contrast points in the same direction "
      "but is underpowered: entry-level complexes containing at least one "
      "face-on contact have a higher median affinity than those with only "
      "edge-on contacts in the general set (+0.48 log units, n = 160 vs "
      "1,003, p = 0.009) but not in the refined set (+0.25, n = 36 vs 398, "
      "p = 0.40).",
      "We report the matched contrasts as the appropriate null model for any "
      "claim that metal-mediated contacts enhance affinity, and provide them "
      "in Tables S13 and S15."]),
    # results 3.8 caveat
    ("Six high-resolution structures",
     ["It should be kept in mind that all six cases were chosen at the tight "
      "end of the distribution (1.68-3.68 A): the median face-on contact of "
      "the census lies at 4.83 A, and two thirds of the face-on population "
      "are beyond 4.5 A (Section 3.2, Figure 9b), so the cases illustrate the "
      "chemistry of the inner regime rather than the bulk of the class."]),
    # conclusions revisions
    ("We present the first geometry-resolved census",
     ["the face-on class is bimodal in distance, with 115 contacts below 3.7 "
      "A - eta6 coordination and tight cation\u2013\u03c0 contacts - and 663 "
      "beyond 4.5 A, where the ring simply stacks over the metal at van der "
      "Waals separation.",
      "The metal itself is, however, a weak predictor compared with the "
      "binding site: 85% of the 1,225 protein targets that bind a metal "
      "through protein residues have no face-on contact at all, and two zinc "
      "families, the matrix metalloproteinases (60.5%) and the carbonic "
      "anhydrases (0.3%), sit at opposite extremes.",
      "(iv) The apparent affinity advantage of metal-contacted complexes is "
      "largely target composition; a target-matched analysis retains only a "
      "modest association between affinity and a protein-bound metal holding "
      "a ligand ring nearby (+0.05 to +0.06 within-target percentile, "
      "p < 0.0001).",
      "Because the distribution is stratified by target class and "
      "coordination environment (Section 3.9), such terms should be "
      "parameterized against the relevant subset rather than against the "
      "pooled census."]),
    ("Beyond force fields, the census supports machine-learning approaches",
     ["The target-class structure of Section 3.9 sets a concrete performance "
      "target for such models: a classifier that predicts face-on versus "
      "edge-on from the pocket alone would have to reproduce a 0-73% range "
      "across protein families, and the four features that carry most of that "
      "signal - coordination number, donor chemistry, ring class and pocket "
      "class - are all available from deposited coordinates."]),
    # case-study caption
    ("Case studies spanning the geometry continuum",
     ["The six cases sample the tight tail of the face-on distribution: the "
      "median face-on contact of the full census lies at 4.83 A, and 67.6% of "
      "face-on contacts are beyond 4.5 A (Figure 9b)."]),
    # methods 2.4: explicit bridging-class ladder
    ("For every non-excluded contact",
     [_BR_LADDER, _BR_PARTNER, _BR_PARAMS]),
    # v3.3 reference-order fixes (pointers added/changed to restore
    # numbering in order of first citation)
    ("All queries were executed against the RCSB PDB Search API",
     ["candidate entries (Table 1)"]),
    ("A 'contact' is defined throughout as any metal-ring pair",
     ["(Table S10, Table 1)"]),

    ("Classifying the non-porphyrin contacts by the coordination environment",
     ["(Section 3.8)"]),
    ("Supporting Information (Word): SI Methods",
     ["SI Tables S1-S18 (screening and QC statistics; metal list; aromatic "
      "patterns; ligand classification; top targets; PDBbind permutation "
      "tests; top approved-drug ligands; approved-drug contacts by metal; "
      "protein-type metal distribution; criterion sensitivity; ring "
      "chemistry; coordination spheres; target-matched affinity contrasts; "
      "target-class face-on summary; rank-normalized affinity contrasts; MMP "
      "isoforms; curated cofactor/additive lists; database variable "
      "definitions)"]),
    # results 3.3: parameterized restatement at first mention
    ("Classifying the non-porphyrin contacts by the coordination environment",
     ["7,854 contacts (59.4%) involve a metal that is coordinated by at "
      "least one protein residue while the ligand ring lies nearby "
      "(bridge-near: >= 1 protein partner and min_dist > 2.8 A; 3,614 "
      "structures)",
      "2,034 contacts (15.4%) are bridge-direct, i.e. the metal coordinates a "
      "protein residue and simultaneously approaches an atom of the contacted "
      "ring to within 2.8 A (950 structures)",
      "A further 3,001 contacts (22.7%) are ligand-held (>= 1 deposited "
      "partner, none of them a protein residue - the metal belongs to the "
      "ligand or is coordinated by water/ions, e.g. the Mg2+ of Mg-ATP "
      "complexes; 964 structures)",
      "definitions and thresholds in Section 2.4 and Table 2"]),
]

# paragraphs that are wholly new (rendered blue end to end)
FULL_PARAS = [
    # introduction (v3.5): rewritten, and the metal-pi definition moved to 3.2
    "Metal ions are integral components of an estimated one third",
    "The contact that results is not a minor one.",
    "The answer matters for modeling, not merely for bookkeeping.",
    "Here we report a geometry-resolved census of metal ion contacts",
    "Metal identity explains only part of the variation described in "
    "Section 3.5",
    "The cleanest illustration is a pair of zinc families",
    "Which property of the metal site generates this difference?",
    "Ring chemistry adds a third, weaker axis",
    "Because the classification rests on a single geometric threshold",
    "What sets the odds of face-on engagement.",
]

# new headings (blue, bold)
NEW_HEADINGS = [
    "3.9. Determinants of Face-On Engagement",
    "3.2. A Projection-Based Classification Separates Two Geometric Regimes",
]















