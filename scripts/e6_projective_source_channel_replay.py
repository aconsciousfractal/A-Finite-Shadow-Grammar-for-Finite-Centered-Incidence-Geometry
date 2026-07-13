#!/usr/bin/env python3
"""Public replay for the projective E6 source-aware control exhibit.

This top-level replay records all E6 checks used by the paper: projective-root
engine, Gram graph, flat-size channel collapse, 3-circuit channel collapse,
source-row ranks, and the bounded U20/U15 split witness.  It is not a standalone
E6 theorem, Schlaefli/27-line route, matroid novelty claim, classifier, or
tiling test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "e6_projective_source_channel_replay.json"

from e6_projective_root_engine import (
    RANK,
    build_projective_action,
    count_graph_automorphisms_by_resolving_base,
    dot,
    find_resolving_base,
    generate_group,
    generate_roots,
    graph_from_pairs,
    graph_parameters,
    srg_identity_holds,
)
from e6_projective_source_rows import (
    adjacency_matrix,
    eigenspace_basis,
    root_reflection_perms,
    row_report,
)

E6_EDGES = {(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)}


def payload_sha256(payload) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def rank_vectors(vectors: list[tuple[int, ...] | list[int]]) -> int:
    mat = [[Fraction(x) for x in row] for row in vectors if any(row)]
    if not mat:
        return 0
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


def flat_closure_indices(pairs: list[tuple[int, ...]], i: int, j: int) -> list[int]:
    base = [pairs[i], pairs[j]]
    base_rank = rank_vectors(base)
    return [k for k, root in enumerate(pairs) if rank_vectors(base + [root]) == base_rank]


def flat_size_channel(pairs: list[tuple[int, ...]]) -> dict:
    mapping: dict[int, set[int]] = defaultdict(set)
    reverse: dict[int, set[int]] = defaultdict(set)
    flat_size_counter: Counter[int] = Counter()
    gram_counter: Counter[int] = Counter()
    mismatches = []
    examples = {}
    for i, j in combinations(range(len(pairs)), 2):
        gram = abs(dot(pairs[i], pairs[j]))
        closure = flat_closure_indices(pairs, i, j)
        flat_size = len(closure)
        mapping[gram].add(flat_size)
        reverse[flat_size].add(gram)
        flat_size_counter[flat_size] += 1
        gram_counter[gram] += 1
        examples.setdefault(f"gram_{gram}_flat_{flat_size}", {"pair": [i, j], "closure_size": flat_size, "closure_indices": closure})
        if (gram == 1 and flat_size != 3) or (gram == 0 and flat_size != 2):
            mismatches.append({"pair": [i, j], "gram": gram, "flat_size": flat_size})
    return {
        "pair_count": sum(flat_size_counter.values()),
        "gram_color_counter": dict(sorted(gram_counter.items())),
        "flat_size_counter": dict(sorted(flat_size_counter.items())),
        "mapping_gram_to_flat_size": {str(k): sorted(v) for k, v in sorted(mapping.items())},
        "mapping_flat_size_to_gram": {str(k): sorted(v) for k, v in sorted(reverse.items())},
        "closure_examples": examples,
        "mismatch_count": len(mismatches),
        "mismatches_first_10": mismatches[:10],
    }


def compute_three_circuits(pairs: list[tuple[int, ...]]) -> list[tuple[int, int, int]]:
    return [triple for triple in combinations(range(len(pairs)), 3) if rank_vectors([pairs[i] for i in triple]) == 2]


def derived_graph_from_circuits(n: int, circuits: list[tuple[int, int, int]]) -> tuple[list[int], Counter, Counter]:
    adj = [0] * n
    pair_count: Counter[tuple[int, int]] = Counter()
    point_count: Counter[int] = Counter()
    for c in circuits:
        for i in c:
            point_count[i] += 1
        for a, b in combinations(c, 2):
            i, j = sorted((a, b))
            pair_count[(i, j)] += 1
            adj[i] |= 1 << j
            adj[j] |= 1 << i
    return adj, pair_count, point_count


def graph_edge_count(adj: list[int]) -> int:
    return sum(row.bit_count() for row in adj) // 2


def permute_circuit(circuit: tuple[int, int, int], perm: tuple[int, ...]) -> tuple[int, int, int]:
    return tuple(sorted(perm[i] for i in circuit))


def generators_preserve_circuits(circuits: list[tuple[int, int, int]], generators: list[tuple[int, ...]]) -> bool:
    circuit_set = set(circuits)
    return all(permute_circuit(circuit, gen) in circuit_set for gen in generators for circuit in circuits)


def circuit_channel(pairs: list[tuple[int, ...]], simple_perms: list[tuple[int, ...]], group: list[tuple[int, ...]], gamma_adj: list[int]) -> dict:
    circuits = compute_three_circuits(pairs)
    circuit_adj, pair_circuit_count, point_circuit_count = derived_graph_from_circuits(len(pairs), circuits)
    pair_incidence_by_gram: dict[str, Counter[int]] = defaultdict(Counter)
    for i, j in combinations(range(len(pairs)), 2):
        key = str(abs(dot(pairs[i], pairs[j])))
        pair_incidence_by_gram[key][pair_circuit_count[(i, j)]] += 1
    base = find_resolving_base(circuit_adj)
    aut_count = count_graph_automorphisms_by_resolving_base(circuit_adj, base)
    simple_preserve = generators_preserve_circuits(circuits, simple_perms)
    return {
        "three_circuit_count": len(circuits),
        "point_circuit_degree_values": sorted(set(point_circuit_count.values())),
        "point_circuit_degree_counter": dict(sorted(Counter(point_circuit_count.values()).items())),
        "pair_circuit_incidence_by_gram": {g: dict(sorted(c.items())) for g, c in sorted(pair_incidence_by_gram.items())},
        "derived_graph_matches_gamma": circuit_adj == gamma_adj,
        "derived_graph_edge_count": graph_edge_count(circuit_adj),
        "derived_graph_aut_order": aut_count["valid_automorphism_count"],
        "derived_graph_resolving_base": aut_count["base"],
        "simple_generators_preserve_circuit_set": simple_preserve,
        "weyl_projective_order": len(group),
        "sample_circuits_first_12": [list(c) for c in circuits[:12]],
    }


def powerset_indices(n: int):
    for r in range(1, n + 1):
        for combo in combinations(range(n), r):
            yield combo


def unique_perms(perms):
    return sorted(set(perms))


def parabolic_type(combo: tuple[int, ...]) -> str:
    nodes = set(combo)
    if not nodes:
        return "trivial"
    adj = {i: set() for i in nodes}
    for a, b in E6_EDGES:
        if a in nodes and b in nodes:
            adj[a].add(b)
            adj[b].add(a)
    seen = set()
    parts = []
    for start in sorted(nodes):
        if start in seen:
            continue
        stack = [start]
        comp = []
        seen.add(start)
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        size = len(comp)
        degs = sorted(len(adj[v]) for v in comp)
        edge_count = sum(len(adj[v]) for v in comp) // 2
        if size == 1:
            parts.append("A1")
        elif edge_count == size - 1 and max(degs) <= 2:
            parts.append(f"A{size}")
        elif size == 4 and degs == [1, 1, 1, 3]:
            parts.append("D4")
        elif size == 5 and degs == [1, 1, 1, 2, 3]:
            parts.append("D5")
        elif size == 6:
            parts.append("E6")
        else:
            parts.append("T" + "".join(str(i) for i in sorted(comp)))
    def key(part: str) -> tuple[int, str]:
        return (int(part[1:]) if part[0] in "ADE" and part[1:].isdigit() else 99, part)
    return "+".join(sorted(parts, key=key, reverse=True))


def compact_row(row: dict, row_type: str | None = None) -> dict:
    out = {
        "label": row["label"],
        "kind": row["kind"],
        "row_size": row["row_size"],
        "rank_std": row["rank_std"],
        "rank_U20": row["rank_U20"],
        "rank_U15": row["rank_U15"],
        "orbit_sizes_on_Pi36": row["orbit_sizes_on_Pi36"],
        "row_col_sums_ok": row["row_col_sums_ok"],
    }
    if row_type is not None:
        out["parabolic_type"] = row_type
    return out


def pair_witnesses(rows: list[dict]) -> dict:
    same_rank_split = []
    same_size_rank_split = []
    same_size_orbit_split = []
    same_type_size_rank_split = []
    for a, b in combinations(rows, 2):
        split_a = (a["rank_U20"], a["rank_U15"])
        split_b = (b["rank_U20"], b["rank_U15"])
        if split_a == split_b:
            continue
        item = {
            "A": a["label"],
            "B": b["label"],
            "A_type": a.get("parabolic_type"),
            "B_type": b.get("parabolic_type"),
            "rank_std_A": a["rank_std"],
            "rank_std_B": b["rank_std"],
            "A_split_U20_U15": list(split_a),
            "B_split_U20_U15": list(split_b),
            "A_size": a["row_size"],
            "B_size": b["row_size"],
            "A_orbits": a["orbit_sizes_on_Pi36"],
            "B_orbits": b["orbit_sizes_on_Pi36"],
        }
        if a["rank_std"] == b["rank_std"]:
            same_rank_split.append(item)
            if a["row_size"] == b["row_size"]:
                same_size_rank_split.append(item)
                if a.get("parabolic_type") == b.get("parabolic_type"):
                    same_type_size_rank_split.append(item)
        if (
            a["row_size"] == b["row_size"]
            and a["orbit_sizes_on_Pi36"] is not None
            and b["orbit_sizes_on_Pi36"] is not None
            and a["orbit_sizes_on_Pi36"] == b["orbit_sizes_on_Pi36"]
            and split_a != split_b
        ):
            same_size_orbit_split.append(item)
    return {
        "same_rank_split": same_rank_split,
        "same_size_rank_split": same_size_rank_split,
        "same_size_orbit_split": same_size_orbit_split,
        "same_type_size_rank_split": same_type_size_rank_split,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    roots = generate_roots()
    pairs, simple_perms = build_projective_action(roots)
    group = generate_group(simple_perms)
    n = len(pairs)
    gamma_adj, pair_inner_colors = graph_from_pairs(pairs)
    params = graph_parameters(gamma_adj)
    base = find_resolving_base(gamma_adj)
    aut_gamma = count_graph_automorphisms_by_resolving_base(gamma_adj, base)
    flat = flat_size_channel(pairs)
    circuit = circuit_channel(pairs, simple_perms, group, gamma_adj)

    adj_mat = adjacency_matrix(gamma_adj)
    basis20 = eigenspace_basis(adj_mat, 2)
    basis15 = eigenspace_basis(adj_mat, -4)
    std_basis = basis20 + basis15

    candidate_rows = [
        compact_row(row_report("G", "subgroup", group, n, basis20, basis15, std_basis)),
        compact_row(row_report("Stab_p0", "subgroup", [g for g in group if g[0] == 0], n, basis20, basis15, std_basis)),
        compact_row(row_report("Ref", "finite_subset", root_reflection_perms(pairs), n, basis20, basis15, std_basis)),
        compact_row(row_report("Simp", "finite_subset", unique_perms(simple_perms), n, basis20, basis15, std_basis)),
    ]
    for combo in powerset_indices(len(simple_perms)):
        label = "Par_" + "".join(str(i) for i in combo)
        subgroup = generate_group([simple_perms[i] for i in combo])
        candidate_rows.append(compact_row(row_report(label, "subgroup", subgroup, n, basis20, basis15, std_basis), parabolic_type(combo)))

    witnesses = pair_witnesses(candidate_rows)
    rank_profiles = Counter(f"std{r['rank_std']}_u{r['rank_U20']}_{r['rank_U15']}" for r in candidate_rows)
    parabolic_rows = [r for r in candidate_rows if r["label"].startswith("Par_")]
    row_by_label = {r["label"]: r for r in candidate_rows}
    named_witness = {"A": row_by_label.get("Par_012"), "B": row_by_label.get("Par_0135")}

    checks = {
        "root_count_72": len(roots) == 72,
        "projective_pair_count_36": n == 36,
        "weyl_group_order_51840": len(group) == 51840,
        "gamma_parameters_36_20_10_12": params["vertices"] == 36 and params["degree_values"] == [20] and params["lambda_values"] == [10] and params["mu_values"] == [12],
        "gamma_srg_identity": srg_identity_holds(gamma_adj, 20, 10, 12),
        "aut_gamma_order_51840": aut_gamma["valid_automorphism_count"] == 51840,
        "basis20_dim": len(basis20) == 20,
        "basis15_dim": len(basis15) == 15,
        "candidate_row_count_67": len(candidate_rows) == 67,
        "parabolic_row_count_63": len(parabolic_rows) == 63,
        "all_row_col_sums_ok": all(r["row_col_sums_ok"] for r in candidate_rows),
        "core_rows_present": {"G", "Stab_p0", "Ref", "Simp"}.issubset({r["label"] for r in candidate_rows}),
        "flat_size_pair_count_630": flat["pair_count"] == 630,
        "flat_size_channel_collapse": flat["mapping_gram_to_flat_size"] == {"0": [2], "1": [3]} and flat["mapping_flat_size_to_gram"] == {"2": [0], "3": [1]} and flat["mismatch_count"] == 0,
        "flat_size_aut_order_51840": aut_gamma["valid_automorphism_count"] == 51840,
        "three_circuit_count_120": circuit["three_circuit_count"] == 120,
        "circuit_derived_graph_matches_gamma": circuit["derived_graph_matches_gamma"],
        "circuit_aut_order_51840": circuit["derived_graph_aut_order"] == 51840,
        "circuit_aut_equals_weyl_by_sandwich": circuit["simple_generators_preserve_circuit_set"] and circuit["derived_graph_aut_order"] == len(group) == 51840,
        "named_witness_types": named_witness["A"] is not None and named_witness["B"] is not None and named_witness["A"].get("parabolic_type") == "A3" and named_witness["B"].get("parabolic_type") == "A2+A1+A1",
        "named_witness_same_size_rank_split": named_witness["A"] is not None and named_witness["B"] is not None and named_witness["A"]["row_size"] == named_witness["B"]["row_size"] == 24 and named_witness["A"]["rank_std"] == named_witness["B"]["rank_std"] == 8 and (named_witness["A"]["rank_U20"], named_witness["A"]["rank_U15"]) == (6, 2) and (named_witness["B"]["rank_U20"], named_witness["B"]["rank_U15"]) == (5, 3),
        "same_type_size_rank_split_count_zero": len(witnesses["same_type_size_rank_split"]) == 0,
        "same_size_orbit_split_count_zero": len(witnesses["same_size_orbit_split"]) == 0,
    }

    artifact = {
        "artifact": "e6_projective_source_channel_replay",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "carrier": "Pi_36 projective E6 root-pairs",
        "engine": {
            "root_count": len(roots),
            "projective_pair_count": n,
            "weyl_projective_order": len(group),
            "gamma_parameters": params,
            "gamma_srg_identity": checks["gamma_srg_identity"],
            "aut_gamma_order": aut_gamma["valid_automorphism_count"],
            "aut_gamma_resolving_base": aut_gamma["base"],
            "pair_abs_inner_counter": dict(sorted(Counter(pair_inner_colors.values()).items())),
        },
        "flat_size_channel": {
            **flat,
            "automorphism_order": aut_gamma["valid_automorphism_count"],
            "reason": "flat-size coloring is a bijective recoding of the Gram/projective-root graph coloring",
        },
        "circuit_channel": circuit,
        "source_row_channel": {
            "channel_dimensions": {"constant": 1, "U20": len(basis20), "U15": len(basis15), "V_std": len(std_basis)},
            "candidate_rows": len(candidate_rows),
            "parabolic_rows": len(parabolic_rows),
            "rank_profile_counter": dict(sorted(rank_profiles.items())),
            "sample_rows_first_12": candidate_rows[:12],
        },
        "witnesses": {
            "named_witness_Par_012_vs_Par_0135": named_witness,
            "same_rank_split_count": len(witnesses["same_rank_split"]),
            "same_size_rank_split_count": len(witnesses["same_size_rank_split"]),
            "same_type_size_rank_split_count": len(witnesses["same_type_size_rank_split"]),
            "same_size_orbit_split_count": len(witnesses["same_size_orbit_split"]),
            "same_size_rank_split_first_20": witnesses["same_size_rank_split"][:20],
        },
        "public_boundary": {
            "reading": "same-size/same-standard-rank parabolic rows can have different U20/U15 splits",
            "not_same_type": len(witnesses["same_type_size_rank_split"]) == 0,
            "not_same_orbit": len(witnesses["same_size_orbit_split"]) == 0,
            "nonclaims": [
                "not a standalone E6 theorem",
                "not a same-type witness",
                "not a same-size/same-orbit witness",
                "not a Schlaefli or 27-line route",
                "not a classifier or tiling test",
            ],
        },
        "checks": checks,
    }
    artifact["payload_sha256_without_this_field"] = payload_sha256(artifact)
    write_json(Path(args.out), artifact)
    print(json.dumps({
        "pass": artifact["pass"],
        "artifact": str(Path(args.out).resolve().relative_to(ROOT)) if Path(args.out).resolve().is_relative_to(ROOT) else str(Path(args.out)),
        "root_count": len(roots),
        "projective_pair_count": n,
        "aut_gamma_order": aut_gamma["valid_automorphism_count"],
        "flat_size_aut_order": aut_gamma["valid_automorphism_count"],
        "three_circuit_count": circuit["three_circuit_count"],
        "circuit_aut_order": circuit["derived_graph_aut_order"],
        "same_type_size_rank_split_count": len(witnesses["same_type_size_rank_split"]),
        "same_size_orbit_split_count": len(witnesses["same_size_orbit_split"]),
    }, indent=2, sort_keys=True))
    return bool(artifact["pass"])


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)