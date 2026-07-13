#!/usr/bin/env python3
"""P20-S5 orbit-centered balance and base ranks.

This replay promotes the S3 smoke ranks for the base rows to theorem-support
status: W, C, and F vanish on V_short^0 + V_long^0, while the two reflection
half-classes have rank 1 on each length orbit and rank 2 on the orbit-centered
channel.
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from p20_s3_channel_engine import (  # noqa: E402
    LABELS,
    MOD,
    SHORT,
    LONG,
    row_defs,
    row_operator,
    mat_vec,
    exact_rank,
    restricted_matrix,
    SHORT_BASIS,
    LONG_BASIS,
    ORBIT_BASIS,
    coords_short,
    coords_long,
    coords_orbit,
)

BASE_ROWS = ("W", "C", "F", "F_short_axis", "F_long_axis")


def block_matrix(mat: list[list[int]], domain: tuple[int, ...], codomain: tuple[int, ...]) -> list[list[int]]:
    return [[mat[i][j] for j in domain] for i in codomain]


def all_entries_equal(mat: list[list[int]], value: int) -> bool:
    return all(x == value for row in mat for x in row)


def row_sums(mat: list[list[int]]) -> list[int]:
    return [sum(row) for row in mat]


def col_sums(mat: list[list[int]]) -> list[int]:
    return [sum(mat[i][j] for i in range(len(mat))) for j in range(len(mat[0]))]


def parity_mode(mat: list[list[int]]) -> str | None:
    """Return same/opposite if mat is the parity-incidence matrix, else None."""
    same = True
    opp = True
    for target in range(MOD):
        for domain in range(MOD):
            expected_same = 1 if (target % 2) == (domain % 2) else 0
            expected_opp = 1 if (target % 2) != (domain % 2) else 0
            if mat[target][domain] != expected_same:
                same = False
            if mat[target][domain] != expected_opp:
                opp = False
    if same:
        return "same_parity"
    if opp:
        return "opposite_parity"
    return None


def rank_restricted(mat: list[list[int]], basis: list[list[int]], coord_fn) -> int:
    return exact_rank(restricted_matrix(mat, basis, coord_fn))


def scaled_centered_block(mat: list[list[int]], row_size: int) -> list[list[int]]:
    """Return 6*N_block - row_size*J_6 to avoid fractions."""
    return [[MOD * mat[i][j] - row_size for j in range(MOD)] for i in range(MOD)]


def main() -> int:
    rows = row_defs()
    failures: list[str] = []
    records = []

    for row_id in BASE_ROWS:
        row = rows[row_id]
        op = row_operator(row)
        size = len(row)
        short_block = block_matrix(op, SHORT, SHORT)
        long_block = block_matrix(op, LONG, LONG)
        short_rank = rank_restricted(op, SHORT_BASIS, coords_short)
        long_rank = rank_restricted(op, LONG_BASIS, coords_long)
        orbit_rank = rank_restricted(op, ORBIT_BASIS, coords_orbit)
        short_uniform_q = None
        long_uniform_q = None
        if size % MOD == 0 and all_entries_equal(short_block, size // MOD):
            short_uniform_q = size // MOD
        if size % MOD == 0 and all_entries_equal(long_block, size // MOD):
            long_uniform_q = size // MOD

        short_centered_scaled_rank = exact_rank(scaled_centered_block(short_block, size))
        long_centered_scaled_rank = exact_rank(scaled_centered_block(long_block, size))
        short_mode = parity_mode(short_block)
        long_mode = parity_mode(long_block)

        if row_id in ("W", "C", "F"):
            ok = (
                short_uniform_q is not None
                and long_uniform_q is not None
                and short_rank == 0
                and long_rank == 0
                and orbit_rank == 0
                and short_centered_scaled_rank == 0
                and long_centered_scaled_rank == 0
            )
        else:
            ok = (
                short_uniform_q is None
                and long_uniform_q is None
                and short_rank == 1
                and long_rank == 1
                and orbit_rank == 2
                and short_mode in ("same_parity", "opposite_parity")
                and long_mode in ("same_parity", "opposite_parity")
            )
        if not ok:
            failures.append(f"{row_id}:orbit_centered_check_failed")

        records.append(
            {
                "row_id": row_id,
                "size": size,
                "short_block_row_sums": row_sums(short_block),
                "short_block_col_sums": col_sums(short_block),
                "long_block_row_sums": row_sums(long_block),
                "long_block_col_sums": col_sums(long_block),
                "short_uniform_multiplicity": short_uniform_q,
                "long_uniform_multiplicity": long_uniform_q,
                "short_parity_mode": short_mode,
                "long_parity_mode": long_mode,
                "short_standard_rank_Q": short_rank,
                "long_standard_rank_Q": long_rank,
                "orbit_centered_rank_Q": orbit_rank,
                "short_centered_scaled_rank_Q": short_centered_scaled_rank,
                "long_centered_scaled_rank_Q": long_centered_scaled_rank,
                "status": "PASS" if ok else "FAIL",
            }
        )

    result = {
        "project": "P20_g2_hexagonal_weyl_shadows",
        "gate": "P20-S5",
        "status": "PASS" if not failures else "FAIL",
        "theorem_support": {
            "orbit_balanced_rows": ["W", "C", "F"],
            "reflection_half_class_rows": ["F_short_axis", "F_long_axis"],
            "statement": "W, C, and F vanish on V_short^0 + V_long^0; each reflection half-class has rank 1 on each length orbit and rank 2 on the orbit-centered channel.",
        },
        "records": records,
        "failures": failures,
        "boundary": "S5 is a bounded orbit-centered rank theorem-support gate for the locked P20 rows only; it is not a general Weyl theorem or classifier claim.",
        "historical_next_gate_at_s5_closeout": "P20-S6 two-mirror root-shadow transfer", "current_next_gate_after_s6": "P20-S7 length-aware fingerprint witness",
    }

    repo = Path(__file__).resolve().parents[1]
    results = repo / "results"
    results.mkdir(exist_ok=True)
    json_path = results / "p20_s5_orbit_centered_balance.json"
    md_path = results / "p20_s5_orbit_centered_balance_summary.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# P20-S5 Orbit-Centered Balance Summary",
        "",
        f"Status: {result['status']}",
        "",
        "## Row Ranks",
        "",
        "| Row | Size | short uniform q | long uniform q | short parity mode | long parity mode | short rank | long rank | orbit rank |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in records:
        lines.append(
            f"| `{row['row_id']}` | {row['size']} | {row['short_uniform_multiplicity']} | "
            f"{row['long_uniform_multiplicity']} | {row['short_parity_mode']} | {row['long_parity_mode']} | "
            f"{row['short_standard_rank_Q']} | {row['long_standard_rank_Q']} | {row['orbit_centered_rank_Q']} |"
        )
    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
        "Historical next task at S5 closeout: P20-S6 two-mirror root-shadow transfer. Current next task after S6: P20-S7 length-aware fingerprint witness.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({"status": result["status"], "json": str(json_path), "md": str(md_path)}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())