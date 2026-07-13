#!/usr/bin/env python3
"""P20-S6 two-mirror root-shadow transfer.

For X_a={tau_0,tau_a}, verify that the short block is the P19 two-mirror
row {s_0,s_a}, the long block is the shifted two-mirror row {s_-1,s_{a-1}},
and both have the same standard rank.  Hence the orbit-centered rank is twice
the P19 vertex rank, while the global standard rank adds the length line.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from p20_s3_channel_engine import (  # noqa: E402
    MOD,
    SHORT,
    LONG,
    row_defs,
    row_operator,
    restricted_matrix,
    exact_rank,
    GLOBAL_BASIS,
    SHORT_BASIS,
    LONG_BASIS,
    ORBIT_BASIS,
    coords_global,
    coords_short,
    coords_long,
    coords_orbit,
)


def block_matrix(mat: list[list[int]], domain: tuple[int, ...], codomain: tuple[int, ...]) -> list[list[int]]:
    return [[mat[i][j] for j in domain] for i in codomain]


def p19_reflection(c: int, m: int = MOD) -> tuple[int, ...]:
    return tuple((c - i) % m for i in range(m))


def p19_perm_matrix(p: tuple[int, ...]) -> list[list[int]]:
    m = len(p)
    mat = [[0 for _ in range(m)] for _ in range(m)]
    for domain, image in enumerate(p):
        mat[image][domain] = 1
    return mat


def p19_row_operator(params: tuple[int, int], m: int = MOD) -> list[list[int]]:
    mat = [[0 for _ in range(m)] for _ in range(m)]
    for c in params:
        pm = p19_perm_matrix(p19_reflection(c, m))
        for i in range(m):
            for j in range(m):
                mat[i][j] += pm[i][j]
    return mat


def p19_vertex_rank(a: int, m: int = MOD) -> int:
    d = math.gcd(a, m)
    quotient = m // d
    return (m - 1) - (d if quotient % 2 == 0 else 0)


def mat_equal(a: list[list[int]], b: list[list[int]]) -> bool:
    return a == b


def rank_on(mat: list[list[int]], basis: list[list[int]], coord_fn) -> int:
    return exact_rank(restricted_matrix(mat, basis, coord_fn))


def main() -> int:
    rows = row_defs()
    failures: list[str] = []
    records = []

    for a in range(1, MOD):
        row_id = f"X_{a}"
        row = rows[row_id]
        op = row_operator(row)
        short_block = block_matrix(op, SHORT, SHORT)
        long_block = block_matrix(op, LONG, LONG)
        expected_short = p19_row_operator((0, a))
        expected_long = p19_row_operator((-1, a - 1))
        vertex_rank = p19_vertex_rank(a)
        d = math.gcd(a, MOD)
        quotient = MOD // d

        short_rank = rank_on(op, SHORT_BASIS, coords_short)
        long_rank = rank_on(op, LONG_BASIS, coords_long)
        orbit_rank = rank_on(op, ORBIT_BASIS, coords_orbit)
        global_rank = rank_on(op, GLOBAL_BASIS, coords_global)
        predicted_orbit = 2 * vertex_rank
        predicted_global = 1 + predicted_orbit

        checks = {
            "short_block_is_P19_s0_sa": mat_equal(short_block, expected_short),
            "long_block_is_P19_shifted_pair": mat_equal(long_block, expected_long),
            "short_rank_matches_vertex_formula": short_rank == vertex_rank,
            "long_rank_matches_vertex_formula": long_rank == vertex_rank,
            "orbit_rank_is_twice_vertex_rank": orbit_rank == predicted_orbit,
            "global_rank_adds_length_line": global_rank == predicted_global,
        }
        if not all(checks.values()):
            failures.append(f"{row_id}:two_mirror_transfer_failed")

        records.append(
            {
                "row_id": row_id,
                "a": a,
                "gcd_a_6": d,
                "quotient_6_over_gcd": quotient,
                "quotient_even": quotient % 2 == 0,
                "p19_vertex_rank_formula": vertex_rank,
                "short_rank_Q": short_rank,
                "long_rank_Q": long_rank,
                "orbit_centered_rank_Q": orbit_rank,
                "global_standard_rank_Q": global_rank,
                "predicted_orbit_centered_rank": predicted_orbit,
                "predicted_global_standard_rank": predicted_global,
                "short_block_parameters": [0, a],
                "long_block_parameters": [-1, a - 1],
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "FAIL",
            }
        )

    result = {
        "project": "P20_g2_hexagonal_weyl_shadows",
        "gate": "P20-S6",
        "status": "PASS" if not failures else "FAIL",
        "statement": "For X_a={tau_0,tau_a}, the short and long blocks are shifted P19 two-mirror rows with the same difference a; rank_orbit=2*r_vertex(a) and rank_global=1+2*r_vertex(a).",
        "records": records,
        "failures": failures,
        "boundary": "S6 transfers the P19 two-mirror arithmetic to the locked G2 short/long root-shadow blocks only. It is not a new G2/Weyl theorem, classifier, or tiling claim.",
        "historical_next_gate_at_s6_closeout": "P20-S7 length-aware fingerprint witness",
        "current_next_gate_after_s7b": "P20-S8 optional controls or skip/defer decision",
    }

    repo = Path(__file__).resolve().parents[1]
    results = repo / "results"
    results.mkdir(exist_ok=True)
    json_path = results / "p20_s6_two_mirror_transfer.json"
    md_path = results / "p20_s6_two_mirror_transfer_summary.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# P20-S6 Two-Mirror Transfer Summary",
        "",
        f"Status: {result['status']}",
        "",
        "| Row | a | gcd(a,6) | 6/gcd | P19 rank r(a) | short rank | long rank | orbit rank | global rank |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rec in records:
        lines.append(
            f"| `{rec['row_id']}` | {rec['a']} | {rec['gcd_a_6']} | {rec['quotient_6_over_gcd']} | "
            f"{rec['p19_vertex_rank_formula']} | {rec['short_rank_Q']} | {rec['long_rank_Q']} | "
            f"{rec['orbit_centered_rank_Q']} | {rec['global_standard_rank_Q']} |"
        )
    lines.extend([
        "",
        "Formula: `r(a)=5-gcd(a,6)*1[(6/gcd(a,6)) is even]`, `rank_orbit=2r(a)`, `rank_global=1+2r(a)`.",
        "",
        "Boundary: locked P20/P19 transfer only; no general Weyl theorem, no classifier, no tiling claim.",
        "",
        "Historical next task at S6 closeout: P20-S7 length-aware fingerprint witness. Current next task: P20-S8 optional controls or skip/defer decision.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({"status": result["status"], "json": str(json_path), "md": str(md_path)}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())