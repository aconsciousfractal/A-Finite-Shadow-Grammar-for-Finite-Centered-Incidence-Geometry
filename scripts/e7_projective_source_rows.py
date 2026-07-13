#!/usr/bin/env python3
"""Helper routines for the public E7 source-channel replay.

The bundled replay imports these functions to work in the reconstructed
F_2^6 symplectic model for Pi_63 and to compute source-aware ranks for
selected rows and simple parabolic subgroup rows.

This module is a library helper, not a separate public theorem or standalone
gate.  The public entry point is e7_projective_source_channel_replay.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import e7_projective_root_engine as s2
import e7_projective_weyl_action as s6

DATE = "2026-07-09"
GATE = "Public E7 source-row replay selected row/fingerprint scout"
N = 63
EXPECTED = {
    "projective_pair_count": 63,
    "source_projective_order": 1451520,
    "point_stabilizer_order": 23040,
    "reflection_row_size": 63,
    "simple_row_size": 7,
    "proper_simple_parabolic_row_count": 126,
    "parabolic_row_count_with_full_formula": 127,
    "dim_U27": 27,
    "dim_U35": 35,
    "dim_standard": 62,
    "ref_scalar_U27": 35,
    "ref_scalar_U35": 27,
}

MatrixF2 = tuple[int, ...]
Perm = tuple[int, ...]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json_payload(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def frac_to_json(x: Fraction) -> int | str:
    if x.denominator == 1:
        return x.numerator
    return f"{x.numerator}/{x.denominator}"


def rank_vectors(vectors: list[list[Fraction] | tuple[Fraction, ...] | tuple[int, ...]]) -> int:
    mat = [[Fraction(x) for x in row] for row in vectors if any(x != 0 for x in row)]
    if not mat:
        return 0
    rows = len(mat)
    cols = len(mat[0])
    rank = 0
    col = 0
    while rank < rows and col < cols:
        pivot = None
        for r in range(rank, rows):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            col += 1
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        pv = mat[rank][col]
        mat[rank] = [x / pv for x in mat[rank]]
        for r in range(rows):
            if r != rank and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][c] - factor * mat[rank][c] for c in range(cols)]
        rank += 1
        col += 1
    return rank


def nullspace(matrix: list[list[int | Fraction]]) -> list[list[Fraction]]:
    mat = [[Fraction(x) for x in row] for row in matrix]
    rows = len(mat)
    cols = len(mat[0]) if rows else 0
    pivot_cols: list[int] = []
    row = 0
    for col in range(cols):
        pivot = None
        for r in range(row, rows):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        mat[row], mat[pivot] = mat[pivot], mat[row]
        pv = mat[row][col]
        mat[row] = [x / pv for x in mat[row]]
        for r in range(rows):
            if r != row and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][c] - factor * mat[row][c] for c in range(cols)]
        pivot_cols.append(col)
        row += 1
        if row == rows:
            break
    free_cols = [c for c in range(cols) if c not in pivot_cols]
    basis = []
    for free in free_cols:
        vec = [Fraction(0) for _ in range(cols)]
        vec[free] = Fraction(1)
        for r, pc in enumerate(pivot_cols):
            vec[pc] = -mat[r][free]
        basis.append(vec)
    return basis


def symp_pair(x: int, y: int) -> int:
    return s6.symp_pair(x, y)


def transvection(center: int) -> MatrixF2:
    cols = []
    for i in range(6):
        basis = 1 << i
        image = basis
        if symp_pair(basis, center):
            image ^= center
        cols.append(image)
    return tuple(cols)


def apply_matrix(cols: MatrixF2, v: int) -> int:
    return s6.apply_matrix(cols, v)


def compose(left: MatrixF2, right: MatrixF2) -> MatrixF2:
    return s6.compose(left, right)


def pack_matrix(cols: MatrixF2) -> int:
    return s6.pack_matrix(cols)


def matrix_to_perm(cols: MatrixF2) -> Perm:
    return tuple(apply_matrix(cols, v) - 1 for v in range(1, 64))


def generated_matrix_group(gens: list[MatrixF2], expected_limit: int | None = None) -> list[MatrixF2]:
    identity = tuple(1 << i for i in range(6))
    seen = {pack_matrix(identity)}
    group = [identity]
    q = deque([identity])
    while q:
        g = q.popleft()
        for gen in gens:
            h = compose(gen, g)
            hp = pack_matrix(h)
            if hp not in seen:
                seen.add(hp)
                if expected_limit is not None and len(seen) > expected_limit:
                    raise RuntimeError(f"matrix group exceeded expected limit {expected_limit}")
                group.append(h)
                q.append(h)
    return group


def aggregate_from_matrices(group: list[MatrixF2]) -> list[list[int]]:
    mat = [[0 for _ in range(N)] for _ in range(N)]
    for g in group:
        for src in range(1, 64):
            dst = apply_matrix(g, src)
            mat[dst - 1][src - 1] += 1
    return mat


def aggregate_from_formula_full_group(size: int) -> list[list[int]]:
    entry = size // N
    return [[entry for _ in range(N)] for _ in range(N)]


def adjacency_matrix() -> list[list[int]]:
    return [[0 if i == j else symp_pair(i + 1, j + 1) for j in range(N)] for i in range(N)]


def identity_matrix() -> list[list[int]]:
    return [[1 if i == j else 0 for j in range(N)] for i in range(N)]


def matrix_add(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [[a[i][j] + b[i][j] for j in range(N)] for i in range(N)]


def matrix_scale(a: list[list[int]], scalar: int) -> list[list[int]]:
    return [[scalar * a[i][j] for j in range(N)] for i in range(N)]


def matrix_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return all(a[i][j] == b[i][j] for i in range(N) for j in range(N))


def mat_vec(mat: list[list[int]], vec: list[Fraction]) -> list[Fraction]:
    return [sum(Fraction(mat[i][j]) * vec[j] for j in range(N)) for i in range(N)]


def channel_rank(mat: list[list[int]], basis: list[list[Fraction]]) -> int:
    return rank_vectors([mat_vec(mat, b) for b in basis])


def scalar_on_basis(mat: list[list[int]], basis: list[list[Fraction]]) -> dict:
    scalar: Fraction | None = None
    for b in basis:
        image = mat_vec(mat, b)
        lam = None
        for idx, val in enumerate(b):
            if val != 0:
                lam = image[idx] / val
                break
        if lam is None:
            continue
        if any(image[i] != lam * b[i] for i in range(N)):
            return {"is_scalar": False, "scalar": None}
        if scalar is None:
            scalar = lam
        elif scalar != lam:
            return {"is_scalar": False, "scalar": None}
    return {"is_scalar": True, "scalar": frac_to_json(scalar if scalar is not None else Fraction(0))}


def row_col_sums_ok(mat: list[list[int]], row_size: int) -> bool:
    return all(sum(row) == row_size for row in mat) and all(sum(mat[i][j] for i in range(N)) == row_size for j in range(N))


def orbit_sizes_from_gens(gens: list[MatrixF2]) -> list[int]:
    remaining = set(range(1, 64))
    sizes = []
    while remaining:
        start = min(remaining)
        orbit = {start}
        q = deque([start])
        while q:
            v = q.popleft()
            for g in gens:
                w = apply_matrix(g, v)
                if w not in orbit:
                    orbit.add(w)
                    q.append(w)
        sizes.append(len(orbit))
        remaining -= orbit
    return sorted(sizes)


def subgroup_projection_summary(row_size: int, rank: int, dim: int) -> dict:
    return {"type": "projection", "eigenvalue_multiplicities": {str(row_size): rank, "0": dim - rank}}


def row_report(label: str, kind: str, size: int, mat: list[list[int]], basis27, basis35, std_basis, gens: list[MatrixF2] | None = None) -> dict:
    rank27 = channel_rank(mat, basis27)
    rank35 = channel_rank(mat, basis35)
    rank_std = channel_rank(mat, std_basis)
    scalar27 = scalar_on_basis(mat, basis27)
    scalar35 = scalar_on_basis(mat, basis35)
    if kind == "subgroup":
        spectrum27 = scalar27 if scalar27["is_scalar"] else subgroup_projection_summary(size, rank27, len(basis27))
        spectrum35 = scalar35 if scalar35["is_scalar"] else subgroup_projection_summary(size, rank35, len(basis35))
    else:
        spectrum27 = scalar27
        spectrum35 = scalar35
    return {
        "label": label,
        "kind": kind,
        "row_size": size,
        "row_col_sums_ok": row_col_sums_ok(mat, size),
        "orbit_sizes_on_Pi63": orbit_sizes_from_gens(gens) if gens is not None else None,
        "rank_std": rank_std,
        "rank_U27": rank27,
        "rank_U35": rank35,
        "rank_additivity_check": rank_std == rank27 + rank35,
        "spectrum_U27": spectrum27,
        "spectrum_U35": spectrum35,
        "aggregate_matrix_sha256": sha256_json_payload(mat),
    }


def eigenspace_bases(A: list[list[int]]) -> tuple[list[list[Fraction]], list[list[Fraction]], list[list[Fraction]]]:
    basis27 = nullspace([[A[i][j] - (4 if i == j else 0) for j in range(N)] for i in range(N)])
    basis35 = nullspace([[A[i][j] - (-4 if i == j else 0) for j in range(N)] for i in range(N)])
    return basis27, basis35, basis27 + basis35


def simple_generator_matrices() -> tuple[list[MatrixF2], dict]:
    pairs = s6.s4.projective_pairs()
    A_root = s6.gram_adjacency(pairs)
    perms = s6.simple_reflection_perms(pairs)
    f2 = s6.build_f2_model(A_root)
    matrices = [s6.matrix_from_perm(p, f2["vertex_to_f2_coord"], f2["coord_to_vertex"]) for p in perms]
    return matrices, {
        "basis_vertices": f2["basis_vertices"],
        "vertex_to_f2_coord_sha256": sha256_json_payload(f2["vertex_to_f2_coord"]),
        "f2_checks": f2["checks"],
    }


def parabolic_label(combo: tuple[int, ...]) -> str:
    return "Par_" + "".join(str(i + 1) for i in combo)


def compact_row(row: dict) -> dict:
    return {
        "label": row["label"],
        "kind": row["kind"],
        "row_size": row["row_size"],
        "rank_std": row["rank_std"],
        "rank_U27": row["rank_U27"],
        "rank_U35": row["rank_U35"],
        "orbit_sizes_on_Pi63": row["orbit_sizes_on_Pi63"],
        "rank_additivity_check": row["rank_additivity_check"],
    }


def pair_witnesses(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    same_rank_split = []
    same_size_rank_split = []
    same_size_orbit_split = []
    for a, b in combinations(rows, 2):
        split_a = (a["rank_U27"], a["rank_U35"])
        split_b = (b["rank_U27"], b["rank_U35"])
        if split_a == split_b:
            continue
        if a["rank_std"] == b["rank_std"]:
            item = {
                "A": a["label"],
                "B": b["label"],
                "rank_std": a["rank_std"],
                "A_split_U27_U35": list(split_a),
                "B_split_U27_U35": list(split_b),
                "A_size": a["row_size"],
                "B_size": b["row_size"],
                "A_orbits": a["orbit_sizes_on_Pi63"],
                "B_orbits": b["orbit_sizes_on_Pi63"],
            }
            same_rank_split.append(item)
            if a["row_size"] == b["row_size"]:
                same_size_rank_split.append(item)
        if (
            a["row_size"] == b["row_size"]
            and a["orbit_sizes_on_Pi63"] is not None
            and b["orbit_sizes_on_Pi63"] is not None
            and a["orbit_sizes_on_Pi63"] == b["orbit_sizes_on_Pi63"]
        ):
            same_size_orbit_split.append({
                "A": a["label"],
                "B": b["label"],
                "row_size": a["row_size"],
                "orbit_sizes": a["orbit_sizes_on_Pi63"],
                "A_rank_std": a["rank_std"],
                "B_rank_std": b["rank_std"],
                "A_split_U27_U35": list(split_a),
                "B_split_U27_U35": list(split_b),
            })
    return same_rank_split, same_size_rank_split, same_size_orbit_split

def main() -> None:
    print(json.dumps({
        "module": "e7_projective_source_rows",
        "role": "helper",
        "entry_point": "scripts/e7_projective_source_channel_replay.py",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()