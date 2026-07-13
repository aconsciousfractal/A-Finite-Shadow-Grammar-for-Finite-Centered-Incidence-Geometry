#!/usr/bin/env python3
"""Public replay for the projective D5 source-channel control exhibit.

This bounded replay uses the signed-edge model of the 20 projective D5 root
lines.  It explicitly enumerates the pair-channel supergroup C2^10:S5, counts
A2-flat preservers, compares them with the projective W(D5) source action, and
checks the fake-flip boundary used in the paper.

It is not a D5 classification, Type-E theorem, tiling test, or classifier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations, permutations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "d5_projective_source_channel_replay.json"
N = 5
SIGNS = (1, -1)


def payload_sha256(payload) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def label_tuple(i: int, j: int, sign: int) -> tuple[int, int, int]:
    if i > j:
        i, j = j, i
    return (i, j, sign)


def label_text(x: tuple[int, int, int]) -> str:
    i, j, sign = x
    return f"L{i}{j}{'+' if sign == 1 else '-'}"


LINES = [label_tuple(i, j, s) for i, j in combinations(range(1, N + 1), 2) for s in SIGNS]
LINE_INDEX = {line: idx for idx, line in enumerate(LINES)}
EDGE_KEYS = [(i, j) for i, j in combinations(range(1, N + 1), 2)]
EDGE_INDEX = {edge: idx for idx, edge in enumerate(EDGE_KEYS)}


def canonical_from_coeffs(a: int, ca: int, b: int, cb: int) -> tuple[int, int, int]:
    """Projectivize ca*e_a + cb*e_b to Lij+/- with i<j."""
    if a > b:
        a, b = b, a
        ca, cb = cb, ca
    if ca < 0:
        ca, cb = -ca, -cb
    if ca != 1 or cb not in SIGNS:
        raise ValueError((a, ca, b, cb))
    return (a, b, cb)


def coord_action(line: tuple[int, int, int], coord_perm: tuple[int, ...]) -> tuple[int, int, int]:
    i, j, sign = line
    return canonical_from_coeffs(coord_perm[i - 1], 1, coord_perm[j - 1], sign)


def signed_action(line: tuple[int, int, int], coord_perm: tuple[int, ...], eps: tuple[int, ...]) -> tuple[int, int, int]:
    i, j, sign = line
    return canonical_from_coeffs(coord_perm[i - 1], eps[i - 1], coord_perm[j - 1], sign * eps[j - 1])


def flip_line(line: tuple[int, int, int]) -> tuple[int, int, int]:
    i, j, sign = line
    return (i, j, -sign)


def perm_from_images(images: list[tuple[int, int, int]]) -> tuple[int, ...]:
    return tuple(LINE_INDEX[x] for x in images)


def pair_channel_supergroup() -> list[tuple[int, ...]]:
    out = []
    for cp in permutations(range(1, N + 1)):
        base = [coord_action(line, cp) for line in LINES]
        for bits in product((0, 1), repeat=len(EDGE_KEYS)):
            images = []
            for y in base:
                if bits[EDGE_INDEX[(y[0], y[1])]]:
                    y = flip_line(y)
                images.append(y)
            out.append(perm_from_images(images))
    return sorted(set(out))


def projective_weyl_group() -> list[tuple[int, ...]]:
    out = set()
    for cp in permutations(range(1, N + 1)):
        for eps in product(SIGNS, repeat=N):
            images = [signed_action(line, cp, eps) for line in LINES]
            out.add(perm_from_images(images))
    return sorted(out)


def a2_triples() -> list[tuple[int, int, int]]:
    triples = set()
    for i, j, k in combinations(range(1, N + 1), 3):
        for sij, sik, sjk in product(SIGNS, repeat=3):
            if sij * sik * sjk == -1:
                triple = tuple(sorted((
                    LINE_INDEX[(i, j, sij)],
                    LINE_INDEX[(i, k, sik)],
                    LINE_INDEX[(j, k, sjk)],
                )))
                triples.add(triple)
    return sorted(triples)


def d4_coordinate_flats() -> list[tuple[int, ...]]:
    flats = []
    for omitted in range(1, N + 1):
        kept = [x for x in range(1, N + 1) if x != omitted]
        flat = tuple(sorted(LINE_INDEX[(i, j, s)] for i, j in combinations(kept, 2) for s in SIGNS))
        flats.append(flat)
    return sorted(flats)


def image_tuple(item: tuple[int, ...], perm: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(perm[i] for i in item))


def preserves_family(perm: tuple[int, ...], family_set: set[tuple[int, ...]]) -> bool:
    return all(image_tuple(item, perm) in family_set for item in family_set)


def preserving_perms(perms: list[tuple[int, ...]], family: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    family_set = set(family)
    return [p for p in perms if preserves_family(p, family_set)]


def single_flip(edge: tuple[int, int] = (1, 2)) -> tuple[int, ...]:
    p = list(range(len(LINES)))
    a = LINE_INDEX[(edge[0], edge[1], 1)]
    b = LINE_INDEX[(edge[0], edge[1], -1)]
    p[a], p[b] = p[b], p[a]
    return tuple(p)


def labels_for_item(item: tuple[int, ...]) -> list[str]:
    return [label_text(LINES[i]) for i in item]


def first_broken_item(perm: tuple[int, ...], family: list[tuple[int, ...]]) -> dict:
    family_set = set(family)
    for item in family:
        image = image_tuple(item, perm)
        if image not in family_set:
            return {"source": labels_for_item(item), "image": labels_for_item(image)}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    pair_group = pair_channel_supergroup()
    source_group = projective_weyl_group()
    a2 = a2_triples()
    d4 = d4_coordinate_flats()
    a2_preservers = preserving_perms(pair_group, a2)
    d4_preservers = preserving_perms(pair_group, d4)
    flip = single_flip((1, 2))
    source_set = set(source_group)
    a2_preserver_set = set(a2_preservers)
    d4_preserver_set = set(d4_preservers)

    checks = {
        "projective_point_count_is_20": len(LINES) == 20,
        "pair_channel_supergroup_order_is_122880": len(pair_group) == 122880,
        "source_projective_weyl_order_is_1920": len(source_group) == 1920,
        "pair_channel_to_source_ratio_is_64": len(pair_group) // len(source_group) == 64,
        "a2_flat_count_is_40": len(a2) == 40,
        "d4_coordinate_flat_count_is_5": len(d4) == 5,
        "d4_flat_size_is_12": all(len(f) == 12 for f in d4),
        "a2_preserver_order_is_1920": len(a2_preservers) == 1920,
        "a2_preservers_equal_source_group": a2_preserver_set == source_set,
        "d4_preserver_order_is_122880": len(d4_preservers) == 122880,
        "d4_preservers_equal_pair_channel": d4_preserver_set == set(pair_group),
        "fake_flip_is_pair_channel_not_source": flip in set(pair_group) and flip not in source_set,
        "fake_flip_breaks_a2_family": not preserves_family(flip, set(a2)),
        "fake_flip_preserves_d4_family": preserves_family(flip, set(d4)),
    }

    artifact = {
        "paper": "A Finite-Shadow Grammar for Finite Centered Incidence Geometry",
        "artifact": "d5_projective_source_channel_replay",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "model": {
            "carrier": "20 projective D5 root lines Lij+/Lij-",
            "pair_channel_supergroup": "C2^10:S5, independent sign flips on coordinate-pair twins plus S5 on coordinates",
            "source_group": "projective W(D5), realized by signed coordinate permutations",
        },
        "counts": {
            "projective_points": len(LINES),
            "pair_channel_order": len(pair_group),
            "source_projective_weyl_order": len(source_group),
            "pair_channel_to_source_ratio": len(pair_group) // len(source_group),
            "a2_flat_count": len(a2),
            "d4_coordinate_flat_count": len(d4),
            "a2_preserver_order_inside_pair_channel": len(a2_preservers),
            "d4_preserver_order_inside_pair_channel": len(d4_preservers),
        },
        "source_recovery": {
            "a2_preservers_equal_projective_weyl_group": a2_preserver_set == source_set,
            "a2_preserver_payload_sha256": payload_sha256(sorted(a2_preservers)),
            "source_group_payload_sha256": payload_sha256(sorted(source_group)),
        },
        "negative_control": {
            "d4_preservers_equal_pair_channel": d4_preserver_set == set(pair_group),
            "d4_preserver_payload_sha256": payload_sha256(sorted(d4_preservers)),
            "pair_channel_payload_sha256": payload_sha256(sorted(pair_group)),
        },
        "fake_flip_boundary": {
            "flip": "L12+ <-> L12-",
            "in_pair_channel_supergroup": flip in set(pair_group),
            "in_projective_weyl_group": flip in source_set,
            "preserves_d4_family": preserves_family(flip, set(d4)),
            "breaks_a2_family": not preserves_family(flip, set(a2)),
            "broken_a2_flat": first_broken_item(flip, a2),
        },
        "samples": {
            "a2_flat_first_5": [labels_for_item(x) for x in a2[:5]],
            "d4_flat_first": labels_for_item(d4[0]),
        },
        "checks": checks,
        "nonclaims": [
            "not a D5 classification",
            "not a general Type-E theorem",
            "not a tiling criterion",
            "not a fingerprint classifier",
        ],
    }
    artifact["payload_sha256_without_this_field"] = payload_sha256(artifact)
    write_json(Path(args.out), artifact)
    print(json.dumps({
        "pass": artifact["pass"],
        "artifact": str(Path(args.out).resolve().relative_to(ROOT)) if Path(args.out).resolve().is_relative_to(ROOT) else str(Path(args.out)),
        "pair_channel_order": len(pair_group),
        "a2_preserver_order": len(a2_preservers),
        "d4_preserver_order": len(d4_preservers),
    }, indent=2, sort_keys=True))
    return bool(artifact["pass"])


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)