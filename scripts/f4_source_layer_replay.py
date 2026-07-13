#!/usr/bin/env python3
"""Aggregate the selected bounded P21 computations used by P13/X20."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "artifacts" / "f4_source_layer_replay.json"

MODULES = {
    "engine": "p21_f4_projective_root_engine",
    "length": "p21_s4_length_line_theorem",
    "matroid": "p21_s5_matroid_source_generator_lock",
    "kernel": "p21_s14_block_triality_true_witness_hunt",
    "flat": "p21_s15_flat_invariant_beyond_length",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", "--output", dest="output", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    reports: dict[str, dict[str, Any]] = {}
    for role, module_name in MODULES.items():
        module = importlib.import_module(module_name)
        reports[role] = module.build_report()

    engine = reports["engine"]
    length = reports["length"]
    matroid = reports["matroid"]
    kernel = reports["kernel"]
    flat = reports["flat"]
    kernel_orbits = {
        row.get("name"): row
        for row in kernel.get("kernel_internal_channel", {}).get("conjugacy_orbits", [])
    }
    flat_counts = {
        int(key): value
        for key, value in flat.get("flat_relation_invariant", {}).get("flat_counts_by_size", {}).items()
    }

    checks = {
        "all_component_pass_flags": all(report.get("pass") is True for report in reports.values()),
        "projective_points_24": engine.get("projective_pair_count") == 24,
        "length_split_12_12": engine.get("projective_length_counts") == {"long": 12, "short": 12},
        "gproj_order_576": engine.get("g_proj_order") == 576,
        "gproj_global_rank_1": length.get("E_global_rank") == 1,
        "gproj_length_rank_0": length.get("E_length_centered_rank") == 0,
        "gmat_order_1152": matroid.get("g_mat_generated_order") == 1152,
        "gmat_global_rank_0": matroid.get("g_mat_global_centered_rank") == 0,
        "kernel_witness_names": set(kernel_orbits) >= {"K_24", "K_16"},
        "kernel_witness_ranks_18": (
            kernel_orbits.get("K_24", {}).get("ranks", {}).get("six_block_centered_rank") == 18
            and kernel_orbits.get("K_16", {}).get("ranks", {}).get("six_block_centered_rank") == 18
        ),
        "flat_counts_72_32_18": flat_counts == {2: 72, 3: 32, 4: 18},
        "kernel_status_bounded_pass": str(kernel.get("status", "")).startswith("PASS_"),
        "flat_status_bounded_pass": str(flat.get("status", "")).startswith("PASS_"),
    }
    passed = all(checks.values())
    artifact = {
        "artifact": "f4_source_layer_replay",
        "status": "PASS_F4_SOURCE_LAYER" if passed else "FAIL_F4_SOURCE_LAYER",
        "pass": passed,
        "checks": checks,
        "claims": {
            "projective_points": engine.get("projective_pair_count"),
            "length_counts": engine.get("projective_length_counts"),
            "gproj_order": engine.get("g_proj_order"),
            "gproj_global_centered_rank": length.get("E_global_rank"),
            "gproj_length_centered_rank": length.get("E_length_centered_rank"),
            "gmat_order": matroid.get("g_mat_generated_order"),
            "gmat_global_centered_rank": matroid.get("g_mat_global_centered_rank"),
            "kernel_six_block_centered_ranks": {
                name: kernel_orbits.get(name, {}).get("ranks", {}).get("six_block_centered_rank")
                for name in ["K_24", "K_16"]
            },
            "flat_counts_by_size": flat_counts,
        },
        "boundary": "selected X20 source-layer computations only; no F4, 24-cell, block, flat, classifier, or tiling classification",
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"pass": passed, "status": artifact["status"], "output": str(output)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
