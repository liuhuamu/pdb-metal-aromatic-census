#!/usr/bin/env python3
"""Keep re-running step4 while downloads are still in flight.

Loop:
  1. delete `no_cif` rows from the excluded table (those entries will be
     retried now that more files have arrived)
  2. run step4_geometry.py (it skips everything already in the DB)
  3. if no `no_cif` rows remain, every candidate has been analysed -> stop
"""
import sqlite3
import subprocess
import sys
import time

DB = r"E:\agent\protein\pdb-metal-pi\data\results.sqlite"
STEP4 = r"E:\agent\protein\pdb-metal-pi\step4_geometry.py"
MAX_ITERS = 60
SLEEP_S = 240


def main() -> None:
    for i in range(MAX_ITERS):
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM excluded WHERE reason = 'no_cif'")
        conn.commit()
        conn.close()

        subprocess.run([sys.executable, STEP4])

        conn = sqlite3.connect(DB)
        nocif = conn.execute(
            "SELECT COUNT(*) FROM excluded WHERE reason = 'no_cif'"
        ).fetchone()[0]
        hits = conn.execute("SELECT COUNT(*) FROM hits").fetchone()[0]
        conn.close()
        print(f"[watch] iter {i}: hits={hits:,} no_cif={nocif:,}", flush=True)
        if nocif == 0:
            print("[watch] all candidates analysed - done")
            return
        time.sleep(SLEEP_S)
    print("[watch] max iterations reached - some entries still missing cif")


if __name__ == "__main__":
    main()
