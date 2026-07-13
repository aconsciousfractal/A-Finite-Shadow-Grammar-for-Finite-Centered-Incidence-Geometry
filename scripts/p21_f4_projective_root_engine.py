#!/usr/bin/env python3
"""P21 F4 projective-root starter engine.

Pure-Python exact checks for the first P21 source-lock gate.
This script intentionally covers only the geometric/projective Weyl layer.
The matroid automorphism layer G_mat is left pending until the source/generator
route is explicitly locked.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

Vec = Tuple[int, int, int, int]
Perm = Tuple[int, ...]


def dot(a: Vec, b: Vec) -> int:
    return sum(x * y for x, y in zip(a, b))


def neg(v: Vec) -> Vec:
    return tuple(-x for x in v)  # type: ignore[return-value]


def canonical_projective(v: Vec) -> Vec:
    """Choose one representative from {v,-v} deterministically."""
    w = neg(v)
    return min(v, w)


def f4_signed_roots_scaled() -> List[Vec]:
    roots = set()

    # Long roots: 2(+-e_i +- e_j).
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1, 1):
                for sj in (-1, 1):
                    v = [0, 0, 0, 0]
                    v[i] = 2 * si
                    v[j] = 2 * sj
                    roots.add(tuple(v))

    # Short coordinate roots: +-2 e_i.
    for i in range(4):
        for s in (-1, 1):
            v = [0, 0, 0, 0]
            v[i] = 2 * s
            roots.add(tuple(v))

    # Short half-sum roots after scaling by 2: (+-1,+-1,+-1,+-1).
    for s0 in (-1, 1):
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                for s3 in (-1, 1):
                    roots.add((s0, s1, s2, s3))

    return sorted(roots)


def squared_length(v: Vec) -> int:
    return dot(v, v)


def length_label(v: Vec) -> str:
    q = squared_length(v)
    if q == 8:
        return "long"
    if q == 4:
        return "short"
    raise ValueError(f"unexpected squared length {q} for {v}")


def reflect(v: Vec, alpha: Vec) -> Vec:
    """Reflect v across the hyperplane perpendicular to alpha."""
    aa = dot(alpha, alpha)
    coeff = Fraction(2 * dot(v, alpha), aa)
    out = []
    for x, a in zip(v, alpha):
        y = Fraction(x) - coeff * a
        if y.denominator != 1:
            raise ArithmeticError((v, alpha, y))
        out.append(int(y))
    return tuple(out)  # type: ignore[return-value]


def simple_roots_scaled() -> List[Vec]:
    # Standard F4 simple-root model scaled by 2.
    return [
        (0, 2, -2, 0),
        (0, 0, 2, -2),
        (0, 0, 0, 2),
        (1, -1, -1, -1),
    ]


def reflection_perm(alpha: Vec, roots: Sequence[Vec], index: Dict[Vec, int]) -> Perm:
    return tuple(index[reflect(v, alpha)] for v in roots)


def compose(p: Perm, q: Perm) -> Perm:
    """Composition p after q for permutations represented by i -> p[i]."""
    return tuple(p[q[i]] for i in range(len(q)))


def generate_group(gens: Sequence[Perm], degree: int) -> List[Perm]:
    identity = tuple(range(degree))
    seen = {identity}
    order: List[Perm] = [identity]
    queue: deque[Perm] = deque([identity])
    while queue:
        g = queue.popleft()
        for s in gens:
            h = compose(s, g)
            if h not in seen:
                seen.add(h)
                order.append(h)
                queue.append(h)
    return order


def projective_pairs(roots: Sequence[Vec]) -> Tuple[List[Vec], Dict[Vec, int], Dict[int, int]]:
    reps = sorted({canonical_projective(v) for v in roots})
    pair_index = {rep: i for i, rep in enumerate(reps)}
    root_to_pair = {i: pair_index[canonical_projective(v)] for i, v in enumerate(roots)}
    return reps, pair_index, root_to_pair


def project_perm(root_perm: Perm, roots: Sequence[Vec], pair_index: Dict[Vec, int], pair_reps: Sequence[Vec], root_index: Dict[Vec, int]) -> Perm:
    out = []
    for rep in pair_reps:
        i = root_index[rep]
        image_root = roots[root_perm[i]]
        out.append(pair_index[canonical_projective(image_root)])
    return tuple(out)


def orbits(perms: Iterable[Perm], degree: int) -> List[List[int]]:
    remaining = set(range(degree))
    result: List[List[int]] = []
    perms_list = list(perms)
    while remaining:
        start = min(remaining)
        orb = {start}
        q = deque([start])
        while q:
            x = q.popleft()
            for p in perms_list:
                y = p[x]
                if y not in orb:
                    orb.add(y)
                    q.append(y)
        result.append(sorted(orb))
        remaining -= orb
    return result


def rank_fraction(mat: List[List[Fraction]]) -> int:
    if not mat:
        return 0
    a = [row[:] for row in mat]
    rows = len(a)
    cols = len(a[0])
    r = 0
    for c in range(cols):
        pivot = None
        for i in range(r, rows):
            if a[i][c] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        pv = a[r][c]
        a[r] = [x / pv for x in a[r]]
        for i in range(rows):
            if i != r and a[i][c] != 0:
                factor = a[i][c]
                a[i] = [x - factor * y for x, y in zip(a[i], a[r])]
        r += 1
        if r == rows:
            break
    return r


def row_sum_matrix(perms: Sequence[Perm], degree: int) -> List[List[Fraction]]:
    mat = [[Fraction(0) for _ in range(degree)] for _ in range(degree)]
    for p in perms:
        for j, i in enumerate(p):
            # Column j maps to row i.
            mat[i][j] += 1
    return mat


def global_centered_rank(perms: Sequence[Perm], degree: int) -> int:
    n = len(perms)
    mat = row_sum_matrix(perms, degree)
    center = Fraction(n, degree)
    centered = [[mat[i][j] - center for j in range(degree)] for i in range(degree)]
    return rank_fraction(centered)


def length_centered_rank(perms: Sequence[Perm], labels: Sequence[str]) -> int:
    degree = len(labels)
    n = len(perms)
    mat = row_sum_matrix(perms, degree)
    counts = {lab: labels.count(lab) for lab in sorted(set(labels))}
    centered = [[mat[i][j] for j in range(degree)] for i in range(degree)]
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            if li == lj:
                centered[i][j] -= Fraction(n, counts[li])
    return rank_fraction(centered)


def preserves_labels(p: Perm, labels: Sequence[str]) -> bool:
    return all(labels[p[i]] == labels[i] for i in range(len(p)))


def central_inversion_perm(roots: Sequence[Vec], root_index: Dict[Vec, int]) -> Perm:
    return tuple(root_index[neg(v)] for v in roots)


def build_report() -> Dict[str, object]:
    roots = f4_signed_roots_scaled()
    root_index = {v: i for i, v in enumerate(roots)}
    pair_reps, pair_index, root_to_pair = projective_pairs(roots)
    pair_labels = [length_label(v) for v in pair_reps]

    gens = [reflection_perm(a, roots, root_index) for a in simple_roots_scaled()]
    w48 = generate_group(gens, len(roots))
    proj = sorted({project_perm(g, roots, pair_index, pair_reps, root_index) for g in w48})

    minus = central_inversion_perm(roots, root_index)
    minus_in_w48 = minus in set(w48)
    minus_projective = project_perm(minus, roots, pair_index, pair_reps, root_index)

    length_counts = {lab: pair_labels.count(lab) for lab in sorted(set(pair_labels))}
    orbit_sizes = sorted(len(o) for o in orbits(proj, len(pair_reps)))

    all_preserve_length = all(preserves_labels(p, pair_labels) for p in proj)

    report: Dict[str, object] = {
        "route_id": "P21",
        "engine": "p21_f4_projective_root_engine.py",
        "scope": "geometric_projective_weyl_layer_only",
        "matroid_layer_status": "LOCKED_IN_S5_SEPARATE_GATE",
        "signed_root_count": len(roots),
        "signed_length_counts": {
            "long": sum(1 for v in roots if length_label(v) == "long"),
            "short": sum(1 for v in roots if length_label(v) == "short"),
        },
        "projective_pair_count": len(pair_reps),
        "projective_length_counts": length_counts,
        "simple_roots_scaled": [list(a) for a in simple_roots_scaled()],
        "w48_order": len(w48),
        "central_inversion_in_w48": minus_in_w48,
        "central_inversion_projective_is_identity": minus_projective == tuple(range(len(pair_reps))),
        "g_proj_order": len(proj),
        "g_proj_preserves_length": all_preserve_length,
        "g_proj_orbit_sizes": orbit_sizes,
        "g_proj_global_centered_rank_scout": global_centered_rank(proj, len(pair_reps)),
        "g_proj_length_centered_rank_scout": length_centered_rank(proj, pair_labels),
        "expected": {
            "signed_root_count": 48,
            "signed_length_counts": {"long": 24, "short": 24},
            "projective_pair_count": 24,
            "projective_length_counts": {"long": 12, "short": 12},
            "w48_order": 1152,
            "central_inversion_in_w48": True,
            "central_inversion_projective_is_identity": True,
            "g_proj_order": 576,
            "g_proj_preserves_length": True,
            "g_proj_orbit_sizes": [12, 12],
            "g_proj_global_centered_rank_scout": 1,
            "g_proj_length_centered_rank_scout": 0,
        },
    }
    report["pass"] = all(
        report[k] == v for k, v in report["expected"].items()  # type: ignore[index,union-attr]
    )
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
            out = Path(__file__).resolve().parents[1] / "results" / "p21_s1_s3_projective_root_engine_replay.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="ascii")
        print(f"WROTE {out}")

    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
