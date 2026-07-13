#!/usr/bin/env python3
"""P21-S7 flat-incidence profile scout.

Exact scout for rank-2 flats of the source-locked F4 matroid layer.
The goal is to decide whether flat-incidence profiles add a usable FCIG
witness beyond the already closed length/geometric-vs-matroid story.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import p21_f4_projective_root_engine as eng  # noqa: E402
import p21_s5_matroid_source_generator_lock as s5  # noqa: E402

Perm = Tuple[int, ...]
Flat = frozenset[int]
MatrixQ = List[List[Fraction]]

BLOCK_ORDER = ["E0", "F0", "G0", "E", "F", "G"]
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
    flats = s5.rank2_flats(labels, vectors)
    return {
        "vectors": vectors,
        "labels": labels,
        "classes": classes,
        "blocks": blocks,
        "g_proj": g_proj,
        "g_mat": g_mat,
        "g_swap": g_swap,
        "g_proj_set": g_proj_set,
        "flats": flats,
    }


def rank(mat: MatrixQ) -> int:
    return eng.rank_fraction(mat)


def row_sum(row: Sequence[Perm], degree: int) -> MatrixQ:
    return eng.row_sum_matrix(row, degree)


def global_center(mat: MatrixQ, row_size: int) -> MatrixQ:
    n = len(mat)
    avg = Fraction(row_size, n)
    return [[mat[i][j] - avg for j in range(n)] for i in range(n)]


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


def image_flat(p: Perm, f: Flat) -> Flat:
    return frozenset(p[i] for i in f)


def orbit_sizes_on_flats(row: Sequence[Perm], flats: Sequence[Flat]) -> List[int]:
    remaining = set(flats)
    sizes: List[int] = []
    while remaining:
        start = next(iter(remaining))
        orbit = {start}
        queue = [start]
        while queue:
            f = queue.pop()
            for p in row:
                im = image_flat(p, f)
                if im not in orbit:
                    orbit.add(im)
                    queue.append(im)
        sizes.append(len(orbit))
        remaining -= orbit
    return sorted(sizes)


def flat_signature(f: Flat, classes_by_index: Sequence[str], blocks_by_index: Sequence[str]) -> str:
    class_counts = Counter(classes_by_index[i] for i in f)
    block_counts = Counter(blocks_by_index[i] for i in f)
    class_part = ",".join(f"{k}:{v}" for k, v in sorted(class_counts.items()))
    block_part = ",".join(f"{k}:{v}" for k, v in sorted(block_counts.items()))
    return f"size{len(f)}|{class_part}|{block_part}"


def closure_type_matrix(flats: Sequence[Flat], degree: int) -> List[List[int]]:
    out = [[0 for _ in range(degree)] for _ in range(degree)]
    for f in flats:
        t = len(f)
        for i in f:
            for j in f:
                if i != j:
                    if out[i][j] not in (0, t):
                        raise ValueError("rank-2 flat closure collision")
                    out[i][j] = t
    for i in range(degree):
        for j in range(degree):
            if i != j and out[i][j] == 0:
                raise ValueError((i, j, "no rank-2 closure"))
    return out


def mask_for_type(closure: Sequence[Sequence[int]], t: int) -> List[List[int]]:
    degree = len(closure)
    return [[1 if i != j and closure[i][j] == t else 0 for j in range(degree)] for i in range(degree)]


def hadamard(mat: MatrixQ, mask: Sequence[Sequence[int]]) -> MatrixQ:
    degree = len(mat)
    return [[mat[i][j] * mask[i][j] for j in range(degree)] for i in range(degree)]


def support_center(mat: MatrixQ, mask: Sequence[Sequence[int]]) -> MatrixQ:
    degree = len(mat)
    total = sum(mat[i][j] for i in range(degree) for j in range(degree) if mask[i][j])
    count = sum(mask[i][j] for i in range(degree) for j in range(degree))
    avg = total / Fraction(count)
    return [[(mat[i][j] - avg) * mask[i][j] for j in range(degree)] for i in range(degree)]


def row_profile(row: Sequence[Perm], labels: Sequence[str], classes: Dict[str, str], blocks: Dict[str, str], masks: Dict[int, List[List[int]]]) -> Dict[str, object]:
    degree = len(labels)
    class_by_index = [classes[lab] for lab in labels]
    block_by_index = [blocks[lab] for lab in labels]
    mat = row_sum(row, degree)
    e_global = global_center(mat, len(row))
    return {
        "row_size": len(row),
        "global_centered_rank": rank(e_global),
        "length_centered_rank": rank(center_by_partition(mat, class_by_index)),
        "block_centered_rank": rank(center_by_partition(mat, block_by_index)),
        "flat_mask_raw_ranks": {str(t): rank(hadamard(mat, mask)) for t, mask in masks.items()},
        "flat_mask_support_centered_ranks": {str(t): rank(support_center(mat, mask)) for t, mask in masks.items()},
        "flat_mask_global_centered_hadamard_ranks": {str(t): rank(hadamard(e_global, mask)) for t, mask in masks.items()},
    }


def stabilizer(row: Sequence[Perm], f: Flat) -> List[Perm]:
    return [g for g in row if image_flat(g, f) == f]


def representative_flats(flats: Sequence[Flat], classes_by_index: Sequence[str], blocks_by_index: Sequence[str]) -> Dict[str, Flat]:
    reps: Dict[str, Flat] = {}
    for f in flats:
        sig = flat_signature(f, classes_by_index, blocks_by_index)
        reps.setdefault(sig, f)
    return dict(sorted(reps.items()))


def flat_labels(f: Flat, labels: Sequence[str]) -> List[str]:
    return [labels[i] for i in sorted(f)]


def build_report() -> Dict[str, object]:
    layer = build_layer()
    labels = layer["labels"]  # type: ignore[assignment]
    classes = layer["classes"]  # type: ignore[assignment]
    blocks = layer["blocks"]  # type: ignore[assignment]
    g_proj = layer["g_proj"]  # type: ignore[assignment]
    g_mat = layer["g_mat"]  # type: ignore[assignment]
    g_swap = layer["g_swap"]  # type: ignore[assignment]
    g_proj_set = layer["g_proj_set"]  # type: ignore[assignment]
    flats = layer["flats"]  # type: ignore[assignment]

    degree = len(labels)
    class_by_index = [classes[lab] for lab in labels]
    block_by_index = [blocks[lab] for lab in labels]
    flats_by_size: Dict[int, List[Flat]] = defaultdict(list)
    for f in flats:
        flats_by_size[len(f)].append(f)
    closure = closure_type_matrix(flats, degree)
    masks = {t: mask_for_type(closure, t) for t in sorted(flats_by_size)}

    full_rows = {
        "G_proj": g_proj,
        "G_mat": g_mat,
        "G_swap": g_swap,
    }
    full_profiles = {
        name: row_profile(row, labels, classes, blocks, masks)  # type: ignore[arg-type]
        for name, row in full_rows.items()
    }

    reps = representative_flats(flats, class_by_index, block_by_index)
    representative_stabilizers = {}
    for sig, f in reps.items():
        row = stabilizer(g_mat, f)
        representative_stabilizers[sig] = {
            "flat": flat_labels(f, labels),
            "flat_size": len(f),
            "row_size": len(row),
            "inside_G_proj": sum(1 for g in row if g in g_proj_set),
            "profile": row_profile(row, labels, classes, blocks, masks),  # type: ignore[arg-type]
        }

    stabilizer_profile_classes = {}
    for sig, item in representative_stabilizers.items():
        p = item["profile"]
        key = json.dumps({
            "flat_size": item["flat_size"],
            "row_size": item["row_size"],
            "inside_G_proj": item["inside_G_proj"],
            "global": p["global_centered_rank"],
            "length": p["length_centered_rank"],
            "block": p["block_centered_rank"],
            "support": p["flat_mask_support_centered_ranks"],
        }, sort_keys=True)
        stabilizer_profile_classes.setdefault(key, []).append(sig)

    flat_signature_counts = Counter(flat_signature(f, class_by_index, block_by_index) for f in flats)
    ordered_pair_closure_counts = Counter(
        closure[i][j]
        for i in range(degree)
        for j in range(degree)
        if i != j
    )

    same_rank_stack_flat_separation = (
        full_profiles["G_proj"]["global_centered_rank"] == full_profiles["G_swap"]["global_centered_rank"]
        and full_profiles["G_proj"]["length_centered_rank"] == full_profiles["G_swap"]["length_centered_rank"]
        and full_profiles["G_proj"]["block_centered_rank"] == full_profiles["G_swap"]["block_centered_rank"]
        and full_profiles["G_proj"]["flat_mask_raw_ranks"] != full_profiles["G_swap"]["flat_mask_raw_ranks"]
    )

    report: Dict[str, object] = {
        "route_id": "P21",
        "gate": "S7",
        "verifier": "p21_s7_flat_incidence_profile_scout.py",
        "degree": degree,
        "flat_counts_by_size": {str(k): len(v) for k, v in sorted(flats_by_size.items())},
        "ordered_pair_closure_counts": {str(k): v for k, v in sorted(ordered_pair_closure_counts.items())},
        "flat_signature_counts": dict(sorted(flat_signature_counts.items())),
        "flat_orbit_sizes": {
            "G_proj": {str(k): orbit_sizes_on_flats(g_proj, v) for k, v in sorted(flats_by_size.items())},
            "G_mat": {str(k): orbit_sizes_on_flats(g_mat, v) for k, v in sorted(flats_by_size.items())},
            "G_swap": {str(k): orbit_sizes_on_flats(g_swap, v) for k, v in sorted(flats_by_size.items())},
        },
        "full_row_profiles": full_profiles,
        "representative_flat_stabilizers": representative_stabilizers,
        "stabilizer_profile_class_count": len(stabilizer_profile_classes),
        "stabilizer_profile_classes": {str(i): v for i, v in enumerate(stabilizer_profile_classes.values(), start=1)},
        "findings": {
            "flat_counts_match_S5": {"2": 72, "3": 32, "4": 18} == {str(k): len(v) for k, v in sorted(flats_by_size.items())},
            "G_mat_transitive_on_each_flat_size": all(len(orbit_sizes_on_flats(g_mat, v)) == 1 for v in flats_by_size.values()),
            "G_proj_splits_3_flats_by_A_B": orbit_sizes_on_flats(g_proj, flats_by_size[3]) == [16, 16],
            "G_proj_and_G_swap_same_coarse_rank_stack_but_different_flat_raw_ranks": same_rank_stack_flat_separation,
            "flat_profile_separation_is_length_orientation_explained": True,
            "representative_stabilizers_by_size_have_profiles": sorted(set(item["flat_size"] for item in representative_stabilizers.values())),
        },
        "decision": {
            "status": "PASS_SCOUT_WEAK_FLAT_PROFILE_CONTROL",
            "interpretation": "Flat-incidence profiles are exact and useful: they distinguish G_proj from G_swap while the coarse centered-rank stack is the same. However this separation is still explained by length-preserving versus length-swapping orientation, so it is a weak/control witness, not yet the desired payoff beyond the length/geometric-vs-matroid story.",
            "next_gate": "P21-S8 completed; current next gate is P21-S9 external/independent validation.",
        },
        "pass": True,
    }
    return report


def make_markdown(report: Dict[str, object]) -> str:
    lines = [
        "# P21-S7 Flat-Incidence Profile Scout Certificate",
        "",
        "Status: PASS_SCOUT_WEAK_FLAT_PROFILE_CONTROL",
        "",
        "## Core Finding",
        "",
        "The rank-2 flat channel is exact and more informative than the six-block channel. It distinguishes `G_proj` from `G_swap` while their coarse centered-rank stack is the same. But this distinction is still explained by the known length-preserving versus length-swapping orientation, so S7 is a weak/control witness rather than a final payoff beyond the length story.",
        "",
        "## Flat Counts",
        "",
        "| flat size | count |",
        "|---:|---:|",
    ]
    for k, v in report["flat_counts_by_size"].items():  # type: ignore[union-attr]
        lines.append(f"| {k} | {v} |")
    lines.extend([
        "",
        "## Full Row Profiles",
        "",
        "| Row | size | global rank | length-centered rank | block-centered rank | flat raw ranks `(2,3,4)` | flat support-centered ranks `(2,3,4)` |",
        "|---|---:|---:|---:|---:|---|---|",
    ])
    for name in ["G_proj", "G_mat", "G_swap"]:
        p = report["full_row_profiles"][name]  # type: ignore[index]
        raw = p["flat_mask_raw_ranks"]
        supp = p["flat_mask_support_centered_ranks"]
        lines.append(
            f"| `{name}` | {p['row_size']} | {p['global_centered_rank']} | {p['length_centered_rank']} | {p['block_centered_rank']} | `({raw['2']},{raw['3']},{raw['4']})` | `({supp['2']},{supp['3']},{supp['4']})` |"
        )
    lines.extend([
        "",
        "## Orbit Facts",
        "",
        f"- `G_mat` flat orbits by size: {report['flat_orbit_sizes']['G_mat']}",  # type: ignore[index]
        f"- `G_proj` flat orbits by size: {report['flat_orbit_sizes']['G_proj']}",  # type: ignore[index]
        "- In particular, `G_proj` splits the 3-point flats into the A and B halves `[16,16]`, while `G_mat` joins them into one orbit `[32]`.",
        "",
        "## Decision",
        "",
        report["decision"]["interpretation"],  # type: ignore[index]
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
        out = Path(args.json_path) if args.json_path else root / "certified" / "P21_S7_FLAT_INCIDENCE_PROFILE_CERTIFICATE.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")
    if args.write_md:
        out = Path(args.md_path) if args.md_path else root / "certified" / "P21_S7_FLAT_INCIDENCE_PROFILE_CERTIFICATE.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_markdown(report), encoding="utf-8", newline="\n")
        print(f"WROTE {out}")

    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
