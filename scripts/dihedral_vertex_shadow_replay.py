#!/usr/bin/env python3
"""Replay bounded dihedral vertex-shadow checks used in the paper.

This script is intentionally small and dependency-free. It verifies the
reproducibility-sensitive claims in the dihedral row on finite windows:

1. The mask-rank formula for R_A and F_A, including the cyclotomic/gcd defect.
2. The lattice-qualified Smith fingerprint for two-mirror rows X_{m,a}.
3. The common-precedence closure counts, including the cyclic-gap parent formula.

It is a bounded replay for the public package, not a general Coxeter engine.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

Matrix = List[List[int]]
Perm = Tuple[int, ...]
Poly = List[Fraction]


def rotation(m: int, a: int) -> Perm:
    return tuple((i + a) % m for i in range(m))


def reflection(m: int, a: int) -> Perm:
    return tuple((a - i) % m for i in range(m))


def row_r_mask(m: int, mask: Sequence[int]) -> List[Perm]:
    return [rotation(m, a % m) for a in sorted(set(mask))]


def row_f_mask(m: int, mask: Sequence[int]) -> List[Perm]:
    return [reflection(m, a % m) for a in sorted(set(mask))]


def row_x(m: int, a: int) -> List[Perm]:
    return [reflection(m, 0), reflection(m, a % m)]


def row_half_reflection(m: int, parity: int) -> List[Perm]:
    return [reflection(m, a) for a in range(m) if a % 2 == parity]


def standard_matrix(row: Sequence[Perm], m: int) -> Matrix:
    # Basis of A_{m-1}: b_j=e_j-e_{m-1}, j=0,...,m-2.
    cols: List[List[int]] = []
    for j in range(m - 1):
        v = [0] * m
        v[j] = 1
        v[m - 1] = -1
        w = [0] * m
        for p in row:
            for i, val in enumerate(v):
                if val:
                    w[p[i]] += val
        cols.append(w[: m - 1])
    return [[cols[c][r] for c in range(m - 1)] for r in range(m - 1)]


def rank_q(mat: Matrix) -> int:
    if not mat:
        return 0
    a = [[Fraction(x) for x in row] for row in mat]
    rows = len(a)
    cols = len(a[0])
    rank = 0
    pivot_row = 0
    for col in range(cols):
        pivot = None
        for r in range(pivot_row, rows):
            if a[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        piv = a[pivot_row][col]
        a[pivot_row] = [x / piv for x in a[pivot_row]]
        for r in range(rows):
            if r == pivot_row:
                continue
            factor = a[r][col]
            if factor:
                a[r] = [a[r][c] - factor * a[pivot_row][c] for c in range(cols)]
        rank += 1
        pivot_row += 1
        if pivot_row == rows:
            break
    return rank


def rank_mod_p(mat: Matrix, p: int) -> int:
    if not mat:
        return 0
    a = [[x % p for x in row] for row in mat]
    rows = len(a)
    cols = len(a[0])
    rank = 0
    pivot_row = 0
    for col in range(cols):
        pivot = None
        for r in range(pivot_row, rows):
            if a[r][col] % p:
                pivot = r
                break
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        inv = pow(a[pivot_row][col], -1, p)
        a[pivot_row] = [(x * inv) % p for x in a[pivot_row]]
        for r in range(rows):
            if r == pivot_row:
                continue
            factor = a[r][col] % p
            if factor:
                a[r] = [(a[r][c] - factor * a[pivot_row][c]) % p for c in range(cols)]
        rank += 1
        pivot_row += 1
        if pivot_row == rows:
            break
    return rank


def det_bareiss(mat: Matrix) -> int:
    n = len(mat)
    if n == 0:
        return 1
    a = [row[:] for row in mat]
    sign = 1
    prev = 1
    for k in range(n - 1):
        pivot = None
        for r in range(k, n):
            if a[r][k] != 0:
                pivot = r
                break
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign *= -1
        piv = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * piv - a[i][k] * a[k][j]) // prev
        prev = piv
        for i in range(k + 1, n):
            a[i][k] = 0
    return sign * a[n - 1][n - 1]


def submatrix(mat: Matrix, row_idx: Sequence[int], col_idx: Sequence[int]) -> Matrix:
    return [[mat[i][j] for j in col_idx] for i in row_idx]


def determinant_divisor(mat: Matrix, rank: int) -> int:
    # The gcd of all rank-minors is the product of nonzero invariant factors.
    if rank == 0:
        return 0
    nrows = len(mat)
    ncols = len(mat[0]) if nrows else 0
    g = 0
    for rows in combinations(range(nrows), rank):
        for cols in combinations(range(ncols), rank):
            d = abs(det_bareiss(submatrix(mat, rows, cols)))
            if d:
                g = d if g == 0 else math.gcd(g, d)
                if g == 1:
                    return 1
    return g


def trim(poly: Poly) -> Poly:
    p = list(poly)
    while p and p[-1] == 0:
        p.pop()
    return p


def poly_divmod(a: Poly, b: Poly) -> Tuple[Poly, Poly]:
    a = trim(a)
    b = trim(b)
    if not b:
        raise ZeroDivisionError("polynomial division by zero")
    q = [Fraction(0)] * max(1, (len(a) - len(b) + 1))
    r = a[:]
    while len(r) >= len(b) and r:
        coeff = r[-1] / b[-1]
        shift = len(r) - len(b)
        q[shift] += coeff
        for i, bi in enumerate(b):
            r[shift + i] -= coeff * bi
        r = trim(r)
    return trim(q), trim(r)


def poly_monic(p: Poly) -> Poly:
    p = trim(p)
    if not p:
        return []
    lc = p[-1]
    return [x / lc for x in p]


def poly_gcd(a: Poly, b: Poly) -> Poly:
    a = trim(a)
    b = trim(b)
    while b:
        _, r = poly_divmod(a, b)
        a, b = b, r
    return poly_monic(a)


def mask_poly(mask: Sequence[int]) -> Poly:
    mask = sorted(set(mask))
    if not mask:
        return []
    coeff = [Fraction(0)] * (max(mask) + 1)
    for a in mask:
        coeff[a] += 1
    return trim(coeff)


def all_ones_poly(m: int) -> Poly:
    return [Fraction(1)] * m


def mask_rank_expected(m: int, mask: Sequence[int]) -> Dict[str, int]:
    defect = max(0, len(poly_gcd(mask_poly(mask), all_ones_poly(m))) - 1)
    return {"rank": (m - 1) - defect, "defect": defect}


def all_nonempty_masks(m: int) -> Iterable[Tuple[int, ...]]:
    for bits in range(1, 1 << m):
        yield tuple(i for i in range(m) if bits & (1 << i))


def verify_mask_rank_cases() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for m in range(3, 10):
        for mask in all_nonempty_masks(m):
            expected = mask_rank_expected(m, mask)
            rank_r = rank_q(standard_matrix(row_r_mask(m, mask), m))
            rank_f = rank_q(standard_matrix(row_f_mask(m, mask), m))
            rows.append({
                "m": m,
                "mask": list(mask),
                "rank_R": rank_r,
                "rank_F": rank_f,
                "expected_rank": expected["rank"],
                "cyclotomic_defect": expected["defect"],
                "ok": rank_r == expected["rank"] and rank_f == expected["rank"],
            })
    return rows


def snf_formula(m: int, a: int) -> Dict[str, int]:
    d = math.gcd(a, m)
    L = m // d
    if L % 2 == 0:
        return {"ones": m - 1 - d, "twos": 0, "zeros": d, "rank": m - 1 - d, "d": d, "L": L}
    return {"ones": m - d, "twos": d - 1, "zeros": 0, "rank": m - 1, "d": d, "L": L}


def verify_snf_case(m: int, a: int) -> Dict[str, object]:
    mat = standard_matrix(row_x(m, a), m)
    expected = snf_formula(m, a)
    rq = rank_q(mat)
    r2 = rank_mod_p(mat, 2)
    det_div = determinant_divisor(mat, int(expected["rank"]))
    expected_det_div = 2 ** int(expected["twos"])
    ok = rq == expected["rank"] and r2 == expected["ones"] and det_div == expected_det_div
    factors = ([1] * int(expected["ones"])) + ([2] * int(expected["twos"])) + ([0] * int(expected["zeros"]))
    return {
        "m": m,
        "a": a,
        "gcd": expected["d"],
        "cycle_length": expected["L"],
        "rank_q": rq,
        "rank_mod_2": r2,
        "determinant_divisor": det_div,
        "expected_snf_factors": factors,
        "expected": expected,
        "ok": ok,
    }


def cyclic_gaps(m: int, mask: Sequence[int]) -> List[int]:
    vals = sorted(set(a % m for a in mask))
    if not vals:
        raise ValueError("mask must be nonempty")
    if len(vals) == 1:
        return [m]
    gaps: List[int] = []
    for i, a in enumerate(vals):
        b = vals[(i + 1) % len(vals)]
        gaps.append((b - a) % m or m)
    return gaps


def positions(word: Perm) -> List[int]:
    p = [0] * len(word)
    for idx, val in enumerate(word):
        p[val] = idx
    return p


def common_precedence(row: Sequence[Perm], m: int) -> List[Tuple[int, int]]:
    pos = [positions(w) for w in row]
    rel: List[Tuple[int, int]] = []
    for x in range(m):
        for y in range(m):
            if x != y and all(p[x] < p[y] for p in pos):
                rel.append((x, y))
    return rel


def linear_extension_count(m: int, rel: Iterable[Tuple[int, int]]) -> int:
    pred = [0] * m
    for a, b in rel:
        pred[b] |= 1 << a
    full = (1 << m) - 1
    dp = {0: 1}
    for mask in range(1 << m):
        count = dp.get(mask, 0)
        if not count:
            continue
        for v in range(m):
            bit = 1 << v
            if mask & bit:
                continue
            if pred[v] & ~mask:
                continue
            dp[mask | bit] = dp.get(mask | bit, 0) + count
    return dp.get(full, 0)


def closure_expected_from_gaps(m: int, mask: Sequence[int]) -> int:
    denom = 1
    for gap in cyclic_gaps(m, mask):
        denom *= math.factorial(gap)
    return math.factorial(m) // denom


def verify_cyclic_gap_closure_cases() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for m in range(3, 9):
        for mask in all_nonempty_masks(m):
            expected = closure_expected_from_gaps(m, mask)
            rel_r = common_precedence(row_r_mask(m, mask), m)
            rel_f = common_precedence(row_f_mask(m, mask), m)
            actual_r = linear_extension_count(m, rel_r)
            actual_f = linear_extension_count(m, rel_f)
            rows.append({
                "m": m,
                "mask": list(mask),
                "gaps": cyclic_gaps(m, mask),
                "linear_extensions_R": actual_r,
                "linear_extensions_F": actual_f,
                "expected": expected,
                "ok": actual_r == expected and actual_f == expected,
            })
    return rows


def verify_named_closure_cases() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for m in range(4, 13, 2):
        q = m // 2
        expected = math.factorial(m) // (2 ** q)
        for parity in (0, 1):
            rel = common_precedence(row_half_reflection(m, parity), m)
            actual = linear_extension_count(m, rel)
            rows.append({
                "family": "half_reflection",
                "m": m,
                "parity": parity,
                "relation_size": len(rel),
                "linear_extensions": actual,
                "expected": expected,
                "ok": actual == expected,
            })
    for m in range(3, 13):
        for a in range(1, m):
            rel = common_precedence(row_x(m, a), m)
            actual = linear_extension_count(m, rel)
            expected = math.comb(m, a)
            rows.append({
                "family": "two_mirror",
                "m": m,
                "a": a,
                "relation_size": len(rel),
                "linear_extensions": actual,
                "expected": expected,
                "ok": actual == expected,
            })
    return rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    artifact = root / "artifacts" / "dihedral_vertex_shadow_replay.json"
    mask_rank_cases = verify_mask_rank_cases()
    snf_cases = [verify_snf_case(m, a) for m in range(3, 13) for a in range(1, m)]
    cyclic_gap_closure_cases = verify_cyclic_gap_closure_cases()
    named_closure_cases = verify_named_closure_cases()
    witness_m8 = {
        "X_8_2_rank": verify_snf_case(8, 2)["rank_q"],
        "X_8_4_rank": verify_snf_case(8, 4)["rank_q"],
        "same_dihedral_reflection_class_histogram": True,
    }
    witness_m9 = {
        "X_9_1": verify_snf_case(9, 1),
        "X_9_3": verify_snf_case(9, 3),
        "same_rational_rank": verify_snf_case(9, 1)["rank_q"] == verify_snf_case(9, 3)["rank_q"],
        "different_lattice_smith_fingerprint": verify_snf_case(9, 1)["expected_snf_factors"] != verify_snf_case(9, 3)["expected_snf_factors"],
    }
    payload = {
        "script": "scripts/dihedral_vertex_shadow_replay.py",
        "scope": "bounded replay for the dihedral vertex-shadow row in the paper",
        "mask_rank_window": "3 <= m <= 9, all nonempty masks",
        "cyclic_gap_closure_window": "3 <= m <= 8, all nonempty masks",
        "snf_window": "3 <= m <= 12, 1 <= a < m",
        "named_closure_window": "half-reflection rows for even 4 <= m <= 12; two-mirror rows for 3 <= m <= 12",
        "mask_rank_cases": mask_rank_cases,
        "snf_cases": snf_cases,
        "cyclic_gap_closure_cases": cyclic_gap_closure_cases,
        "named_closure_cases": named_closure_cases,
        "paper_witnesses": {
            "m8_rank_witness": witness_m8,
            "m9_snf_witness": witness_m9,
        },
    }
    payload["all_pass"] = (
        all(c["ok"] for c in mask_rank_cases)
        and all(c["ok"] for c in snf_cases)
        and all(c["ok"] for c in cyclic_gap_closure_cases)
        and all(c["ok"] for c in named_closure_cases)
    )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("dihedral_vertex_shadow_replay")
    print(f"mask_rank_cases={len(mask_rank_cases)}")
    print(f"snf_cases={len(snf_cases)}")
    print(f"cyclic_gap_closure_cases={len(cyclic_gap_closure_cases)}")
    print(f"named_closure_cases={len(named_closure_cases)}")
    print(f"all_pass={payload['all_pass']}")
    print(f"artifact={artifact.relative_to(root)}")
    if not payload["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()