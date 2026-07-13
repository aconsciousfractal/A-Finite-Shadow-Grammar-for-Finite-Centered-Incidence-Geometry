#!/usr/bin/env python3
"""Short deterministic audit of the frozen X05 census and lat565 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "x05"
DEFAULT_OUT = ROOT / "artifacts" / "x05_m19_lat565_evidence_check.json"


def load(name: str) -> Any:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def digest(name: str) -> str:
    return hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest().upper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", "--output", dest="output", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load("census_rows1000_v2.json")
    summary = load("census_summary1000_v2.json")
    pair = load("lat565_pair_dependency_verification.json")
    linear = load("lat565_global_rankdrop_linearization.json")
    linear_check = load("lat565_global_linearization_check.json")

    tag_counts = Counter(row.get("tag") for row in rows)
    sudoku_types = Counter(str(row.get("type")) for row in rows if row.get("tag") == "sudoku")
    latin_types = Counter(str(row.get("type")) for row in rows if row.get("tag") == "latin")
    equiv_types = Counter(str(row.get("type")) for row in rows if row.get("tag") == "m19_equiv")
    lat565_rows = [row for row in rows if row.get("grid_id") == "lat565"]
    complement_count = sum(
        row.get("k_class", {}).get("has_complement") is True
        for row in rows
    )

    pair_checks = {
        "pair_status_pass": pair.get("status") == "PASS",
        "pair_rank_locus_62": pair.get("rank_locus_replay", {}).get("exact_rank_drop_count") == 62,
        "pair_coset_32": pair.get("pair_dependency", {}).get("criterion_count") == 32,
        "pair_coset_exact": pair.get("pair_dependency", {}).get("criterion_equals_stored_coset") is True,
        "pair_group_order_32": pair.get("group_mechanism", {}).get("generated_order") == 32,
        "pair_left_not_right": (
            pair.get("group_mechanism", {}).get("stored_coset_is_left_K_pi") is True
            and pair.get("group_mechanism", {}).get("stored_coset_is_right_pi_K") is False
        ),
    }
    linear_checks = linear_check.get("checks", {})

    checks = {
        "rows_are_list": isinstance(rows, list),
        "row_count_2009": len(rows) == 2009,
        "tag_counts": tag_counts == Counter({"sudoku": 1000, "latin": 1000, "m19_equiv": 8, "m19": 1}),
        "summary_seed": summary.get("seed") == 12345,
        "summary_sudoku_n": summary.get("sudoku", {}).get("n") == 1000,
        "summary_latin_n": summary.get("latin", {}).get("n") == 1000,
        "summary_equiv_n": summary.get("m19_equiv", {}).get("n") == 8,
        "sudoku_type_distribution": sudoku_types == Counter(summary.get("sudoku", {}).get("type_dist", {})),
        "latin_type_distribution": latin_types == Counter(summary.get("latin", {}).get("type_dist", {})),
        "equiv_type_distribution": equiv_types == Counter(summary.get("m19_equiv", {}).get("type_dist", {})),
        "complement_count_2009": complement_count == 2009,
        "lat565_unique": len(lat565_rows) == 1,
        "lat565_rank_locus_62": len(lat565_rows) == 1 and lat565_rows[0].get("Gamma_rank_size") == 62,
        "lat565_group_order_32": len(lat565_rows) == 1 and lat565_rows[0].get("group", {}).get("order") == 32,
        "linear_decomposition_32_8_22": linear.get("decomposition_counts") == {
            "C32_pair_coset": 32,
            "C8_second_pair_equality": 8,
            "R22_sporadic_residual": 22,
        },
        "pair_checks_all": all(pair_checks.values()),
        "linear_check_status": linear_check.get("status") == "PASS",
        "linear_checks_all": bool(linear_checks) and all(value is True for value in linear_checks.values()),
    }
    passed = all(checks.values())
    artifact = {
        "artifact": "x05_m19_lat565_evidence_check",
        "status": "PASS_FROZEN_EVIDENCE_AUDIT" if passed else "FAIL_FROZEN_EVIDENCE_AUDIT",
        "pass": passed,
        "checks": checks,
        "counts": {
            "rows": len(rows),
            "tags": dict(sorted(tag_counts.items(), key=lambda item: str(item[0]))),
            "complement_witnesses": complement_count,
            "lat565_decomposition": linear.get("decomposition_counts"),
        },
        "source_sha256": {
            name: digest(name)
            for name in [
                "census_rows1000_v2.json",
                "census_summary1000_v2.json",
                "lat565_pair_dependency_verification.json",
                "lat565_global_rankdrop_linearization.json",
                "lat565_global_linearization_check.json",
            ]
        },
        "pair_checks": pair_checks,
        "boundary": "audit of frozen empirical evidence; no census regeneration and no mechanism theorem",
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pass": passed, "status": artifact["status"], "output": str(output)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
