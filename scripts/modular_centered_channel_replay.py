#!/usr/bin/env python3
"""Replay the modular centered-channel exhibit used by the paper.

The replay is intentionally small and self-contained.  It enumerates the four
Type-A incidence layers displayed in the modular centered-channel table,
constructs their position-value matrices, restricts them to the anchored
augmentation lattice, computes rational rank, finite-field rank, Smith invariant
factors in that fixed lattice, and the reduced quotient rank when p divides N.
"""

from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


def layer_matrix(n: int, k: int, l: int):
    rho = lambda i: n - 1 - i
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    size = 0
    for sigma in itertools.permutations(range(n)):
        main_hits = sum(1 for pos, val in enumerate(sigma) if val == pos)
        refl_hits = sum(1 for pos, val in enumerate(sigma) if val == rho(pos))
        if main_hits == k and refl_hits == l:
            size += 1
            for pos, val in enumerate(sigma):
                matrix[val][pos] += 1
    return matrix, size


def augmentation_restriction(matrix):
    n = len(matrix)
    # Anchored basis b_j=e_j-e_{n-1}.  The j-th restricted column is
    # M e_j - M e_{n-1}; coordinates are the first n-1 entries.
    return [[matrix[i][j] - matrix[i][n - 1] for j in range(n - 1)] for i in range(n - 1)]


