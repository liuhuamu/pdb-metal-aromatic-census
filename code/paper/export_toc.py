"""Export both TOC variants as 600-dpi TIFF and write the TOC text fields."""
from pathlib import Path

from PIL import Image

FIG = Path(r"E:\agent\protein\pdb-metal-pi\paper\figures")
MS = Path(r"E:\agent\protein\pdb-metal-pi\paper\manuscript")

# primary: metal-mediated binding concept
img = Image.open(FIG / "toc_mediation.png").convert("RGB")
img.save(FIG / "toc_mediation.tif", format="TIFF", dpi=(600, 600),
         compression="tiff_lzw")
img.save(MS / "TOC_graphic.tif", format="TIFF", dpi=(600, 600),
         compression="tiff_lzw")

# alternative: face-on / edge-on concept
alt = Image.open(FIG / "toc_graphic.png").convert("RGB")
alt.save(MS / "TOC_graphic_alternative_faceon.tif", format="TIFF",
         dpi=(600, 600), compression="tiff_lzw")

caption = (
    "TOC graphic (ACS: 3.25 x 1.75 in, 600 dpi).\n"
    "Primary version: TOC_graphic.tif (metal-ion-mediated binding).\n"
    "Alternative: TOC_graphic_alternative_faceon.tif (face-on / edge-on).\n\n"
    "Synopsis:\n"
    "Most metal-aromatic contacts in the PDB are mediated by a protein-bound "
    "metal: 15.4% are direct protein-metal-ligand bridges, 59.4% are "
    "metal-near contacts and 22.7% are ligand-held, so the metal, not the "
    "ligand scaffold, sets how an aromatic inhibitor is anchored.\n"
)
(FIG / "toc_caption.txt").write_text(caption, encoding="utf-8")
print("exported:", MS / "TOC_graphic.tif", MS / "TOC_graphic_alternative_faceon.tif")
