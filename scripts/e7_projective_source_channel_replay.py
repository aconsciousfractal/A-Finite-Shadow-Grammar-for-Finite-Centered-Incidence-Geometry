#!/usr/bin/env python3
"""Public replay for the projective E7 source-exact control exhibit.

This bounded replay checks exactly the E7 payload used by the paper: the
63-point projective root carrier, the Gram-square graph, the rank-2 flat-size
collapse, the projective source action order, the reflection-row identity, and
the embedded A5 parabolic separator.

It is not an E7 theorem, Sp_6(2) theorem, reflection-subgroup classification,
root-system matroid novelty claim, E8/Type-E family theorem, classifier, or
tiling test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

import e7_projective_root_engine as root
import e7_projective_flat_channel as flat
import e7_projective_weyl_action as weyl
import e7_projective_source_rows as rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "e7_projective_source_channel_replay.json"

EXPECTED = {
    "root_count": 126,
    "projective_pair_count": 63,
    "srg": {"vertices": 63, "degree": 32, "lambda": 16, "mu": 16, "edge_count": 1008},
    "source_order": 1451520,
    "sp6_order": 1451520,
    "flat_pair_counter": {"2": 945, "3": 1008},
    "gram_counter": {"0": 945, "1": 1008},
}


def payload_sha256(payload) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def graph_parameters(adj: list[list[int]]) -> dict:
    n = len(adj)
    degrees = [sum(row) for row in adj]
    lambda_values = []
    mu_values = []
    for i, j in combinations(range(n), 2):
        common = sum(adj[i][k] and adj[j][k] for k in range(n))
        if adj[i][j]:
            lambda_values.append(common)
        else:
            mu_values.append(common)
    return {
        "vertices": n,
        "degree_values": sorted(set(degrees)),
        "edge_count": sum(degrees) // 2,
        "lambda_values": sorted(set(lambda_values)),
        "mu_values": sorted(set(mu_values)),
    }


def flat_channel_summary(pairs: list[tuple[int, ...]]) -> dict:
    gram_counter: Counter[str] = Counter()
    flat_counter: Counter[str] = Counter()
    unique_flats = set()
    gram_to_flat: dict[str, set[int]] = {}
    flat_to_gram: dict[str, set[int]] = {}
    mismatches = []
    for i, j in combinations(range(len(pairs)), 2):
        gram = root.gram_square_value(pairs[i], pairs[j])
        if gram.denominator != 1:
            raise ValueError(f"unexpected Gram-square value {gram}")
        flat_indices = flat.rank2_flat_indices(pairs, i, j)
        flat_size = len(flat_indices)
        g = str(gram.numerator)
        f = str(flat_size)
        gram_counter[g] += 1
        flat_counter[f] += 1
        unique_flats.add(flat_indices)
        gram_to_flat.setdefault(g, set()).add(flat_size)
        flat_to_gram.setdefault(f, set()).add(gram.numerator)
        if not ((gram.numerator == 0 and flat_size == 2) or (gram.numerator == 1 and flat_size == 3)):
            mismatches.append({"pair": [i, j], "gram_square": gram.numerator, "flat_size": flat_size})
    return {
        "unordered_pair_count": sum(flat_counter.values()),
        "gram_counter": dict(sorted(gram_counter.items(), key=lambda kv: int(kv[0]))),
        "pair_flat_size_counter": dict(sorted(flat_counter.items(), key=lambda kv: int(kv[0]))),
        "unique_flat_size_counter": dict(sorted(Counter(str(len(x)) for x in unique_flats).items(), key=lambda kv: int(kv[0]))),
        "gram_to_flat_size": {k: sorted(v) for k, v in sorted(gram_to_flat.items(), key=lambda kv: int(kv[0]))},
        "flat_size_to_gram": {k: sorted(v) for k, v in sorted(flat_to_gram.items(), key=lambda kv: int(kv[0]))},
        "mismatch_count": len(mismatches),
        "mismatches_first_10": mismatches[:10],
    }


def parse_label(label: str) -> tuple[int, ...]:
    if not label.startswith("Par_"):
        raise ValueError(label)
    return tuple(int(ch) for ch in label[4:])


def simple_edges(vertices) -> set[tuple[int, int]]:
    verts = sorted(vertices)
    out = set()
    gram = root.LOCKED_SIMPLE_GRAM
    for a, b in combinations(verts, 2):
        if gram[a - 1][b - 1] == -1:
            out.add((a, b))
    return out


def connected_components(vertices, edges):
    verts = set(vertices)
    adj = {v: set() for v in verts}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    comps = []
    while verts:
        start = min(verts)
        q = deque([start])
        verts.remove(start)
        comp = []
        while q:
            v = q.popleft()
            comp.append(v)
            for w in sorted(adj[v]):
                if w in verts:
                    verts.remove(w)
                    q.append(w)
        comps.append(sorted(comp))
    return comps


def component_type(comp, edges) -> str:
    n = len(comp)
    if n == 1:
        return "A1"
    adj = {v: set() for v in comp}
    for a, b in edges:
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    degs = sorted(len(adj[v]) for v in comp)
    if max(degs) <= 2:
        return f"A{n}"
    branch = [v for v in comp if len(adj[v]) == 3]
    if len(branch) == 1:
        b = branch[0]
        arms = []
        for nb in adj[b]:
            prev = b
            cur = nb
            length = 1
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
    return "Unknown"


def dynkin_type(label: str) -> str:
    verts = parse_label(label)
    edges = simple_edges(verts)
    comps = connected_components(verts, edges)
    pieces = [component_type(comp, edges) for comp in comps]
    def key(piece: str):
        return (-int(piece[1:]) if len(piece) > 1 and piece[1:].isdigit() else 0, piece)
    return "+".join(sorted(pieces, key=key))


def center_of_transvection(mat: rows.MatrixF2) -> int:
    for a in range(1, 64):
        if rows.transvection(a) == mat:
            return a
    raise ValueError("matrix is not a transvection")


def orbit_centers(group: list[rows.MatrixF2], starts: list[int]) -> list[int]:
    out = set()
    for g in group:
        for c in starts:
            out.add(rows.apply_matrix(g, c))
    return sorted(out)


def compact_row_report(label: str, simple_mats, basis27, basis35, std_basis) -> dict:
    idx = [i - 1 for i in parse_label(label)]
    gens = [simple_mats[i] for i in idx]
    group = rows.generated_matrix_group(gens, None)
    aggregate = rows.aggregate_from_matrices(group)
    report = rows.row_report(label, "subgroup", len(group), aggregate, basis27, basis35, std_basis, gens)
    return {
        "label": label,
        "abstract_type": dynkin_type(label),
        "order": len(group),
        "rank_std": report["rank_std"],
        "rank_U27": report["rank_U27"],
        "rank_U35": report["rank_U35"],
        "orbit_sizes_on_Pi63": report["orbit_sizes_on_Pi63"],
        "rank_additivity_check": report["rank_additivity_check"],
        "row_col_sums_ok": report["row_col_sums_ok"],
        "aggregate_matrix_sha256": report["aggregate_matrix_sha256"],
    }


def reflection_row_for_subset(label: str, simple_mats, simple_centers, basis27, basis35, std_basis) -> dict:
    idx = [i - 1 for i in parse_label(label)]
    gens = [simple_mats[i] for i in idx]
    group = rows.generated_matrix_group(gens, None)
    centers = orbit_centers(group, [simple_centers[i] for i in idx])
    mats = [rows.transvection(c) for c in centers]
    aggregate = rows.aggregate_from_matrices(mats)
    report = rows.row_report("RefSub_" + label[4:], "finite_subset", len(mats), aggregate, basis27, basis35, std_basis, mats)
    return {
        "label": report["label"],
        "parent_parabolic": label,
        "abstract_type": dynkin_type(label),
        "parabolic_order": len(group),
        "reflection_count": len(mats),
        "rank_std": report["rank_std"],
        "rank_U27": report["rank_U27"],
        "rank_U35": report["rank_U35"],
        "orbit_sizes_on_Pi63": report["orbit_sizes_on_Pi63"],
        "rank_additivity_check": report["rank_additivity_check"],
    }


def build_artifact() -> dict:
    type_i, type_ii, all_roots = root.generate_roots()
    pairs = flat.projective_pairs()
    graph = weyl.gram_adjacency(pairs)
    graph_params = graph_parameters(graph)
    flat_summary = flat_channel_summary(pairs)

    simple_perms = weyl.simple_reflection_perms(pairs)
    f2 = weyl.build_f2_model(graph)
    simple_mats = [weyl.matrix_from_perm(p, f2["vertex_to_f2_coord"], f2["coord_to_vertex"]) for p in simple_perms]
    source_order = weyl.generated_matrix_group_order(simple_mats, EXPECTED["source_order"])
    source_orbits = weyl.permutation_orbit_sizes(simple_perms, len(pairs))

    adjacency = rows.adjacency_matrix()
    basis27, basis35, std_basis = rows.eigenspace_bases(adjacency)
    reflection_mats = [rows.transvection(c) for c in range(1, 64)]
    reflection_aggregate = rows.aggregate_from_matrices(reflection_mats)
    reflection_formula = rows.matrix_add(rows.matrix_scale(rows.identity_matrix(), 31), adjacency)
    reflection_report = rows.row_report("Ref", "finite_subset", len(reflection_mats), reflection_aggregate, basis27, basis35, std_basis, reflection_mats)

    simple_centers = [center_of_transvection(mat) for mat in simple_mats]
    par_a = compact_row_report("Par_12345", simple_mats, basis27, basis35, std_basis)
    par_b = compact_row_report("Par_12347", simple_mats, basis27, basis35, std_basis)
    support = [
        [compact_row_report("Par_135", simple_mats, basis27, basis35, std_basis), compact_row_report("Par_137", simple_mats, basis27, basis35, std_basis)],
        [compact_row_report("Par_1235", simple_mats, basis27, basis35, std_basis), compact_row_report("Par_1237", simple_mats, basis27, basis35, std_basis)],
    ]
    negative = [reflection_row_for_subset(label, simple_mats, simple_centers, basis27, basis35, std_basis) for label in ["Par_12345", "Par_12347", "Par_135", "Par_137", "Par_1235", "Par_1237"]]

    checks = {
        "root_count": len(all_roots) == EXPECTED["root_count"],
        "projective_pair_count": len(pairs) == EXPECTED["projective_pair_count"],
        "srg_vertices": graph_params["vertices"] == EXPECTED["srg"]["vertices"],
        "srg_degree": graph_params["degree_values"] == [EXPECTED["srg"]["degree"]],
        "srg_edge_count": graph_params["edge_count"] == EXPECTED["srg"]["edge_count"],
        "srg_lambda": graph_params["lambda_values"] == [EXPECTED["srg"]["lambda"]],
        "srg_mu": graph_params["mu_values"] == [EXPECTED["srg"]["mu"]],
        "flat_channel_gram_counter": flat_summary["gram_counter"] == EXPECTED["gram_counter"],
        "flat_channel_pair_counter": flat_summary["pair_flat_size_counter"] == EXPECTED["flat_pair_counter"],
        "flat_channel_no_mismatch": flat_summary["mismatch_count"] == 0,
        "source_order": source_order == EXPECTED["source_order"],
        "sp6_upper_bound_order": weyl.sp6_order() == EXPECTED["sp6_order"],
        "source_orbit_transitive": source_orbits == [63],
        "simple_generators_symplectic": all(weyl.matrix_preserves_symplectic(m) for m in simple_mats),
        "reflection_formula_31I_plus_A": rows.matrix_equal(reflection_aggregate, reflection_formula),
        "reflection_rank": [reflection_report["rank_std"], reflection_report["rank_U27"], reflection_report["rank_U35"]] == [62, 27, 35],
        "main_A5_same_type": par_a["abstract_type"] == par_b["abstract_type"] == "A5",
        "main_A5_same_order": par_a["order"] == par_b["order"] == 720,
        "main_A5_rank_separator": [par_a["rank_std"], par_a["rank_U27"], par_a["rank_U35"], par_b["rank_std"], par_b["rank_U27"], par_b["rank_U35"]] == [5, 3, 2, 6, 3, 3],
        "main_A5_orbits": par_a["orbit_sizes_on_Pi63"] == [1, 6, 6, 15, 15, 20] and par_b["orbit_sizes_on_Pi63"] == [1, 1, 1, 15, 15, 15, 15],
        "support_witnesses_rank_separate": all(pair[0]["rank_std"] != pair[1]["rank_std"] for pair in support),
        "negative_reflection_rows_full_rank": all([x["rank_std"], x["rank_U27"], x["rank_U35"]] == [62, 27, 35] for x in negative),
    }

    artifact = {
        "paper": "A Finite-Shadow Grammar for Finite Centered Incidence Geometry",
        "artifact": "e7_projective_source_channel_replay",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "model": {
            "carrier": "63 projective E7 root pairs from the doubled 8-coordinate E7 root model",
            "graph_channel": "squared Gram value 1 gives the projective root graph",
            "flat_channel": "rank-2 projective flat size is a recoding of the Gram-square channel",
            "source_action": "projective Weyl action reconstructed as a matrix group over F2^6",
            "row_channel": "centered ranks on U27 and U35 for selected embedded parabolic subgroup rows",
        },
        "counts": {
            "type_I_roots": len(type_i),
            "type_II_roots": len(type_ii),
            "roots": len(all_roots),
            "projective_pairs": len(pairs),
            "source_projective_order": source_order,
            "sp6_upper_bound_order": weyl.sp6_order(),
        },
        "graph": graph_params,
        "flat_channel": flat_summary,
        "source_decomposition": {"constant": 1, "U27": len(basis27), "U35": len(basis35), "V_std": len(std_basis)},
        "reflection_row": {
            "identity": "N_Ref = 31I + A",
            "rank_std": reflection_report["rank_std"],
            "rank_U27": reflection_report["rank_U27"],
            "rank_U35": reflection_report["rank_U35"],
            "spectrum_U27": reflection_report["spectrum_U27"],
            "spectrum_U35": reflection_report["spectrum_U35"],
            "aggregate_matrix_sha256": reflection_report["aggregate_matrix_sha256"],
        },
        "main_A5_witness": {"A": par_a, "B": par_b},
        "support_witnesses": support,
        "negative_reflection_controls": negative,
        "checks": checks,
        "boundary": [
            "no standalone E7 theorem",
            "no Sp_6(2) theorem",
            "no reflection-subgroup classification",
            "no root-system matroid novelty claim",
            "no E8 or Type-E family theorem",
            "no 56-weight/Gosset/minuscule route",
            "no classifier",
            "no tiling",
        ],
    }
    artifact["payload_sha256_without_this_field"] = payload_sha256(artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT), help="artifact path")
    args = parser.parse_args()
    artifact = build_artifact()
    if args.out:
        write_json(Path(args.out), artifact)
    print(json.dumps({
        "artifact": "e7_projective_source_channel_replay",
        "pass": artifact["pass"],
        "projective_pair_count": artifact["counts"]["projective_pairs"],
        "source_projective_order": artifact["counts"]["source_projective_order"],
        "graph_parameters": artifact["graph"],
        "main_A5_ranks": {
            "Par_12345": [artifact["main_A5_witness"]["A"]["rank_std"], artifact["main_A5_witness"]["A"]["rank_U27"], artifact["main_A5_witness"]["A"]["rank_U35"]],
            "Par_12347": [artifact["main_A5_witness"]["B"]["rank_std"], artifact["main_A5_witness"]["B"]["rank_U27"], artifact["main_A5_witness"]["B"]["rank_U35"]],
        },
        "artifact_path": str(Path(args.out).resolve().relative_to(ROOT)) if args.out and Path(args.out).resolve().is_relative_to(ROOT) else str(Path(args.out)),
    }, indent=2, sort_keys=True))
    if not artifact["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
