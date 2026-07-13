#!/usr/bin/env python3
"""P21-S5 F4 matroid source/generator lock verifier.

This script uses the Fried-Gerek-Gordon-Perunicic labels for M(F4), verifies
an explicit length-swap automorphism sigma from Lemma 3.6, and checks that
<G_proj, sigma> has the source-claimed order 1152.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import p21_f4_projective_root_engine as eng  # noqa: E402

VecQ = Tuple[Fraction, Fraction, Fraction, Fraction]
Perm = Tuple[int, ...]


def qvec(xs: Sequence[int | Fraction]) -> VecQ:
    return tuple(Fraction(x) for x in xs)  # type: ignore[return-value]


def basis(i: int) -> VecQ:
    return qvec([1 if k == i else 0 for k in range(4)])


def add(a: VecQ, b: VecQ) -> VecQ:
    return tuple(x + y for x, y in zip(a, b))  # type: ignore[return-value]


def sub(a: VecQ, b: VecQ) -> VecQ:
    return tuple(x - y for x, y in zip(a, b))  # type: ignore[return-value]


def dot(a: VecQ, b: VecQ) -> Fraction:
    return sum(x * y for x, y in zip(a, b))


def reflect(v: VecQ, alpha: VecQ) -> VecQ:
    coeff = Fraction(2) * dot(v, alpha) / dot(alpha, alpha)
    return tuple(x - coeff * a for x, a in zip(v, alpha))  # type: ignore[return-value]


def normalize_projective(v: VecQ) -> Tuple[int, int, int, int]:
    den_lcm = 1
    for x in v:
        den_lcm = math.lcm(den_lcm, x.denominator)
    ints = [int(x * den_lcm) for x in v]
    g = 0
    for x in ints:
        g = math.gcd(g, abs(x))
    if g == 0:
        raise ValueError("zero vector")
    ints = [x // g for x in ints]
    neg = [-x for x in ints]
    return tuple(min(ints, neg))  # type: ignore[return-value]


def source_vectors() -> Dict[str, VecQ]:
    e = [basis(i) for i in range(4)]
    labels: Dict[str, VecQ] = {}

    for i in range(4):
        for j in range(i + 1, 4):
            labels[f"ap{i+1}{j+1}"] = add(e[i], e[j])
            labels[f"am{i+1}{j+1}"] = sub(e[i], e[j])

    total = qvec([1, 1, 1, 1])
    for i in range(4):
        labels[f"e{i+1}"] = e[i]
        labels[f"f{i+1}"] = sub(total, qvec([2 if k == i else 0 for k in range(4)]))

    labels["g1"] = qvec([1, 1, 1, 1])
    labels["g2"] = qvec([1, 1, -1, -1])
    labels["g3"] = qvec([1, -1, 1, -1])
    labels["g4"] = qvec([1, -1, -1, 1])
    return labels


def label_classes(labels: Sequence[str]) -> Dict[str, str]:
    out = {}
    for lab in labels:
        out[lab] = "A_long" if lab.startswith("a") else "B_short"
    return out


def block_labels(labels: Sequence[str]) -> Dict[str, str]:
    blocks = {}
    for lab in labels:
        if lab in {"ap12", "am12", "ap34", "am34"}:
            blocks[lab] = "E0"
        elif lab in {"ap13", "am13", "ap24", "am24"}:
            blocks[lab] = "F0"
        elif lab in {"ap14", "am14", "ap23", "am23"}:
            blocks[lab] = "G0"
        elif lab.startswith("e"):
            blocks[lab] = "E"
        elif lab.startswith("f"):
            blocks[lab] = "F"
        elif lab.startswith("g"):
            blocks[lab] = "G"
        else:
            raise ValueError(lab)
    return blocks


def rank_vectors(vectors: Sequence[VecQ]) -> int:
    if not vectors:
        return 0
    mat = [[v[row] for v in vectors] for row in range(4)]
    rows = len(mat)
    cols = len(mat[0])
    r = 0
    for c in range(cols):
        pivot = None
        for i in range(r, rows):
            if mat[i][c] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        mat[r], mat[pivot] = mat[pivot], mat[r]
        pv = mat[r][c]
        mat[r] = [x / pv for x in mat[r]]
        for i in range(rows):
            if i != r and mat[i][c] != 0:
                factor = mat[i][c]
                mat[i] = [x - factor * y for x, y in zip(mat[i], mat[r])]
        r += 1
        if r == rows:
            break
    return r


def perm_from_mapping(labels: Sequence[str], mapping: Dict[str, str]) -> Perm:
    idx = {lab: i for i, lab in enumerate(labels)}
    return tuple(idx[mapping.get(lab, lab)] for lab in labels)


def sigma_mapping() -> Dict[str, str]:
    pairs = [
        ("e1", "ap12"),
        ("e2", "am12"),
        ("e3", "ap34"),
        ("e4", "am34"),
        ("f1", "am23"),
        ("f2", "ap23"),
        ("f3", "am14"),
        ("f4", "ap14"),
        ("g1", "ap13"),
        ("g2", "am13"),
        ("g3", "ap24"),
        ("g4", "am24"),
    ]
    m: Dict[str, str] = {}
    for a, b in pairs:
        m[a] = b
        m[b] = a
    return m


def simple_roots_unscaled_for_reflections() -> List[VecQ]:
    # Scaling a root does not change its reflecting hyperplane.
    return [
        qvec([0, 1, -1, 0]),
        qvec([0, 0, 1, -1]),
        qvec([0, 0, 0, 1]),
        qvec([1, -1, -1, -1]),
    ]


def source_reflection_perm(alpha: VecQ, labels: Sequence[str], vectors: Dict[str, VecQ], proj_index: Dict[Tuple[int, int, int, int], int]) -> Perm:
    out = []
    for lab in labels:
        image = normalize_projective(reflect(vectors[lab], alpha))
        out.append(proj_index[image])
    return tuple(out)


def preserves_classes(p: Perm, classes_by_index: Sequence[str]) -> bool:
    return all(classes_by_index[p[i]] == classes_by_index[i] for i in range(len(p)))


def swaps_classes(p: Perm, classes_by_index: Sequence[str]) -> bool:
    return all(classes_by_index[p[i]] != classes_by_index[i] for i in range(len(p)))


def matroid_rank_preserved(p: Perm, labels: Sequence[str], vectors: Dict[str, VecQ]) -> Tuple[bool, int]:
    checked = 0
    for size in range(5):
        for subset in itertools.combinations(range(len(labels)), size):
            image = tuple(sorted(p[i] for i in subset))
            r1 = rank_vectors([vectors[labels[i]] for i in subset])
            r2 = rank_vectors([vectors[labels[i]] for i in image])
            checked += 1
            if r1 != r2:
                return False, checked
    return True, checked


def rank2_flats(labels: Sequence[str], vectors: Dict[str, VecQ]) -> List[frozenset[int]]:
    flats = set()
    for i, j in itertools.combinations(range(len(labels)), 2):
        base_rank = rank_vectors([vectors[labels[i]], vectors[labels[j]]])
        if base_rank != 2:
            continue
        closure = []
        for k in range(len(labels)):
            if rank_vectors([vectors[labels[i]], vectors[labels[j]], vectors[labels[k]]]) == 2:
                closure.append(k)
        flats.add(frozenset(closure))
    return sorted(flats, key=lambda f: (len(f), sorted(f)))


def row_sum_matrix(perms: Sequence[Perm], degree: int) -> List[List[Fraction]]:
    return eng.row_sum_matrix(perms, degree)


def centered_rank(perms: Sequence[Perm], degree: int) -> int:
    return eng.global_centered_rank(perms, degree)


def matrix_is_constant(mat: List[List[Fraction]], value: Fraction) -> bool:
    return all(x == value for row in mat for x in row)


def cross_centered_rank(perms: Sequence[Perm], classes_by_index: Sequence[str]) -> int:
    degree = len(classes_by_index)
    n = len(perms)
    mat = row_sum_matrix(perms, degree)
    counts = Counter(classes_by_index)
    centered = [[mat[i][j] for j in range(degree)] for i in range(degree)]
    for i, ci in enumerate(classes_by_index):
        for j, cj in enumerate(classes_by_index):
            if ci != cj:
                centered[i][j] -= Fraction(n, counts[ci])
    return eng.rank_fraction(centered)


def mat_vec_mul(mat: List[List[Fraction]], vec: Sequence[Fraction]) -> List[Fraction]:
    return [sum(row[j] * vec[j] for j in range(len(vec))) for row in mat]


def build_report() -> Dict[str, object]:
    vectors = source_vectors()
    labels = sorted(vectors)
    classes = label_classes(labels)
    blocks = block_labels(labels)
    class_by_index = [classes[lab] for lab in labels]
    proj_index = {normalize_projective(vectors[lab]): i for i, lab in enumerate(labels)}

    root_gens = [source_reflection_perm(alpha, labels, vectors, proj_index) for alpha in simple_roots_unscaled_for_reflections()]
    g_proj = eng.generate_group(root_gens, len(labels))

    sigma = perm_from_mapping(labels, sigma_mapping())
    sigma_rank_ok, rank_subsets_checked = matroid_rank_preserved(sigma, labels, vectors)

    g_mat = eng.generate_group(root_gens + [sigma], len(labels))
    g_proj_set = set(g_proj)
    g_swap = [g for g in g_mat if g not in g_proj_set]


    flats = rank2_flats(labels, vectors)
    flat_size_counts = Counter(len(f) for f in flats)
    flat3_A = 0
    flat3_B = 0
    flat4_mixed_2_2 = 0
    for f in flats:
        cls = [class_by_index[i] for i in f]
        if len(f) == 3 and all(c == "A_long" for c in cls):
            flat3_A += 1
        if len(f) == 3 and all(c == "B_short" for c in cls):
            flat3_B += 1
        if len(f) == 4 and cls.count("A_long") == 2 and cls.count("B_short") == 2:
            flat4_mixed_2_2 += 1

    n_gmat = row_sum_matrix(g_mat, len(labels))
    n_gswap = row_sum_matrix(g_swap, len(labels))
    u_len = [Fraction(1) if c == "A_long" else Fraction(-1) for c in class_by_index]
    n_gmat_u = mat_vec_mul(n_gmat, u_len)
    n_gswap_u = mat_vec_mul(n_gswap, u_len)

    report: Dict[str, object] = {
        "route_id": "P21",
        "gate": "S5",
        "verifier": "p21_s5_matroid_source_generator_lock.py",
        "source": "Fried-Gerek-Gordon-Perunicic 2007, EJC 14(1), R78",
        "source_pdf": "sources/fried_gerek_gordon_perunicic_2007_f4_matroid_automorphisms.pdf",
        "degree": len(labels),
        "A_long_count": sum(1 for c in class_by_index if c == "A_long"),
        "B_short_count": sum(1 for c in class_by_index if c == "B_short"),
        "block_counts": dict(sorted(Counter(blocks.values()).items())),
        "g_proj_order_source_labels": len(g_proj),
        "g_proj_preserves_A_B": all(preserves_classes(g, class_by_index) for g in g_proj),
        "sigma_swaps_A_B": swaps_classes(sigma, class_by_index),
        "sigma_is_in_g_proj": sigma in g_proj_set,
        "sigma_rank_preserved_subsets_le_4": sigma_rank_ok,
        "sigma_rank_subsets_checked": rank_subsets_checked,
        "g_mat_generated_order": len(g_mat),
        "g_swap_size": len(g_swap),
        "g_mat_transitive_orbit_sizes": sorted(len(o) for o in eng.orbits(g_mat, len(labels))),
        "g_proj_orbit_sizes": sorted(len(o) for o in eng.orbits(g_proj, len(labels))),
        "generator_rank_route": "projective_reflections_are_linear; sigma_checked_on_all_subsets_size_le_4",
        "rank2_flat_size_counts": dict(sorted(flat_size_counts.items())),
        "flat3_A_count": flat3_A,
        "flat3_B_count": flat3_B,
        "flat4_mixed_2_2_count": flat4_mixed_2_2,
        "g_mat_global_centered_rank": centered_rank(g_mat, len(labels)),
        "g_mat_row_sum_constant_48": matrix_is_constant(n_gmat, Fraction(48)),
        "g_mat_kills_length_line": n_gmat_u == [Fraction(0) for _ in labels],
        "g_swap_cross_centered_rank": cross_centered_rank(g_swap, class_by_index),
        "g_swap_reverses_length_line": n_gswap_u == [Fraction(-len(g_swap)) * x for x in u_len],
        "expected": {
            "degree": 24,
            "A_long_count": 12,
            "B_short_count": 12,
            "block_counts": {"E": 4, "E0": 4, "F": 4, "F0": 4, "G": 4, "G0": 4},
            "g_proj_order_source_labels": 576,
            "g_proj_preserves_A_B": True,
            "sigma_swaps_A_B": True,
            "sigma_is_in_g_proj": False,
            "sigma_rank_preserved_subsets_le_4": True,
            "sigma_rank_subsets_checked": 12951,
            "g_mat_generated_order": 1152,
            "g_swap_size": 576,
            "g_mat_transitive_orbit_sizes": [24],
            "g_proj_orbit_sizes": [12, 12],
            "rank2_flat_size_counts": {2: 72, 3: 32, 4: 18},
            "flat3_A_count": 16,
            "flat3_B_count": 16,
            "flat4_mixed_2_2_count": 18,
            "g_mat_global_centered_rank": 0,
            "g_mat_row_sum_constant_48": True,
            "g_mat_kills_length_line": True,
            "g_swap_cross_centered_rank": 0,
            "g_swap_reverses_length_line": True,
        },
    }
    report["pass"] = all(report[k] == v for k, v in report["expected"].items())  # type: ignore[index,union-attr]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", action="store_true")
    parser.add_argument("--json-path", default=None)
    args = parser.parse_args()

    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)

    if args.write_json:
        if args.json_path:
            out = Path(args.json_path)
        else:
            out = Path(__file__).resolve().parents[1] / "results" / "p21_s5_matroid_source_generator_lock_replay.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")

    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
