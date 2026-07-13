#!/usr/bin/env python3
"""P21-S15 flat invariant beyond length orientation.

S15 separates two questions.

1. The flat closure-size relation is genuinely finer than the long/short
   length partition, and even finer than the six-block quotient for the
   size-2 and size-4 masks.
2. This flat relation does not produce a new canonical row separator for the
   already-admitted rows after the length/block explanations are normalized
   away.  In particular, it does not separate the S14 kernel rows K_24/K_16.
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
import p21_s7_flat_incidence_profile_scout as s7  # noqa: E402
import p21_s14_block_triality_true_witness_hunt as s14  # noqa: E402

Perm = Tuple[int, ...]
MatrixQ = List[List[Fraction]]

FLAT_SIZES = [2, 3, 4]
LENGTH_ORDER = ["A_long", "B_short"]
BLOCK_ORDER = s14.BLOCK_ORDER


def frac_str(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def matrix_rank_int(mat: Sequence[Sequence[int]]) -> int:
    return s7.rank([[Fraction(x) for x in row] for row in mat])


def offdiag_partition_center(mat: Sequence[Sequence[int | Fraction]], partition: Sequence[str]) -> MatrixQ:
    n = len(mat)
    labels = sorted(set(partition))
    out = [[Fraction(mat[i][j]) for j in range(n)] for i in range(n)]
    for a in labels:
        I = [i for i, x in enumerate(partition) if x == a]
        for b in labels:
            J = [j for j, x in enumerate(partition) if x == b]
            pairs = [(i, j) for i in I for j in J if i != j]
            if not pairs:
                continue
            avg = sum(Fraction(mat[i][j]) for i, j in pairs) / len(pairs)
            for i, j in pairs:
                out[i][j] -= avg
    for i in range(n):
        out[i][i] = Fraction(0)
    return out


def hadamard(a: MatrixQ, b: MatrixQ) -> MatrixQ:
    n = len(a)
    return [[a[i][j] * b[i][j] for j in range(n)] for i in range(n)]


def perm_inverse(p: Perm) -> Perm:
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return tuple(out)


def conjugate(a: Perm, x: Perm) -> Perm:
    return eng.compose(eng.compose(a, x), perm_inverse(a))


def kernel_conjugacy_rows(layer14: Dict[str, Any], degree: int) -> Dict[str, List[Perm]]:
    kernel = layer14["fibers"][tuple(range(len(BLOCK_ORDER)))]
    group = layer14["g_mat"]
    identity = tuple(range(degree))
    remaining = set(kernel)
    rows: Dict[str, List[Perm]] = {}
    while remaining:
        start = next(iter(remaining))
        orbit = {start}
        queue: deque[Perm] = deque([start])
        while queue:
            x = queue.popleft()
            for a in group:
                y = conjugate(a, x)
                if y not in orbit:
                    orbit.add(y)
                    queue.append(y)
        remaining -= orbit
        if identity in orbit:
            name = "K_id"
        elif len(orbit) == 6:
            name = "K_24"
        elif len(orbit) == 9:
            name = "K_16"
        else:
            name = f"K_{len(orbit)}"
        rows[name] = sorted(orbit)
    return dict(sorted(rows.items()))


def flat_relation_report(labels: Sequence[str], classes: Dict[str, str], blocks: Dict[str, str], flats: Sequence[frozenset[int]]) -> Dict[str, Any]:
    degree = len(labels)
    class_by_index = [classes[lab] for lab in labels]
    block_by_index = [blocks[lab] for lab in labels]
    triality_by_index = [blocks[lab][0] for lab in labels]
    closure = s7.closure_type_matrix(flats, degree)
    masks = {t: s7.mask_for_type(closure, t) for t in FLAT_SIZES}

    flat_counts = Counter(len(f) for f in flats)
    length_closure_counts = Counter()
    row_patterns = Counter()
    block_pair_signature_counts = Counter()

    for i in range(degree):
        row_patterns[(class_by_index[i], tuple(sorted(Counter(closure[i][j] for j in range(degree) if i != j).items())))] += 1
        for j in range(degree):
            if i == j:
                continue
            length_closure_counts[(class_by_index[i], class_by_index[j], closure[i][j])] += 1

    block_pair_counts: Dict[Tuple[str, str], Counter[int]] = defaultdict(Counter)
    for i in range(degree):
        for j in range(degree):
            if i == j:
                continue
            block_pair_counts[(block_by_index[i], block_by_index[j])][closure[i][j]] += 1
    for counts in block_pair_counts.values():
        block_pair_signature_counts[tuple(sorted(counts.items()))] += 1

    mask_profiles = {}
    for t, mat in masks.items():
        mask_profiles[str(t)] = {
            "raw_rank": matrix_rank_int(mat),
            "length_offdiag_centered_rank": s7.rank(offdiag_partition_center(mat, class_by_index)),
            "triality_offdiag_centered_rank": s7.rank(offdiag_partition_center(mat, triality_by_index)),
            "six_block_offdiag_centered_rank": s7.rank(offdiag_partition_center(mat, block_by_index)),
        }

    closure_profiles = {
        "length_offdiag_centered_rank": s7.rank(offdiag_partition_center(closure, class_by_index)),
        "triality_offdiag_centered_rank": s7.rank(offdiag_partition_center(closure, triality_by_index)),
        "six_block_offdiag_centered_rank": s7.rank(offdiag_partition_center(closure, block_by_index)),
    }

    return {
        "flat_counts_by_size": {str(k): v for k, v in sorted(flat_counts.items())},
        "ordered_pair_closure_counts_by_length": {
            "|".join((a, b, str(t))): v
            for (a, b, t), v in sorted(length_closure_counts.items())
        },
        "row_closure_patterns_by_length": {
            f"{length}|{pattern}": v for (length, pattern), v in sorted(row_patterns.items())
        },
        "block_pair_signature_counts": {
            ",".join(f"{k}:{v}" for k, v in sig): count
            for sig, count in sorted(block_pair_signature_counts.items())
        },
        "mask_profiles": mask_profiles,
        "closure_value_matrix_profiles": closure_profiles,
        "not_length_derived_witness": "A->A and B->B pairs split between closure sizes 3 and 4; A->B and B->A pairs split between closure sizes 2 and 4.",
        "not_six_block_derived_witness": "The size-2 and size-4 masks have six-block-offdiagonal-centered rank 18; only the size-3 mask is six-block-derived.",
    }


def row_profile(row: Sequence[Perm], labels: Sequence[str], classes: Dict[str, str], blocks: Dict[str, str], masks: Dict[int, List[List[int]]]) -> Dict[str, Any]:
    p = s7.row_profile(row, labels, classes, blocks, masks)
    return {
        "row_size": p["row_size"],
        "coarse_rank_stack": {
            "global": p["global_centered_rank"],
            "length": p["length_centered_rank"],
            "six_block": p["block_centered_rank"],
        },
        "flat_raw_ranks": p["flat_mask_raw_ranks"],
        "flat_support_centered_ranks": p["flat_mask_support_centered_ranks"],
        "flat_global_centered_hadamard_ranks": p["flat_mask_global_centered_hadamard_ranks"],
    }


def row_channel_report(layer7: Dict[str, Any], layer14: Dict[str, Any], flat_relation: Dict[str, Any]) -> Dict[str, Any]:
    labels = layer7["labels"]
    classes = layer7["classes"]
    blocks = layer7["blocks"]
    flats = layer7["flats"]
    degree = len(labels)
    block_by_index = [blocks[lab] for lab in labels]
    closure = s7.closure_type_matrix(flats, degree)
    masks = {t: s7.mask_for_type(closure, t) for t in FLAT_SIZES}

    rows: Dict[str, List[Perm]] = {
        "G_proj": layer7["g_proj"],
        "G_mat": layer7["g_mat"],
        "G_swap": layer7["g_swap"],
    }
    kernel_rows = kernel_conjugacy_rows(layer14, degree)
    rows.update(kernel_rows)
    rows["K_all"] = layer14["fibers"][tuple(range(len(BLOCK_ORDER)))]

    profiles = {name: row_profile(row, labels, classes, blocks, masks) for name, row in sorted(rows.items())}

    gproj = profiles["G_proj"]
    gswap = profiles["G_swap"]
    k24 = profiles["K_24"]
    k16 = profiles["K_16"]

    block_centered_flat_residuals = {
        t: offdiag_partition_center(masks[t], block_by_index) for t in FLAT_SIZES
    }
    interaction_ranks: Dict[str, Dict[str, int]] = {}
    for name in ["G_proj", "G_swap", "K_all", "K_id", "K_24", "K_16"]:
        mat = s7.row_sum(rows[name], degree)
        block_centered_row = s7.center_by_partition(mat, block_by_index)
        interaction_ranks[name] = {
            str(t): s7.rank(hadamard(block_centered_row, block_centered_flat_residuals[t]))
            for t in FLAT_SIZES
        }

    return {
        "profiles": profiles,
        "comparisons": {
            "G_proj_G_swap_same_coarse_stack": gproj["coarse_rank_stack"] == gswap["coarse_rank_stack"],
            "G_proj_G_swap_raw_flat_profiles_differ": gproj["flat_raw_ranks"] != gswap["flat_raw_ranks"],
            "G_proj_G_swap_length_neutral_flat_profiles_equal": (
                gproj["flat_support_centered_ranks"] == gswap["flat_support_centered_ranks"]
                and gproj["flat_global_centered_hadamard_ranks"] == gswap["flat_global_centered_hadamard_ranks"]
            ),
            "K24_K16_same_coarse_stack": k24["coarse_rank_stack"] == k16["coarse_rank_stack"],
            "K24_K16_same_flat_size_profiles": (
                k24["flat_raw_ranks"] == k16["flat_raw_ranks"]
                and k24["flat_support_centered_ranks"] == k16["flat_support_centered_ranks"]
                and k24["flat_global_centered_hadamard_ranks"] == k16["flat_global_centered_hadamard_ranks"]
            ),
            "block_kernel_flat_residual_interaction_zero": all(
                all(rank == 0 for rank in interaction_ranks[name].values())
                for name in ["K_all", "K_id", "K_24", "K_16"]
            ),
        },
        "block_centered_row_times_block_centered_flat_mask_ranks": interaction_ranks,
    }


def build_report() -> Dict[str, Any]:
    layer7 = s7.build_layer()
    layer14 = s14.build_layer()
    labels = layer7["labels"]
    classes = layer7["classes"]
    blocks = layer7["blocks"]
    flats = layer7["flats"]

    flat_relation = flat_relation_report(labels, classes, blocks, flats)
    row_channels = row_channel_report(layer7, layer14, flat_relation)

    checks = {
        "flat_counts_match": flat_relation["flat_counts_by_size"] == {"2": 72, "3": 32, "4": 18},
        "closure_relation_not_length_derived": flat_relation["closure_value_matrix_profiles"]["length_offdiag_centered_rank"] == 22,
        "closure_relation_not_six_block_derived": flat_relation["closure_value_matrix_profiles"]["six_block_offdiag_centered_rank"] == 18,
        "size2_mask_not_length_or_block_derived": flat_relation["mask_profiles"]["2"]["length_offdiag_centered_rank"] == 18 and flat_relation["mask_profiles"]["2"]["six_block_offdiag_centered_rank"] == 18,
        "size3_mask_is_six_block_derived_but_not_length_derived": flat_relation["mask_profiles"]["3"]["length_offdiag_centered_rank"] == 22 and flat_relation["mask_profiles"]["3"]["six_block_offdiag_centered_rank"] == 0,
        "size4_mask_not_length_or_block_derived": flat_relation["mask_profiles"]["4"]["length_offdiag_centered_rank"] == 22 and flat_relation["mask_profiles"]["4"]["six_block_offdiag_centered_rank"] == 18,
        "G_proj_G_swap_length_neutral_profiles_equal": row_channels["comparisons"]["G_proj_G_swap_length_neutral_flat_profiles_equal"],
        "K24_K16_same_flat_size_profiles": row_channels["comparisons"]["K24_K16_same_flat_size_profiles"],
        "block_kernel_flat_residual_interaction_zero": row_channels["comparisons"]["block_kernel_flat_residual_interaction_zero"],
    }

    status = "PASS_FLAT_RELATION_INVARIANT_NO_EXTRA_ROW_PROMOTION" if all(checks.values()) else "FAIL"
    return {
        "route_id": "P21",
        "gate": "S15",
        "date": "2026-07-08",
        "verifier": "p21_s15_flat_invariant_beyond_length.py",
        "status": status,
        "flat_relation_invariant": flat_relation,
        "row_channel_tests": row_channels,
        "checks": checks,
        "pass": all(checks.values()),
        "interpretation": "The rank-2 flat closure-size relation is not reducible to the long/short length partition. It also has a size-2/size-4 component not reducible to the six-block quotient. However, after length-neutral row normalization, it does not supply an additional canonical row witness: G_proj/G_swap become equal in the length-neutral flat profiles, and K_24/K_16 have identical flat-size profiles. The S14 block-kernel witness is orthogonal to the block-centered flat residual channel.",
        "boundary": "S15 promotes the flat closure-size relation as a finite incidence invariant, not a new full row classification and not an extra P13 insertion by itself. S16 has closed the local application decision; any P13 use still requires the later P13-side integration/order gate.",
        "next_gate": "P13-side integration/order gate with P20/P21 coordination",
    }


def make_table(report: Dict[str, Any]) -> str:
    flat = report["flat_relation_invariant"]
    rows = [
        "# P21-S15 Flat Invariant Beyond Length Table",
        "",
        f"Status: {report['status']}",
        "",
        "## Flat Closure Masks",
        "",
        "| mask | raw rank | length-offdiag residual rank | triality-offdiag residual rank | six-block-offdiag residual rank |",
        "|---:|---:|---:|---:|---:|",
    ]
    for t in ["2", "3", "4"]:
        p = flat["mask_profiles"][t]
        rows.append(f"| {t} | {p['raw_rank']} | {p['length_offdiag_centered_rank']} | {p['triality_offdiag_centered_rank']} | {p['six_block_offdiag_centered_rank']} |")
    c = flat["closure_value_matrix_profiles"]
    rows.extend([
        "",
        "## Closure-Value Matrix",
        "",
        "| centering | residual rank |",
        "|---|---:|",
        f"| length offdiag | {c['length_offdiag_centered_rank']} |",
        f"| triality offdiag | {c['triality_offdiag_centered_rank']} |",
        f"| six-block offdiag | {c['six_block_offdiag_centered_rank']} |",
        "",
        "## Row-Channel Decision",
        "",
        "| comparison | result |",
        "|---|---|",
    ])
    for k, v in report["row_channel_tests"]["comparisons"].items():
        rows.append(f"| `{k}` | `{v}` |")
    rows.extend([
        "",
        "Prossima task: P13-side integration/order gate with P20/P21 coordination.",
    ])
    return "\n".join(rows) + "\n"


def make_markdown(report: Dict[str, Any], title: str) -> str:
    flat = report["flat_relation_invariant"]
    lines = [
        f"# {title}",
        "",
        f"Status: {report['status']}",
        "Verifier: `scripts/p21_s15_flat_invariant_beyond_length.py`",
        "",
        "## Result In Simple Terms",
        "",
        "The flat layer does contain a real invariant beyond the long/short length orientation.  For an ordered pair of distinct points, the size of its rank-2 closure can be `2`, `3`, or `4`, and this is not determined by whether the two points are long or short.",
        "",
        "The stronger row-level question is negative: after length-neutral normalization, the flat masks do not produce another canonical row witness on top of S14.  In particular, `K_24` and `K_16` have the same flat-size profile, and the block-centered S14 kernel residual has zero Hadamard interaction with the block-centered flat residual masks.",
        "",
        "## Incidence Invariant",
        "",
        "The closure-size matrix has the following off-diagonal residual ranks after subtracting the best partition-only model:",
        "",
        "| relation | length | triality | six-block |",
        "|---|---:|---:|---:|",
        f"| closure value `c(i,j)` | {flat['closure_value_matrix_profiles']['length_offdiag_centered_rank']} | {flat['closure_value_matrix_profiles']['triality_offdiag_centered_rank']} | {flat['closure_value_matrix_profiles']['six_block_offdiag_centered_rank']} |",
        "",
        "For the binary closure-size masks:",
        "",
        "| mask | raw rank | length residual | triality residual | six-block residual |",
        "|---:|---:|---:|---:|---:|",
    ]
    for t in ["2", "3", "4"]:
        p = flat["mask_profiles"][t]
        lines.append(f"| {t} | {p['raw_rank']} | {p['length_offdiag_centered_rank']} | {p['triality_offdiag_centered_rank']} | {p['six_block_offdiag_centered_rank']} |")
    lines.extend([
        "",
        "The length-only failure is visible directly in the ordered-pair counts: same-length pairs split between closure sizes `3` and `4`, while cross-length pairs split between closure sizes `2` and `4`.",
        "",
        "## Row Boundary",
        "",
        "| test | result |",
        "|---|---|",
    ])
    for k, v in report["row_channel_tests"]["comparisons"].items():
        lines.append(f"| `{k}` | `{v}` |")
    lines.extend([
        "",
        "Thus S15 should be used as an incidence-layer statement: the flat closure relation is a genuine source layer beyond length, but it is not promoted as a new row-classification theorem or as a second independent row witness beyond S14.",
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
        out = Path(args.json_path) if args.json_path else root / "results" / "p21_s15_flat_invariant_beyond_length_replay.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        cert = root / "certified" / "P21_S15_FLAT_INVARIANT_BEYOND_LENGTH_CERTIFICATE.json"
        cert.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")
        print(f"WROTE {cert}")

    if args.write_md:
        out = Path(args.md_path) if args.md_path else root / "certified" / "P21_S15_FLAT_INVARIANT_BEYOND_LENGTH_CERTIFICATE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report, "P21-S15 Flat Invariant Beyond Length Certificate"), encoding="ascii")
        print(f"WROTE {out}")

    if args.write_table:
        out = Path(args.table_path) if args.table_path else root / "tables" / "P21_S15_FLAT_INVARIANT_BEYOND_LENGTH_TABLE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_table(report), encoding="ascii")
        print(f"WROTE {out}")

    if args.write_doc:
        out = Path(args.doc_path) if args.doc_path else root / "docs" / "P21_S15_FLAT_INVARIANT_BEYOND_LENGTH_2026_07_08.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report, "P21-S15 Flat Invariant Beyond Length"), encoding="ascii")
        print(f"WROTE {out}")

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())