#!/usr/bin/env python3
"""P21-S14 block/triality true witness hunt.

This gate revisits the six source-locked blocks E0,F0,G0,E,F,G after
S12-S13.  It separates two phenomena:

1. quotient-defined block rows, i.e. unions of complete fibers of the
   six-block action, collapse after six-block centering;
2. the internal kernel of the six-block action has two nontrivial canonical
   conjugacy classes, and each gives a positive six-block-centered residual.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict, deque
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import p21_f4_projective_root_engine as eng  # noqa: E402
import p21_s6_block_triality_channel_scout as s6  # noqa: E402

Perm = Tuple[int, ...]
MatrixQ = List[List[Fraction]]

BLOCK_ORDER = s6.BLOCK_ORDER
TRIALITY_ORDER = s6.TRIALITY_ORDER


def frac_str(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def perm_inverse(p: Perm) -> Perm:
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return tuple(out)


def conjugate(a: Perm, x: Perm) -> Perm:
    return eng.compose(eng.compose(a, x), perm_inverse(a))


def quotient_compose(p: Perm, q: Perm) -> Perm:
    return tuple(p[q[i]] for i in range(len(q)))


def build_layer() -> Dict[str, Any]:
    layer = s6.build_layer()
    labels: List[str] = layer["labels"]
    classes: Dict[str, str] = layer["classes"]
    blocks: Dict[str, str] = layer["blocks"]
    block_by_index = [blocks[lab] for lab in labels]
    class_by_index = [classes[lab] for lab in labels]
    triality_by_index = [blocks[lab][0] for lab in labels]

    fibers: Dict[Perm, List[Perm]] = defaultdict(list)
    for g in layer["g_mat"]:
        q = s6.induced_block_perm(g, block_by_index)
        if q is None:
            raise AssertionError("G_mat element does not induce a six-block permutation")
        fibers[q].append(g)

    return {
        **layer,
        "block_by_index": block_by_index,
        "class_by_index": class_by_index,
        "triality_by_index": triality_by_index,
        "fibers": dict(fibers),
    }


def row_ranks(row: Sequence[Perm], partitions: Dict[str, Sequence[str]], degree: int) -> Dict[str, int]:
    mat = s6.row_sum(row, degree)
    return {
        "global_centered_rank": s6.rank(s6.global_center(mat, len(row))),
        "length_centered_rank": s6.rank(s6.center_by_partition(mat, partitions["length"])),
        "triality_centered_rank": s6.rank(s6.center_by_partition(mat, partitions["triality"])),
        "six_block_centered_rank": s6.rank(s6.center_by_partition(mat, partitions["block"])),
    }


def verify_fiber_block_uniformity(fibers: Dict[Perm, List[Perm]], block_by_index: Sequence[str], degree: int) -> Dict[str, Any]:
    block_indices = {
        block: [i for i, b in enumerate(block_by_index) if b == block]
        for block in BLOCK_ORDER
    }
    bad_active: List[Any] = []
    bad_inactive: List[Any] = []
    fiber_ranks = Counter()
    active_values = Counter()

    for q, row in fibers.items():
        mat = s6.row_sum(row, degree)
        centered = s6.center_by_partition(mat, block_by_index)
        fiber_ranks[s6.rank(centered)] += 1
        expected_active = Fraction(len(row), len(block_indices[BLOCK_ORDER[0]]))
        for src_pos, src_block in enumerate(BLOCK_ORDER):
            dst_block = BLOCK_ORDER[q[src_pos]]
            active_pair = (dst_block, src_block)
            for out_block in BLOCK_ORDER:
                I = block_indices[out_block]
                J = block_indices[src_block]
                vals = {mat[i][j] for i in I for j in J}
                if out_block == dst_block:
                    active_values[tuple(sorted(frac_str(v) for v in vals))] += 1
                    if vals != {expected_active}:
                        bad_active.append({
                            "quotient": q,
                            "active_pair": active_pair,
                            "values": sorted(frac_str(v) for v in vals),
                            "expected": frac_str(expected_active),
                        })
                else:
                    if vals != {Fraction(0)}:
                        bad_inactive.append({
                            "quotient": q,
                            "inactive_pair": (out_block, src_block),
                            "values": sorted(frac_str(v) for v in vals),
                        })

    return {
        "all_fibers_block_uniform": not bad_active and not bad_inactive,
        "bad_active_count": len(bad_active),
        "bad_inactive_count": len(bad_inactive),
        "fiber_six_block_centered_rank_counts": {str(k): v for k, v in sorted(fiber_ranks.items())},
        "active_block_value_sets": {str(k): v for k, v in sorted(active_values.items())},
    }


def bits_iter(bits: int) -> Iterable[int]:
    while bits:
        lsb = bits & -bits
        yield lsb.bit_length() - 1
        bits -= lsb


def quotient_subgroup_census(quotients: Sequence[Perm]) -> Dict[str, Any]:
    q_list = sorted(quotients)
    idx = {q: i for i, q in enumerate(q_list)}
    qid = tuple(range(len(q_list[0])))
    id_index = idx[qid]
    n = len(q_list)

    mul = [[idx[quotient_compose(q_list[i], q_list[j])] for j in range(n)] for i in range(n)]
    inv = []
    for q in q_list:
        inv.append(idx[perm_inverse(q)])

    def closure(bits: int) -> int:
        gens = set(bits_iter(bits))
        gens |= {inv[g] for g in list(gens)}
        seen = 1 << id_index
        queue: deque[int] = deque([id_index])
        while queue:
            a = queue.popleft()
            for g in gens:
                for h in (mul[g][a], mul[a][g]):
                    if not ((seen >> h) & 1):
                        seen |= 1 << h
                        queue.append(h)
        return seen

    subgroups = {1 << id_index}
    changed = True
    iterations = 0
    while changed:
        changed = False
        iterations += 1
        for H in list(subgroups):
            for q in range(n):
                if (H >> q) & 1:
                    continue
                C = closure(H | (1 << q))
                if C not in subgroups:
                    subgroups.add(C)
                    changed = True

    coset_total = 0
    coset_order_counts = Counter()
    for H in subgroups:
        remaining = (1 << n) - 1
        h_list = list(bits_iter(H))
        while remaining:
            a = (remaining & -remaining).bit_length() - 1
            C = 0
            for h in h_list:
                C |= 1 << mul[a][h]
            coset_total += 1
            coset_order_counts[H.bit_count()] += 1
            remaining &= ~C

    return {
        "quotient_order": n,
        "subgroup_count": len(subgroups),
        "subgroup_order_counts": {str(k): v for k, v in sorted(Counter(H.bit_count() for H in subgroups).items())},
        "quotient_coset_total": coset_total,
        "quotient_coset_counts_by_subgroup_order": {str(k): v for k, v in sorted(coset_order_counts.items())},
        "enumeration_iterations": iterations,
    }


def fixed_and_moved_blocks(p: Perm, block_by_index: Sequence[str]) -> Tuple[List[str], List[str], int]:
    fixed: List[str] = []
    moved: List[str] = []
    total_moved = 0
    for block in BLOCK_ORDER:
        inds = [i for i, b in enumerate(block_by_index) if b == block]
        moved_here = sum(1 for i in inds if p[i] != i)
        total_moved += moved_here
        if moved_here == 0:
            fixed.append(block)
        else:
            moved.append(block)
    return fixed, moved, total_moved


def kernel_conjugacy_orbits(kernel: Sequence[Perm], group: Sequence[Perm], partitions: Dict[str, Sequence[str]], degree: int) -> List[Dict[str, Any]]:
    identity = tuple(range(degree))
    remaining = set(kernel)
    raw_orbits: List[set[Perm]] = []
    while remaining:
        start = next(iter(remaining))
        orbit = {start}
        queue = deque([start])
        while queue:
            x = queue.popleft()
            for a in group:
                y = conjugate(a, x)
                if y not in orbit:
                    orbit.add(y)
                    queue.append(y)
        raw_orbits.append(orbit)
        remaining -= orbit

    def orbit_sort_key(orb: set[Perm]) -> Tuple[int, int]:
        return (0 if identity in orb else 1, len(orb))

    out: List[Dict[str, Any]] = []
    for orb in sorted(raw_orbits, key=orbit_sort_key):
        row = sorted(orb)
        fixed_patterns = Counter()
        total_moved_counts = Counter()
        for p in row:
            fixed, _, total_moved = fixed_and_moved_blocks(p, partitions["block"])
            fixed_patterns[tuple(fixed)] += 1
            total_moved_counts[total_moved] += 1

        if identity in orb:
            name = "K_id"
            interpretation = "identity class"
        elif set(total_moved_counts) == {24}:
            name = "K_24"
            interpretation = "nonidentity kernel class acting fixed-point-free on all six 4-point blocks"
        elif set(total_moved_counts) == {16}:
            name = "K_16"
            interpretation = "nonidentity kernel class fixing exactly one long block and one short block pointwise"
        else:
            name = f"K_orbit_{len(out)+1}"
            interpretation = "unclassified kernel conjugacy class"

        ranks = row_ranks(row, partitions, degree)
        qmat = s6.quotient_matrix(row, partitions["block"], BLOCK_ORDER)
        mat = s6.row_sum(row, degree)
        centered = s6.center_by_partition(mat, partitions["block"])
        diagonal_value_sets: Dict[str, List[str]] = {}
        for block in BLOCK_ORDER:
            inds = [i for i, b in enumerate(partitions["block"]) if b == block]
            vals = sorted({centered[i][j] for i in inds for j in inds})
            diagonal_value_sets[block] = [frac_str(v) for v in vals]

        out.append({
            "name": name,
            "size": len(row),
            "contains_identity": identity in orb,
            "interpretation": interpretation,
            "fixed_block_pattern_counts": {"|".join(k) if k else "none": v for k, v in sorted(fixed_patterns.items())},
            "total_moved_point_counts": {str(k): v for k, v in sorted(total_moved_counts.items())},
            "ranks": ranks,
            "block_quotient_rank": s6.q_rank_int(qmat),
            "block_quotient_global_centered_rank": s6.q_global_center_rank(qmat),
            "six_block_centered_diagonal_value_sets": diagonal_value_sets,
        })
    return out


def kernel_subgroup_census(kernel: Sequence[Perm], partitions: Dict[str, Sequence[str]], degree: int) -> Dict[str, Any]:
    elems = sorted(kernel)
    idx = {g: i for i, g in enumerate(elems)}
    identity = tuple(range(degree))
    id_index = idx[identity]
    n = len(elems)
    mul = [[idx[eng.compose(elems[i], elems[j])] for j in range(n)] for i in range(n)]
    inv = [idx[perm_inverse(g)] for g in elems]

    def closure(bits: int) -> int:
        gens = set(bits_iter(bits))
        gens |= {inv[g] for g in list(gens)}
        seen = 1 << id_index
        queue: deque[int] = deque([id_index])
        while queue:
            a = queue.popleft()
            for g in gens:
                for h in (mul[g][a], mul[a][g]):
                    if not ((seen >> h) & 1):
                        seen |= 1 << h
                        queue.append(h)
        return seen

    subgroups = {1 << id_index}
    changed = True
    while changed:
        changed = False
        for H in list(subgroups):
            for g in range(n):
                if (H >> g) & 1:
                    continue
                C = closure(H | (1 << g))
                if C not in subgroups:
                    subgroups.add(C)
                    changed = True

    rank_profiles = Counter()
    for H in subgroups:
        row = [elems[i] for i in bits_iter(H)]
        ranks = row_ranks(row, partitions, degree)
        key = (
            len(row),
            ranks["global_centered_rank"],
            ranks["length_centered_rank"],
            ranks["six_block_centered_rank"],
        )
        rank_profiles[key] += 1

    return {
        "kernel_order": n,
        "kernel_subgroup_count": len(subgroups),
        "kernel_subgroup_order_counts": {str(k): v for k, v in sorted(Counter(H.bit_count() for H in subgroups).items())},
        "rank_profile_counts": {
            f"order={k[0]},global={k[1]},length={k[2]},six={k[3]}": v
            for k, v in sorted(rank_profiles.items())
        },
    }


def build_report() -> Dict[str, Any]:
    layer = build_layer()
    labels: List[str] = layer["labels"]
    g_mat: List[Perm] = layer["g_mat"]
    g_proj: List[Perm] = layer["g_proj"]
    g_swap: List[Perm] = layer["g_swap"]
    fibers: Dict[Perm, List[Perm]] = layer["fibers"]
    degree = len(labels)
    partitions = {
        "length": layer["class_by_index"],
        "triality": layer["triality_by_index"],
        "block": layer["block_by_index"],
    }

    qid = tuple(range(len(BLOCK_ORDER)))
    kernel = fibers[qid]
    fiber_uniformity = verify_fiber_block_uniformity(fibers, partitions["block"], degree)
    quotient_census = quotient_subgroup_census(list(fibers))
    orbits = kernel_conjugacy_orbits(kernel, g_mat, partitions, degree)
    subgroup_census = kernel_subgroup_census(kernel, partitions, degree)

    nonidentity_orbits = [o for o in orbits if not o["contains_identity"]]
    positive_witnesses = [
        o for o in nonidentity_orbits
        if o["ranks"]["six_block_centered_rank"] > 0
    ]

    checks = {
        "G_mat_order_1152": len(g_mat) == 1152,
        "G_proj_order_576": len(g_proj) == 576,
        "G_swap_order_576": len(g_swap) == 576,
        "quotient_order_72": len(fibers) == 72,
        "fiber_sizes_all_16": sorted({len(v) for v in fibers.values()}) == [16],
        "all_fibers_block_uniform": fiber_uniformity["all_fibers_block_uniform"],
        "all_fibers_six_block_centered_rank_zero": fiber_uniformity["fiber_six_block_centered_rank_counts"] == {"0": 72},
        "quotient_subgroup_count_112": quotient_census["subgroup_count"] == 112,
        "quotient_coset_total_1934": quotient_census["quotient_coset_total"] == 1934,
        "kernel_order_16": len(kernel) == 16,
        "kernel_subgroup_count_67": subgroup_census["kernel_subgroup_count"] == 67,
        "kernel_conjugacy_orbit_sizes_1_6_9": [o["size"] for o in orbits] == [1, 6, 9],
        "nonidentity_kernel_classes_have_six_rank_18": [o["ranks"]["six_block_centered_rank"] for o in nonidentity_orbits] == [18, 18],
        "positive_kernel_conjugacy_witness_exists": len(positive_witnesses) == 2,
    }

    status = "PASS_POSITIVE_KERNEL_CONJUGACY_WITNESS_AND_QUOTIENT_COLLAPSE" if all(checks.values()) else "FAIL"
    report: Dict[str, Any] = {
        "route_id": "P21",
        "gate": "S14",
        "date": "2026-07-08",
        "verifier": "p21_s14_block_triality_true_witness_hunt.py",
        "status": status,
        "degree": degree,
        "block_order": BLOCK_ORDER,
        "row_orders": {"G_proj": len(g_proj), "G_mat": len(g_mat), "G_swap": len(g_swap)},
        "six_block_quotient": {
            "order": len(fibers),
            "fiber_size_set": sorted({len(v) for v in fibers.values()}),
            "kernel_size": len(kernel),
            "fiber_uniformity": fiber_uniformity,
            "quotient_subgroup_census": quotient_census,
            "consequence": "Every row that is a union of complete six-block-action fibers is block-constant on every source/destination block pair, hence has six-block-centered rank 0.",
        },
        "kernel_internal_channel": {
            "conjugacy_orbits": orbits,
            "kernel_subgroup_census": subgroup_census,
            "positive_witness_names": [o["name"] for o in positive_witnesses],
        },
        "checks": checks,
        "pass": all(checks.values()),
        "interpretation": "The six-block quotient itself gives no residual witness: complete quotient fibers and all quotient-defined unions collapse after six-block centering. The genuine block/triality payoff is internal to the block-action kernel: its two nonidentity G_mat-conjugacy classes K_24 and K_16 are canonical finite rows with six-block-centered rank 18.",
        "boundary": "This is a finite P21 kernel-conjugacy witness, not a classification of all block/triality rows and not a P13 insertion by itself. S15/S16 have closed downstream orientation; any P13 use still requires the later P13-side integration/order gate.",
        "next_gate": "P13-side integration/order gate with P20/P21 coordination",
    }
    return report


def make_table(report: Dict[str, Any]) -> str:
    lines = [
        "# P21-S14 Block/Triality True Witness Table",
        "",
        f"Status: {report['status']}",
        "",
        "## Quotient Layer",
        "",
        "| item | value |",
        "|---|---:|",
        f"| six-block quotient order | {report['six_block_quotient']['order']} |",
        f"| fiber size | {report['six_block_quotient']['fiber_size_set']} |",
        f"| kernel size | {report['six_block_quotient']['kernel_size']} |",
        f"| quotient subgroups | {report['six_block_quotient']['quotient_subgroup_census']['subgroup_count']} |",
        f"| quotient cosets across all subgroups | {report['six_block_quotient']['quotient_subgroup_census']['quotient_coset_total']} |",
        f"| fiber six-block rank counts | `{report['six_block_quotient']['fiber_uniformity']['fiber_six_block_centered_rank_counts']}` |",
        "",
        "## Kernel Conjugacy Rows",
        "",
        "| row | size | description | global rank | length rank | triality rank | six-block rank |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for item in report["kernel_internal_channel"]["conjugacy_orbits"]:
        ranks = item["ranks"]
        lines.append(
            f"| `{item['name']}` | {item['size']} | {item['interpretation']} | {ranks['global_centered_rank']} | {ranks['length_centered_rank']} | {ranks['triality_centered_rank']} | {ranks['six_block_centered_rank']} |"
        )
    lines.extend([
        "",
        "Prossima task: P13-side integration/order gate with P20/P21 coordination.",
    ])
    return "\n".join(lines) + "\n"


def make_markdown(report: Dict[str, Any], title: str) -> str:
    q = report["six_block_quotient"]
    lines = [
        f"# {title}",
        "",
        f"Status: {report['status']}",
        "Verifier: `scripts/p21_s14_block_triality_true_witness_hunt.py`",
        "",
        "## Result In Simple Terms",
        "",
        "The S6 negative result was not the full story.  The six-block quotient still has no internal residual: every complete fiber over a six-block permutation is perfectly uniform inside the relevant 4-by-4 block, so any row defined only as a union of complete quotient fibers has six-block-centered rank `0`.",
        "",
        "But the block-action kernel has canonical internal structure.  Its two nonidentity `G_mat`-conjugacy classes are finite rows `K_24` and `K_16`, and both have six-block-centered rank `18`.  This is a genuine block/triality-side witness beyond length and beyond quotient bookkeeping.",
        "",
        "## Quotient Collapse",
        "",
        "```text",
        f"|Q| = {q['order']}",
        f"fiber sizes = {q['fiber_size_set']}",
        f"|ker(pi)| = {q['kernel_size']}",
        f"quotient subgroups = {q['quotient_subgroup_census']['subgroup_count']}",
        f"quotient cosets across all quotient subgroups = {q['quotient_subgroup_census']['quotient_coset_total']}",
        f"fiber six-block rank counts = {q['fiber_uniformity']['fiber_six_block_centered_rank_counts']}",
        "```",
        "",
        "The verifier checks all `72` complete fibers.  Each active 4-by-4 source/destination block has constant value `4`, and inactive block pairs have value `0`.  By linearity, every union of complete fibers is block-constant on the six-block partition and therefore six-block-centered zero.",
        "",
        "## Positive Kernel Witness",
        "",
        "| row | size | description | global rank | length rank | triality rank | six-block rank |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for item in report["kernel_internal_channel"]["conjugacy_orbits"]:
        ranks = item["ranks"]
        lines.append(
            f"| `{item['name']}` | {item['size']} | {item['interpretation']} | {ranks['global_centered_rank']} | {ranks['length_centered_rank']} | {ranks['triality_centered_rank']} | {ranks['six_block_centered_rank']} |"
        )
    lines.extend([
        "",
        "The two positive rows are the nonidentity classes:",
        "",
        "- `K_24`: six elements acting fixed-point-free on all six source blocks.",
        "- `K_16`: nine elements fixing exactly one long block and one short block pointwise, and moving all points in the other four blocks.",
        "",
        "## Boundary",
        "",
        report["boundary"],
        "",
        "Prossima task: P13-side integration/order gate with P20/P21 coordination.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", action="store_true")
    parser.add_argument("--write-md", action="store_true")
    parser.add_argument("--write-table", action="store_true")
    parser.add_argument("--write-doc", action="store_true")
    parser.add_argument("--json-path", default=None)
    parser.add_argument("--md-path", default=None)
    parser.add_argument("--table-path", default=None)
    parser.add_argument("--doc-path", default=None)
    args = parser.parse_args()

    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)

    root = Path(__file__).resolve().parents[1]
    if args.write_json:
        out = Path(args.json_path) if args.json_path else root / "results" / "p21_s14_block_triality_true_witness_hunt_replay.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        cert = root / "certified" / "P21_S14_BLOCK_TRIALITY_TRUE_WITNESS_CERTIFICATE.json"
        cert.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")
        print(f"WROTE {cert}")

    if args.write_md:
        out = Path(args.md_path) if args.md_path else root / "certified" / "P21_S14_BLOCK_TRIALITY_TRUE_WITNESS_CERTIFICATE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report, "P21-S14 Block/Triality True Witness Certificate"), encoding="ascii")
        print(f"WROTE {out}")

    if args.write_table:
        out = Path(args.table_path) if args.table_path else root / "tables" / "P21_S14_BLOCK_TRIALITY_TRUE_WITNESS_TABLE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_table(report), encoding="ascii")
        print(f"WROTE {out}")

    if args.write_doc:
        out = Path(args.doc_path) if args.doc_path else root / "docs" / "P21_S14_BLOCK_TRIALITY_TRUE_WITNESS_HUNT_2026_07_08.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report, "P21-S14 Block/Triality True Witness Hunt"), encoding="ascii")
        print(f"WROTE {out}")

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())