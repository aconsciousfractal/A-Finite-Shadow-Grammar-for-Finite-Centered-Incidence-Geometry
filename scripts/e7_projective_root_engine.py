#!/usr/bin/env python3
"""Helper routines for the public E7 projective-root replay.

No external dependencies.  The helper uses the doubled 8-coordinate model,
generates the 126 oriented E7 roots directly, projectivizes antipodal roots,
checks the locked simple-reflection action, and records Gram-square values on
the 63 projective root pairs.

This module supplies finite root-system functions used by the bundled public
E7 replay.  It is not a separate public theorem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Iterable

DATE = "2026-07-09"
GATE = "Public E7 engine exact projective-root engine"
RANK_TARGET = 7
EXPECTED = {
    "type_I_root_count": 56,
    "type_II_root_count": 70,
    "root_count": 126,
    "projective_pair_count": 63,
    "root_span_rank": 7,
    "simple_reflection_closure_count": 126,
    "same_point_gram_square": [4],
    "off_diagonal_gram_square_values": [0, 1],
}

SIMPLE_ROOTS = (
    (2, -2, 0, 0, 0, 0, 0, 0),
    (0, 2, -2, 0, 0, 0, 0, 0),
    (0, 0, 2, -2, 0, 0, 0, 0),
    (0, 0, 0, 2, -2, 0, 0, 0),
    (0, 0, 0, 0, 2, -2, 0, 0),
    (0, 0, 0, 0, 0, 2, -2, 0),
    (-1, -1, -1, -1, 1, 1, 1, 1),
)

LOCKED_SIMPLE_GRAM = (
    (2, -1, 0, 0, 0, 0, 0),
    (-1, 2, -1, 0, 0, 0, 0),
    (0, -1, 2, -1, 0, 0, 0),
    (0, 0, -1, 2, -1, 0, -1),
    (0, 0, 0, -1, 2, -1, 0),
    (0, 0, 0, 0, -1, 2, 0),
    (0, 0, 0, -1, 0, 0, 2),
)


def dot(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    return sum(a * b for a, b in zip(u, v))


def neg(v: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-x for x in v)


def canon(v: tuple[int, ...]) -> tuple[int, ...]:
    """Lexicographically positive representative of {v,-v}."""
    nv = neg(v)
    return v if v > nv else nv


def actual_inner_num(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    """Numerator for the actual inner product dot(u,v)/4."""
    return dot(u, v)


def norm_value(v: tuple[int, ...]) -> Fraction:
    return Fraction(dot(v, v), 4)


def gram_square_value(u: tuple[int, ...], v: tuple[int, ...]) -> Fraction:
    return Fraction(dot(u, v) * dot(u, v), 16)


def generate_type_I_roots() -> list[tuple[int, ...]]:
    roots = []
    for i in range(8):
        for j in range(8):
            if i == j:
                continue
            v = [0] * 8
            v[i] = 2
            v[j] = -2
            roots.append(tuple(v))
    return sorted(roots)


def generate_type_II_roots() -> list[tuple[int, ...]]:
    roots = []
    for plus_positions in combinations(range(8), 4):
        plus = set(plus_positions)
        roots.append(tuple(1 if i in plus else -1 for i in range(8)))
    return sorted(roots)


def generate_roots() -> tuple[list[tuple[int, ...]], list[tuple[int, ...]], list[tuple[int, ...]]]:
    type_I = generate_type_I_roots()
    type_II = generate_type_II_roots()
    roots = sorted(set(type_I) | set(type_II))
    return type_I, type_II, roots


def reflect(v: tuple[int, ...], a: tuple[int, ...]) -> tuple[int, ...]:
    d = dot(v, a)
    if d % 4 != 0:
        raise ValueError(f"nonintegral reflection coefficient dot/4={d}/4")
    coeff = d // 4
    return tuple(v[i] - coeff * a[i] for i in range(8))


def simple_gram_matrix() -> list[list[int]]:
    return [[dot(a, b) // 4 for b in SIMPLE_ROOTS] for a in SIMPLE_ROOTS]


def closure_under_simple_reflections(seeds: Iterable[tuple[int, ...]]) -> set[tuple[int, ...]]:
    seen = set(seeds)
    q = deque(seen)
    while q:
        v = q.popleft()
        for a in SIMPLE_ROOTS:
            w = reflect(v, a)
            if w not in seen:
                seen.add(w)
                q.append(w)
    return seen


def rational_rank(rows: list[tuple[int, ...]]) -> int:
    mat = [[Fraction(x) for x in row] for row in rows]
    if not mat:
        return 0
    m = len(mat)
    n = len(mat[0])
    rank = 0
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, m):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        mat[row], mat[pivot] = mat[pivot], mat[row]
        pv = mat[row][col]
        mat[row] = [x / pv for x in mat[row]]
        for r in range(m):
            if r != row and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][c] - factor * mat[row][c] for c in range(n)]
        rank += 1
        row += 1
        if row == m:
            break
    return rank


def fraction_to_json(x: Fraction) -> int | str:
    if x.denominator == 1:
        return x.numerator
    return f"{x.numerator}/{x.denominator}"


def sha256_json_payload(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    print(json.dumps({
        "module": "e7_projective_root_engine",
        "role": "root-engine helper",
        "entry_point": "scripts/e7_projective_source_channel_replay.py",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()