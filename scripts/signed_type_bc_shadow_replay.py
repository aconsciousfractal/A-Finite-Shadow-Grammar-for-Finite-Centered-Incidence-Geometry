#!/usr/bin/env python3
"""Public X15 adapter for the selected P14 independent recompute."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DEFAULT_OUT = ROOT / "artifacts" / "signed_type_bc_shadow_replay.json"
VERIFY_OUTPUT_DIR = ROOT / "artifacts" / ".verify"

EXPECTED_ROWS = {
    "BI3_0_0": (16, 90),
    "BI3_0_1": (12, 300),
    "BI3_1_0": (12, 300),
    "S6_deterministic_random_size_B3": (48, 715),
    "BI4_0_1": (64, 10710),
    "BI4_1_1": (48, 17220),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recompute", action="store_true")
    parser.add_argument("--out", "--output", dest="output", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def validate_output(
    output: Path,
    recompute: bool,
) -> tuple[Path | None, str | None]:
    target = output if output.is_absolute() else ROOT / output
    try:
        lexical = target.absolute()
        resolved = target.resolve()
        root_lexical = ROOT.absolute()
        root_resolved = ROOT.resolve()
        verify_lexical = VERIFY_OUTPUT_DIR.absolute()
        verify_resolved = VERIFY_OUTPUT_DIR.resolve()
    except (OSError, RuntimeError, UnicodeError) as exc:
        return None, f"resolve_failed:{type(exc).__name__}"

    touches_package = (
        lexical.is_relative_to(root_lexical)
        or resolved.is_relative_to(root_resolved)
    )
    if touches_package:
        if recompute:
            expected_verify = root_resolved / "artifacts" / ".verify"
            safe = (
                lexical.is_relative_to(verify_lexical)
                and verify_resolved == expected_verify
                and resolved.is_relative_to(expected_verify)
            )
            if not safe:
                return (
                    None,
                    "recompute_output_must_be_under_artifacts_verify",
                )
        else:
            try:
                safe = (
                    lexical == DEFAULT_OUT.absolute()
                    and target.parent.resolve()
                    == root_resolved / "artifacts"
                )
            except (OSError, RuntimeError, UnicodeError):
                safe = False
            if not safe:
                return None, "audit_output_must_use_default_artifact"
    return target, None


def load_payload(recompute: bool) -> tuple[dict[str, Any], str]:
    if recompute:
        scripts = ROOT / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        source = importlib.import_module("p14_s7_independent_recompute")
        original_results = source.RESULTS
        original_docs = source.DOCS
        original_tables = source.TABLES
        original_certified = source.CERTIFIED
        original_write_outputs = source.write_outputs
        try:
            with TemporaryDirectory(prefix="p13_x15_") as temp_dir:
                scratch = Path(temp_dir)
                source.RESULTS = scratch / "results"
                source.DOCS = scratch / "docs"
                source.TABLES = scratch / "tables"
                source.CERTIFIED = scratch / "certified"
                source.write_outputs = lambda payload: None
                payload = source.run()
        finally:
            source.RESULTS = original_results
            source.DOCS = original_docs
            source.TABLES = original_tables
            source.CERTIFIED = original_certified
            source.write_outputs = original_write_outputs
        return payload, "independent_recompute"
    path = RESULTS / "p14_s7_independent_recompute.json"
    return json.loads(path.read_text(encoding="utf-8")), "frozen_result_audit"


def main() -> int:
    args = parse_args()
    output, output_error = validate_output(args.output, args.recompute)
    if output is None or output_error is not None:
        print(
            f"Unsafe X15 output: {output_error or 'invalid_output'}",
            file=sys.stderr,
        )
        return 2
    try:
        if output.is_dir():
            print("Unsafe X15 output: output_is_directory", file=sys.stderr)
            return 2
        if output.exists() or output.is_symlink():
            output.unlink()
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(
            f"Unsafe X15 output: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    payload, mode = load_payload(args.recompute)
    summary = payload.get("summary", {})
    source_checks = summary.get("checks", {})
    rows = list(payload.get("s4_surface", {}).get("rows", []))
    rows.extend(payload.get("b4_recompute", {}).get("rows", []))
    by_id = {row.get("object_id"): row for row in rows}

    table = {}
    row_checks = {}
    for row_id, (expected_size, expected_mass) in EXPECTED_ROWS.items():
        row = by_id.get(row_id, {})
        size = row.get("size_recomputed")
        mass = row.get("rank_mass_recomputed_left_ideal_mod_p")
        table[row_id] = {"size": size, "rank_mass": mass}
        row_checks[row_id] = (
            size == expected_size
            and mass == expected_mass
            and row.get("size_matches") is True
            and row.get("rank_mass_matches") is True
        )

    checks = {
        "source_status_pass": summary.get("status") == "PASS",
        "source_checks_all": bool(source_checks) and all(value is True for value in source_checks.values()),
        "six_rows_present": set(table) == set(EXPECTED_ROWS),
        "six_rows_exact": all(row_checks.values()),
        "mirror_checks_pass": summary.get("mirror_checks_pass") is True,
        "boundary_retained": "no classification" in str(summary.get("boundary", "")),
    }
    passed = all(checks.values())
    artifact = {
        "artifact": "signed_type_bc_shadow_replay",
        "status": "PASS_SIGNED_TYPE_BC_SHADOW" if passed else "FAIL_SIGNED_TYPE_BC_SHADOW",
        "pass": passed,
        "mode": mode,
        "checks": checks,
        "row_checks": row_checks,
        "table": table,
        "boundary": "six bounded P13 rows; no Type-B/C classification, tiling criterion, or native equivalence",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pass": passed, "status": artifact["status"], "mode": mode, "output": str(output)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
