"""ACS/JCIM reference formatting helpers.

Reference style (J. Chem. Inf. Model.):
    Authors. Title. *Journal Abbrev.* **Year**, *Volume*, Pages.
    https://doi.org/...

* journal name italic, year bold, volume italic
* authors "Family, F. M." separated by semicolons; > 10 authors -> et al.
* en dash for page ranges; software/manual entries are set in roman type only
"""
from __future__ import annotations

import re
import unicodedata

JOURNAL_ABBREV = {
    "ACS Medicinal Chemistry Letters": "ACS Med. Chem. Lett.",
    "Accounts of Chemical Research": "Acc. Chem. Res.",
    "Acta Crystallographica Section D: Biological Crystallography":
        "Acta Crystallogr., Sect. D: Biol. Crystallogr.",
    "AmberTools (software documentation)": "AmberTools (software documentation)",
    "Biochemical Journal": "Biochem. J.",
    "Bioinformatics": "Bioinformatics",
    "Bone": "Bone",
    "Briefings in Bioinformatics": "Brief. Bioinform.",
    "Cancer Research": "Cancer Res.",
    "Cancers": "Cancers",
    "Cell": "Cell",
    "Chem Commun (Camb)": "Chem. Commun.",
    "Chemical Reviews": "Chem. Rev.",
    "Drug Discovery Today": "Drug Discovery Today",
    "IUCrJ": "IUCrJ",
    "JBIC Journal of Biological Inorganic Chemistry": "J. Biol. Inorg. Chem.",
    "Journal of Chemical Information and Modeling": "J. Chem. Inf. Model.",
    "Journal of Chemical Theory and Computation": "J. Chem. Theory Comput.",
    "Journal of Medicinal Chemistry": "J. Med. Chem.",
    "Journal of Open Source Software": "J. Open Source Softw.",
    "Journal of the American Chemical Society": "J. Am. Chem. Soc.",
    "Molecules": "Molecules",
    "Nature": "Nature",
    "Nucleic Acids Res": "Nucleic Acids Res.",
    "Nucleic Acids Research": "Nucleic Acids Res.",
    "Pesticide Synthesis Handbook": "Pesticide Synthesis Handbook",
    "Pharmaceuticals": "Pharmaceuticals",
    "Proceedings of the National Academy of Sciences":
        "Proc. Natl. Acad. Sci. U.S.A.",
    "Proceedings of the Python in Science Conference":
        "Proc. Python Sci. Conf.",
    "RCSB Protein Data Bank": "RCSB Protein Data Bank",
    "Science": "Science",
    "WIREs Computational Molecular Science": "WIREs Comput. Mol. Sci.",
}

# entries that are not journal articles: no italics, no bold year
PLAIN_JOURNALS = {
    "AmberTools (software documentation)",
    "Pesticide Synthesis Handbook",
    "RCSB Protein Data Bank",
}

_ORG_HINTS = ("consortium", "committee", "group", "team", "initiative")


def abbrev_journal(name: str | None) -> str:
    if not name or name == "?":
        return ""
    return JOURNAL_ABBREV.get(name, name)


def _initials(given: str) -> str:
    """'Dennis A' -> 'D. A.'; 'J.-E.' -> 'J.-E.'; 'G.J.' -> 'G. J.'."""
    given = unicodedata.normalize("NFC", given).replace("\u00a0", " ")
    given = given.strip().rstrip(".")
    out: list[str] = []
    for word in given.split():
        if "-" in word:
            subs = [s for s in word.split("-") if s]
            out.append("-".join(_initials(s) for s in subs))
        elif re.fullmatch(r"[A-Z.]+", word):
            out.extend(ch + "." for ch in word if ch.isalpha())
        else:
            out.append(word[0].upper() + ".")
    return " ".join(out)


