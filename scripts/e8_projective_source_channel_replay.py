#!/usr/bin/env python3
"""Public replay for the projective E8 source-channel exhibit.

This bounded replay checks the E8 payload used by the paper: the 120-point
projective root carrier, the Gram-square graph, the rank-2 flat-size collapse,
the root-reflection row identity, and the main A7 subsystem-row separator.

Two compact public certificates are also checked:

* `artifacts/e8_standard_parabolic_fusion_certificate.json` records that the
  standard simple-parabolic same-type/order placements fuse under G_proj.
* `artifacts/e8_subsystem_separator_witnesses.json` records the five bounded
  parabolic-vs-coordinate-D8 subsystem-row witnesses.

The equality Aut(Gamma_E8)=G_proj is recorded through the bundled Sage transcript
`artifacts/e8_projective_automorphism_transcript.txt`. This script verifies the
transcript values but does not run Sage.

It is not an E8 theorem, Type-E theorem, root-subsystem classification,
root-system matroid novelty claim, classifier, or tiling test.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "e8_projective_source_channel_replay.json"
TRANSCRIPT = ROOT / "artifacts" / "e8_projective_automorphism_transcript.txt"
FUSION_CERT = ROOT / "artifacts" / "e8_standard_parabolic_fusion_certificate.json"
SUBSYSTEM_CERT = ROOT / "artifacts" / "e8_subsystem_separator_witnesses.json"

PROJECTIVE_WEYL_ORDER = 348_364_800
WEYL_ORDER = 696_729_600
W_FUNC = (1, 3, 9, 27, 81, 243, 729, 2187)


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_sha256(payload) -> str:
    return hashlib.sha256((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dot(a, b) -> int:
    return sum(x * y for x, y in zip(a, b))


def neg(v):
    return tuple(-x for x in v)


def canon(v):
    return min(v, neg(v))


def e8_scaled_roots():
    roots = []
    for i, j in itertools.combinations(range(8), 2):
        for si in (-2, 2):
            for sj in (-2, 2):
                v = [0] * 8
                v[i] = si
                v[j] = sj
                roots.append(tuple(v))
    for signs in itertools.product((-1, 1), repeat=8):
        if sum(1 for x in signs if x == -1) % 2 == 0:
            roots.append(tuple(signs))
    return sorted(set(roots))


def root_type(v):
    abs_values = sorted(abs(x) for x in v)
    if abs_values == [0, 0, 0, 0, 0, 0, 2, 2]:
        return "coordinate"
    if abs_values == [1] * 8:
        return "half"
    return "unknown"


def projective_roots(roots):
    return sorted({canon(v) for v in roots})


def gram_square_value(a, b) -> int:
    d = dot(a, b)
    q, r = divmod(d * d, 16)
    if r:
        raise ValueError(f"nonintegral Gram-square value from dot={d}")
    return q


def gram_square_matrix(points):
    return [[gram_square_value(a, b) for b in points] for a in points]


def rank_over_q(rows) -> int:
    mat = [[Fraction(x) for x in row] for row in rows if any(x != 0 for x in row)]
    if not mat:
        return 0
    m, n = len(mat), len(mat[0])
    rank = 0
    col = 0
    while rank < m and col < n:
        pivot = None
        for r in range(rank, m):
            if mat[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            col += 1
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        pv = mat[rank][col]
        mat[rank] = [x / pv for x in mat[rank]]
        for r in range(m):
            if r != rank and mat[r][col] != 0:
                factor = mat[r][col]
                mat[r] = [x - factor * y for x, y in zip(mat[r], mat[rank])]
        rank += 1
        col += 1
    return rank


def graph_parameters(adj):
    n = len(adj)
    degrees = [sum(row) for row in adj]
    lambdas = []
    mus = []
    for i, j in itertools.combinations(range(n), 2):
        common = sum(adj[i][k] and adj[j][k] for k in range(n))
        if adj[i][j]:
            lambdas.append(common)
        else:
            mus.append(common)
    return {
        "vertices": n,
        "degree_values": sorted(set(degrees)),
        "edge_count": sum(degrees) // 2,
        "lambda_values": sorted(set(lambdas)),
        "mu_values": sorted(set(mus)),
    }


def flat_channel_summary(points, gram, root_set, point_index):
    flat_counter = Counter()
    gram_counter = Counter()
    unique_flats = set()
    mismatches = []
    missing = []
    for i, j in itertools.combinations(range(len(points)), 2):
        a, b = points[i], points[j]
        d = dot(a, b)
        g = gram[i][j]
        if d == 0:
            flat = tuple(sorted((i, j)))
        elif abs(d) == 4:
            third = tuple(a[k] - b[k] for k in range(8)) if d == 4 else tuple(a[k] + b[k] for k in range(8))
            if third not in root_set:
                missing.append({"pair": [i, j], "dot_scaled": d, "third": list(third)})
                flat = tuple(sorted((i, j)))
            else:
                flat = tuple(sorted((i, j, point_index[canon(third)])))
        else:
            flat = tuple(sorted((i, j)))
            mismatches.append({"pair": [i, j], "unexpected_dot_scaled": d, "gram_square": g})
        unique_flats.add(flat)
        flat_counter[str(len(flat))] += 1
        gram_counter[str(g)] += 1
        if not ((g == 0 and len(flat) == 2) or (g == 1 and len(flat) == 3)):
            mismatches.append({"pair": [i, j], "dot_scaled": d, "gram_square": g, "flat_size": len(flat)})
    return {
        "pair_flat_size_counter": dict(sorted(flat_counter.items(), key=lambda kv: int(kv[0]))),
        "gram_counter": dict(sorted(gram_counter.items(), key=lambda kv: int(kv[0]))),
        "unique_flat_size_counter": dict(sorted(Counter(str(len(x)) for x in unique_flats).items(), key=lambda kv: int(kv[0]))),
        "missing_third_root_count": len(missing),
        "mismatch_count": len(mismatches),
    }


def reflect(x, a):
    d = dot(x, a)
    if d % 4 != 0:
        raise ValueError(f"nonintegral reflection coefficient: dot={d}")
    q = d // 4
    return tuple(x[i] - q * a[i] for i in range(8))


def find_simple_roots(roots):
    height_vectors = [
        (1, 2, 4, 8, 16, 32, 64, 128),
        (1, 3, 5, 7, 11, 13, 17, 19),
        (3, 5, 11, 17, 29, 41, 59, 83),
        (1, 5, 12, 27, 58, 121, 244, 497),
    ]
    for h in height_vectors:
        if any(dot(r, h) == 0 for r in roots):
            continue
        positive = [r for r in roots if dot(r, h) > 0]
        positive_set = set(positive)
        simple = []
        for r in positive:
            if not any(tuple(r[i] - a[i] for i in range(8)) in positive_set for a in positive):
                simple.append(r)
        if len(simple) == 8:
            return h, simple
    raise RuntimeError("failed to find simple roots")


def projective_reflection_permutation(points, point_index, root):
    return tuple(point_index[canon(reflect(p, root))] for p in points)


def reflection_row_summary(points, point_index, gram):
    n = len(points)
    aggregate = [[0 for _ in range(n)] for _ in range(n)]
    perms = []
    for root in points:
        perm = projective_reflection_permutation(points, point_index, root)
        perms.append(perm)
        for i, j in enumerate(perm):
            aggregate[i][j] += 1
    mismatches = []
    for i in range(n):
        for j in range(n):
            expected = 64 if i == j else 1 if gram[i][j] == 1 else 0
            if aggregate[i][j] != expected:
                mismatches.append([i, j, aggregate[i][j], expected])
    return {
        "reflection_count": len(set(perms)),
        "identity": "N_Ref = 64I + A_Gamma",
        "mismatch_count": len(mismatches),
        "row_sum_values": sorted(set(sum(row) for row in aggregate)),
        "column_sum_values": sorted(set(sum(aggregate[i][j] for i in range(n)) for j in range(n))),
        "centered_rank_from_nonzero_srg_eigenvalues": "119=35+84",
    }


def connected_components(vertices, edges):
    remaining = set(vertices)
    adj = {v: set() for v in remaining}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    comps = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        q = deque([start])
        comp = []
        while q:
            v = q.popleft()
            comp.append(v)
            for w in sorted(adj[v]):
                if w in remaining:
                    remaining.remove(w)
                    q.append(w)
        comps.append(sorted(comp))
    return comps


def component_type(comp, edges):
    n = len(comp)
    if n == 1:
        return "A1"
    adj = {v: set() for v in comp}
    for a, b in edges:
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    degrees = sorted(len(adj[v]) for v in comp)
    if max(degrees) <= 2:
        return f"A{n}"
    branch = [v for v in comp if len(adj[v]) == 3]
    if len(branch) == 1:
        center = branch[0]
        arms = []
        for nb in adj[center]:
            prev, cur, length = center, nb, 1
            while len(adj[cur]) == 2:
                nxt = next(x for x in adj[cur] if x != prev)
                prev, cur = cur, nxt
                length += 1
            arms.append(length)
        arms = sorted(arms)
        if arms == [1, 1, n - 3]:
            return f"D{n}"
        if arms == [1, 2, 2] and n == 6:
            return "E6"
        if arms == [1, 2, 3] and n == 7:
            return "E7"
        if arms == [1, 2, 4] and n == 8:
            return "E8_projective"
    return "Unknown"


def sorted_type(pieces):
    if not pieces:
        return "0"
    def key(piece):
        tail = piece[1:].replace("_projective", "")
        return (piece[0], int(tail) if tail.isdigit() else 0, piece)
    return "+".join(sorted(pieces, key=key))


def dynkin_type_from_base(base_roots):
    if not base_roots:
        return "0"
    edges = set()
    for a, b in itertools.combinations(range(len(base_roots)), 2):
        if dot(base_roots[a], base_roots[b]) == -4:
            edges.add((a, b))
    return sorted_type([component_type(comp, edges) for comp in connected_components(range(len(base_roots)), edges)])


def abstract_order(type_label):
    if type_label == "0":
        return 1
    total = 1
    for piece in type_label.split("+"):
        if piece.startswith("A") and piece[1:].isdigit():
            total *= math.factorial(int(piece[1:]) + 1)
        elif piece.startswith("D") and piece[1:].isdigit():
            n = int(piece[1:])
            total *= (2 ** (n - 1)) * math.factorial(n)
        elif piece == "E6":
            total *= 51840
        elif piece == "E7":
            total *= 2903040
        elif piece == "E8_projective":
            total *= PROJECTIVE_WEYL_ORDER
        else:
            raise ValueError(f"unknown type {piece}")
    return total


def closure_from_roots(gens, roots, root_index):
    subsystem = set()
    for g in gens:
        subsystem.add(root_index[g])
        subsystem.add(root_index[neg(g)])
    changed = True
    while changed:
        changed = False
        for ri in list(subsystem):
            r = roots[ri]
            for si in list(subsystem):
                image = reflect(roots[si], r)
                ii = root_index[image]
                if ii not in subsystem:
                    subsystem.add(ii)
                    changed = True
    return frozenset(subsystem)


def quotient_rank_nullity(matrix, eigenvalue):
    shifted = []
    for i, row in enumerate(matrix):
        shifted.append([row[j] - (eigenvalue if i == j else 0) for j in range(len(row))])
    return len(matrix) - rank_over_q(shifted)


def orbits_from_generators(gens, n):
    remaining = set(range(n))
    out = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        q = deque([start])
        orbit = [start]
        while q:
            x = q.popleft()
            for gen in gens:
                y = gen[x]
                if y in remaining:
                    remaining.remove(y)
                    orbit.append(y)
                    q.append(y)
        out.append(sorted(orbit))
    return sorted(out, key=lambda o: (len(o), o[0]))


def quotient_matrix(orbits, adjacency):
    index_to_orbit = {}
    for oi, orbit in enumerate(orbits):
        for v in orbit:
            index_to_orbit[v] = oi
    quotient = []
    equitable = True
    for orbit in orbits:
        row_counts = []
        for v in orbit:
            counts = [0 for _ in orbits]
            for w, val in enumerate(adjacency[v]):
                if val == 1:
                    counts[index_to_orbit[w]] += 1
            row_counts.append(counts)
        first = row_counts[0]
        if any(counts != first for counts in row_counts):
            equitable = False
        quotient.append(first)
    return quotient, equitable


def base_of_root_indices(indices, roots):
    positive = []
    for idx in indices:
        val = dot(roots[idx], W_FUNC)
        if val > 0:
            positive.append(idx)
        elif val == 0:
            raise ValueError("non-generic height vector")
    positive_roots = {roots[idx] for idx in positive}
    base = []
    for idx in positive:
        rv = roots[idx]
        decomposable = False
        for jdx in positive:
            if jdx == idx:
                continue
            if tuple(a - b for a, b in zip(rv, roots[jdx])) in positive_roots:
                decomposable = True
                break
        if not decomposable:
            base.append(rv)
    return base


def type_of_root_indices(indices, roots):
    return dynkin_type_from_base(base_of_root_indices(indices, roots))


def complement_root_indices(gens, roots):
    return [idx for idx, root in enumerate(roots) if all(dot(root, gen) == 0 for gen in gens)]


def row_record(label, origin, base_indices, base_roots, roots, root_index, points, point_index, adjacency):
    gens = [base_roots[i] for i in base_indices]
    typ = dynkin_type_from_base(gens)
    subsystem = closure_from_roots(gens, roots, root_index)
    pset = {point_index[canon(roots[idx])] for idx in subsystem}
    perms = [projective_reflection_permutation(points, point_index, gen) for gen in gens]
    orbits = orbits_from_generators(perms, len(points))
    quotient, equitable = quotient_matrix(orbits, adjacency)
    rank_u35 = quotient_rank_nullity(quotient, 8)
    rank_u84 = quotient_rank_nullity(quotient, -4)
    comp_indices = complement_root_indices(gens, roots)
    return {
        "label": label,
        "origin": origin,
        "base_nodes": [i + 1 for i in base_indices],
        "abstract_type": typ,
        "row_size_or_order": abstract_order(typ),
        "subsystem_projective_pair_count": len(pset),
        "complement_type": type_of_root_indices(comp_indices, roots),
        "complement_projective_pair_count": len({point_index[canon(roots[idx])] for idx in comp_indices}),
        "orbit_sizes_on_Pi120": sorted(len(o) for o in orbits),
        "quotient_equitable": equitable,
        "rank_std": rank_u35 + rank_u84,
        "rank_U35": rank_u35,
        "rank_U84": rank_u84,
        "point_set_sha256": sha256_text(canonical_json(sorted(pset))),
    }


def transcript_summary():
    text = TRANSCRIPT.read_text(encoding="utf-8") if TRANSCRIPT.exists() else ""
    required = [
        "|roots| = 240",
        "|Pi_120| = 120",
        "SRG target (120,56,28,24)? True",
        "|G_proj generated by simple reflections| = 348364800",
        "expected |W(E8)|/2 = 348364800",
        "|Aut(Gamma)| = 348364800",
        "Aut(Gamma)=G_proj by inclusion+same order? True",
        "PASS",
    ]
    return {
        "path": "artifacts/e8_projective_automorphism_transcript.txt",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None,
        "required_lines_present": {line: line in text for line in required},
    }


def support_certificate_summary(path: Path):
    data = load_json(path)
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pass": bool(data.get("pass")),
        "status": data.get("status"),
        "summary": data.get("summary"),
    }, data


def main() -> None:
    roots = e8_scaled_roots()
    root_index = {root: i for i, root in enumerate(roots)}
    points = projective_roots(roots)
    point_index = {point: i for i, point in enumerate(points)}
    gram = gram_square_matrix(points)
    adjacency = [[0 if i == j else gram[i][j] for j in range(len(points))] for i in range(len(points))]
    graph = graph_parameters(adjacency)
    flat = flat_channel_summary(points, gram, set(roots), point_index)
    reflection = reflection_row_summary(points, point_index, gram)
    _, simple_roots = find_simple_roots(roots)
    d8_base = [
        (2, -2, 0, 0, 0, 0, 0, 0),
        (0, 2, -2, 0, 0, 0, 0, 0),
        (0, 0, 2, -2, 0, 0, 0, 0),
        (0, 0, 0, 2, -2, 0, 0, 0),
        (0, 0, 0, 0, 2, -2, 0, 0),
        (0, 0, 0, 0, 0, 2, -2, 0),
        (0, 0, 0, 0, 0, 0, 2, -2),
        (0, 0, 0, 0, 0, 0, 2, 2),
    ]
    par_a7 = row_record("Par_1234567", "standard_parabolic", tuple(range(7)), simple_roots, roots, root_index, points, point_index, adjacency)
    d8_a7 = row_record("D8_1234567", "coordinate_D8_subdiagram", tuple(range(7)), d8_base, roots, root_index, points, point_index, adjacency)
    sage = transcript_summary()
    fusion_summary, fusion = support_certificate_summary(FUSION_CERT)
    subsystem_summary, subsystem = support_certificate_summary(SUBSYSTEM_CERT)
    witness_types = subsystem.get("summary", {}).get("display_witness_types", [])

    checks = {
        "root_count": len(roots) == 240,
        "projective_pair_count": len(points) == 120,
        "coordinate_half_split": [sum(1 for p in points if root_type(p) == "coordinate"), sum(1 for p in points if root_type(p) == "half")] == [56, 64],
        "graph_srg": graph == {"vertices": 120, "degree_values": [56], "edge_count": 3360, "lambda_values": [28], "mu_values": [24]},
        "flat_channel_collapse": flat["mismatch_count"] == 0 and flat["missing_third_root_count"] == 0 and flat["pair_flat_size_counter"] == {"2": 3780, "3": 3360},
        "reflection_identity": reflection["mismatch_count"] == 0 and reflection["reflection_count"] == 120,
        "sage_transcript_aut_equality": all(sage["required_lines_present"].values()),
        "fusion_certificate_pass": fusion_summary["pass"] and fusion.get("summary", {}).get("multi_placement_groups") == 27 and fusion.get("summary", {}).get("all_multi_group_placements_conjugate") is True,
        "subsystem_certificate_pass": subsystem_summary["pass"] and witness_types == ["4A1", "A3+2A1", "2A3", "A5+A1", "A7"],
        "a7_direct_recompute": par_a7["abstract_type"] == "A7" and d8_a7["abstract_type"] == "A7" and par_a7["row_size_or_order"] == 40320 and d8_a7["row_size_or_order"] == 40320 and par_a7["orbit_sizes_on_Pi120"] == [8, 28, 28, 56] and d8_a7["orbit_sizes_on_Pi120"] == [1, 28, 28, 28, 35] and [par_a7["rank_std"], par_a7["rank_U35"], par_a7["rank_U84"]] == [3, 1, 2] and [d8_a7["rank_std"], d8_a7["rank_U35"], d8_a7["rank_U84"]] == [4, 1, 3],
    }
    artifact = {
        "date": "2026-07-09",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "scope": "bounded public replay for X26/E8 projective root-shadow source-channel exhibit",
        "counts": {
            "roots": len(roots),
            "projective_root_pairs": len(points),
            "coordinate_projective_pairs": sum(1 for p in points if root_type(p) == "coordinate"),
            "half_projective_pairs": sum(1 for p in points if root_type(p) == "half"),
        },
        "gram_square_graph": graph,
        "rank2_flat_size_channel": flat,
        "source_action": {
            "projective_weyl_order": PROJECTIVE_WEYL_ORDER,
            "weyl_order": WEYL_ORDER,
            "aut_equality_certificate": sage,
            "aut_gamma_equals_gproj_by_transcript": checks["sage_transcript_aut_equality"],
        },
        "reflection_row": reflection,
        "standard_parabolic_fusion_certificate": fusion_summary,
        "subsystem_separator_certificate": subsystem_summary,
        "a7_showcase_direct_recompute": {
            "parabolic": par_a7,
            "d8_internal": d8_a7,
        },
        "checks": checks,
        "boundary": [
            "bounded X26/E8 replay only",
            "no E8 theorem or Type-E theorem",
            "no full root-subsystem classification",
            "no Dynkin/Borel-de Siebenthal/Oshima novelty claim",
            "no root-system matroid novelty claim",
            "no classifier or tiling claim",
        ],
    }
    artifact["sha256"] = payload_sha256(artifact)
    write_json(OUT, artifact)
    print(f"status={artifact['status']}")
    print(f"roots={len(roots)}")
    print(f"Pi_120={len(points)}")
    print(f"Aut transcript PASS={checks['sage_transcript_aut_equality']}")
    print(f"fusion PASS={checks['fusion_certificate_pass']}")
    print(f"witness_types={','.join(witness_types)}")
    print(f"a7_par_orbits={par_a7['orbit_sizes_on_Pi120']}")
    print(f"a7_d8_orbits={d8_a7['orbit_sizes_on_Pi120']}")
    print(f"artifact_sha256={artifact['sha256']}")
    return bool(artifact["pass"])


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)