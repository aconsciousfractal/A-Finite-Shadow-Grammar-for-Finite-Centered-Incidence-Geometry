#!/usr/bin/env python3
"""Public replay for the projective H3 source-channel exhibit.

This is a bounded replay for the paper package, not a general H3, Coxeter,
matroid, classifier, or tiling engine. It recomputes the two edge-coloring
automorphism groups on the exported 15-point payload, checks the displayed
non-geometric witness, and verifies the ordinary standard and (13,2) rank
readings used by the paper.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROW_NAMES = (
    "G_mat_flat_auts",
    "G_geo_projective",
    "G_ng_odd_coset",
    "G_gram_color",
)


def perm_from_word(word: str, labels: list[str]) -> tuple[int, ...]:
    idx = {c: i for i, c in enumerate(labels)}
    return tuple(idx[c] for c in word)


def perm_word(p: tuple[int, ...], labels: list[str]) -> str:
    return "".join(labels[i] for i in p)


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[i] for i in q)


def inverse(p: tuple[int, ...]) -> tuple[int, ...]:
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return tuple(out)


def is_group(row: frozenset[tuple[int, ...]], n: int) -> bool:
    ident = tuple(range(n))
    return bool(row) and ident in row and all(inverse(a) in row for a in row) and all(compose(a, b) in row for a in row for b in row)


def edge_key(edge: str, labels: list[str]) -> tuple[int, int]:
    idx = {c: i for i, c in enumerate(labels)}
    a, b = idx[edge[0]], idx[edge[1]]
    return (a, b) if a < b else (b, a)


def color_dict(edge_color_list: list[dict[str, object]], labels: list[str]) -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for item in edge_color_list:
        out[edge_key(str(item["edge"]), labels)] = str(item["color"])
    expected = len(labels) * (len(labels) - 1) // 2
    if len(out) != expected:
        raise RuntimeError(f"edge-color payload has {len(out)} edges, expected {expected}")
    return out


def color_matrix(colors: dict[tuple[int, int], str], n: int) -> list[list[str | None]]:
    mat: list[list[str | None]] = [[None] * n for _ in range(n)]
    for (a, b), color in colors.items():
        mat[a][b] = mat[b][a] = color
    return mat


def vertex_signatures(mat: list[list[str | None]]) -> list[tuple[tuple[str | None, int], ...]]:
    signatures = []
    for i, row in enumerate(mat):
        counts = Counter(row[j] for j in range(len(row)) if j != i)
        signatures.append(tuple(sorted(counts.items(), key=lambda kv: str(kv[0]))))
    return signatures


def color_automorphisms(colors: dict[tuple[int, int], str], n: int) -> tuple[frozenset[tuple[int, ...]], dict[str, int]]:
    mat = color_matrix(colors, n)
    signatures = vertex_signatures(mat)
    signature_classes: dict[tuple[tuple[str | None, int], ...], set[int]] = {}
    for i, sig in enumerate(signatures):
        signature_classes.setdefault(sig, set()).add(i)
    candidates = [set(signature_classes[signatures[i]]) for i in range(n)]
    image: list[int | None] = [None] * n
    used = [False] * n
    automorphisms: list[tuple[int, ...]] = []
    stats = {"nodes": 0, "dead_ends": 0, "leaves": 0, "max_depth": 0}

    def compatible(i: int, y: int) -> bool:
        for j, x in enumerate(image):
            if x is not None and mat[i][j] != mat[y][x]:
                return False
        return True

    def rec(depth: int = 0) -> None:
        stats["nodes"] += 1
        stats["max_depth"] = max(stats["max_depth"], depth)
        if depth == n:
            automorphisms.append(tuple(x for x in image if x is not None))
            stats["leaves"] += 1
            return
        best_i = None
        best_options = None
        for i in range(n):
            if image[i] is not None:
                continue
            options = [y for y in sorted(candidates[i]) if not used[y] and compatible(i, y)]
            if best_options is None or len(options) < len(best_options):
                best_i = i
                best_options = options
        if best_i is None or not best_options:
            stats["dead_ends"] += 1
            return
        for y in best_options:
            image[best_i] = y
            used[y] = True
            rec(depth + 1)
            used[y] = False
            image[best_i] = None

    rec()
    return frozenset(automorphisms), stats


def preserves_colors(p: tuple[int, ...], colors: dict[tuple[int, int], str]) -> bool:
    for (a, b), color in colors.items():
        x, y = sorted((p[a], p[b]))
        if colors[(x, y)] != color:
            return False
    return True


def first_color_defect(p: tuple[int, ...], colors: dict[tuple[int, int], str], labels: list[str]) -> dict[str, str] | None:
    for (a, b), color in sorted(colors.items()):
        x, y = sorted((p[a], p[b]))
        image_color = colors[(x, y)]
        if image_color != color:
            return {
                "edge": labels[a] + labels[b],
                "edge_color": color,
                "image_edge": labels[x] + labels[y],
                "image_color": image_color,
            }
    return None


def changed_edge_count(p: tuple[int, ...], colors: dict[tuple[int, int], str]) -> int:
    changed = 0
    for (a, b), color in colors.items():
        x, y = sorted((p[a], p[b]))
        if colors[(x, y)] != color:
            changed += 1
    return changed


def cycle_counts(p: tuple[int, ...]) -> Counter[int]:
    seen = [False] * len(p)
    counts: Counter[int] = Counter()
    for i in range(len(p)):
        if seen[i]:
            continue
        j = i
        length = 0
        while not seen[j]:
            seen[j] = True
            length += 1
            j = p[j]
        counts[length] += 1
    return counts


def char_standard(p: tuple[int, ...]) -> int:
    c = cycle_counts(p)
    return c[1] - 1


def char_n_minus_2_2(p: tuple[int, ...]) -> int:
    c = cycle_counts(p)
    fixed_two_sets = c[1] * (c[1] - 1) // 2 + c[2]
    return fixed_two_sets - c[1]


def subgroup_rank(row: frozenset[tuple[int, ...]], char_fn) -> int:
    numerator = sum(char_fn(p) for p in row)
    if numerator % len(row) != 0:
        raise ArithmeticError((numerator, len(row)))
    return numerator // len(row)


def coset_checks(geo: frozenset[tuple[int, ...]], ng: frozenset[tuple[int, ...]]) -> dict[str, bool]:
    if not ng:
        return {"left_coset": False, "right_coset": False, "disjoint": ng.isdisjoint(geo)}
    t = next(iter(ng))
    left = frozenset(compose(t, h) for h in geo)
    right = frozenset(compose(h, t) for h in geo)
    return {"left_coset": left == ng, "right_coset": right == ng, "disjoint": ng.isdisjoint(geo)}


def ordered_ranks(groups: dict[str, frozenset[tuple[int, ...]]], coset_ok: bool) -> dict[str, dict[str, int]]:
    standard = {
        "G_mat_flat_auts": subgroup_rank(groups["G_mat_flat_auts"], char_standard),
        "G_geo_projective": subgroup_rank(groups["G_geo_projective"], char_standard),
        "G_gram_color": subgroup_rank(groups["G_gram_color"], char_standard),
    }
    separator = {
        "G_mat_flat_auts": subgroup_rank(groups["G_mat_flat_auts"], char_n_minus_2_2),
        "G_geo_projective": subgroup_rank(groups["G_geo_projective"], char_n_minus_2_2),
        "G_gram_color": subgroup_rank(groups["G_gram_color"], char_n_minus_2_2),
    }
    if coset_ok:
        standard["G_ng_odd_coset"] = standard["G_geo_projective"]
        separator["G_ng_odd_coset"] = separator["G_geo_projective"]
    else:
        standard["G_ng_odd_coset"] = -1
        separator["G_ng_odd_coset"] = -1
    return {"standard_(14,1)": standard, "separator_(13,2)": separator}


def normalize_expected_rank_map(obj: dict[str, object]) -> dict[str, int]:
    return {k: int(v) for k, v in obj.items()}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    seed_path = root / "artifacts" / "h3_projective_source_channel_replay_seed.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    labels = list(seed["labels"])
    n = len(labels)
    groups = {
        name: frozenset(perm_from_word(word, labels) for word in seed["groups"][name])
        for name in ROW_NAMES
    }
    flat_colors = color_dict(seed["edge_colors"]["flat_size"], labels)
    gram_colors = color_dict(seed["edge_colors"]["gram_squared_inner_product"], labels)
    flat_aut, flat_stats = color_automorphisms(flat_colors, n)
    gram_aut, gram_stats = color_automorphisms(gram_colors, n)
    witness = perm_from_word(seed["expected"]["selected_witness"], labels)
    cosets = coset_checks(groups["G_geo_projective"], groups["G_ng_odd_coset"])
    ranks = ordered_ranks(groups, cosets["left_coset"] and cosets["right_coset"])
    expected_standard = normalize_expected_rank_map(seed["expected"]["standard_ranks"])
    expected_separator = normalize_expected_rank_map(seed["expected"]["first_separator_ranks"])
    expected_defect = dict(seed["expected"]["selected_witness_first_defect"])

    checks = {
        "labels_15": n == 15,
        "flat_color_payload_has_105_edges": len(flat_colors) == 105,
        "gram_color_payload_has_105_edges": len(gram_colors) == 105,
        "group_rows_have_expected_sizes": {name: len(groups[name]) for name in ROW_NAMES} == {
            "G_mat_flat_auts": 120,
            "G_geo_projective": 60,
            "G_ng_odd_coset": 60,
            "G_gram_color": 60,
        },
        "group_rows_are_groups_where_claimed": all(is_group(groups[name], n) for name in ("G_mat_flat_auts", "G_geo_projective", "G_gram_color")),
        "nongeometric_row_is_not_group": not is_group(groups["G_ng_odd_coset"], n),
        "flat_aut_order_120": len(flat_aut) == int(seed["expected"]["flat_aut_order"]),
        "gram_aut_order_60": len(gram_aut) == int(seed["expected"]["gram_aut_order"]),
        "flat_aut_equals_G_mat": flat_aut == groups["G_mat_flat_auts"],
        "gram_aut_equals_G_geo": gram_aut == groups["G_geo_projective"],
        "gram_aut_equals_G_gram": gram_aut == groups["G_gram_color"],
        "G_geo_equals_G_gram": groups["G_geo_projective"] == groups["G_gram_color"],
        "G_ng_is_geo_coset": cosets["left_coset"] and cosets["right_coset"] and cosets["disjoint"],
        "G_ng_has_no_gram_preservers": not any(preserves_colors(p, gram_colors) for p in groups["G_ng_odd_coset"]),
        "witness_in_matroid_not_geometric": witness in groups["G_mat_flat_auts"] and witness in groups["G_ng_odd_coset"] and witness not in groups["G_geo_projective"],
        "witness_preserves_flat_size": preserves_colors(witness, flat_colors),
        "witness_changes_gram": not preserves_colors(witness, gram_colors),
        "witness_changes_60_edges": changed_edge_count(witness, gram_colors) == 60,
        "witness_first_defect_locked": first_color_defect(witness, gram_colors, labels) == expected_defect,
        "standard_block_blind": ranks["standard_(14,1)"] == expected_standard,
        "separator_13_2_ranks_locked": ranks["separator_(13,2)"] == expected_separator,
    }
    all_pass = all(checks.values())
    result = {
        "script": "scripts/h3_projective_source_channel_replay.py",
        "scope": "bounded public replay for the projective H3 source-channel exhibit",
        "all_pass": all_pass,
        "checks": checks,
        "orders": {
            "Aut_flat_size": len(flat_aut),
            "Aut_Gram": len(gram_aut),
            "G_mat_flat_auts": len(groups["G_mat_flat_auts"]),
            "G_geo_projective": len(groups["G_geo_projective"]),
            "G_ng_odd_coset": len(groups["G_ng_odd_coset"]),
        },
        "search_stats": {"flat_size": flat_stats, "gram": gram_stats},
        "witness": {
            "word": seed["expected"]["selected_witness"],
            "first_gram_defect": first_color_defect(witness, gram_colors, labels),
            "changed_gram_edges": changed_edge_count(witness, gram_colors),
        },
        "ordinary_specht_ranks": ranks,
        "boundary": "This replay is not a general H3, Coxeter, matroid, classifier, or tiling theorem.",
    }
    out = root / "artifacts" / "h3_projective_source_channel_replay.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("h3_projective_source_channel_replay")
    print(f"all_pass={all_pass}")
    print(f"Aut_flat_size={len(flat_aut)}")
    print(f"Aut_Gram={len(gram_aut)}")
    print(f"witness={result['witness']['word']}")
    print(f"standard_ranks={ranks['standard_(14,1)']}")
    print(f"separator_13_2_ranks={ranks['separator_(13,2)']}")
    print(f"artifact={out.relative_to(root)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())