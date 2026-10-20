#!/usr/bin/env python3
"""L3a - download candidate structures in BOTH mmCIF and PDB formats.

v2 optimisations (after live throughput measurement):
  * downloads the gzip variants (.cif.gz / .pdb.gz, 3-4x smaller) and
    decompresses locally - bandwidth is the bottleneck, not CPU
  * reuses per-thread HTTP sessions (keeps TCP/TLS connections alive)

* source: https://files.rcsb.org/download/<ID>.cif.gz and .pdb.gz
* resumes automatically (existing .cif/.pdb files are skipped)
* a missing .pdb (a few very large entries have no PDB-format file) is
  tolerated and logged; a missing .cif is an error and gets logged too

Outputs
    cache/cif/<ID>.cif
    cache/pdb/<ID>.pdb
    data/download_errors.json
"""
from __future__ import annotations

import gzip
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import (CANDIDATES_PATH, CIF_DIR, DOWNLOAD_ERRORS_PATH,
                    DOWNLOAD_THREADS, DOWNLOAD_TIMEOUT_S, FILES_URL, PDB_DIR)

FILES_URL = "https://files.rcsb.org/download/{pdb_id}.{ext}.gz"

_tls = threading.local()


def _session() -> requests.Session:
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
    return _tls.s


def _fetch(url: str) -> bytes:
    r = _session().get(url, timeout=DOWNLOAD_TIMEOUT_S)
    if r.status_code == 404:
        raise FileNotFoundError("404")
    r.raise_for_status()
    return gzip.decompress(r.content)


def _download_one(pdb_id: str) -> list:
    """Download <pdb_id>.cif and <pdb_id>.pdb. Returns list of error dicts."""
    errors = []
    for ext, dest_dir in (("cif", CIF_DIR), ("pdb", PDB_DIR)):
        dest = dest_dir / f"{pdb_id}.{ext}"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        try:
            data = _fetch(FILES_URL.format(pdb_id=pdb_id, ext=ext))
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.rename(dest)
        except FileNotFoundError:
            # cif is required, pdb is optional (huge entries lack it)
            errors.append({"pdb_id": pdb_id, "ext": ext,
                           "error": "404 not found"})
        except requests.RequestException as exc:
            errors.append({"pdb_id": pdb_id, "ext": ext, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            errors.append({"pdb_id": pdb_id, "ext": ext,
                           "error": f"{type(exc).__name__}: {exc}"})
    return errors


def main() -> None:
    candidates = json.loads(CANDIDATES_PATH.read_text())
    ids = sorted(candidates)
    print(f"[L3a] downloading {len(ids):,} structures "
          f"(cif.gz+pdb.gz, decompressed on arrival) "
          f"with {DOWNLOAD_THREADS} threads ...", flush=True)

    errors = []
    done = 0
    with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as pool:
        futures = {pool.submit(_download_one, i): i for i in ids}
        for fut in as_completed(futures):
            done += 1
            errors.extend(fut.result())
            if done % 500 == 0 or done == len(ids):
                print(f"[L3a] {done:,}/{len(ids):,} done, "
                      f"{len(errors)} errors so far", flush=True)

    DOWNLOAD_ERRORS_PATH.write_text(json.dumps(errors, indent=1))

    n_cif = len(list(CIF_DIR.glob('*.cif')))
    n_pdb = len(list(PDB_DIR.glob('*.pdb')))
    fatal = [e for e in errors if e["ext"] == "cif"]
    print(f"\n[L3a] cache: {n_cif:,} cif files, {n_pdb:,} pdb files")
    if fatal:
        print(f"[L3a] WARNING: {len(fatal)} entries missing cif "
              f"(see {DOWNLOAD_ERRORS_PATH})")
    print(f"[L3a] errors logged -> {DOWNLOAD_ERRORS_PATH}")


if __name__ == "__main__":
    main()
