#!/usr/bin/env python3
"""Generate the JCIM submission cover letter (Word).

Includes four suggested reviewers drawn from the cited literature, with
e-mail addresses taken from the reviewers' public institutional pages
(sources noted in the change log).
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt

ROOT = Path(r"E:\agent\protein\pdb-metal-pi")
OUTDIR = ROOT / "paper" / "manuscript"
OUTDIR.mkdir(parents=True, exist_ok=True)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)


def P(text="", bold=False, italic=False, space_after=8, indent=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    p.paragraph_format.space_after = Pt(space_after)
    if indent is not None:
        p.paragraph_format.left_indent = Pt(indent)
    return p


def reviewer(n, name, aff, email, expertise):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(18)
    p.paragraph_format.first_line_indent = Pt(-18)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f"{n}. Prof. {name}")
    r.bold = True
    p.add_run(f", {aff}. E-mail: {email}. Expertise: {expertise}.")


# ---------------------------------------------------------------- header ----
P("[Institution letterhead / corresponding-author address]", italic=True,
  space_after=2)
P("[E-mail of corresponding author]  |  [ORCID]", italic=True)
P("[Date]", italic=True, space_after=16)

P("Prof. Kenneth M. Merz Jr.", space_after=0)
P("Editor-in-Chief", space_after=0)
P("Journal of Chemical Information and Modeling", space_after=0)
P("American Chemical Society", space_after=16)

P("Dear Professor Merz,", space_after=10)

# ---------------------------------------------------------------- body ------
P("We are pleased to submit our manuscript \u201cHow Metal Ions Engage "
  "Aromatic Ligands: A Geometry-Resolved PDB Census\u201d for consideration "
  "as an Article in the Journal of Chemical Information and Modeling.")

P("Metal ions anchor inhibitors to a large share of metalloenzyme drug "
  "targets, and they modulate ligand binding even in families without a "
  "catalytic metal, such as the allosteric Na+ site of G protein-coupled "
  "receptors. Yet no systematic, geometry-resolved account exists of how a "
  "metal ion engages the aromatic ring of a bound ligand. Our study fills "
  "that gap with a three-stage screen of the complete PDB archive "
  "(261,301 experimental entries; accessed October 2026): a ligand-entity "
  "aromatic substructure search (nine ring patterns, queried so that protein "
  "side chains cannot contaminate the census), exact-formula queries for 25 "
  "biologically relevant metals, and geometric analysis of all 37,336 "
  "qualifying structures. The result is an annotated database of 13,231 "
  "non-porphyrin metal-aromatic contacts in 5,107 entries; 44,347 further "
  "contacts involving porphyrin macrocycles are archived separately as a "
  "control set.")

P("Four findings are, to our knowledge, new. (i) A projection-based "
  "classification shows that 92.6% of contacts are edge-on and only 7.4% are "
  "face-on metal-\u03c0 interactions; the face-on class is bimodal in "
  "distance, with 115 contacts below 3.7 A (eta6 coordination and tight "
  "cation-\u03c0 contacts) and 663 beyond 4.5 A (rings stacked over the metal "
  "at van der Waals separation), and the tight end is documented by six "
  "high-resolution case studies. (ii) About 75% of contacts involve a "
  "protein-coordinated metal and 2,034 are direct protein-metal-ligand "
  "bridges, which quantifies at archive scale how metal ions mediate ligand "
  "binding. (iii) Face-on engagement is a property of the binding site "
  "rather than of the ion: 85% of the 1,225 protein targets have no face-on "
  "contact at all, and two zinc families sit at opposite extremes (matrix "
  "metalloproteinases 60.5%, carbonic anhydrases 0.3%), with coordination "
  "number, donor chemistry, ring class and pocket class as the strongest "
  "predictors. (iv) Face-on contacts are enriched for K, Zn and Na, whereas "
  "the apparent copper enrichment of an unfiltered analysis comes entirely "
  "from the CuB site of cytochrome c oxidase above porphyrin macrocycles - a "
  "caution for anyone mining the PDB chemically.")

P("The work is squarely within the scope of JCIM, and its outputs are built "
  "for immediate reuse. The census defines a design grammar for "
  "metal-anchored inhibitor scaffolds: the metal-binding group fixes the "
  "pose, and the metal-to-ring geometry then determines which subpockets the "
  "aromatic decoration can reach. It also shows where face-on metal-\u03c0 "
  "engagement is a realistic design option (alkali and d10 cation sites, and "
  "the target classes identified here) and where it is not. The classified "
  "complexes form a labelled training set for metal-aware machine learning: "
  "metal identity, coordination sphere, ring class and the per-contact "
  "geometric descriptors are precisely the features that current affinity "
  "models and scoring functions do not encode. A target-matched re-analysis "
  "of PDBbind v2020 shows that the large uncorrected affinity difference "
  "between metal-contacted and metal-free complexes is mostly target "
  "composition, with only a modest within-target association surviving "
  "matching; we report this explicitly so that the database is used with the "
  "right null model. Finally, 235 structures with approved drugs provide "
  "reusable design precedents, including 11 drugs that engage a metal "
  "face-on.")

# ------------------------------------------------------- reviewers ---------
P("Suggested reviewers.", bold=True, space_after=4)
P("The four colleagues below work on the problems this manuscript addresses "
  "and have each published work cited in it; none is a collaborator, a "
  "co-author, or affiliated with our institution.", space_after=6)

reviewer(1, "Antonio Rosato",
         "Magnetic Resonance Center (CERM) and Department of Chemistry, "
         "University of Florence, Sesto Fiorentino (FI), Italy",
         "rosato@cerm.unifi.it",
         "metal-site databases (MetalPDB) and structural bioinformatics of "
         "metalloproteins; cited in the manuscript")
reviewer(2, "Jean-Didier Maréchal",
         "Departament de Química, Universitat Autònoma de Barcelona, "
         "Cerdanyola del Vallès, Spain",
         "jeandidier.marechal@uab.es",
         "prediction of metal-binding sites and metal-mediated docking "
         "(BioMetAll); cited in the manuscript")
reviewer(3, "Pengfei Li",
         "Department of Chemistry and Biochemistry, Loyola University "
         "Chicago, Chicago, IL, USA",
         "pli4@luc.edu",
         "metal-ion force fields and parameterization (MCPB.py, 12-6-4 "
         "potential); cited in the manuscript")
reviewer(4, "Claudia Andreini",
         "Magnetic Resonance Center (CERM) and Department of Chemistry, "
         "University of Florence, Sesto Fiorentino (FI), Italy",
         "claudia.andreini@unifi.it",
         "metalloproteome annotation and metal-site curation (MetalPDB); "
         "cited in the manuscript")
P("", space_after=4)

# ------------------------------------------------------- declarations ------
P("The manuscript is original, has not been published previously, and is not "
  "under consideration by any other journal. All authors have approved the "
  "submission and declare no competing financial interests. All data, code, "
  "per-figure source data and supporting tables are included in the "
  "submission package (SI_Tables.xlsx, source-data CSVs, the complete "
  "analysis code and the core SQLite database) and will be deposited in a "
  "public repository with a DOI upon acceptance.")

P("Thank you for considering our submission; we look forward to the "
  "reviewers' comments.")

P("Sincerely,", space_after=18)
P("[Corresponding author name, signature, and affiliation]", space_after=2)
P("[on behalf of all authors]", italic=True)

out = OUTDIR / "JCIM_coverletter.docx"
doc.save(out)
print("cover letter ->", out)
