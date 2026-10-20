"""Central configuration for the PDB metal-aromatic screening pipeline.

Confirmed decisions (2026-10-15):
  * heme-class "metal embedded in macrocycle" -> separate `chelated` bucket
  * face-on : offset <= 1.5 A  and  2.5 <= d_plane <= 4.5 A
    edge-on : offset >  2.5 A
    mid     : everything else within the 6.0 A centroid cutoff
  * resolution cutoff 3.0 A
  * v1 analyses the asymmetric unit only (no assembly expansion)
"""
from pathlib import Path

# ---------------------------------------------------------------- paths ----
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CACHE_DIR = ROOT / "cache"
CIF_DIR = CACHE_DIR / "cif"
PDB_DIR = CACHE_DIR / "pdb"
OUTPUT_DIR = ROOT / "output"
STRUCTURES_DIR = OUTPUT_DIR / "structures"
FIG_DIR = ROOT / "figures"

AROMATIC_ENTRIES_PATH = DATA_DIR / "aromatic_entries.json"
AROMATIC_LIGANDS_PATH = DATA_DIR / "aromatic_ligands.json"
CANDIDATES_PATH = DATA_DIR / "candidates.json"
DOWNLOAD_ERRORS_PATH = DATA_DIR / "download_errors.json"
RESULTS_DB = DATA_DIR / "results.sqlite"

for _d in (DATA_DIR, CIF_DIR, PDB_DIR, OUTPUT_DIR, STRUCTURES_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------- L1: aromatic ring patterns ---
# NOTE: `c1ccccc1` already covers every benzene-fused system (indole,
# quinoline, purines, FAD, heme ...) because substructure matching allows
# fused-ring atom sharing.  The remaining patterns target stand-alone
# five-membered heteroaromatics and pyridine-type rings.
AROMATIC_SMILES = {
    "benzene":   "c1ccccc1",
    "pyridine":  "c1ccncc1",
    "pyrrole":   "c1cc[nH]c1",
    "imidazole": "c1cnc[nH]1",
    "furan":     "c1ccoc1",
    "thiophene": "c1ccsc1",
    "thiazole":  "c1cscn1",
    "oxazole":   "c1cocn1",
    "triazole":  "c1nnc[nH]1",
}

# ------------------------------------------------------- L2: metal list -----
# element (formula-query value) -> bucket
#   A  d10 post-transition / coinage ions  - classic metal-pi protagonists
#   B  alkali + alkaline-earth             - classic cation-pi (K+, Na+, ...)
#   C  other transition metals             - mostly coordination-driven
#   D  noble / platinum-group metals        - metallodrug complexes
METAL_BUCKETS = {
    "Zn": "A", "Cd": "A", "Hg": "A", "Cu": "A", "Ag": "A", "Au": "A",
    "Li": "B", "Na": "B", "K": "B", "Rb": "B", "Cs": "B",
    "Mg": "B", "Ca": "B", "Sr": "B", "Ba": "B",
    "Fe": "C", "Mn": "C", "Co": "C", "Ni": "C", "Cr": "C",
    "Mo": "C", "W": "C", "V": "C", "Ti": "C",
    "Pt": "D", "Pd": "D", "Ir": "D", "Rh": "D", "Ru": "D", "Os": "D",
}

# PDB comp_id -> (element, formal charge) for the most common metal comps.
# Anything not listed is still detected by element; its charge is recorded as
# NULL (extend this table if you need exact oxidation states for rare comps).
METAL_COMPS = {
    "ZN": ("Zn", +2), "CD": ("Cd", +2), "HG": ("Hg", +2),
    "CU": ("Cu", +2), "CU1": ("Cu", +1), "CU3": ("Cu", +3),
    "AG": ("Ag", +1), "AU": ("Au", +3), "AU1": ("Au", +1), "AU3": ("Au", +3),
    "LI": ("Li", +1), "NA": ("Na", +1), "K": ("K", +1),
    "RB": ("Rb", +1), "CS": ("Cs", +1),
    "MG": ("Mg", +2), "CA": ("Ca", +2), "SR": ("Sr", +2), "BA": ("Ba", +2),
    "FE": ("Fe", +3), "FE2": ("Fe", +2),
    "MN": ("Mn", +2), "MN3": ("Mn", +3),
    "CO": ("Co", +2), "NI": ("Ni", +2), "CR": ("Cr", +3),
    "PT": ("Pt", +2), "PD": ("Pd", +2),
}

# ------------------------------------------------------ L3: geometry rules --
D_CENTROID_MAX = 6.0          # overall hit threshold (metal ... ring centroid)
FACE_ON_OFFSET_MAX = 2.5      # face-on: lateral projection within ~2.5 A of
                              # the ring centre (the atomic envelope radius
                              # of a benzene ring; para-H...H ~ 5.0 A)
PORPHYRIN_KEYWORDS = ("porphyrin", "porphine", "chlorophyll", "chlorin",
                      "corrin", "siroheme", "sirohaem", "phthalocyanine",
                      "cobalamin", "pheophorbide", "heme")
METAL_MIN_OCCUPANCY = 0.5     # metals with lower occupancy are ignored
RESOLUTION_MAX = 3.0          # entries worse than this are excluded

# ---------------------------------------------------------- L3: downloads --
DOWNLOAD_THREADS = 16
DOWNLOAD_TIMEOUT_S = 120
FILES_URL = "https://files.rcsb.org/download/{pdb_id}.{ext}"

# ------------------------------------------- L5: output folder organisation -
# bucket key -> folder name used under output/structures/
BUCKET_FOLDERS = {
    "A": "A_d10_metpi",
    "B": "B_alkali_cationpi",
    "C": "C_transition",
    "D": "D_noble",
    "chelated": "chelated",
}
