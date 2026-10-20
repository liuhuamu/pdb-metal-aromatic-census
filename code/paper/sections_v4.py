#!/usr/bin/env python3
"""Results and Conclusions, v4: restructured paragraphs + added discussion.

Sentences retained from the previous version are left unmarked; every sentence
that is new or substantively rewritten is wrapped in the blue revision markers
(U+F8F0 / U+F8F1), so the delta of this rewrite is visible in the document.
"""
from __future__ import annotations

B = "\uf8f0"   # blue on
E = "\uf8f1"   # blue off


def blue(t: str) -> str:
    return B + t + E


SECTIONS = [
    ("H1", "3. Results and Discussion"),

    # ---------------------------------------------------------------- 3.1 --
    ("H2", "3.1. A Geometry-Resolved Census of 13,231 Contacts"),
    ("P",
     "The screen (Figure 1a) starts from the full archive of 261,301 "
     "experimental PDB entries (all methods; accessed 16 October 2026). Of "
     "these, 92,487 contain a non-polymeric ligand with at least one aromatic "
     "ring (37,877 distinct ligand components; Table S4), of which 37,337 also "
     "contain one of the 25 configured metals. Geometric analysis of all "
     "downloaded structures identified 57,578 metal-aromatic contacts within "
     "6 A, of which 44,347 involve porphyrin-family macrocycles or embedded "
     "metals and are excluded from the two-class census. The qualifying set "
     "comprises 13,231 non-porphyrin contacts in 5,107 entries (Figure 1b): "
     "981 face-on (7.4%) and 12,250 edge-on (92.6%)."),
    ("P",
     "Contacts and entries are different units: the 13,231 contacts are "
     "unevenly distributed over the 5,107 entries (median 2, mean 2.6, and "
     "maximum 48 contacts per entry; 2,345 entries contain exactly one "
     "contact). " +
     blue("That skew is not a bookkeeping detail. A single well-ordered "
          "metalloprotein can contribute dozens of contacts, so contact-level "
          "percentages are dominated by a few heavily crystallized systems; "
          "every proportion reported below therefore carries an "
          "entry-clustered confidence interval (Section 2.7), and the "
          "target-level analyses of Section 3.9 weight each protein equally "
          "rather than each contact.")),
    ("P",
     "The 44,347 excluded contacts are dominated by chlorophylls (CLA, CHL, "
     "CL7, BCB, and related; 26,496 contacts, mostly to Mg2+ of the "
     "photosynthetic apparatus) and hemes (HEM, HEC, HEA, SRM, and related; "
     "14,535 contacts, mostly to the embedded Fe). They are archived with the "
     "same geometric annotations so that macrocycle specialists can reuse "
     "them (Table 1). The archived set has the signature of covalent "
     "chelation rather than of a contact: the median metal...centroid "
     "distance is 3.24 A, the median closest metal...ring-atom distance is "
     "2.04 A, and 43,906 of the 44,347 contacts (99.0%) involve a metal "
     "embedded in the ligand itself, with Mg (28,229, chlorophylls) and Fe "
     "(14,310, hemes) accounting for 96% of the contacts. " +
     blue("Keeping the two populations apart changes conclusions, not only "
          "counts. In a tetrapyrrole the metal sits inside the ring system it "
          "coordinates, so its distance is a bond length and its angle is "
          "dictated by the macrocycle; pooling such contacts with genuine "
          "ones does not merely add noise, it manufactures geometry - an "
          "effect quantified in Section 3.5, where the same exclusion removes "
          "a spurious copper signal entirely.")),
    ("FIG", "fig1_funnel.png"),
    ("TABLE", 1),

    # ---------------------------------------------------------------- 3.2 --
    ("H2", "3.2. A Projection-Based Classification Separates Two Geometric "
           "Regimes"),
    ("P",
     "Throughout, metal–π denotes the continuum of contacts between a metal "
     "ion and the π-electron system of an aromatic ring: at one end covalent "
     "eta6-arene coordination bonds, as in organometallic arene complexes and "
     "their anticancer scaffolds,{c:yan_ruarene_2005} at the other the purely "
     "electrostatic cation–π interaction of a solvated alkali cation above a "
     "ring face.{c:dougherty_cationpi_2013} The 13,231 contacts analyzed here "
     "sample this whole continuum, which is why we resolve them by geometry "
     "rather than by energy. Figure 1c defines the geometric quantities and "
     "Figure 1d schematizes the two classes and the porphyrin exclusion; the "
     "underlying (offset, d_plane) positions of all 13,231 contacts are "
     "provided as Source Data. In the (offset, d_plane) plane the face-on "
     "class corresponds to the region left of the 2.5 A offset line, and the "
     "6 A cutoff bounds the point cloud along a quarter circle. The two "
     "classes separate cleanly: edge-on contacts populate the large-offset "
     "region (coordination-driven, e.g. a metal held by attached donor atoms "
     "with the ring hanging to the side), whereas face-on contacts occupy the "
     "region with projections inside the ring radius."),
    ("P",
     "The face-on class is therefore geometrically homogeneous but "
     "energetically not: its 981 members are spread over the whole 6 A window "
     "(median d_centroid 4.83 A, range 1.68-6.00 A) and split into three "
     "regimes (Table 1). Only 115 contacts (11.7%) fall below 3.7 A, where "
     "the metal approaches the ring atoms closely enough to overlap with the "
     "pi system - 12 lie at or below 2.5 A, in eta-coordination range, and 45 "
     "of the 115 are simultaneously classified as bridge-direct, i.e. the "
     "metal is also bonded to a ring atom; 203 contacts (20.7%) lie at "
     "3.7-4.5 A, and 663 (67.6%) are longer than 4.5 A, with a median "
     "closest metal...ring-atom distance of 4.81 A. The short contacts are "
     "the chemically decisive ones - eta6-arene coordination at one end and "
     "classical cation–π contacts at the other, whose energetics has been "
     "examined by free-energy calculations of protein-ligand cation–π "
     "interactions.{c:cationpi_ddg}"),
    ("P",
     blue("The three regimes are not interchangeable. Below 3.7 A the metal "
          "overlaps the pi system and the interaction is a coordination bond "
          "in all but name - the eta6-arene complexes and the 45 ring-bonded "
          "cases sit here - so its energy is governed by orbital overlap and "
          "charge transfer. Between 4.5 and 6 A, where two thirds of the "
          "face-on contacts lie, the ring face still points at the metal but "
          "no atom approaches closer than about 4.5 A; that is an "
          "electrostatic and dispersive contact, of the kind a scoring "
          "function should model with a soft, distance-decaying term rather "
          "than with a bond. Labeling all three regimes 'face-on' therefore "
          "hides an order-of-magnitude difference in interaction energy, "
          "which is why the per-contact distances are retained in the "
          "database.")),
    ("P",
     "Two remarks concern the reliability of very short contacts. First, a "
     "short d_centroid does not imply penetration of the ring: d_centroid = "
     "1.7 A corresponds to metal...carbon distances of ~2.2 A, i.e. normal "
     "eta6 coordination-bond lengths (Fe...C = 2.04 A in ferrocene), so the "
     "shortest contacts in the census are established organometallic "
     "geometries rather than anomalies. Second, the genuine crystallographic "
     "risks are metal misassignment - the classic Mg2+/water "
     "confusion{c:leonarski_mg_2017} - and density misplacement at low "
     "resolution; both are addressed by established metal-site validation "
     "practice{c:zheng_cmm_2024} and mitigated here by our QC criteria "
     "(resolution <= 3.0 A, occupancy >= 0.5), by consistency of the "
     "deposited metal geometries with PDB-wide metal-ligand distance "
     "statistics for the relevant elements,{c:harding_nak_2002} and by the "
     "fact that the six case structures are refined at 1.09-1.64 A, where "
     "coordinate uncertainty is far smaller than the contacts discussed."),
    ("P",
     blue("Because the entire classification rests on one geometric "
          "threshold, we asked how much of the census depends on it and "
          "whether the conclusions survive reclassification (Table S10).") +
     " The angular coordinate is largely redundant with the projection: the "
     "median theta of the 981 face-on contacts is 22.6 deg, 90% are below "
     "34.3 deg and only 18 (1.8%) exceed 45 deg, so adding a theta <= 45 deg "
     "gate removes 18 contacts and moves the face-on fraction from 7.4% to "
     "7.3%. Only three face-on contacts tilt beyond 60 deg, all with "
     "imidazole rings, and one of them - a Zn whose closest ring atom is "
     "1.24 A away (PDB 2VZ5, theta 87.5 deg) - is a clear model error rather "
     "than a face contact; we flag such outliers in the database instead of "
     "removing them."),
    ("P",
     "Moving the offset cutoff over the 1.5-3.0 A range "
     "changes the size of the face-on class by a factor of five (321 to "
     "1,569 contacts) but leaves K, Zn and Na in the top three metals at "
     "every cutoff, although their internal order changes (Zn leads below "
     "2.0 A, K above 2.5 A). Restricting the census to high-quality data "
     "(resolution <= 2.0 A and metal occupancy >= 0.9; 5,344 contacts) gives "
     "a face-on fraction of 7.3% (entry-clustered 95% CI 6.2-8.4), "
     "indistinguishable from the archive-wide value. The face-on fraction "
     "does rise with worsening resolution across the archive (4.3% below 1.5 "
     "A, 8.2% at 2.6-3.0 A), but that trend is between targets and not "
     "within them: across 44 targets with at least 15 contacts and at least "
     "four distinct resolution values, the median within-target correlation "
     "between resolution and face-on status is r = 0.01 (19% positive). The "
     "face-on population is therefore not a low-resolution artifact; it is a "
     "property of particular binding sites, which Section 3.9 examines."),

    # ---------------------------------------------------------------- 3.3 --
    ("H2", "3.3. Most Contacts Are Protein-Bridged"),
    ("P",
     "Classifying the non-porphyrin contacts by the coordination environment "
     "of the metal shows that metal-mediated binding is the dominant "
     "configuration (Figure 2; definitions and thresholds in Section 2.4 and "
     "Table 2): 7,854 contacts (59.4%) involve a metal that is coordinated "
     "by at least one protein residue while the ligand ring lies nearby "
     "(bridge-near: >= 1 protein partner and min_dist > 2.8 A; 3,614 "
     "structures), and 2,034 contacts (15.4%) are bridge-direct, i.e. the "
     "metal coordinates a protein residue and simultaneously approaches an "
     "atom of the contacted ring to within 2.8 A (950 structures). A further "
     "3,001 contacts (22.7%) are ligand-held (>= 1 deposited partner, none of "
     "them a protein residue - the metal belongs to the ligand or is "
     "coordinated by water/ions, e.g. the Mg2+ of Mg-ATP complexes; 964 "
     "structures), and 342 (2.6%) lack a coordination annotation."),
    ("P",
     "Bridge-direct contacts concentrate in metalloenzyme-inhibitor complexes "
     "- the carbonic anhydrase/benzenesulfonamide{c:supuran_ca_2016}, "
     "farnesyl diphosphate synthase/bisphosphonate"
     "{c:ebetino_bisphosphonates_2011}, and HDAC/hydroxamate families - and "
     "constitute the chemically unambiguous 'metal anchors the drug' "
     "configuration (Table 2); the zinc-binding group is likewise the "
     "pharmacophore around which inhibitors of zinc enzymes are most often "
     "designed.{c:geurs_zbg_2023!} For medicinal chemistry this defines a "
     "concrete design grammar: the metal-binding group fixes the inhibitor "
     "pose, and the metal-to-ring geometry then determines which subpockets "
     "the aromatic decoration can reach (Section 3.8). Conversely, the "
     "promiscuity of metal sites as ligand anchors makes off-target metal "
     "binding a selectivity liability, so the protein environment around the "
     "metal must supply the selectivity filter. " +
     blue("The three configurations are not equally informative for design. "
          "Ligand-held contacts (22.7%) describe cofactors and chelators that "
          "carry their own metal and say little about inhibitor design; "
          "bridge-near contacts (59.4%) are the working majority, in which "
          "the protein holds the ion while the ligand decorates the pocket; "
          "bridge-direct contacts (15.4%) are the only ones in which the "
          "metal-ligand bond and the metal-ring geometry are coupled, and "
          "therefore the only configuration in which anchor and metal–π terms "
          "must be parameterized together. The same split converts a "
          "statistic into a design question: a scaffold that anchors through "
          "a donor atom inherits an edge-on geometry (Section 3.9), so a "
          "face-on pose has to be built from the decoration rather than from "
          "the anchor.")),
    ("FIG", "fig3_bridging.png"),
    ("TABLE", 2),

    # ---------------------------------------------------------------- 3.4 --
    ("H2", "3.4. Targets: Metal-Aromatic Contacts Enrich in Metalloenzyme "
           "Drug Targets"),
    ("P",
     "Attributing every contact to the protein chain that coordinates the "
     "metal and clustering at the UniProt level (1,296 targets, of which "
     "1,225 carry at least one protein-coordinated contact; Figure 3a, Table "
     "S5) shows that the census is dominated by established drug targets "
     "rather than incidental metal sites. Carbonic anhydrase II alone "
     "contributes 674 contacts in 631 entries (123 of them with "
     "DrugBank-annotated ligands); lysine-specific demethylase 4A (252 "
     "contacts), the metallo-beta-lactamases VIM-1 and VIM-2 (404 contacts "
     "combined; antimicrobial resistance targets), autotaxin (171), tubulin "
     "(166), and cytochrome c oxidase subunit 1 (165) complete the top "
     "group. 304 hit entries (3.8%) lack a UniProt mapping, and metal sites "
     "of multi-chain complexes that are not protein-coordinated (e.g. "
     "ribosomal Mg2+) are labeled '(multi-chain complex)' and excluded from "
     "target ranking to avoid subunit inflation."),
    ("P",
     "For protein-type analysis, protein-family annotations from "
     "Pfam{c:mistry_pfam_2021} - a curated database of protein families "
     "represented by profile hidden Markov models - were retrieved for all "
     "hit entries (families per polymer entity, with chain identifiers) from "
     "the RCSB Data API (GraphQL), and each metal-coordinating chain was "
     "assigned to one of 41 broad protein types by keyword rules over its "
     "Pfam family names (e.g. 'Carb_anhydrase' to Carbonic anhydrase, '7tm' "
     "to GPCR; the complete rule list is provided in the analysis code). "
     "Contacts were attributed to the protein type of the coordinating "
     "chain, and contacts without protein coordination inherited the Pfam "
     "types of their entry. The same clustering restricted to "
     "DrugBank-annotated ligands is shown in Figure 3b."),
    ("P",
     "The target list also extends beyond classical metalloenzymes into "
     "signaling receptors: 42 entries with G-protein-coupled-receptor-related "
     "titles contain metal contacts, a context recently reviewed by Zou et "
     "al., who document how Na+ and other ions allosterically modulate GPCR "
     "ligand binding.{c:zou_gpcr_2021} " +
     blue("Metal-dependent pharmacology is not confined to class A GPCRs: on "
          "the NMDA receptor, a high-affinity extracellular Zn2+ site "
          "converges with proton inhibition on the same gating "
          "machinery,{c:cell_nmda_2018!} so a metal ion can shape the "
          "response to a ligand without contacting that ligand at all. ") +
     "At the protein-type level, the "
     "contacts span 940 Pfam families, which collapse into 41 broad types; "
     "carbonic anhydrases are almost exclusively Zn-bound, the "
     "photosynthetic apparatus is dominated by the Mg of chlorophylls, "
     "ribosomal contacts are almost entirely Mg, and proteases and "
     "dehydrogenases are Zn-rich (Figure 4, Table S9). This class-level "
     "metal specificity turns metal identity into a target-class signature "
     "rather than a random property: Zn classes coordinate inhibitors "
     "through their catalytic metal, Mg classes bind cofactor or structural "
     "metals near ligand rings, and Mn classes form their own cohort - "
     "exactly the feature a metal-aware machine-learning model should "
     "exploit when featurizing binding sites. " +
     blue("Two cautions follow from the composition of this list. First, the "
          "census is zinc-dominated (5,142 of 13,231 contacts, 39%), so "
          "Figure 4 is partly a map of zinc usage: classes that employ Zn as "
          "a catalytic or structural ion are over-represented, while classes "
          "that rely on Mg, Ca or Fe dominate other rows of the same figure. "
          "Second, the 41 types are deliberately coarse - 'protease' spans "
          "endopeptidases from four mechanistic families - so the clustering "
          "establishes where contacts occur, not why. Both caveats lead to "
          "the same question: if the metal is a target-class signature, how "
          "much of the geometry does the metal itself determine? Section 3.5 "
          "answers for the element and Section 3.9 for the site.")),
    ("FIG", "fig7_targets.png"),
    ("FIG", "fig_classes.png"),

    # ---------------------------------------------------------------- 3.5 --
    ("H2", "3.5. Metal Specificity: K, Na, and Zn Enrich the Face-On Class; "
           "Cu Does Not"),
    ("P",
     "The face-on fraction varies strongly between metals (Figure 5). " +
     blue("Among metals with at least 50 contacts, K (12.8%), Zn (10.9%), "
          "and Na (10.8%) show the highest face-on fractions, followed by Fe "
          "(8.0%), Ni (7.1%), Mg (4.5%), Cd (4.4%), and Ca (4.1%), while Co "
          "(0.3%), Au (0.0%), Mn (1.7%), and Cu (2.0%) are effectively "
          "edge-on only; rarer metals such as Ru (39.1% of only 23 contacts) "
          "are too sparsely sampled to rank.") +
     " This ordering is chemically "
     "coherent: soft, fully coordinated d10 cations (Zn2+, Cd2+) and hard, "
     "hydrated alkali cations (K+, Na+) engage aromatic π systems as cations "
     "- a preference consistent with the cation–π binding-energy ordering of "
     "simple cations.{c:mecozzzi} K+ and Na+ cation–π contacts are also "
     "reminiscent of the aromatic residues that line potassium-selective "
     "channels{c:doyle_kchannel_1998} - whereas open-shell transition metals "
     "approach aromatic rings through attached donor atoms (edge-on)."),
    ("P",
     "The most instructive observation concerns copper: in an analysis "
     "without the porphyrin exclusion, Cu appears as the dominant face-on "
     "metal (57.7% of its contacts under the projection criterion); the "
     "entire signal originates from the CuB site of cytochrome c oxidase, "
     "where Cu+ sits 4.5 A above the porphyrin macrocycle of heme a3. Once "
     "porphyrin-family ligands are excluded, the Cu face-on fraction drops "
     "to 2.0% (3 of 149 contacts, all with projections just inside the ring "
     "radius and modest tilts of 34-49 deg). Geometry-resolved censuses of "
     "metal-aromatic interactions therefore need to treat metal-coordinating "
     "macrocycles explicitly. " +
     blue("The lesson generalizes beyond copper. Any chemical search that "
          "does not exclude the macrocycle ranks metals by the abundance of "
          "porphyrin proteins rather than by the geometry of their ligand "
          "contacts, and the resulting ranking follows phylogeny - "
          "photosynthetic and respiratory systems - rather than chemistry. "
          "Because such a signal is large, systematic and chemically "
          "plausible, it is precisely the kind of artifact that survives "
          "casual inspection; excluding it requires an explicit structural "
          "criterion (Section 2.3), not a statistical correction.")),
    ("P",
     "For inhibitor design, the practical consequence is that face-on "
     "metal–π engagement is a realistic option mainly at alkali and d10 "
     "cation sites, whereas open-shell metal sites will usually require a "
     "coordinating anchor - a distinction that determines which scaffolds "
     "can exploit a given metal site. The metal is nevertheless a coarse "
     "predictor: within a single metal species the face-on fraction of "
     "individual targets ranges from 0 to 73% (Section 3.9). " +
     blue("The two statements do not conflict, and reading them together is "
          "the central methodological point of this study: element-level "
          "enrichment is real, reproducible and mechanistically explicable, "
          "yet it accounts for only a modest share of the variation once the "
          "binding site is known. A metal-aware scoring term or docking "
          "filter built on the element alone would reproduce the averages of "
          "Figure 5 while missing every individual case that matters - the "
          "metalloproteinase that stacks an aryl group on its zinc, or the "
          "carbonic anhydrase that never does.")),
    ("FIG", "fig4_geomclass.png"),

    # ---------------------------------------------------------------- 3.6 --
    ("H2", "3.6. Drug Subset: 235 Structures with Approved Drugs"),
    ("P",
     "DrugBank annotation{c:wishart_drugbank_2018} of all aromatic ligand "
     "components (Table S4) shows that 468 contacts in 235 structures involve "
     "approved drugs, with Mg (225 contacts, 120 structures) and Zn (128 "
     "contacts in 66 structures) dominating (Figure 6b, Table S8). The "
     "category census and the top approved-drug ligands are shown in Figure "
     "6a and Figure 6c (Table S7). The top approved-drug ligands are the "
     "bisphosphonates zoledronic acid (66 contacts) and risedronate (27), "
     "both anchored to the Mg2+/Mn2+ pair of farnesyl diphosphate synthase by "
     "their phosphonate groups while the imidazole/pyridine rings hang "
     "nearby;{c:ebetino_bisphosphonates_2011} tetracycline-class and other "
     "antibiotics, adenine, and tacrine complete the top group. "
     "Drug-experimental ligands contribute 1,392 contacts in 653 structures, "
     "including metalloporphyrin therapeutics and catechol/phenanthroline "
     "metal-binding scaffolds."),
    ("P",
     "Geometry adds a distinction that the ligand census alone does not make: "
     "36 of the 468 approved-drug contacts (7.7%) are face-on, and they are "
     "contributed by only 11 of the 73 approved drugs (22 structures) - "
     "face-on engagement is the exception even within the drug subset. The "
     "face-on contacts concentrate on Zn (25 of 128 contacts, 19.5%) rather "
     "than on Mg (9 of 225, 4.0%), and the individual cases are instructive: "
     "roflumilast stacks its dichloropyridine ring over the catalytic Zn2+ of "
     "phosphodiesterase 4 (d_centroid 5.26 A, theta 19-21 deg), pentostatin "
     "(2'-deoxycoformycin) lies 3.7-4.0 A above Zn in adenosine deaminase "
     "(theta 32-34 deg), and risedronate presents the face of its pyridine "
     "ring to the Mg2+ of farnesyl diphosphate synthase (4.8-5.0 A, theta 29 "
     "deg) while its phosphonates anchor the metal pair."),
    ("P",
     "The cofactor subset shows the same selectivity: ATP (14.4% of 382 "
     "contacts), FAD (15.2% of 33) and NADP (14.4% of 132) place an adenine "
     "or flavin face over a metal in a substantial minority of their "
     "complexes, whereas ADP (0 of 82) and GDP (1.7% of 230) do not, i.e. "
     "the geometry depends on which nucleotide and which metal site rather "
     "than on the nucleotide class. These subsets provide directly reusable "
     "starting points for metal-mediated drug design, and computational "
     "tools for predicting the binding pose of metal-binding pharmacophores "
     "are beginning to appear.{c:karges_2022!} " +
     blue("Three practical lessons follow. First, the approved drugs that "
          "already place a ring over a metal mostly pair a phosphonate or a "
          "nitrogen heterocycle with an aromatic system set back from the "
          "anchor (risedronate, zoledronic acid, pentostatin), which is the "
          "geometry a short, rigid linker between anchor and ring produces. "
          "Second, the Zn/Mg split (19.5% vs 4.0%) tracks the coordination "
          "chemistry of Sections 3.5 and 3.9 rather than the pharmacological "
          "class: magnesium sites are octahedral and hydrated, zinc sites "
          "tetrahedral and buried, and a ring face is found chiefly at the "
          "latter. Third, the fact that 62 of the 73 approved drugs never "
          "make a face contact is itself design information - for most "
          "metal-binding drugs the aromatic decoration is placed to fill "
          "adjacent subpockets, and moving it over the ion would require "
          "rebuilding the scaffold rather than decorating it.")),
    ("FIG", "fig5_drugs.png"),

    # ---------------------------------------------------------------- 3.7 --
    ("H2", "3.7. Affinity Association: A Large Apparent Effect That Is Mostly "
           "Target Composition"),
    ("P",
     "Joining the PDBbind v2020 indexes{c:wang_pdbbind_2004}"
     "{c:wang_pdbbind_2005} with our classification yields affinity data for "
     "19,443 general-set and 5,316 refined-set complexes (Table 3, Figure 7; "
     "the general-set box plots are shown in Figure S5, and the permutation "
     "tests in Tables S6a and S6b). In the uncorrected comparison in the "
     "refined set (all Kd/Ki-derived), complexes whose ligand makes a "
     "bridge-near metal contact have the highest median affinity (-log Kd/Ki "
     "= 7.52, n = 379), significantly above both the metal-free control "
     "(6.74, n = 2,400; median difference +1.16, permutation p < 0.0001) and "
     "the metal-present but contact-free control (6.36, +1.16 log units as "
     "well, p < 0.0001). Bridge-direct complexes (n = 55) are also above the "
     "metal-free control (+0.70, p = 0.0496). The association is reproduced "
     "in the general set (+0.4 to +1.2 log units) and within the Kd- and "
     "IC50-only strata, although the strongest subgroup switches between "
     "bridge-near and bridge-direct, and the Ki-only stratum shows near-equal "
     "medians (7.46 vs 7.42)."),
    ("P",
     "These stratum differences most likely reflect the target composition of "
     "each measure stratum rather than a dependence on the affinity type, and "
     "we therefore repeated the comparison with the target held fixed "
     "(Section 2.6). Affinities were converted to within-target percentile "
     "ranks (985 UniProt targets with at least four complexes in the general "
     "set, 36 protein types) and group labels were permuted within target. "
     "The bridge-near advantage over the metal-present but contact-free "
     "control survives this matching in both sets and at both levels of "
     "stratification (general set: +0.053 within-target percentile units, "
     "i.e. about five percentile points, p < 0.0001; refined set: +0.062, "
     "p < 0.0001; protein-type strata: +0.075 and +0.115, both p < 0.0001), "
     "and the stricter paired analysis - only targets with at least three "
     "complexes per group, median of within-target median differences - "
     "agrees (general set +0.37 log units over 25 targets, permutation "
     "p = 0.010; refined set +0.75 over 5 targets, p = 0.005). The advantage "
     "over metal-free complexes, by contrast, collapses once the target is "
     "matched (+0.036 percentile, p = 0.014 in the general set but +0.029, "
     "p = 0.43 in the refined set), and the bridge-direct group becomes "
     "indistinguishable from both controls in the general set (+0.034, "
     "p = 0.30; +0.043, p = 0.14)."),
    ("P",
     "We therefore revise the interpretation of the uncorrected comparison: "
     "the large global difference (+1.16 log units) is largely a "
     "target-composition effect, and the part that survives matching is a "
     "modest association between affinity and a protein-bound metal that "
     "holds a ligand ring nearby. A geometry-resolved exploratory contrast "
     "points in the same direction but is underpowered: entry-level "
     "complexes containing at least one face-on contact have a higher median "
     "affinity than those with only edge-on contacts in the general set "
     "(+0.48 log units, n = 160 vs 1,003, p = 0.009) but not in the refined "
     "set (+0.25, n = 36 vs 398, p = 0.40). " +
     blue("This revision determines how the database should be used. The "
          "uncorrected difference is reproducible across sets and will be "
          "found by anyone who repeats it, but it measures which proteins "
          "populate the PDBbind collection rather than what a metal contact "
          "does to affinity: metal-containing complexes in the refined set "
          "belong disproportionately to a handful of heavily studied "
          "metalloenzymes, whose inhibitors are themselves optimized to high "
          "affinity. Only the within-target contrast - same protein, same "
          "assay type, with and without a ring adjacent to the metal - "
          "isolates the contribution of the contact, and that contrast, "
          "though modest, is consistent across four stratifications and in "
          "the paired analysis. The defensible statement is therefore that "
          "metal-ring proximity is compatible with, and on average mildly "
          "favorable for, high affinity - not that it causes it. Benchmark "
          "studies that pool targets will overstate the effect, which is why "
          "the matched contrasts are released alongside the raw tables "
          "(Tables S13 and S15).")),
    ("FIG", "fig_pdbbind_refined_2020.png"),

    # ---------------------------------------------------------------- 3.8 --
    ("H2", "3.8. Case Studies Across the Metal–π Continuum"),
    ("P",
     "Six high-resolution structures (1.09-1.64 A) span the observed geometry "
     "space (Figure 8). We walk down the d_centroid scale from electrostatic "
     "to covalent. At the classical cation–π end, Na+ lies 3.68 A above an "
     "aromatic ring of lysozyme (PDB 9GOG) (Figure 8a) and the Mg2+ of "
     "ADP-ribose glycohydrolase ARH3 sits 3.29 A above the adenine ring of a "
     "bound NAD analogue (PDB 7ARW) (Figure 8b) - both drug-target systems. "
     "3-hydroxyanthranilate dioxygenase with a DrugBank-annotated picolinate "
     "ligand (PDB 4HSJ; d_centroid 2.57 A; Figure 8c) extends the series to "
     "Fe, and the nicking endonuclease/imidazole complex (PDB 9QGV; 1.55 A, "
     "d_centroid 2.06 A; Figure 8d) shows the tightest non-organometallic "
     "Zn–π contact of the census - already within coordination-bonding range "
     "of the ring."),
    ("P",
     "At the edge-on end, carbonic anhydrase II with benzeneselenol (PDB "
     "6HWZ; 1.64 A; Figure 8e) shows the canonical bridge-direct "
     "configuration: the selenolate coordinates Zn2+ (2.47 A) with the ring "
     "hanging to the side (d_centroid 4.29 A). The extreme face-on case is a "
     "cupin protein (a small beta-barrel metalloprotein family) metallocated "
     "with a Ru(eta6-p-cymene) fragment (PDB 9XS9) (Figure 8f), in which the "
     "Ru sits 1.68 A above the arene centroid - an eta6 coordination bond "
     "(all six arene carbons coordinated to the metal), i.e. the covalent "
     "end of the metal–π continuum; organoruthenium arene fragments are "
     "themselves pharmacophores of anticancer drug candidates."
     "{c:yan_ruarene_2005} Read together, the six cases show that contact "
     "geometry is dictated by the coordination chemistry of the metal: a "
     "back-bonding organometallic fragment forms an eta6 bond, a "
     "tetrahedrally saturated Zn2+ site forces an edge-on approach, and a "
     "hydrated alkali cation stacks electrostatically - so d_centroid is not "
     "a free parameter but a direct readout of the metal's coordination "
     "state, which is what makes it an informative feature for classifying "
     "metal sites in structure-based drug design."),
    ("P",
     "It should be kept in mind that all six cases were chosen at the tight "
     "end of the distribution (1.68-3.68 A): the median face-on contact of "
     "the census lies at 4.83 A, and two thirds of the face-on population "
     "are beyond 4.5 A (Section 3.2, Figure 9b), so the cases illustrate the "
     "chemistry of the inner regime rather than the bulk of the class. " +
     blue("Read as boundary conditions rather than as a survey, the series "
          "marks the two ends of what medicinal chemistry can build. Where "
          "the metal is part of the pharmacophore itself - the eta6-arene "
          "case - the ring-metal bond is covalent and the geometry is fixed. "
          "Where the metal is a hydrated alkali cation, the contact is weak "
          "enough that any competing polar group can displace it, which is "
          "why such contacts are easy to see in a crystal and easy to lose in "
          "solution. Between these extremes the zinc cases divide by a single "
          "structural question: whether the ring hangs from a coordinating "
          "atom (6HWZ) or is merely suspended over the ion (9QGV) - the same "
          "distinction that Sections 3.3 and 3.9 quantify over the whole "
          "archive.")),
    ("FIG", "fig6_cases.png"),

    # ---------------------------------------------------------------- 3.9 --
    ("H2", "3.9. Determinants of Face-On Engagement: Target Class, "
           "Coordination Sphere and Ring Chemistry"),
    ("P",
     "Metal identity explains only part of the variation described in Section "
     "3.5, so we asked which other property of a contact predicts its "
     "geometry. Stratifying the contacts by the Pfam-derived protein type of "
     "the coordinating chain (Table 4, Figure 9a) shows that the face-on "
     "fraction is not a uniform background but varies over two orders of "
     "magnitude between target classes: highest in deaminases (37.8% of 254 "
     "contacts), proteases (24.5% of 805), phosphodiesterases (18.5% of 422) "
     "and 2OG-Fe(II) oxygenases (11.0% of 154), and lowest - or absent - in "
     "dehydrogenases (0.5% of 594), carbonic anhydrases (0.2% of 975), "
     "histone demethylases (0 of 412), tubulins (0 of 189) and "
     "dehydratases/lyases (0 of 273). The protease signal is entirely due to "
     "the matrix metalloproteinases: excluding them, the remaining proteases "
     "are face-on in only 6.4% of 543 contacts. The skew persists at the "
     "level of individual targets - of 1,225 UniProt targets with at least "
     "one protein-coordinated contact, 1,046 (85.4%) have no face-on contact "
     "at all and the median target has a face-on fraction of 0% - and the "
     "census-wide 7.4% is not an artifact of a few over-represented targets, "
     "since the equal-target-weighted mean (7.5%) coincides with it. "
     "Face-on metal-aromatic engagement is a property of particular binding "
     "sites, not of metal-ligand complexes in general."),
    ("P",
     "The cleanest illustration is a pair of zinc families at the two extremes "
     "(Table 4). Matrix metalloproteinases - long pursued as anticancer and "
     "anti-inflammatory targets{c:augoff_2022!} - present the aromatic "
     "substituents of their inhibitors to the catalytic zinc in the majority "
     "of their contacts (MMP-12 57.7%, MMP-9 63.9%, MMP-3 73.3%; 60.5% "
     "overall, 164 of 271, entry-clustered 95% CI 52.2-69.1), whereas "
     "carbonic anhydrase II, the most frequently represented target in the "
     "census (662 contacts in 620 entries), almost never does (0.3%, 2 of "
     "662; 95% CI 0.0-0.8). Both sites bind Zn2+ through three histidine "
     "nitrogens, so the difference cannot be attributed to the ion, its "
     "charge or its donor set; it reflects the shape of the pocket through "
     "which a ring must pass, and it holds across five MMP isoforms (Table "
     "S16) and at atomic resolution in the batimastat complex of MMP-12 (PDB "
     "1JK3, 1.09 A), where the thiophene ring sits 4.90 A above the zinc with "
     "its face toward the metal (theta 17.8 deg) while both hydroxamate "
     "oxygens remain bonded to it. " +
     blue("The two cavities differ in what lies beyond the coordination "
          "sphere, and we take the pocket rather than the ion to be the "
          "determinant: the metalloproteinase zinc opens onto an elongated "
          "S1' channel that funnels inhibitor substituents over the metal, "
          "whereas the carbonic anhydrase zinc sits at the bottom of a "
          "compact, water-filled cone lined by hydrophilic residues and "
          "ordered solvent. This is a hypothesis rather than a measurement - "
          "the census cannot resolve the solvent - but it predicts that "
          "face-on fractions should track pocket openness rather than metal "
          "identity, and it implies that a metal–π term calibrated on one of "
          "these enzymes will be systematically wrong for the other.")),
    ("P",
     "Two structural features of the site modulate this further (Figure 9c "
     "and 9d). " +
     blue("Face-on approach is favored where the metal retains a free "
          "coordination site: contacts at CN <= 4 are face-on in 8.8% of "
          "cases against 4.8% at CN >= 6 (95% CI 7.7-9.9 vs 3.8-5.7; "
          "Mantel-Haenszel OR 1.21 over 11 metal strata, p = 0.005), an "
          "effect carried by open-shell metals (Fe 17.1% vs 3.0%) and absent "
          "for Zn (10.2% vs 10.4%). The chemical class of the donors matters "
          "more than their number: nitrogen-only ligation gives 16.0% "
          "face-on against 3.6% for oxygen-only ligation (OR 2.23 over 10 "
          "metal strata, p < 0.0001), and the contrast survives within zinc "
          "itself (16.4% vs 1.5%).") +
     " Ring chemistry adds a weaker axis: carbocyclic arenes are face-on in "
     "9.4% of their contacts and N-heteroarenes in 6.1% (OR 1.22 after "
     "stratification over metals, p = 0.005), the gap opening where the "
     "cation–π regime dominates and closing for Zn (12.0% vs 10.3%), as "
     "expected when a ring nitrogen competes with the pi face. The limiting "
     "case of sigma-donation is essentially incompatible with a face "
     "contact: only 45 of the 2,034 bridge-direct contacts (2.2%) are "
     "face-on, and a scaffold that needs both must anchor through a "
     "substituent, as the hydroxamates and bisphosphonates of Section 3.6 "
     "do."),
    ("P",
     "Read together, these axes explain why the census-wide 7.4% describes no "
     "individual site well and why the metal-level ordering of Section 3.5, "
     "although robust, is a coarse predictor: the most face-on-rich class "
     "(proteases) and the largest class with none (carbonic anhydrases) are "
     "both almost exclusively zinc. " +
     blue("Interaction-profiling tools already tabulate metal and aromatic contacts "
          "per complex,{c:binana2_2022!} but they report their presence and "
          "count, not the resolved geometry of the approach; that geometry is "
          "what the present census supplies. ") +
     blue("Three working rules follow, stated as hypotheses for design rather "
          "than as finished laws. First, place the ring, not the anchor, over "
          "the metal: a ring-atom bond forces an edge-on geometry (2.2% "
          "face-on), whereas a substituent anchor leaves the face free. "
          "Second, expect face-on contact only in pockets that can "
          "accommodate a second shell over the ion - the metalloproteinase "
          "S1' channel, the deaminase and phosphodiesterase sites - and not "
          "in compact, water-filled cavities such as the carbonic anhydrase "
          "site. Third, match the ring to the ion: electron-rich carbocycles "
          "where an alkali or alkaline-earth cation is the partner, and "
          "either ring class for zinc.")),
    ("FIG", "fig9_determinants.png"),
    ("TABLE", 4),

    # ------------------------------------------------------------ conclusions
    ("H1", "4. Conclusions"),
    ("P",
     "We present the first geometry-resolved census of metal ions contacting "
     "the aromatic rings of non-polymeric ligands across the PDB. Four "
     "results stand out. (i) Among 13,231 non-porphyrin contacts, 92.6% are "
     "edge-on (coordination-driven or ionic edge contacts) and only 7.4% are "
     "face-on metal–π interactions; the face-on class is bimodal in distance, "
     "with 115 contacts below 3.7 A - eta6 coordination and tight cation–π "
     "contacts - and 663 beyond 4.5 A, where the ring simply stacks over the "
     "metal at van der Waals separation. (ii) Approximately 75% of contacts "
     "involve a protein-coordinated metal - metal mediation of ligand binding "
     "is a dominant configuration, not an edge case - and 15.4% are direct "
     "protein-metal-ligand bridges. (iii) Face-on contacts are enriched for "
     "K, Na, and Zn, whereas the apparent face-on enrichment of Cu in "
     "unfiltered analyses is entirely a porphyrin-macrocycle artifact. The "
     "metal itself is, however, a weak predictor compared with the binding "
     "site: 85% of the 1,225 protein targets that bind a metal through "
     "protein residues have no face-on contact at all, and two zinc families, "
     "the matrix metalloproteinases (60.5%) and the carbonic anhydrases "
     "(0.3%), sit at opposite extremes. (iv) The apparent affinity advantage "
     "of metal-contacted complexes is largely target composition; a "
     "target-matched analysis retains only a modest association between "
     "affinity and a protein-bound metal holding a ligand ring nearby (+0.05 "
     "to +0.06 within-target percentile, p < 0.0001)."),
    ("P",
     blue("What does this census change for metal-ion-mediated drug "
          "discovery? The geometry of a ligand ring near a metal is "
          "target-encoded, and can therefore be looked up before it is "
          "designed: metalloproteinases, deaminases, phosphodiesterases and "
          "2OG-Fe oxygenases populate the upper end of Table 4, carbonic "
          "anhydrases, dehydrogenases, demethylases and tubulins the lower "
          "end, and 85% of annotated targets have no face-on contact at all. "
          "Treating a metal–π term as a general feature of metalloenzyme "
          "binding would therefore over-parameterize most sites and mis-score "
          "the few where it matters. Where the pocket does permit the pose it "
          "is reachable with ordinary medicinal-chemistry groups - "
          "roflumilast, pentostatin, risedronate and the adenine of ATP "
          "achieve it without a covalent metal bond - yet only 11 of the 73 "
          "approved drugs in the census do. The rule that follows is "
          "asymmetric, because ring and anchor compete for the same site (a "
          "ring atom bonded to the metal is edge-on in 97.8% of cases): if an "
          "anchor is required, anchor through a substituent and hold the ring "
          "off the metal on a short, rigid linker; if the pocket is compact "
          "and water-filled, direct the ring away.")),
    ("P",
     blue("For scoring functions, force fields and machine learning the "
          "census supplies measured geometry distributions and says how to "
          "use them. The three distance regimes are not interchangeable, so a "
          "term fitted to the 663 outer contacts cannot reproduce the 115 "
          "inner-sphere ones; parameterizations such as "
          "MCPB.py,{c:li_merz_mcpb_2016} the 12-6-4 "
          "potential,{c:li_1264_2013} or bonded and dummy-atom models within "
          "classical metal-ion modeling{c:li_merz_review_2017} should be "
          "fitted per regime and per coordination environment rather than to "
          "the pooled census. For metal-aware learning the same structure "
          "applies: the 24-field contact table is a labeled dataset, the "
          "0-73% range across protein targets is the performance a "
          "pocket-only classifier must reproduce, and the porphyrin lesson of "
          "Section 3.5 is a reminder that curation of the data decides "
          "whether a metal–π signal is real. Five limitations bound this "
          "version - asymmetric unit only, oxidation states from a static "
          "dictionary,{c:oxidstates_2022!} coordination inferred from "
          "struct_conn, resolution "
          "limiting the weakest contacts, and a single archive snapshot - and "
          "each is addressable by assembly expansion, curated oxidation "
          "states and re-mining at later dates, including the "
          "solvent-resolved comparison of face-on-rich and face-on-poor zinc "
          "sites that would turn the pocket-architecture hypothesis into a "
          "predictive rule. The contact database, structure library and "
          "analysis code are released as benchmark material for exactly that "
          "work.")),
]
