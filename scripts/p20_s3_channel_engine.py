#!/usr/bin/env python3
"""P20-S3 channel engine and convention replay.

This script fixes exact channel conventions for the source-locked G2 12-root
finite shadow. It is an engine/convention gate: numerical ranks are smoke
checks for later theorem gates, not promoted mathematical claims.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Iterable

MOD = 6
LABELS = [f"S{i}" for i in range(MOD)] + [f"L{i}" for i in range(MOD)]
SHORT = tuple(range(0, MOD))
LONG = tuple(range(MOD, 2 * MOD))
N = len(LABELS)
IDENTITY = tuple(range(N))

Perm = tuple[int, ...]
Matrix = list[list[int]]


def s(i: int) -> int:
    return i % MOD


def l(i: int) -> int:
    return MOD + (i % MOD)


def compose(p: Perm, q: Perm) -> Perm:
    """Return p after q, with permutations represented by images p[i]."""
    return tuple(p[q[i]] for i in range(len(p)))


def rotation(a: int) -> Perm:
    return tuple([s(i + a) for i in range(MOD)] + [l(i + a) for i in range(MOD)])


def reflection(a: int) -> Perm:
    return tuple([s(a - i) for i in range(MOD)] + [l(a - i - 1) for i in range(MOD)])


def row_defs() -> dict[str, list[Perm]]:
    rotations = [rotation(a) for a in range(MOD)]
    reflections = [reflection(a) for a in range(MOD)]
    rows: dict[str, list[Perm]] = {
        "W": rotations + reflections,
        "C": rotations,
        "F": reflections,
        "F_short_axis": [reflection(a) for a in (0, 2, 4)],
        "F_long_axis": [reflection(a) for a in (1, 3, 5)],
    }
    for a in range(1, MOD):
        rows[f"X_{a}"] = [reflection(0), reflection(a)]
    return rows


def perm_matrix(p: Perm) -> Matrix:
    mat = [[0 for _ in range(N)] for _ in range(N)]
    for domain, image in enumerate(p):
        mat[image][domain] = 1
    return mat


def row_operator(row: Iterable[Perm]) -> Matrix:
    mat = [[0 for _ in range(N)] for _ in range(N)]
    for p in row:
        pm = perm_matrix(p)
        for i in range(N):
            for j in range(N):
                mat[i][j] += pm[i][j]
    return mat


def mat_vec(mat: Matrix, vec: list[int]) -> list[int]:
    return [sum(mat[i][j] * vec[j] for j in range(len(vec))) for i in range(len(mat))]


def exact_rank(mat: list[list[int]]) -> int:
    if not mat:
        return 0
    a = [[Fraction(x) for x in row] for row in mat]
    rows = len(a)
    cols = len(a[0]) if rows else 0
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
        pv = a[pivot_row][col]
        a[pivot_row] = [x / pv for x in a[pivot_row]]
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


def basis_vector(pos: int, neg: int) -> list[int]:
    v = [0] * N
    v[pos] = 1
    v[neg] = -1
    return v


GLOBAL_BASIS = [basis_vector(i, N - 1) for i in range(N - 1)]
SHORT_BASIS = [basis_vector(i, MOD - 1) for i in range(MOD - 1)]
LONG_BASIS = [basis_vector(MOD + i, N - 1) for i in range(MOD - 1)]
ORBIT_BASIS = SHORT_BASIS + LONG_BASIS
LENGTH_LINE = [1 if i in SHORT else -1 for i in range(N)]
ONES = [1] * N


def coords_global(vec: list[int]) -> list[int]:
    assert sum(vec) == 0
    return vec[: N - 1]


def coords_short(vec: list[int]) -> list[int]:
    assert all(vec[i] == 0 for i in LONG)
    assert sum(vec[i] for i in SHORT) == 0
    return [vec[i] for i in range(MOD - 1)]


def coords_long(vec: list[int]) -> list[int]:
    assert all(vec[i] == 0 for i in SHORT)
    assert sum(vec[i] for i in LONG) == 0
    return [vec[MOD + i] for i in range(MOD - 1)]


def coords_orbit(vec: list[int]) -> list[int]:
    assert sum(vec[i] for i in SHORT) == 0
    assert sum(vec[i] for i in LONG) == 0
    return [vec[i] for i in range(MOD - 1)] + [vec[MOD + i] for i in range(MOD - 1)]


def restricted_matrix(mat: Matrix, basis: list[list[int]], coord_fn) -> list[list[int]]:
    cols = [coord_fn(mat_vec(mat, b)) for b in basis]
    if not cols:
        return []
    return [[cols[j][i] for j in range(len(cols))] for i in range(len(cols[0]))]


def length_line_scalar(mat: Matrix) -> int | None:
    image = mat_vec(mat, LENGTH_LINE)
    if all(image[i] == image[0] for i in SHORT) and all(image[i] == image[MOD] for i in LONG) and image[0] == -image[MOD]:
        return image[0]
    return None


def row_col_sums(mat: Matrix) -> dict[str, object]:
    return {
        "row_sums": [sum(row) for row in mat],
        "col_sums": [sum(mat[i][j] for i in range(N)) for j in range(N)],
    }


def length_preserving(p: Perm) -> bool:
    return set(p[i] for i in SHORT) == set(SHORT) and set(p[i] for i in LONG) == set(LONG)


def fixed_profile(p: Perm) -> dict[str, int]:
    return {
        "fixed_short": sum(1 for i in SHORT if p[i] == i),
        "fixed_long": sum(1 for i in LONG if p[i] == i),
    }


def image_multiplicity(row: list[Perm], domain: tuple[int, ...]) -> int | None:
    values = set()
    for i in domain:
        counts = {j: 0 for j in domain}
        for p in row:
            counts[p[i]] += 1
        values.update(counts.values())
    return values.pop() if len(values) == 1 else None


def matrix_signature(mat: list[list[int]]) -> dict[str, object]:
    return {
        "rows": len(mat),
        "cols": len(mat[0]) if mat else 0,
        "rank_Q": exact_rank(mat),
    }


def main() -> int:
    rows = row_defs()
    result_rows = []
    failures: list[str] = []

    channel_dimensions = {
        "ambient": N,
        "trivial_line": 1,
        "global_standard": len(GLOBAL_BASIS),
        "length_line": 1,
        "short_standard": len(SHORT_BASIS),
        "long_standard": len(LONG_BASIS),
        "orbit_centered": len(ORBIT_BASIS),
    }

    for row_id, row in rows.items():
        op = row_operator(row)
        sums = row_col_sums(op)
        all_length = all(length_preserving(p) for p in row)
        global_mat = restricted_matrix(op, GLOBAL_BASIS, coords_global)
        short_mat = restricted_matrix(op, SHORT_BASIS, coords_short)
        long_mat = restricted_matrix(op, LONG_BASIS, coords_long)
        orbit_mat = restricted_matrix(op, ORBIT_BASIS, coords_orbit)
        length_scalar = length_line_scalar(op)

        checks = {
            "all_elements_length_preserving": all_length,
            "row_sums_equal_size": all(x == len(row) for x in sums["row_sums"]),
            "col_sums_equal_size": all(x == len(row) for x in sums["col_sums"]),
            "length_line_eigen_scalar_equals_size": length_scalar == len(row),
            "global_dim_decomposes": channel_dimensions["global_standard"] == channel_dimensions["length_line"] + channel_dimensions["orbit_centered"],
        }
        for name, ok in checks.items():
            if not ok:
                failures.append(f"{row_id}:{name}")

        reflection_profiles = [fixed_profile(p) for p in row]
        result_rows.append(
            {
                "row_id": row_id,
                "size": len(row),
                "checks": checks,
                "short_uniform_multiplicity": image_multiplicity(row, SHORT),
                "long_uniform_multiplicity": image_multiplicity(row, LONG),
                "length_profile": {
                    "fixed_short_counts": sorted(fp["fixed_short"] for fp in reflection_profiles),
                    "fixed_long_counts": sorted(fp["fixed_long"] for fp in reflection_profiles),
                },
                "channel_smoke_ranks": {
                    "global_standard_rank_Q": exact_rank(global_mat),
                    "length_line_rank_Q": 1 if length_scalar else 0,
                    "short_standard_rank_Q": exact_rank(short_mat),
                    "long_standard_rank_Q": exact_rank(long_mat),
                    "orbit_centered_rank_Q": exact_rank(orbit_mat),
                },
                "channel_matrix_signatures": {
                    "global_standard": matrix_signature(global_mat),
                    "short_standard": matrix_signature(short_mat),
                    "long_standard": matrix_signature(long_mat),
                    "orbit_centered": matrix_signature(orbit_mat),
                },
                "length_line_scalar": length_scalar,
            }
        )

    result = {
        "project": "P20_g2_hexagonal_weyl_shadows",
        "gate": "P20-S3",
        "status": "PASS" if not failures else "FAIL",
        "composition_convention": "compose(p,q)=p_after_q; permutation matrix has P[p[i]][i]=1",
        "labels": LABELS,
        "length_orbits": {
            "short": [LABELS[i] for i in SHORT],
            "long": [LABELS[i] for i in LONG],
        },
        "channel_dimensions": channel_dimensions,
        "channel_decomposition": "Q^Omega = Q*1 + Q*u_len + V_short^0 + V_long^0; global_standard = Q*u_len + orbit_centered",
        "u_len": LENGTH_LINE,
        "rows": result_rows,
        "failures": failures,
        "boundary": "S3 fixes engine/channel conventions only; channel ranks are smoke checks for later gates, not theorem promotion.",
        "historical_next_gate_at_s3_closeout": "P20-S4 length-defect theorem candidate", "current_next_gate_after_s4": "P20-S5 orbit-centered balance and base ranks",
    }

    repo = Path(__file__).resolve().parents[1]
    results = repo / "results"
    results.mkdir(exist_ok=True)
    json_path = results / "p20_s3_channel_engine.json"
    md_path = results / "p20_s3_channel_engine_summary.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# P20-S3 Channel Engine Summary",
        "",
        f"Status: {result['status']}",
        "",
        "## Channel Dimensions",
        "",
        "| Channel | Dimension |",
        "|---|---:|",
    ]
    for key in ["ambient", "trivial_line", "global_standard", "length_line", "short_standard", "long_standard", "orbit_centered"]:
        lines.append(f"| `{key}` | {channel_dimensions[key]} |")
    lines.extend([
        "",
        "## Row Smoke Ranks",
        "",
        "These are engine smoke outputs, not theorem promotions.",
        "",
        "| Row | Size | global std rank | length scalar | short rank | long rank | orbit rank |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in result_rows:
        ranks = row["channel_smoke_ranks"]
        lines.append(
            f"| `{row['row_id']}` | {row['size']} | {ranks['global_standard_rank_Q']} | "
            f"{row['length_line_scalar']} | {ranks['short_standard_rank_Q']} | "
            f"{ranks['long_standard_rank_Q']} | {ranks['orbit_centered_rank_Q']} |"
        )
    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
        "Historical next task at S3 closeout: P20-S4 length-defect theorem candidate. Current next task after S4: P20-S5 orbit-centered balance and base ranks.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({"status": result["status"], "json": str(json_path), "md": str(md_path)}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
