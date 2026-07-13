#!/usr/bin/env python3
"""Public E6 projective-root engine replay helper.

No external dependencies.  The engine uses simple-root coordinates for E6,
generates roots by exact simple reflections, projectivizes antipodal roots,
constructs the projective root graph, and verifies the projective Weyl action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

# E6 Cartan matrix: chain 1-2-3-4-5 with node 6 attached to 3.
CARTAN = (
    (2, -1, 0, 0, 0, 0),
    (-1, 2, -1, 0, 0, 0),
    (0, -1, 2, -1, 0, -1),
    (0, 0, -1, 2, -1, 0),
    (0, 0, 0, -1, 2, 0),
    (0, 0, -1, 0, 0, 2),
)
RANK = 6
EXPECTED = {
    "root_count": 72,
    "projective_pair_count": 36,
    "weyl_projective_order": 51840,
    "gamma_vertices": 36,
    "gamma_degree": 20,
    "gamma_lambda": 10,
    "gamma_mu": 12,
    "aut_gamma_order": 51840,
}


def dot(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    return sum(u[i] * CARTAN[i][j] * v[j] for i in range(RANK) for j in range(RANK))


def reflect_vec(v: tuple[int, ...], i: int) -> tuple[int, ...]:
    # s_i(v) = v - (v, alpha_i) alpha_i.  Since alpha_i is the i-th basis vector,
    # only coordinate i changes.
    inner = sum(v[j] * CARTAN[j][i] for j in range(RANK))
    w = list(v)
    w[i] -= inner
    return tuple(w)


def neg(v: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-x for x in v)


def canonical_pair(v: tuple[int, ...]) -> tuple[int, ...]:
    nv = neg(v)
    return min(v, nv)


def generate_roots() -> list[tuple[int, ...]]:
    seeds = []
    for i in range(RANK):
        e = tuple(1 if j == i else 0 for j in range(RANK))
        seeds.append(e)
        seeds.append(neg(e))
    roots = set(seeds)
    q = deque(seeds)
    while q:
        v = q.popleft()
        for i in range(RANK):
            w = reflect_vec(v, i)
            if w not in roots:
                roots.add(w)
                q.append(w)
    return sorted(roots)


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    # q after p: i -> q[p[i]]
    return tuple(q[p[i]] for i in range(len(p)))


def generate_group(generators: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    n = len(generators[0])
    identity = tuple(range(n))
    seen = {identity}
    group = [identity]
    q = deque([identity])
    while q:
        g = q.popleft()
        for s in generators:
            h = compose(g, s)
            if h not in seen:
                seen.add(h)
                group.append(h)
                q.append(h)
    return group


def build_projective_action(roots: list[tuple[int, ...]]):
    pairs = sorted({canonical_pair(r) for r in roots})
    pair_index = {p: i for i, p in enumerate(pairs)}
    root_to_pair = {r: pair_index[canonical_pair(r)] for r in roots}
    generators = []
    for i in range(RANK):
        perm = []
        for p in pairs:
            perm.append(root_to_pair[reflect_vec(p, i)])
        generators.append(tuple(perm))
    return pairs, generators


def graph_from_pairs(pairs: list[tuple[int, ...]]):
    n = len(pairs)
    adj = [0] * n
    colors = {}
    for i, j in combinations(range(n), 2):
        val = abs(dot(pairs[i], pairs[j]))
        colors[(i, j)] = val
        if val == 1:
            adj[i] |= 1 << j
            adj[j] |= 1 << i
        elif val != 0:
            raise ValueError(f"unexpected absolute inner product {val} for pair {(i, j)}")
    return adj, colors


def graph_parameters(adj: list[int]) -> dict:
    n = len(adj)
    degrees = [adj[i].bit_count() for i in range(n)]
    lambda_values = []
    mu_values = []
    for i, j in combinations(range(n), 2):
        common = (adj[i] & adj[j]).bit_count()
        if adj[i] & (1 << j):
            lambda_values.append(common)
        else:
            mu_values.append(common)
    return {
        "vertices": n,
        "degree_values": sorted(set(degrees)),
        "degree_counter": dict(sorted(Counter(degrees).items())),
        "lambda_values": sorted(set(lambda_values)),
        "mu_values": sorted(set(mu_values)),
        "edge_count": sum(degrees) // 2,
        "nonedge_count": n * (n - 1) // 2 - sum(degrees) // 2,
    }


def srg_identity_holds(adj: list[int], k: int, lam: int, mu: int) -> bool:
    n = len(adj)
    for i in range(n):
        for j in range(n):
            common = (adj[i] & adj[j]).bit_count()
            if i == j:
                if common != k:
                    return False
            elif adj[i] & (1 << j):
                if common != lam:
                    return False
            else:
                if common != mu:
                    return False
    return True


def orbit_sizes(group: list[tuple[int, ...]], n: int) -> list[int]:
    unseen = set(range(n))
    sizes = []
    while unseen:
        start = next(iter(unseen))
        orb = {g[start] for g in group}
        sizes.append(len(orb))
        unseen -= orb
    return sorted(sizes)


def is_graph_automorphism(perm: tuple[int, ...], adj: list[int]) -> bool:
    n = len(adj)
    for i in range(n):
        mapped_mask = 0
        row = adj[i]
        for j in range(n):
            if row & (1 << j):
                mapped_mask |= 1 << perm[j]
        if mapped_mask != adj[perm[i]]:
            return False
    return True


def signatures_for_base(adj: list[int], base: tuple[int, ...]) -> list[tuple[int, ...]]:
    sigs = []
    for v in range(len(adj)):
        parts = []
        for b in base:
            if v == b:
                parts.append(2)
            elif adj[v] & (1 << b):
                parts.append(1)
            else:
                parts.append(0)
        sigs.append(tuple(parts))
    return sigs


def signature_counter(adj: list[int], base: tuple[int, ...]) -> Counter:
    return Counter(signatures_for_base(adj, base))


def find_resolving_base(adj: list[int]) -> tuple[int, ...]:
    n = len(adj)
    base: tuple[int, ...] = tuple()
    while True:
        sigs = signatures_for_base(adj, base)
        if len(set(sigs)) == n:
            return base
        best_v = None
        best_score = (-1, -1)
        for v in range(n):
            if v in base:
                continue
            new_base = base + (v,)
            counter = signature_counter(adj, new_base)
            distinct = len(counter)
            largest_cell = max(counter.values())
            score = (distinct, -largest_cell)
            if score > best_score:
                best_score = score
                best_v = v
        assert best_v is not None
        base = base + (best_v,)


def count_graph_automorphisms_by_resolving_base(adj: list[int], base: tuple[int, ...]) -> dict:
    n = len(adj)
    base_sigs = signatures_for_base(adj, base)
    if len(set(base_sigs)) != n:
        raise ValueError("base is not resolving")
    full_counter = signature_counter(adj, base)
    valid_count = 0
    invalid_candidate_count = 0
    partial_counter_prunes = 0
    candidates_visited = 0
    valid_examples = []

    def recurse(chosen: list[int]) -> None:
        nonlocal valid_count, invalid_candidate_count, partial_counter_prunes, candidates_visited
        k = len(chosen)
        if k == len(base):
            candidates_visited += 1
            image_base = tuple(chosen)
            if signature_counter(adj, image_base) != full_counter:
                invalid_candidate_count += 1
                return
            image_sigs = signatures_for_base(adj, image_base)
            sig_to_vertex = {sig: i for i, sig in enumerate(image_sigs)}
            if len(sig_to_vertex) != n:
                invalid_candidate_count += 1
                return
            perm = tuple(sig_to_vertex[sig] for sig in base_sigs)
            if is_graph_automorphism(perm, adj):
                valid_count += 1
                if len(valid_examples) < 3:
                    valid_examples.append(list(perm))
            else:
                invalid_candidate_count += 1
            return

        b = base[k]
        for c in range(n):
            if c in chosen:
                continue
            ok = True
            for idx, prev_c in enumerate(chosen):
                prev_b = base[idx]
                if bool(adj[b] & (1 << prev_b)) != bool(adj[c] & (1 << prev_c)):
                    ok = False
                    break
            if not ok:
                continue
            trial = tuple(chosen + [c])
            # Necessary pruning: every partial signature multiplicity must match.
            if signature_counter(adj, base[: k + 1]) != signature_counter(adj, trial):
                partial_counter_prunes += 1
                continue
            recurse(chosen + [c])

    recurse([])
    return {
        "base": list(base),
        "base_size": len(base),
        "valid_automorphism_count": valid_count,
        "candidate_tuples_checked": candidates_visited,
        "invalid_candidate_count": invalid_candidate_count,
        "partial_counter_prunes": partial_counter_prunes,
        "valid_example_count_recorded": len(valid_examples),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="write JSON artifact")
    args = parser.parse_args()

    roots = generate_roots()
    root_norms = sorted(set(dot(r, r) for r in roots))
    pairs, simple_perms = build_projective_action(roots)
    group = generate_group(simple_perms)
    adj, pair_inner_colors = graph_from_pairs(pairs)
    params = graph_parameters(adj)
    simple_are_aut = all(is_graph_automorphism(s, adj) for s in simple_perms)
    group_sample_are_aut = all(is_graph_automorphism(g, adj) for g in group[: min(100, len(group))])
    base = find_resolving_base(adj)
    aut_count = count_graph_automorphisms_by_resolving_base(adj, base)

    pair_color_counter = Counter(pair_inner_colors.values())
    srg_ok = srg_identity_holds(adj, 20, 10, 12)
    checks = {
        "root_count": len(roots) == EXPECTED["root_count"],
        "projective_pair_count": len(pairs) == EXPECTED["projective_pair_count"],
        "root_norms_all_2": root_norms == [2],
        "weyl_projective_order": len(group) == EXPECTED["weyl_projective_order"],
        "projective_action_transitive": orbit_sizes(group, len(pairs)) == [36],
        "gamma_vertices": params["vertices"] == EXPECTED["gamma_vertices"],
        "gamma_degree": params["degree_values"] == [EXPECTED["gamma_degree"]],
        "gamma_lambda": params["lambda_values"] == [EXPECTED["gamma_lambda"]],
        "gamma_mu": params["mu_values"] == [EXPECTED["gamma_mu"]],
        "gamma_srg_identity": srg_ok,
        "simple_generators_preserve_gamma": simple_are_aut,
        "group_sample_preserves_gamma": group_sample_are_aut,
        "aut_gamma_order": aut_count["valid_automorphism_count"] == EXPECTED["aut_gamma_order"],
    }

    artifact = {
        "artifact": "e6_projective_root_engine",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "model": {
            "cartan_matrix": [list(row) for row in CARTAN],
            "rank": RANK,
            "coordinate_model": "simple-root integer coordinates",
            "projectivization": "alpha ~ -alpha",
        },
        "counts": {
            "root_count": len(roots),
            "projective_pair_count": len(pairs),
            "weyl_projective_order": len(group),
            "root_norm_values": root_norms,
            "projective_orbit_sizes": orbit_sizes(group, len(pairs)),
            "simple_generator_count": len(simple_perms),
        },
        "gamma": {
            "parameters": params,
            "pair_abs_inner_counter": dict(sorted(pair_color_counter.items())),
            "srg_identity_holds": srg_ok,
            "expected_eigenvalues_from_srg": {"20": 1, "2": 20, "-4": 15},
        },
        "automorphism_count": aut_count,
        "checks": checks,
    }
    blob = json.dumps(artifact, indent=2, sort_keys=True)
    artifact["artifact_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    blob = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob, encoding="utf-8", newline="\n")
    print(json.dumps({
        "pass": artifact["pass"],
        "root_count": len(roots),
        "projective_pair_count": len(pairs),
        "weyl_projective_order": len(group),
        "gamma_degree_values": params["degree_values"],
        "gamma_lambda_values": params["lambda_values"],
        "gamma_mu_values": params["mu_values"],
        "aut_gamma_order": aut_count["valid_automorphism_count"],
        "resolving_base_size": aut_count["base_size"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()