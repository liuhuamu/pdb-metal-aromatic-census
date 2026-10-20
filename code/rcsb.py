"""Shared helpers for the RCSB PDB Search API v2.

All query templates in this module were validated against the live API on
2026-10-15:

* service name is ``chemical`` (NOT ``chem``)
* descriptor parameters use ``type`` (NOT ``query_type``)
* SMILES substructure  -> match_type "sub-struct-graph-relaxed"
* metal ion            -> formula query, e.g. {"value": "Zn", "type": "formula",
                          "match_subset": false}; a formula query automatically
                          covers oxidation-state comp variants (Fe -> FE + FE2)
* searches MUST be sent as POST for large boolean combinations
  (GET is limited to 2048-char URLs)
* HTTP 204 means "query OK, zero hits"
"""
from __future__ import annotations

import json
import sys
import time

import requests

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
PAGE_SIZE = 10_000          # max rows per page documented by the API
PAUSE_S = 0.4               # politeness pause between paged requests
MAX_RETRY = 5
TIMEOUT_S = 300


def chem_descriptor(smiles: str,
                    match_type: str = "sub-struct-graph-relaxed") -> dict:
    """Terminal node: SMILES substructure / similarity search."""
    return {
        "type": "terminal",
        "service": "chemical",
        "parameters": {
            "value": smiles,
            "type": "descriptor",
            "descriptor_type": "SMILES",
            "match_type": match_type,
        },
    }


def chem_formula(formula: str, match_subset: bool = False) -> dict:
    """Terminal node: molecular-formula search (exact ions by default)."""
    return {
        "type": "terminal",
        "service": "chemical",
        "parameters": {
            "value": formula,
            "type": "formula",
            "match_subset": match_subset,
        },
    }


def group(nodes: list, op: str = "and") -> dict:
    """Boolean group node ('and' / 'or')."""
    return {"type": "group", "logical_operator": op, "nodes": nodes}


def _post(body: dict):
    """POST one search request with retry/backoff. Returns json or None (204)."""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = requests.post(SEARCH_URL, json=body, timeout=TIMEOUT_S)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 204:
                return None
            if r.status_code == 429 or r.status_code >= 500:
                wait = 5 * attempt
                print(f"  [warn] HTTP {r.status_code}; retry {attempt}/{MAX_RETRY} "
                      f"in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
        except requests.RequestException as exc:
            print(f"  [warn] {exc}; retry {attempt}/{MAX_RETRY}", file=sys.stderr)
            time.sleep(5 * attempt)
    raise RuntimeError(f"Search failed after {MAX_RETRY} retries: "
                       f"{json.dumps(body)[:300]}")


def search_ids(query_node: dict, return_type: str = "entry") -> list:
    """Run a search with transparent pagination; returns identifier list."""
    ids: list = []
    start = 0
    while True:
        body = {
            "query": query_node,
            "return_type": return_type,
            "request_options": {
                "paginate": {"start": start, "rows": PAGE_SIZE},
                "results_content_type": ["experimental"],
            },
        }
        res = _post(body)
        if res is None:
            break
        batch = [h["identifier"] for h in res.get("result_set", [])]
        ids.extend(batch)
        total = res.get("total_count", 0)
        start += PAGE_SIZE
        if not batch or start >= total:
            break
        time.sleep(PAUSE_S)
    return ids
