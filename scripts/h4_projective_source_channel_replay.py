from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "artifacts" / "h4_projective_source_channel_replay_seed.json"
OUT = ROOT / "artifacts" / "h4_projective_source_channel_replay.json"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return sha256_text(text)


def validate_matrix(matrix: list[list[int]], n: int, name: str) -> None:
    if len(matrix) != n:
        raise ValueError(f"{name}: expected {n} rows, got {len(matrix)}")
    for i, row in enumerate(matrix):
        if len(row) != n:
            raise ValueError(f"{name}: row {i} has length {len(row)}")
        if row[i] != -1:
            raise ValueError(f"{name}: diagonal {i} is not -1")
        for j in range(i + 1, n):
            if matrix[i][j] != matrix[j][i]:
                raise ValueError(f"{name}: nonsymmetric at {(i, j)}")


def color_histogram(matrix: list[list[int]]) -> dict[str, int]:
    counts: Counter[int] = Counter()
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            counts[matrix[i][j]] += 1
    return {str(k): v for k, v in sorted(counts.items())}


def preserves_color_matrix(p: tuple[int, ...], matrix: list[list[int]]) -> bool:
    n = len(matrix)
    for i in range(n):
        pi = p[i]
        for j in range(i + 1, n):
            if matrix[i][j] != matrix[pi][p[j]]:
                return False
    return True


def vector_to_base(v: int, base: list[int], matrix: list[list[int]]) -> tuple[int, ...]:
    return tuple(matrix[v][b] for b in base)


def is_resolving(base: list[int], matrix: list[list[int]]) -> bool:
    return len({vector_to_base(v, base, matrix) for v in range(len(matrix))}) == len(matrix)


def find_resolving_base(matrix: list[list[int]]) -> list[int]:
    n = len(matrix)
    base: list[int] = []
    remaining = set(range(n))
    while not is_resolving(base, matrix):
        best = None
        best_score = None
        for cand in sorted(remaining):
            trial = base + [cand]
            classes = Counter(vector_to_base(v, trial, matrix) for v in range(n))
            score = (max(classes.values()), -len(classes), cand)
            if best_score is None or score < best_score:
                best_score = score
                best = cand
        if best is None:
            raise RuntimeError("failed to extend resolving base")
        base.append(best)
        remaining.remove(best)
    return base


def enumerate_base_images(base: list[int], matrix: list[list[int]]) -> list[tuple[int, ...]]:
    n = len(matrix)
    images: list[tuple[int, ...]] = []

    def rec(partial: list[int], used: set[int]) -> None:
        idx = len(partial)
        if idx == len(base):
            images.append(tuple(partial))
            return
        b = base[idx]
        for cand in range(n):
            if cand in used:
                continue
            ok = True
            for t, img_t in enumerate(partial):
                if matrix[b][base[t]] != matrix[cand][img_t]:
                    ok = False
                    break
            if ok:
                partial.append(cand)
                used.add(cand)
                rec(partial, used)
                used.remove(cand)
                partial.pop()

    rec([], set())
    return images


def extension_from_base_image(base: list[int], image: tuple[int, ...], matrix: list[list[int]]) -> tuple[int, ...] | None:
    n = len(matrix)
    target_vectors: dict[tuple[int, ...], int] = {}
    for u in range(n):
        vec = tuple(matrix[u][img] for img in image)
        if vec in target_vectors:
            return None
        target_vectors[vec] = u
    p: list[int] = []
    for v in range(n):
        vec = tuple(matrix[v][b] for b in base)
        if vec not in target_vectors:
            return None
        p.append(target_vectors[vec])
    perm = tuple(p)
    for b, img in zip(base, image):
        if perm[b] != img:
            return None
    return perm if preserves_color_matrix(perm, matrix) else None


def color_automorphisms(matrix: list[list[int]]) -> tuple[list[int], int, list[tuple[int, ...]]]:
    base = find_resolving_base(matrix)
    images = enumerate_base_images(base, matrix)
    automorphisms: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for image in images:
        perm = extension_from_base_image(base, image, matrix)
        if perm is not None and perm not in seen:
            seen.add(perm)
            automorphisms.append(perm)
    automorphisms.sort()
    return base, len(images), automorphisms


def normalized_pair(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)



def pair_orbit_count(group: list[tuple[int, ...]], n: int) -> int:
    unseen = {normalized_pair(i, j) for i in range(n) for j in range(i + 1, n)}
    count = 0
    while unseen:
        seed_pair = next(iter(unseen))
        orbit = {normalized_pair(g[seed_pair[0]], g[seed_pair[1]]) for g in group}
        unseen.difference_update(orbit)
        count += 1
    return count

