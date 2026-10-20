Case-study structures for PyMOL rendering (fig 6, v2 classification)
=====================================================================
Six cases spanning the face-on distance continuum
(d_centroid 1.68 - 3.68 A) plus one edge-on prototype.
Files provided as cif (+pdb where RCSB offers one; 9GOG is mmCIF-only).

--------------------------------------------------------------------
Case A - 6HWZ | Carbonic anhydrase II + benzeneselenol (GXE)
          Zn edge-on (theta_plane = 34.2 deg), 1.64 A
  metal         : ZN 301 (chains A and B)
  ligand        : GXE 302 (benzeneselenol; Se-Zn 2.47 A)
  coordinated by: HIS95, HIS97, HIS120 (Zn-N 2.10/2.02/1.98 A)
  geometry      : d_centroid 4.29, d_plane 2.41, offset 3.54,
                  theta(to normal) 55.8 -> edge-on
  PyMOL: load 6HWZ.cif
         select metal, resn ZN
         select lig, resn GXE
         select site, resi 95+97+120 and chain A
         dist Zn_Se, (resn ZN and chain A), (resn GXE and name SE)

--------------------------------------------------------------------
Case B - 9XS9 | Cupin protein + Ru(eta6-p-cymene) complex
          Ru face-on (eta6-arene coordination), 1.09 A
  metal         : RU (organoruthenium half-sandwich)
  ligand        : MML (p-cymene; eta6-bound to Ru, min_dist 2.09 A)
  geometry      : d_centroid 1.68, d_plane 1.68, theta(to normal) 3.9
                  -> face-on (the extreme: metal-arene coordination bond)
  PyMOL: load 9XS9.cif
         select ru, resn RU
         select arene, resn MML
  note: protein metallocation structure - the Ru is also coordinated
        by protein residues (visible within 2.9 A).

--------------------------------------------------------------------
Case C - 9QGV | Nicking endonuclease + imidazole (IMD)
          Zn face-on (theta_plane = 82.3 deg), 1.55 A
  metal         : ZN
  ligand        : IMD (imidazole; crystallization additive)
  geometry      : d_centroid 2.06, d_plane 2.04, theta(to normal) 7.7,
                  min_dist 2.22 -> face-on
  note          : the tightest non-organometallic Zn...pi contact in the
                  census - Zn sits essentially on the imidazole face.
  PyMOL: load 9QGV.cif
         select zn, resn ZN
         select imd, resn IMD
         dist Zn_ring, resn ZN, (resn IMD and name C*)

--------------------------------------------------------------------
Case D - 4HSJ | 3-hydroxyanthranilate 3,4-dioxygenase + picolinate (6PC)
          Fe face-on (theta_plane = 62.4 deg), 1.88 A
  metal         : FE
  ligand        : 6PC (pyridine-2-carboxylic acid; DrugBank-annotated
                  experimental compound)
  geometry      : d_centroid 2.57, d_plane 2.28, theta(to normal) 27.6,
                  min_dist 2.33 -> face-on
  PyMOL: load 4HSJ.cif
         select fe, resn FE
         select pic, resn 6PC

--------------------------------------------------------------------
Case E - 7ARW | ADP-ribose glycohydrolase ARH3 + NAD analogue (8NA)
          Mg face-on over the adenine ring (theta_plane = 69.6 deg), 1.31 A
  metal         : MG
  ligand        : 8NA (alpha-diphosphopyridine nucleotide analogue)
  geometry      : d_centroid 3.29, d_plane 3.09, theta(to normal) 20.4,
                  min_dist 3.10 -> face-on
  note          : ARH3 is an ADP-ribosylhydrolase drug target; the Mg
                  engages the adenine ring of the nucleotide.
  PyMOL: load 7ARW.cif
         select mg, resn MG
         select nad, resn 8NA

--------------------------------------------------------------------
Case F - 9GOG | Lysozyme C + dioxidovanadium complex; Na+ face-on
          Na face-on (theta_plane = 77.5 deg), 1.24 A
  metal         : NA (crystallization Na+ above an aromatic ring)
  ligand        : A1IOM (dioxidovanadium(V) complex with an aromatic ring)
  geometry      : d_centroid 3.68, d_plane 3.60, theta(to normal) 12.5,
                  min_dist 3.65 -> face-on
  note          : this entry has no legacy .pdb file at RCSB (mmCIF-only);
                  use the .cif
  PyMOL: load 9GOG.cif
         select na, resn NA
         select lig, resn A1IOM

--------------------------------------------------------------------
Suggested rendering: metal as sphere, ligand + coordinating residues as
sticks, dashed distances via `dist`, cartoon for the protein,
orthoscopic ray for publication.
The six cases span d_centroid 1.68 - 3.68 A: the full range of tight
metal...aromatic-ring face contacts in the census, plus one edge-on
prototype (A).
