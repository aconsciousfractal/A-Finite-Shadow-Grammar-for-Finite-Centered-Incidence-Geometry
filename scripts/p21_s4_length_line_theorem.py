#!/usr/bin/env python3
"""P21-S4 length-line theorem verifier.

This verifier certifies the first P21 theorem for the geometric projective
F4 root shadow. It assumes only the projective Weyl layer built by
p21_f4_projective_root_engine.py and keeps the matroid layer pending.
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import p21_f4_projective_root_engine as eng  # noqa: E402


def mat_vec_mul(mat: List[List[Fraction]], vec: Sequence[Fraction]) -> List[Fraction]:
    return [sum(row[j] * vec[j] for j in range(len(vec))) for row in mat]


def subtract_matrices(a: List[List[Fraction]], b: List[List[Fraction]]) -> List[List[Fraction]]:
    return [[x - y for x, y in zip(row_a, row_b)] for row_a, row_b in zip(a, b)]


def zero_matrix(rows: int, cols: int) -> List[List[Fraction]]:
    return [[Fraction(0) for _ in range(cols)] for _ in range(rows)]


def matrix_is_zero(mat: List[List[Fraction]]) -> bool:
    return all(x == 0 for row in mat for x in row)


def matrix_distinct_values_by_block(mat: List[List[Fraction]], labels: Sequence[str]) -> Dict[str, List[str]]:
    buckets = {
        "long_long": set(),
        "short_short": set(),
        "long_short": set(),
        "short_long": set(),
    }
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            key = f"{li}_{lj}"
            buckets[key].add(mat[i][j])
    return {k: sorted(str(v) for v in vals) for k, vals in buckets.items()}


def build_projective_layer():
    roots = eng.f4_signed_roots_scaled()
    root_index = {v: i for i, v in enumerate(roots)}
    pair_reps, pair_index, _ = eng.projective_pairs(roots)
    labels = [eng.length_label(v) for v in pair_reps]
    gens = [eng.reflection_perm(a, roots, root_index) for a in eng.simple_roots_scaled()]
    w48 = eng.generate_group(gens, len(roots))
    g_proj = sorted({eng.project_perm(g, roots, pair_index, pair_reps, root_index) for g in w48})
    return pair_reps, labels, g_proj


def build_report() -> Dict[str, object]:
    pair_reps, labels, g_proj = build_projective_layer()
    degree = len(pair_reps)
    group_order = len(g_proj)
    length_counts = {lab: labels.count(lab) for lab in sorted(set(labels))}

    nmat = eng.row_sum_matrix(g_proj, degree)
    expected_n = zero_matrix(degree, degree)
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            if li == lj:
                expected_n[i][j] = Fraction(group_order, length_counts[li])
    n_matches_two_orbit_projection = nmat == expected_n

    global_center = [[Fraction(group_order, degree) for _ in range(degree)] for _ in range(degree)]
    global_e = subtract_matrices(nmat, global_center)
    length_centered = subtract_matrices(nmat, expected_n)

    u_len = [Fraction(1) if lab == "long" else Fraction(-1) for lab in labels]
    ones = [Fraction(1) for _ in labels]

    n_u = mat_vec_mul(nmat, u_len)
    e_u = mat_vec_mul(global_e, u_len)
    j_u = mat_vec_mul(global_center, u_len)
    e_ones = mat_vec_mul(global_e, ones)

    expected_n_u = [Fraction(group_order) * x for x in u_len]
    expected_e_u = [Fraction(group_order) * x for x in u_len]
    zero_vec = [Fraction(0) for _ in labels]

    report: Dict[str, object] = {
        "route_id": "P21",
        "gate": "S4",
        "verifier": "p21_s4_length_line_theorem.py",
        "scope": "full_projective_weyl_row_G_proj_only",
        "matroid_layer_status": "LOCKED_IN_S5_SEPARATE_GATE",
        "degree": degree,
        "group_order": group_order,
        "length_counts": length_counts,
        "two_orbit_matrix_entry": str(Fraction(group_order, 12)),
        "global_center_entry": str(Fraction(group_order, degree)),
        "N_distinct_values_by_block": matrix_distinct_values_by_block(nmat, labels),
        "E_global_distinct_values_by_block": matrix_distinct_values_by_block(global_e, labels),
        "N_matches_two_orbit_projection": n_matches_two_orbit_projection,
        "N_u_len_equals_group_order_u_len": n_u == expected_n_u,
        "J_u_len_equals_zero": j_u == zero_vec,
        "E_global_u_len_equals_group_order_u_len": e_u == expected_e_u,
        "E_global_kills_ones": e_ones == zero_vec,
        "E_global_rank": eng.rank_fraction(global_e),
        "E_length_centered_zero_matrix": matrix_is_zero(length_centered),
        "E_length_centered_rank": eng.rank_fraction(length_centered),
        "expected": {
            "degree": 24,
            "group_order": 576,
            "length_counts": {"long": 12, "short": 12},
            "N_matches_two_orbit_projection": True,
            "N_u_len_equals_group_order_u_len": True,
            "J_u_len_equals_zero": True,
            "E_global_u_len_equals_group_order_u_len": True,
            "E_global_kills_ones": True,
            "E_global_rank": 1,
            "E_length_centered_zero_matrix": True,
            "E_length_centered_rank": 0,
        },
    }
    report["pass"] = all(report[k] == v for k, v in report["expected"].items())  # type: ignore[index,union-attr]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", action="store_true")
    parser.add_argument("--json-path", default=None)
    args = parser.parse_args()

    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)

    if args.write_json:
        if args.json_path:
            out = Path(args.json_path)
        else:
            out = Path(__file__).resolve().parents[1] / "results" / "p21_s4_length_line_theorem_replay.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")

    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