def same_pair_orbit(group: list[tuple[int, ...]], pair_a: tuple[int, int], pair_b: tuple[int, int]) -> bool:
    target = normalized_pair(*pair_b)
    for g in group:
        if normalized_pair(g[pair_a[0]], g[pair_a[1]]) == target:
            return True
    return False


def main() -> None:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    labels = seed["point_labels"]
    n = len(labels)
    gram = seed["gram_square_color_matrix"]
    flat = seed["flat_size_matrix"]
    expected = seed["expected"]

    validate_matrix(gram, n, "gram_square_color_matrix")
    validate_matrix(flat, n, "flat_size_matrix")

    gram_base, gram_base_image_count, gram_aut = color_automorphisms(gram)
    flat_base, flat_base_image_count, flat_aut = color_automorphisms(flat)

    witness = expected["witness"]
    pair_a = tuple(witness["pair_a"])
    pair_b = tuple(witness["pair_b"])
    gram_labels = seed["gram_square_color_labels"]
    gram_color_a = gram_labels[str(gram[pair_a[0]][pair_a[1]])]
    gram_color_b = gram_labels[str(gram[pair_b[0]][pair_b[1]])]

    gram_pair_orbit_count = pair_orbit_count(gram_aut, n)
    flat_pair_orbit_count = pair_orbit_count(flat_aut, n)

    checks = {
        "points_are_60": n == 60,
        "unordered_pairs_are_1770": n * (n - 1) // 2 == 1770,
        "gram_histogram_matches_seed": color_histogram(gram) == expected["gram_square_color_histogram"],
        "flat_size_histogram_matches_seed": color_histogram(flat) == expected["flat_size_histogram"],
        "gram_automorphism_order_is_7200": len(gram_aut) == expected["gram_square_automorphism_order"],
        "flat_size_automorphism_order_is_14400": len(flat_aut) == expected["flat_size_automorphism_order"],
        "gram_square_pair_orbit_count_is_4": gram_pair_orbit_count == expected["gram_square_pair_orbit_count"],
        "flat_size_pair_orbit_count_is_3": flat_pair_orbit_count == expected["flat_size_pair_orbit_count"],
        "witness_gram_colors_match_seed": gram_color_a == witness["gram_color_a"] and gram_color_b == witness["gram_color_b"],
        "witness_gram_colors_are_distinct": gram_color_a != gram_color_b,
        "witness_same_flat_size_orbit": same_pair_orbit(flat_aut, pair_a, pair_b) is True,
        "witness_not_same_gram_square_orbit": same_pair_orbit(gram_aut, pair_a, pair_b) is False,
    }

    artifact = {
        "paper": seed["paper"],
        "artifact": "h4_projective_source_channel_replay",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "pass": all(checks.values()),
        "counts": {
            "points": n,
            "unordered_pairs": n * (n - 1) // 2,
            "gram_square_color_histogram": color_histogram(gram),
            "flat_size_histogram": color_histogram(flat),
            "gram_square_automorphism_order": len(gram_aut),
            "flat_size_automorphism_order": len(flat_aut),
            "gram_square_pair_orbit_count": gram_pair_orbit_count,
            "flat_size_pair_orbit_count": flat_pair_orbit_count,
            "gram_square_base_size": len(gram_base),
            "flat_size_base_size": len(flat_base),
            "gram_square_base_image_count": gram_base_image_count,
            "flat_size_base_image_count": flat_base_image_count,
        },
        "resolving_bases": {
            "gram_square": [labels[i] for i in gram_base],
            "flat_size": [labels[i] for i in flat_base],
        },
        "witness": {
            "pair_a": witness["pair_a_labels"],
            "pair_b": witness["pair_b_labels"],
            "gram_color_a": gram_color_a,
            "gram_color_b": gram_color_b,
            "same_flat_size_orbit": checks["witness_same_flat_size_orbit"],
            "same_gram_square_orbit": not checks["witness_not_same_gram_square_orbit"],
        },
        "checks": checks,
        "boundary": seed["boundary"],
    }
    digest = write_json(OUT, artifact)
    print(f"status={artifact['status']}")
    print(f"points={n}")
    print(f"unordered_pairs={n * (n - 1) // 2}")
    print(f"gram_square_automorphism_order={len(gram_aut)}")
    print(f"flat_size_automorphism_order={len(flat_aut)}")
    print(f"gram_square_pair_orbit_count={gram_pair_orbit_count}")
    print(f"flat_size_pair_orbit_count={flat_pair_orbit_count}")
    print(f"artifact_sha256={digest}")
    return bool(artifact["pass"])


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)