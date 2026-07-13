#!/usr/bin/env python3
"""Helper routines for the public E7 rank-2 flat-size channel.

No external dependencies.  The helper imports the E7 projective-root helper,
computes the projective rank-2 closure of every unordered pair of E7
projective root pairs, and compares that flat-size coloring with the
Gram-square coloring.

This module supplies finite channel functions used by the bundled public E7
replay.  It is not a separate public theorem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import e7_projective_root_engine as s2

DATE = "2026-07-09"
GATE = "Public E7 flat-channel replay rank-2 flat-size channel and Gram/flat collapse"
EXPECTED = {
    "projective_pair_count": 63,
    "unordered_pair_count": 1953,
    "gram_counter": {"0": 945, "1": 1008},
    "pair_flat_size_counter": {"2": 945, "3": 1008},
    "unique_flat_size_counter": {"2": 945, "3": 336},
    "gram_to_flat_size": {"0": [2], "1": [3]},
    "flat_size_to_gram": {"2": [0], "3": [1]},
    "point_incidence_size2_flats": 30,
    "point_incidence_size3_flats": 16,
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json_payload(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def projective_pairs() -> list[tuple[int, ...]]:
    _, _, roots = s2.generate_roots()
    return sorted({s2.canon(r) for r in roots})


def rank2_flat_indices(pairs: list[tuple[int, ...]], i: int, j: int) -> tuple[int, ...]:
    base_rank = s2.rational_rank([pairs[i], pairs[j]])
    if base_rank != 2:
        raise ValueError(f"distinct projective pair has rank {base_rank}: {(i, j)}")
    closure = []
    for k, r in enumerate(pairs):
        if s2.rational_rank([pairs[i], pairs[j], r]) == base_rank:
            closure.append(k)
    return tuple(closure)

def main() -> None:
    print(json.dumps({
        "module": "e7_projective_flat_channel",
        "role": "rank-2 flat-channel helper",
        "entry_point": "scripts/e7_projective_source_channel_replay.py",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()