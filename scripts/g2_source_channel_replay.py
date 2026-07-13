#!/usr/bin/env python3
"""Aggregate the selected bounded P20 computations used by P13/X19."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib
from io import StringIO
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DEFAULT_OUT = ROOT / "artifacts" / "g2_source_channel_replay.json"

MODULES = [
    ("p20_s3_channel_engine", "p20_s3_channel_engine.json"),
    ("p20_s4_length_defect_certificate", "p20_s4_length_defect_certificate.json"),
    ("p20_s5_orbit_centered_balance", "p20_s5_orbit_centered_balance.json"),
    ("p20_s6_two_mirror_transfer", "p20_s6_two_mirror_transfer.json"),
    ("p20_s10d_source_profile_witness", "p20_s10d_source_profile_witness.json"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", "--output", dest="output", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def load(results: Path, name: str) -> dict[str, Any]:
    return json.loads((results / name).read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    modules = {
        module_name: importlib.import_module(module_name)
        for module_name, _ in MODULES
    }
    component_exit = {}
    reports = {}
    with TemporaryDirectory(prefix="p13_x19_") as temp_dir:
        scratch = Path(temp_dir)
        scratch_scripts = scratch / "scripts"
        scratch_results = scratch / "results"
        scratch_scripts.mkdir(parents=True, exist_ok=True)
        scratch_results.mkdir(parents=True, exist_ok=True)
        original_globals: dict[str, dict[str, Any]] = {}
        try:
            for module_name, _ in MODULES:
                module = modules[module_name]
                saved: dict[str, Any] = {"__file__": module.__file__}
                if module_name == "p20_s10d_source_profile_witness":
                    saved["ROOT"] = module.ROOT
                    saved["RESULTS"] = module.RESULTS
                original_globals[module_name] = saved
                module.__file__ = str(scratch_scripts / f"{module_name}.py")
                if module_name == "p20_s10d_source_profile_witness":
                    module.ROOT = scratch
                    module.RESULTS = scratch_results

            with redirect_stdout(StringIO()):
                for module_name, _ in MODULES:
                    value = modules[module_name].main()
                    component_exit[module_name] = 0 if value is None else int(value)

            reports = {
                module_name: load(scratch_results, output_name)
                for module_name, output_name in MODULES
            }
        finally:
            for module_name, saved in original_globals.items():
                module = modules[module_name]
                module.__file__ = saved["__file__"]
                if "ROOT" in saved:
                    module.ROOT = saved["ROOT"]
                    module.RESULTS = saved["RESULTS"]
    s3 = reports["p20_s3_channel_engine"]
    s4 = reports["p20_s4_length_defect_certificate"]
    s5 = reports["p20_s5_orbit_centered_balance"]
    s6 = reports["p20_s6_two_mirror_transfer"]
    s10d = reports["p20_s10d_source_profile_witness"]

    s5_records = {row.get("row_id"): row for row in s5.get("records", [])}
    s6_records = s6.get("records", [])
    source_checks = s10d.get("checks", {})
    checks = {
        "component_exits_zero": all(value == 0 for value in component_exit.values()),
        "component_statuses_pass": all(report.get("status") == "PASS" for report in reports.values()),
        "carrier_dimension_12": s3.get("channel_dimensions", {}).get("ambient") == 12,
        "orbit_centered_dimension_10": s3.get("channel_dimensions", {}).get("orbit_centered") == 10,
        "length_line_dimension_1": s3.get("channel_dimensions", {}).get("length_line") == 1,
        "length_obstruction_has_no_failures": not s4.get("failures"),
        "orbit_repair_has_no_failures": not s5.get("failures"),
        "base_rows_orbit_ranks": (
            s5_records.get("W", {}).get("orbit_centered_rank_Q") == 0
            and s5_records.get("C", {}).get("orbit_centered_rank_Q") == 0
            and s5_records.get("F", {}).get("orbit_centered_rank_Q") == 0
            and s5_records.get("F_short_axis", {}).get("orbit_centered_rank_Q") == 2
            and s5_records.get("F_long_axis", {}).get("orbit_centered_rank_Q") == 2
        ),
        "two_mirror_five_rows": len(s6_records) == 5,
        "two_mirror_checks_all": all(
            row.get("status") == "PASS"
            and all(value is True for value in row.get("checks", {}).values())
            for row in s6_records
        ),
        "source_profile_checks_all": bool(source_checks) and all(value is True for value in source_checks.values()),
    }
    passed = all(checks.values())
    artifact = {
        "artifact": "g2_source_channel_replay",
        "status": "PASS_G2_SOURCE_CHANNEL" if passed else "FAIL_G2_SOURCE_CHANNEL",
        "pass": passed,
        "checks": checks,
        "component_exit": component_exit,
        "claims": {
            "carrier": "Omega_short disjoint union Omega_long, each of size 6",
            "global_decomposition_dimensions": [1, 1, 5, 5],
            "base_orbit_centered_ranks": {
                key: s5_records.get(key, {}).get("orbit_centered_rank_Q")
                for key in ["W", "C", "F", "F_short_axis", "F_long_axis"]
            },
            "two_mirror_orbit_ranks": {
                row.get("row_id"): row.get("orbit_centered_rank_Q")
                for row in s6_records
            },
        },
        "boundary": "selected X19 source-channel computations only; no general G2, Weyl, classifier, or tiling theorem",
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pass": passed, "status": artifact["status"], "output": str(output)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
