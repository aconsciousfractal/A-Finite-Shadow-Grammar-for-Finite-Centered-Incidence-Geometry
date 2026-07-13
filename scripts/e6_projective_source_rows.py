#!/usr/bin/env python3
"""Public E6 projective source-row replay helper.

Rows: full projective Weyl group G, point stabilizer Stab_p, and the finite
reflection row Ref.  The script computes aggregate permutation operators on the
36 projective roots and their ranks on V_std = U_20 + U_15.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

from e6_projective_root_engine import (
    RANK,
    dot,
    generate_roots,
    build_projective_action,
    graph_from_pairs,
    generate_group,
    canonical_pair,
)


def frac_to_string(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def rank_vectors(vectors: list[list[Fraction] | tuple[Fraction, ...] | tuple[int, ...]]) -> int:
    mat = [[Fraction(x) for x in row] for row in vectors if any(x != 0 for x in row)]
    if not mat:
        return 0
    m = len(mat)
    n = len(mat[0])
    rank = 0
    col = 0
    while rank < m and col < n:
        pivot = None
        for r in range(rank, m):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            col += 1
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        pv = mat[rank][col]
        mat[rank] = [x / pv for x in mat[rank]]
        for r in range(m):
            if r != rank and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][c] - factor * mat[rank][c] for c in range(n)]
        rank += 1
        col += 1
    return rank


def nullspace(matrix: list[list[int | Fraction]]) -> list[list[Fraction]]:
    mat = [[Fraction(x) for x in row] for row in matrix]
    m = len(mat)
    n = len(mat[0]) if m else 0
    pivot_cols: list[int] = []
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
        pivot_cols.append(col)
        row += 1
        if row == m:
            break
    free_cols = [c for c in range(n) if c not in pivot_cols]
    basis = []
    for free in free_cols:
        vec = [Fraction(0) for _ in range(n)]
        vec[free] = Fraction(1)
        for r, pc in enumerate(pivot_cols):
            vec[pc] = -mat[r][free]
        basis.append(vec)
    return basis


def mat_vec(mat: list[list[int]], vec: list[Fraction]) -> list[Fraction]:
    return [sum(Fraction(mat[i][j]) * vec[j] for j in range(len(vec))) for i in range(len(mat))]


def aggregate_matrix(perms: list[tuple[int, ...]], n: int) -> list[list[int]]:
    mat = [[0 for _ in range(n)] for _ in range(n)]
    for perm in perms:
        for src, dst in enumerate(perm):
            mat[dst][src] += 1
    return mat


def matmul_int(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    n = len(a)
    out = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for k in range(n):
            if a[i][k] == 0:
                continue
            aik = a[i][k]
            for j in range(n):
                if b[k][j]:
                    out[i][j] += aik * b[k][j]
    return out


def matrix_equals_scaled(a: list[list[int]], b: list[list[int]], scale: int) -> bool:
    return all(a[i][j] == scale * b[i][j] for i in range(len(a)) for j in range(len(a)))


def row_col_sums_ok(mat: list[list[int]], size: int) -> bool:
    n = len(mat)
    return all(sum(mat[i]) == size for i in range(n)) and all(sum(mat[i][j] for i in range(n)) == size for j in range(n))


def reflect_in_root_vec(x: tuple[int, ...], root: tuple[int, ...]) -> tuple[int, ...]:
    inner = dot(x, root)
    return tuple(x[i] - inner * root[i] for i in range(RANK))


def root_reflection_perms(pairs: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    pair_index = {p: i for i, p in enumerate(pairs)}
    perms = set()
    for root in pairs:
        perm = []
        for p in pairs:
            image = canonical_pair(reflect_in_root_vec(p, root))
            perm.append(pair_index[image])
        perms.add(tuple(perm))
    return sorted(perms)


def adjacency_matrix(adj_bits: list[int]) -> list[list[int]]:
    n = len(adj_bits)
    return [[1 if (adj_bits[i] & (1 << j)) else 0 for j in range(n)] for i in range(n)]


def eigenspace_basis(adj_mat: list[list[int]], eigenvalue: int) -> list[list[Fraction]]:
    n = len(adj_mat)
    return nullspace([[adj_mat[i][j] - (eigenvalue if i == j else 0) for j in range(n)] for i in range(n)])


def channel_rank(mat: list[list[int]], basis: list[list[Fraction]]) -> int:
    images = [mat_vec(mat, b) for b in basis]
    return rank_vectors(images)


def scalar_on_basis(mat: list[list[int]], basis: list[list[Fraction]]) -> dict:
    scalar = None
    for b in basis:
        image = mat_vec(mat, b)
        lam = None
        for idx, val in enumerate(b):
            if val != 0:
                lam = image[idx] / val
                break
        if lam is None:
            continue
        if any(image[i] != lam * b[i] for i in range(len(b))):
            return {"is_scalar": False, "scalar": None}
        if scalar is None:
            scalar = lam
        elif scalar != lam:
            return {"is_scalar": False, "scalar": None}
    return {"is_scalar": True, "scalar": frac_to_string(scalar if scalar is not None else Fraction(0))}


def subgroup_projection_spectrum(row_size: int, rank: int, dim: int, projection_identity: bool) -> dict:
    if not projection_identity:
        return {"type": "not_certified"}
    return {"type": "projection", "eigenvalue_multiplicities": {str(row_size): rank, "0": dim - rank}}


def orbit_sizes(perms: list[tuple[int, ...]], n: int) -> list[int]:
    unseen = set(range(n))
    sizes = []
    while unseen:
        start = next(iter(unseen))
        seen = {start}
        q = deque([start])
        while q:
            v = q.popleft()
            for p in perms:
                w = p[v]
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        sizes.append(len(seen))
        unseen -= seen
    return sorted(sizes)


def row_report(label: str, kind: str, perms: list[tuple[int, ...]], n: int, basis20, basis15, std_basis) -> dict:
    mat = aggregate_matrix(perms, n)
    row_size = len(perms)
    rank_std = channel_rank(mat, std_basis)
    rank20 = channel_rank(mat, basis20)
    rank15 = channel_rank(mat, basis15)
    scalar20 = scalar_on_basis(mat, basis20)
    scalar15 = scalar_on_basis(mat, basis15)
    projection_identity = False
    if kind == "subgroup":
        projection_identity = matrix_equals_scaled(matmul_int(mat, mat), mat, row_size)
    spectrum20 = scalar20 if scalar20["is_scalar"] else subgroup_projection_spectrum(row_size, rank20, len(basis20), projection_identity)
    spectrum15 = scalar15 if scalar15["is_scalar"] else subgroup_projection_spectrum(row_size, rank15, len(basis15), projection_identity)
    return {
        "label": label,
        "kind": kind,
        "row_size": row_size,
        "row_col_sums_ok": row_col_sums_ok(mat, row_size),
        "orbit_sizes_on_Pi36": orbit_sizes(perms, n) if kind == "subgroup" else None,
        "projection_identity_N2_equals_size_N": projection_identity if kind == "subgroup" else None,
        "rank_std": rank_std,
        "rank_U20": rank20,
        "rank_U15": rank15,
        "spectrum_U20": spectrum20,
        "spectrum_U15": spectrum15,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    roots = generate_roots()
    pairs, simple_perms = build_projective_action(roots)
    group = generate_group(simple_perms)
    n = len(pairs)
    adj_bits, _colors = graph_from_pairs(pairs)
    adj_mat = adjacency_matrix(adj_bits)
    basis20 = eigenspace_basis(adj_mat, 2)
    basis15 = eigenspace_basis(adj_mat, -4)
    std_basis = basis20 + basis15
    stabilizer0 = [g for g in group if g[0] == 0]
    ref_row = root_reflection_perms(pairs)

    rows = [
        row_report("G", "subgroup", group, n, basis20, basis15, std_basis),
        row_report("Stab_p0", "subgroup", stabilizer0, n, basis20, basis15, std_basis),
        row_report("Ref", "finite_subset", ref_row, n, basis20, basis15, std_basis),
    ]

    checks = {
        "basis20_dim": len(basis20) == 20,
        "basis15_dim": len(basis15) == 15,
        "std_basis_dim": len(std_basis) == 35,
        "group_size": len(group) == 51840,
        "stabilizer_size": len(stabilizer0) == 1440,
        "reflection_row_size": len(ref_row) == 36,
        "all_row_col_sums_ok": all(r["row_col_sums_ok"] for r in rows),
        "G_rank_std_zero": rows[0]["rank_std"] == 0,
        "Stab_rank_std_two": rows[1]["rank_std"] == 2,
        "Ref_rank_std_full": rows[2]["rank_std"] == 35,
        "Stab_orbits_1_15_20": rows[1]["orbit_sizes_on_Pi36"] == [1, 15, 20],
        "subgroup_projection_identities": rows[0]["projection_identity_N2_equals_size_N"] and rows[1]["projection_identity_N2_equals_size_N"],
    }
    artifact = {
        "artifact": "e6_projective_source_rows",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "carrier": "Pi_36 projective E6 root-pairs",
        "channel_dimensions": {"constant": 1, "U20": len(basis20), "U15": len(basis15), "V_std": len(std_basis)},
        "rows": rows,
        "checks": checks,
    }
    blob = json.dumps(artifact, indent=2, sort_keys=True)
    artifact["artifact_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    blob = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob, encoding="utf-8", newline="\n")
    print(json.dumps({
        "pass": artifact["pass"],
        "channel_dimensions": artifact["channel_dimensions"],
        "rows": [{"label": r["label"], "size": r["row_size"], "rank_std": r["rank_std"], "rank_U20": r["rank_U20"], "rank_U15": r["rank_U15"], "orbit_sizes": r["orbit_sizes_on_Pi36"]} for r in rows],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()