def _is_given(token: str) -> bool:
    """True for 'Declan A.', 'S. K.', 'João Morais', 'H. C. Stephen'."""
    parts = token.split()
    if not parts:
        return False
    for w in parts:
        if re.fullmatch(r"[A-Z]\.?", w):                 # single initial
            continue
        if re.fullmatch(r"(?:[A-Z]\.)+[A-Z]?", w):       # "K." / "G.J."
            continue
        if re.fullmatch(r"[A-Z]\w+", w):                 # full given name
            continue
        if re.fullmatch(r"[A-Z]\w+\-[A-Z]\w+", w):       # Jean-Didier
            continue
        return False
    return True


def _is_family(token: str) -> bool:
    if not token or not token[0].isupper():
        return False
    if re.fullmatch(r"(?:[A-Z]\.?\s*)+", token):         # initials, not a family
        return False
    return True


def _acs_one(token: str) -> str:
    fam, given = token.split(",", 1)
    fam = fam.strip()
    given = given.strip()
    return f"{fam}, {_initials(given)}" if given else fam


def normalize_authors(authors) -> list[str]:
    raw = [unicodedata.normalize("NFC", a) for a in (authors or [])
           if isinstance(a, str) and a.strip()]
    tokens: list[str] = []
    for a in raw:
        for part in a.replace("\u00a0", " ").split(";"):
            part = part.strip()
            if part:
                tokens.append(part)
    if not tokens:
        return []

    # already "Family, Given" style
    if all("," in t for t in tokens):
        return [_acs_one(t) for t in tokens]

    # alternating "Family", "Given" pairs
    even = len(tokens) % 2 == 0
    if even and all(_is_family(tokens[i]) for i in range(0, len(tokens), 2)) \
            and all(_is_given(tokens[i]) for i in range(1, len(tokens), 2)):
        return [f"{tokens[i]}, {_initials(tokens[i + 1])}"
                for i in range(0, len(tokens), 2)]

    # "Family Initials" (e.g. "Burley SK") or organisation names
    out = []
    for t in tokens:
        if any(h in t.lower() for h in _ORG_HINTS):
            out.append(t)
            continue
        parts = t.split()
        if len(parts) == 1:
            out.append(t)
        elif re.fullmatch(r"[A-Z]{1,3}", parts[-1]):
            out.append(f"{' '.join(parts[:-1])}, {_initials(parts[-1])}")
        else:
            out.append(f"{parts[0]}, {_initials(' '.join(parts[1:]))}")
    return out


def format_authors(authors) -> str:
    names = normalize_authors(authors)
    if len(names) > 10:
        names = names[:10] + ["et al."]
    return "; ".join(names).rstrip(".")


def format_pages(page) -> str:
    if not page:
        return ""
    p = str(page).strip()
    p = re.sub(r"(?<=[0-9A-Za-z])\s*[-\u2013\u2212]\s*(?=[0-9A-Za-z])",
               "\u2013", p)
    return p


def reference_runs(ref: dict, number: int) -> list[tuple[str, dict]]:
    """Return [(text, {italic, bold})] runs for one numbered reference."""
    runs: list[tuple[str, dict]] = []
    authors = format_authors(ref.get("authors"))
    title = (ref.get("title") or "").strip().rstrip(".")
    journal = abbrev_journal(ref.get("journal"))
    plain = (ref.get("journal") in PLAIN_JOURNALS)
    year = ref.get("year") or ""
    vol = str(ref.get("volume") or "").strip()
    pages = format_pages(ref.get("page"))

    runs.append((f"({number}) ", {}))
    if authors:
        runs.append((authors + ". ", {}))
    if title:
        tail = "" if title.endswith(("?", "!")) else "."
        runs.append((title + tail + " ", {}))
    if journal:
        runs.append((journal, {"plain" if plain else "italic"}))
        runs.append((", " if plain else " ", {}))
    if year:
        runs.append((str(year), {"plain" if plain else "bold"}))
        runs.append((", " if (vol or pages) else ". ", {}))
    if vol:
        runs.append((vol, {"italic"}))
        runs.append((", " if pages else ". ", {}))
    if pages:
        runs.append((pages + ". ", {}))
    return runs


