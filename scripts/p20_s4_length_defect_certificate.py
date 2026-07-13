#!/usr/bin/env python3
"""P20-S4 length-defect theorem certificate.

This is a theorem-support replay for the locked G2 12-root shadow.  It checks
that every admitted nonempty length-preserving row has the length line
u_len = 1_short - 1_long as a nonzero global-standard eigenline of the centered
operator.  Therefore no such row is globally position-value balanced on all
12 roots.
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
    LENGTH_LINE,
    N,
    ONES,
    SHORT,
    LONG,
    row_defs,
    row_operator,
    mat_vec,
    length_preserving,
)


def dot(a: list[int], b: list[int]) -> int:
    return sum(x * y for x, y in zip(a, b))


def j_image(vec: list[int]) -> list[int]:
    total = sum(vec)
    return [total for _ in vec]


def centered_image(mat: list[list[int]], row_size: int, vec: list[int]) -> list[Fraction]:
    image = mat_vec(mat, vec)
    jv = j_image(vec)
    return [Fraction(image[i], 1) - Fraction(row_size, N) * jv[i] for i in range(N)]


def multiples(vec: list[Fraction] | list[int], base: list[int]) -> Fraction | None:
    scalar: Fraction | None = None
    for x, b in zip(vec, base):
        xq = Fraction(x, 1) if isinstance(x, int) else x
        if b == 0:
            if xq != 0:
                return None
            continue
        candidate = xq / b
        if scalar is None:
            scalar = candidate
        elif scalar != candidate:
            return None
    return scalar if scalar is not None else Fraction(0, 1)


def main() -> int:
    rows = row_defs()
    failures: list[str] = []
    checked_rows = []

    length_line_sum = sum(LENGTH_LINE)
    length_line_in_global_standard = length_line_sum == 0
    j_kills_length_line = j_image(LENGTH_LINE) == [0] * N
    length_line_nonzero = any(x != 0 for x in LENGTH_LINE)

    if not length_line_in_global_standard:
        failures.append("length_line_not_in_global_standard")
    if not j_kills_length_line:
        failures.append("J_does_not_kill_length_line")
    if not length_line_nonzero:
        failures.append("length_line_zero")

    for row_id, row in rows.items():
        row_size = len(row)
        op = row_operator(row)
        all_length_preserving = all(length_preserving(p) for p in row)
        raw_image = mat_vec(op, LENGTH_LINE)
        centered = centered_image(op, row_size, LENGTH_LINE)
        raw_scalar = multiples(raw_image, LENGTH_LINE)
        centered_scalar = multiples(centered, LENGTH_LINE)
        expected = Fraction(row_size, 1)
        nonzero_obstruction = centered_scalar == expected and expected != 0
        row_ok = (
            row_size > 0
            and all_length_preserving
            and raw_scalar == expected
            and centered_scalar == expected
            and nonzero_obstruction
        )
        if not row_ok:
            failures.append(f"{row_id}:length_defect_check_failed")
        checked_rows.append(
            {
                "row_id": row_id,
                "size": row_size,
                "all_elements_length_preserving": all_length_preserving,
                "N_X_u_len_scalar": str(raw_scalar),
                "E_X_u_len_scalar": str(centered_scalar),
                "J_u_len_zero": j_kills_length_line,
                "global_balance_blocked": nonzero_obstruction,
                "status": "PASS" if row_ok else "FAIL",
            }
        )

    result = {
        "project": "P20_g2_hexagonal_weyl_shadows",
        "gate": "P20-S4",
        "status": "PASS" if not failures else "FAIL",
        "theorem_candidate": "For every nonempty admitted length-preserving source row X, the centered operator E_X has u_len as an eigenline with eigenvalue |X|; hence global balance on all 12 roots is impossible.",
        "labels": LABELS,
        "short_orbit": [LABELS[i] for i in SHORT],
        "long_orbit": [LABELS[i] for i in LONG],
        "u_len": LENGTH_LINE,
        "u_len_dot_ones": dot(LENGTH_LINE, ONES),
        "length_line_in_global_standard": length_line_in_global_standard,
        "J_kills_length_line": j_kills_length_line,
        "rows_checked": checked_rows,
        "failures": failures,
        "boundary": "This proves a length-color obstruction inside the locked G2 12-root shadow. It is not a new general Weyl/Coxeter theorem and does not imply tiling or classification claims.",
        "historical_next_gate_at_s4_closeout": "P20-S5 orbit-centered balance and base ranks", "current_next_gate_after_s5": "P20-S6 two-mirror root-shadow transfer",
    }

    repo = Path(__file__).resolve().parents[1]
    results = repo / "results"
    results.mkdir(exist_ok=True)
    json_path = results / "p20_s4_length_defect_certificate.json"
    md_path = results / "p20_s4_length_defect_certificate_summary.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# P20-S4 Length-Defect Certificate Summary",
        "",
        f"Status: {result['status']}",
        "",
        "## Certified Mechanism",
        "",
        "The length line `u_len = 1_short - 1_long` lies in the global standard channel because its coordinate sum is zero.",
        "The all-ones operator `J` kills `u_len`. Since every admitted row preserves the short/long partition, `N_X u_len = |X| u_len`; therefore the centered operator `E_X = N_X - (|X|/12)J` also satisfies `E_X u_len = |X| u_len`.",
        "",
        "Consequently no nonempty admitted row is globally balanced on all 12 roots.",
        "",
        "## Checked Rows",
        "",
        "| Row | Size | N_X scalar on u_len | E_X scalar on u_len | Global balance blocked |",
        "|---|---:|---:|---:|---|",
    ]
    for row in checked_rows:
        lines.append(
            f"| `{row['row_id']}` | {row['size']} | {row['N_X_u_len_scalar']} | "
            f"{row['E_X_u_len_scalar']} | {row['global_balance_blocked']} |"
        )
    lines.extend([
        "",
        "## Boundary",
        "",
        result["boundary"],
        "",
        "Historical next task at S4 closeout: P20-S5 orbit-centered balance and base ranks. Current next task after S5: P20-S6 two-mirror root-shadow transfer.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({"status": result["status"], "json": str(json_path), "md": str(md_path)}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