def rank_q(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    rows = len(a)
    cols = len(a[0]) if rows else 0
    rank = 0
    for col in range(cols):
        pivot = next((i for i in range(rank, rows) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        pv = a[rank][col]
        a[rank] = [x / pv for x in a[rank]]
        for i in range(rows):
            if i != rank and a[i][col]:
                factor = a[i][col]
                a[i] = [a[i][j] - factor * a[rank][j] for j in range(cols)]
        rank += 1
    return rank


def rank_mod(matrix, p: int):
    a = [[x % p for x in row] for row in matrix]
    rows = len(a)
    cols = len(a[0]) if rows else 0
    rank = 0
    for col in range(cols):
        pivot = next((i for i in range(rank, rows) if a[i][col] % p), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, p)
        a[rank] = [(x * inv) % p for x in a[rank]]
        for i in range(rows):
            if i != rank and a[i][col] % p:
                factor = a[i][col] % p
                a[i] = [(a[i][j] - factor * a[rank][j]) % p for j in range(cols)]
        rank += 1
    return rank


def quotient_rank_mod(augmentation_matrix, p: int):
    # Rank of the induced map on A_N / K*1.  If c=(1,...,1) in anchored
    # augmentation coordinates, then rank on the quotient is
    # dim(im(M)+<c>)-1.
    d = len(augmentation_matrix)
    columns = [[augmentation_matrix[i][j] for i in range(d)] for j in range(d)]
    constant = [1 for _ in range(d)]
    combined = [[col[i] for col in columns] + [constant[i]] for i in range(d)]
    return rank_mod(combined, p) - 1


def det_bareiss(square):
    n = len(square)
    if n == 0:
        return 1
    a = [row[:] for row in square]
    sign = 1
    prev = 1
    for k in range(n - 1):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign *= -1
        pv = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * pv - a[i][k] * a[k][j]) // prev
        prev = pv
        for i in range(k + 1, n):
            a[i][k] = 0
        for j in range(k + 1, n):
            a[k][j] = 0
    return sign * a[-1][-1]


def smith_invariants(matrix):
    if not matrix or not matrix[0]:
        return []
    row_ids = range(len(matrix))
    col_ids = range(len(matrix[0]))
    divisors = [1]
    for k in range(1, min(len(matrix), len(matrix[0])) + 1):
        gcd_value = 0
        for rows in itertools.combinations(row_ids, k):
            for cols in itertools.combinations(col_ids, k):
                minor = [[matrix[i][j] for j in cols] for i in rows]
                det = abs(det_bareiss(minor))
                if det:
                    gcd_value = det if gcd_value == 0 else math.gcd(gcd_value, det)
        if gcd_value == 0:
            break
        divisors.append(gcd_value)
    return [divisors[i] // divisors[i - 1] for i in range(1, len(divisors))]


def predicted_rank_from_smith(invariants, p: int):
    return sum(1 for d in invariants if d and d % p != 0)


CASES = [
    {
        "role": "good_characteristic_torsion_collapse",
        "label": "I_7(1,1)",
        "n": 7,
        "k": 1,
        "l": 1,
        "p": 2,
        "expected_size": 656,
        "expected_snf": [4, 4, 8],
        "expected_rank_q": 3,
        "expected_rank_mod_p": 0,
        "expected_quotient_rank_mod_p": None,
    },
    {
        "role": "max_bounded_scout_drop",
        "label": "I_8(4,1)",
        "n": 8,
        "k": 4,
        "l": 1,
        "p": 3,
        "expected_size": 192,
        "expected_snf": [12, 12, 12, 72, 576, 576, 576],
        "expected_rank_q": 7,
        "expected_rank_mod_p": 0,
        "expected_quotient_rank_mod_p": None,
    },
    {
        "role": "quotient_drop_without_augmentation_drop",
        "label": "I_3(0,1)",
        "n": 3,
        "k": 0,
        "l": 1,
        "p": 3,
        "expected_size": 2,
        "expected_snf": [1, 1],
        "expected_rank_q": 2,
        "expected_rank_mod_p": 2,
        "expected_quotient_rank_mod_p": 1,
    },
    {
        "role": "augmentation_drop_separate_quotient",
        "label": "I_6(0,4)",
        "n": 6,
        "k": 0,
        "l": 4,
        "p": 2,
        "expected_size": 12,
        "expected_snf": [1, 1, 8, 48, 48],
        "expected_rank_q": 5,
        "expected_rank_mod_p": 2,
        "expected_quotient_rank_mod_p": 2,
    },
]


def replay_case(case):
    matrix, size = layer_matrix(case["n"], case["k"], case["l"])
    aug = augmentation_restriction(matrix)
    invariants = smith_invariants(aug)
    rank_over_q = rank_q(aug)
    rank_over_fp = rank_mod(aug, case["p"])
    predicted = predicted_rank_from_smith(invariants, case["p"])
    quotient = None
    if case["n"] % case["p"] == 0:
        quotient = quotient_rank_mod(aug, case["p"])
    checks = {
        "size": size == case["expected_size"],
        "snf_lattice": invariants == case["expected_snf"],
        "rank_q": rank_over_q == case["expected_rank_q"],
        "rank_mod_p": rank_over_fp == case["expected_rank_mod_p"],
        "snf_predicts_rank_mod_p": predicted == rank_over_fp,
        "quotient_rank_mod_p": quotient == case["expected_quotient_rank_mod_p"],
    }
    return {
        "role": case["role"],
        "label": case["label"],
        "n": case["n"],
        "k": case["k"],
        "l": case["l"],
        "p": case["p"],
        "layer_size": size,
        "snf_lattice": invariants,
        "rank_q_augmentation": rank_over_q,
        "rank_mod_p_augmentation": rank_over_fp,
        "rank_mod_p_predicted_from_snf": predicted,
        "rank_mod_p_reduced_quotient": quotient,
        "checks": checks,
        "pass": all(checks.values()),
    }


def main():
    rows = [replay_case(case) for case in CASES]
    payload = {
        "artifact": "modular_centered_channel_replay",
        "row_id": "X16",
        "description": "Bounded replay for the modular centered-channel exhibit: characteristic, augmentation channel, reduced quotient, and lattice-qualified SNF data.",
        "cases": rows,
        "all_pass": all(row["pass"] for row in rows),
    }
    out = Path("artifacts") / "modular_centered_channel_replay.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_pass": payload["all_pass"], "case_count": len(rows), "artifact": str(out)}, sort_keys=True))
    if not payload["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()