#!/usr/bin/env python3
"""P21-S6 block/triality channel scout.

Exact scout for the six source-locked blocks E0,F0,G0,E,F,G.
The goal is deliberately bounded: decide whether the block/triality channel
produces a new residual witness beyond the already-closed length/geometric vs
matroid story, or whether it should be parked as quotient-level source data.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import p21_f4_projective_root_engine as eng  # noqa: E402
import p21_s5_matroid_source_generator_lock as s5  # noqa: E402

Perm = Tuple[int, ...]
MatrixQ = List[List[Fraction]]

BLOCK_ORDER = ["E0", "F0", "G0", "E", "F", "G"]
TRIALITY_ORDER = ["E", "F", "G"]
LENGTH_ORDER = ["A_long", "B_short"]


def build_layer() -> Dict[str, object]:
    vectors = s5.source_vectors()
    labels = sorted(vectors)
    classes = s5.label_classes(labels)
    blocks = s5.block_labels(labels)
    proj_index = {s5.normalize_projective(vectors[lab]): i for i, lab in enumerate(labels)}
    root_gens = [
        s5.source_reflection_perm(alpha, labels, vectors, proj_index)
        for alpha in s5.simple_roots_unscaled_for_reflections()
    ]
    g_proj = eng.generate_group(root_gens, len(labels))
    sigma = s5.perm_from_mapping(labels, s5.sigma_mapping())
    g_mat = eng.generate_group(root_gens + [sigma], len(labels))
    g_proj_set = set(g_proj)
    g_swap = [g for g in g_mat if g not in g_proj_set]
    return {
        "vectors": vectors,
        "labels": labels,
        "classes": classes,
        "blocks": blocks,
        "g_proj": g_proj,
        "g_mat": g_mat,
        "g_swap": g_swap,
        "g_proj_set": g_proj_set,
    }


def rank(mat: MatrixQ) -> int:
    return eng.rank_fraction(mat)


def row_sum(row: Sequence[Perm], degree: int) -> MatrixQ:
    return eng.row_sum_matrix(row, degree)


def center_by_partition(mat: MatrixQ, partition: Sequence[str]) -> MatrixQ:
    labels = sorted(set(partition))
    inds = {lab: [i for i, x in enumerate(partition) if x == lab] for lab in labels}
    out = [r[:] for r in mat]
    for a in labels:
        for b in labels:
            I = inds[a]
            J = inds[b]
            total = sum(mat[i][j] for i in I for j in J)
            avg = total / Fraction(len(I) * len(J))
            for i in I:
                for j in J:
                    out[i][j] -= avg
    return out


def global_center(mat: MatrixQ, row_size: int) -> MatrixQ:
    n = len(mat)
    avg = Fraction(row_size, n)
    return [[mat[i][j] - avg for j in range(n)] for i in range(n)]


def quotient_matrix(row: Sequence[Perm], partition: Sequence[str], order: Sequence[str]) -> List[List[int]]:
    pos = {lab: i for i, lab in enumerate(order)}
    out = [[0 for _ in order] for _ in order]
    for p in row:
        for j, src_lab in enumerate(partition):
            dst_lab = partition[p[j]]
            out[pos[dst_lab]][pos[src_lab]] += 1
    return out


def q_rank_int(mat: List[List[int]]) -> int:
    return rank([[Fraction(x) for x in row] for row in mat])


def q_global_center_rank(mat: List[List[int]]) -> int:
    k = len(mat)
    total = sum(sum(row) for row in mat)
    avg = Fraction(total, k * k)
    centered = [[Fraction(mat[i][j]) - avg for j in range(k)] for i in range(k)]
    return rank(centered)


def block_matrix(p: Perm, block_by_index: Sequence[str]) -> Tuple[Tuple[int, ...], ...]:
    pos = {lab: i for i, lab in enumerate(BLOCK_ORDER)}
    out = [[0 for _ in BLOCK_ORDER] for _ in BLOCK_ORDER]
    for j, src_block in enumerate(block_by_index):
        dst_block = block_by_index[p[j]]
        out[pos[dst_block]][pos[src_block]] += 1
    return tuple(tuple(r) for r in out)


def induced_block_perm(p: Perm, block_by_index: Sequence[str]) -> Tuple[int, ...] | None:
    mat = block_matrix(p, block_by_index)
    image = []
    for c in range(len(BLOCK_ORDER)):
        rows = [r for r in range(len(BLOCK_ORDER)) if mat[r][c] == 4]
        if len(rows) != 1:
            return None
        image.append(rows[0])
    return tuple(image)


def block_action_profile(row: Sequence[Perm], block_by_index: Sequence[str]) -> Dict[str, object]:
    perms = []
    for p in row:
        q = induced_block_perm(p, block_by_index)
        if q is not None:
            perms.append(q)
    counts = Counter(perms)
    fiber_sizes = sorted(set(counts.values()))
    return {
        "all_elements_are_block_permutations": len(perms) == len(row),
        "induced_block_action_size": len(counts),
        "kernel_or_fiber_sizes": fiber_sizes,
    }


def row_profile(name: str, row: Sequence[Perm], labels: Sequence[str], classes: Dict[str, str], blocks: Dict[str, str]) -> Dict[str, object]:
    degree = len(labels)
    class_by_index = [classes[lab] for lab in labels]
    block_by_index = [blocks[lab] for lab in labels]
    triality_by_index = [blocks[lab][0] for lab in labels]
    mat = row_sum(row, degree)

    block_q = quotient_matrix(row, block_by_index, BLOCK_ORDER)
    tri_q = quotient_matrix(row, triality_by_index, TRIALITY_ORDER)
    len_q = quotient_matrix(row, class_by_index, LENGTH_ORDER)

    return {
        "name": name,
        "row_size": len(row),
        "global_centered_rank": rank(global_center(mat, len(row))),
        "length_centered_rank": rank(center_by_partition(mat, class_by_index)),
        "triality_centered_rank": rank(center_by_partition(mat, triality_by_index)),
        "six_block_centered_rank": rank(center_by_partition(mat, block_by_index)),
        "length_quotient_matrix": len_q,
        "triality_quotient_matrix": tri_q,
        "block_quotient_matrix": block_q,
        "length_quotient_rank": q_rank_int(len_q),
        "triality_quotient_rank": q_rank_int(tri_q),
        "block_quotient_rank": q_rank_int(block_q),
        "length_quotient_global_centered_rank": q_global_center_rank(len_q),
        "triality_quotient_global_centered_rank": q_global_center_rank(tri_q),
        "block_quotient_global_centered_rank": q_global_center_rank(block_q),
        "block_action": block_action_profile(row, block_by_index),
    }


def block_stabilizer_rows(g_mat: Sequence[Perm], labels: Sequence[str], blocks: Dict[str, str], g_proj_set: set[Perm]) -> Dict[str, Dict[str, object]]:
    block_by_index = [blocks[lab] for lab in labels]
    out = {}
    for block in BLOCK_ORDER:
        inds = {i for i, b in enumerate(block_by_index) if b == block}
        row = [g for g in g_mat if {g[i] for i in inds} == inds]
        out[f"Stab_{block}"] = {
            "row": row,
            "size": len(row),
            "inside_G_proj": sum(1 for g in row if g in g_proj_set),
            "inside_G_swap": sum(1 for g in row if g not in g_proj_set),
        }
    return out


def build_report() -> Dict[str, object]:
    layer = build_layer()
    labels = layer["labels"]  # type: ignore[assignment]
    classes = layer["classes"]  # type: ignore[assignment]
    blocks = layer["blocks"]  # type: ignore[assignment]
    g_proj = layer["g_proj"]  # type: ignore[assignment]
    g_mat = layer["g_mat"]  # type: ignore[assignment]
    g_swap = layer["g_swap"]  # type: ignore[assignment]
    g_proj_set = layer["g_proj_set"]  # type: ignore[assignment]

    rows: Dict[str, Sequence[Perm]] = {
        "G_proj": g_proj,
        "G_mat": g_mat,
        "G_swap": g_swap,
    }
    stabs = block_stabilizer_rows(g_mat, labels, blocks, g_proj_set)  # type: ignore[arg-type]
    for name, data in stabs.items():
        rows[name] = data["row"]  # type: ignore[assignment]

    profiles = {
        name: row_profile(name, row, labels, classes, blocks)  # type: ignore[arg-type]
        for name, row in rows.items()
    }

    full_row_names = ["G_proj", "G_mat", "G_swap"]
    stabilizer_names = [f"Stab_{b}" for b in BLOCK_ORDER]
    all_tested_names = full_row_names + stabilizer_names

    full_rows_block_center_zero = all(profiles[n]["six_block_centered_rank"] == 0 for n in full_row_names)
    all_tested_block_center_zero = all(profiles[n]["six_block_centered_rank"] == 0 for n in all_tested_names)
    full_rows_block_perm = all(profiles[n]["block_action"]["all_elements_are_block_permutations"] for n in full_row_names)  # type: ignore[index]

    report: Dict[str, object] = {
        "route_id": "P21",
        "gate": "S6",
        "verifier": "p21_s6_block_triality_channel_scout.py",
        "source_blocks": BLOCK_ORDER,
        "triality_order": TRIALITY_ORDER,
        "degree": len(labels),
        "row_orders": {"G_proj": len(g_proj), "G_mat": len(g_mat), "G_swap": len(g_swap)},
        "block_counts": dict(sorted(Counter(blocks.values()).items())),  # type: ignore[union-attr]
        "profiles": profiles,
        "block_stabilizers": {k: {kk: vv for kk, vv in v.items() if kk != "row"} for k, v in stabs.items()},
        "findings": {
            "G_mat_preserves_six_block_partition_setwise": profiles["G_mat"]["block_action"]["all_elements_are_block_permutations"],  # type: ignore[index]
            "G_proj_induced_block_action_size": profiles["G_proj"]["block_action"]["induced_block_action_size"],  # type: ignore[index]
            "G_swap_induced_block_action_size": profiles["G_swap"]["block_action"]["induced_block_action_size"],  # type: ignore[index]
            "G_mat_induced_block_action_size": profiles["G_mat"]["block_action"]["induced_block_action_size"],  # type: ignore[index]
            "induced_block_action_kernel_size": profiles["G_mat"]["block_action"]["kernel_or_fiber_sizes"],  # type: ignore[index]
            "full_rows_block_center_zero": full_rows_block_center_zero,
            "all_tested_rows_block_center_zero": all_tested_block_center_zero,
            "full_rows_all_block_permutation_rows": full_rows_block_perm,
            "block_stabilizer_size": sorted(set(v["size"] for v in stabs.values())),
            "block_stabilizers_inside_G_swap": sorted(set(v["inside_G_swap"] for v in stabs.values())),
        },
        "decision": {
            "status": "PASS_SCOUT_NO_NEW_RESIDUAL_WITNESS",
            "interpretation": "The six-block channel is source-coherent and quotient-nontrivial, but every tested row has zero six-block-centered residual. The observed signal is block-quotient/orbit bookkeeping, not a new FCIG witness beyond length/geometric-vs-matroid data.",
            "next_gate": "P21-S8 completed; current next gate is P21-S9 external/independent validation",
        },
        "pass": bool(full_rows_block_perm and all_tested_block_center_zero),
    }
    return report


def make_markdown(report: Dict[str, object]) -> str:
    profiles = report["profiles"]  # type: ignore[assignment]
    lines = [
        "# P21-S6 Block/Triality Channel Scout Certificate",
        "",
        "Status: PASS_SCOUT_NO_NEW_RESIDUAL_WITNESS",
        "",
        "## Core Finding",
        "",
        "The six source blocks `E0,F0,G0,E,F,G` are coherent: every tested element acts by a permutation of the six blocks.  However, after centering by the six-block partition, all tested rows have rank `0`.  The block/triality signal is therefore quotient-level source bookkeeping, not a new residual FCIG witness.",
        "",
        "## Full Rows",
        "",
        "| Row | size | block action size | global rank | length-centered rank | triality-centered rank | six-block-centered rank |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["G_proj", "G_mat", "G_swap"]:
        p = profiles[name]
        lines.append(
            f"| `{name}` | {p['row_size']} | {p['block_action']['induced_block_action_size']} | {p['global_centered_rank']} | {p['length_centered_rank']} | {p['triality_centered_rank']} | {p['six_block_centered_rank']} |"
        )
    lines.extend([
        "",
        "## Block Stabilizers",
        "",
        "| Row | size | in `G_proj` | in `G_swap` | global rank | length-centered rank | triality-centered rank | six-block-centered rank |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    stabs = report["block_stabilizers"]  # type: ignore[assignment]
    for block in BLOCK_ORDER:
        name = f"Stab_{block}"
        p = profiles[name]
        s = stabs[name]
        lines.append(
            f"| `{name}` | {s['size']} | {s['inside_G_proj']} | {s['inside_G_swap']} | {p['global_centered_rank']} | {p['length_centered_rank']} | {p['triality_centered_rank']} | {p['six_block_centered_rank']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        report["decision"]["interpretation"],  # type: ignore[index]
        "",
        "S6 is useful as a control layer and as source-lock metadata for later flat-incidence work, but it is not promoted as an additional witness.",
        "",
        "Prossima task: P21-S9 external/independent validation.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", action="store_true")
    parser.add_argument("--write-md", action="store_true")
    parser.add_argument("--json-path", default=None)
    parser.add_argument("--md-path", default=None)
    args = parser.parse_args()

    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)

    root = Path(__file__).resolve().parents[1]
    if args.write_json:
        out = Path(args.json_path) if args.json_path else root / "certified" / "P21_S6_BLOCK_TRIALITY_CHANNEL_CERTIFICATE.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")
    if args.write_md:
        out = Path(args.md_path) if args.md_path else root / "certified" / "P21_S6_BLOCK_TRIALITY_CHANNEL_CERTIFICATE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report), encoding="utf-8", newline="\n")
        print(f"WROTE {out}")

    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
