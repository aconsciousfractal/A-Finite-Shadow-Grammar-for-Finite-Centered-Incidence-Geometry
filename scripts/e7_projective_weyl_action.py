#!/usr/bin/env python3
"""Helper routines for the public E7 source-action replay.

No external dependencies.  The helper builds the projective simple-reflection
action on the 63 E7 projective roots, reconstructs a symplectic F_2^6 model
from the Gram graph, and counts the generated projective source action as a
matrix group over F_2.

The bounded channel conclusion used by the bundled replay is:

  Aut(Gram-square graph) = Aut(rank-2 flat-size pair channel) = G_proj,
  all of order 1451520.

This module supplies source-action functions used by the bundled public E7
replay.  It is not a standalone E7 theorem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

import e7_projective_root_engine as s2
import e7_projective_flat_channel as s4

DATE = "2026-07-09"
GATE = "Public E7 source-action replay projective Weyl/action and automorphism-channel replay"
EXPECTED = {
    "projective_pair_count": 63,
    "simple_generator_count": 7,
    "source_projective_order": 1451520,
    "sp6_2_order": 1451520,
    "aut_gram_order": 1451520,
    "aut_flat_pair_channel_order": 1451520,
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json_payload(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def gram_adjacency(pairs: list[tuple[int, ...]]) -> list[list[int]]:
    n = len(pairs)
    A = [[0 for _ in range(n)] for _ in range(n)]
    for i, j in combinations(range(n), 2):
        gram = s2.gram_square_value(pairs[i], pairs[j])
        if gram == 1:
            A[i][j] = A[j][i] = 1
        elif gram != 0:
            raise ValueError(f"unexpected off-diagonal gram-square {gram}")
    return A


def row_masks(A: list[list[int]]) -> list[int]:
    masks = []
    for row in A:
        mask = 0
        for j, x in enumerate(row):
            if x:
                mask |= 1 << j
        masks.append(mask)
    return masks


def simple_reflection_perms(pairs: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    index = {p: i for i, p in enumerate(pairs)}
    perms = []
    for a in s2.SIMPLE_ROOTS:
        image = []
        for p in pairs:
            image.append(index[s2.canon(s2.reflect(p, a))])
        perms.append(tuple(image))
    return perms


def perm_is_bijection(perm: tuple[int, ...], n: int) -> bool:
    return sorted(perm) == list(range(n))


def preserves_adjacency(perm: tuple[int, ...], A: list[list[int]]) -> bool:
    n = len(A)
    return all(A[i][j] == A[perm[i]][perm[j]] for i in range(n) for j in range(n))


def find_symplectic_basis(A: list[list[int]]) -> list[int]:
    n = len(A)
    target = [[0] * 6 for _ in range(6)]
    for i in range(3):
        target[2 * i][2 * i + 1] = 1
        target[2 * i + 1][2 * i] = 1

    basis: list[int] = []

    def backtrack(pos: int) -> bool:
        if pos == 6:
            return True
        for v in range(n):
            if v in basis:
                continue
            ok = True
            for k, b in enumerate(basis):
                if A[v][b] != target[pos][k]:
                    ok = False
                    break
            if ok:
                basis.append(v)
                if backtrack(pos + 1):
                    return True
                basis.pop()
        return False

    if not backtrack(0):
        raise RuntimeError("could not find symplectic basis in graph")
    return basis


def coord_from_basis(v: int, basis: list[int], A: list[list[int]]) -> int:
    # basis order is e1,f1,e2,f2,e3,f3.  In characteristic 2,
    # coeff(e_i)=<v,f_i> and coeff(f_i)=<v,e_i>.
    out = 0
    for i in range(3):
        e = basis[2 * i]
        f = basis[2 * i + 1]
        if A[v][f]:
            out |= 1 << (2 * i)
        if A[v][e]:
            out |= 1 << (2 * i + 1)
    return out


def symp_pair(x: int, y: int) -> int:
    val = 0
    for i in range(3):
        a = (x >> (2 * i)) & 1
        b = (x >> (2 * i + 1)) & 1
        c = (y >> (2 * i)) & 1
        d = (y >> (2 * i + 1)) & 1
        val ^= (a & d) ^ (b & c)
    return val


def build_f2_model(A: list[list[int]]) -> dict:
    basis = find_symplectic_basis(A)
    coords = [coord_from_basis(v, basis, A) for v in range(len(A))]
    coord_to_vertex = {c: i for i, c in enumerate(coords)}
    masks = row_masks(A)
    xor_failures = []
    for i, j in combinations(range(len(A)), 2):
        zcoord = coords[i] ^ coords[j]
        z = coord_to_vertex.get(zcoord)
        if z is None or masks[z] != (masks[i] ^ masks[j]):
            xor_failures.append([i, j, z])
            if len(xor_failures) >= 5:
                break
    adjacency_mismatches = []
    for i, j in combinations(range(len(A)), 2):
        if A[i][j] != symp_pair(coords[i], coords[j]):
            adjacency_mismatches.append([i, j, coords[i], coords[j]])
            if len(adjacency_mismatches) >= 5:
                break
    checks = {
        "basis_size": len(basis) == 6,
        "basis_pairing_pattern": all(A[basis[i]][basis[j]] == (1 if i // 2 == j // 2 and i != j and {i % 2, j % 2} == {0, 1} else 0) for i in range(6) for j in range(6)),
        "coordinates_are_all_nonzero": sorted(coords) == list(range(1, 64)),
        "coordinate_map_is_bijective": len(coord_to_vertex) == 63,
        "adjacency_equals_symplectic_pairing": not adjacency_mismatches,
        "adjacency_character_xor_reconstructs_addition": not xor_failures,
    }
    return {
        "basis_vertices": basis,
        "vertex_to_f2_coord": coords,
        "coord_to_vertex": coord_to_vertex,
        "checks": checks,
        "xor_failures": xor_failures,
        "adjacency_mismatches": adjacency_mismatches,
    }


def apply_matrix(cols: tuple[int, ...], v: int) -> int:
    out = 0
    for i in range(6):
        if (v >> i) & 1:
            out ^= cols[i]
    return out


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    # left after right, with column images of basis vectors.
    return tuple(apply_matrix(left, col) for col in right)


def pack_matrix(cols: tuple[int, ...]) -> int:
    out = 0
    for i, col in enumerate(cols):
        out |= col << (6 * i)
    return out


def matrix_from_perm(perm: tuple[int, ...], coords: list[int], coord_to_vertex: dict[int, int]) -> tuple[int, ...]:
    cols = []
    for i in range(6):
        vertex = coord_to_vertex[1 << i]
        cols.append(coords[perm[vertex]])
    mat = tuple(cols)
    for v, coord in enumerate(coords):
        if apply_matrix(mat, coord) != coords[perm[v]]:
            raise ValueError("permutation is not linear in reconstructed F2 model")
    return mat


def matrix_preserves_symplectic(cols: tuple[int, ...]) -> bool:
    for x in range(1, 64):
        mx = apply_matrix(cols, x)
        if mx == 0:
            return False
        for y in range(1, 64):
            if symp_pair(mx, apply_matrix(cols, y)) != symp_pair(x, y):
                return False
    return True


def generated_matrix_group_order(gens: list[tuple[int, ...]], expected_limit: int) -> int:
    identity = tuple(1 << i for i in range(6))
    seen = {pack_matrix(identity)}
    q = deque([identity])
    while q:
        g = q.popleft()
        for gen in gens:
            h = compose(gen, g)
            hp = pack_matrix(h)
            if hp not in seen:
                seen.add(hp)
                if len(seen) > expected_limit:
                    raise RuntimeError(f"matrix group exceeded expected limit {expected_limit}")
                q.append(h)
    return len(seen)


def sp6_order() -> int:
    # |Sp(2n,2)| = 2^(n^2) * product_{i=1..n}(2^(2i)-1), here n=3.
    out = 2 ** 9
    for i in range(1, 4):
        out *= 2 ** (2 * i) - 1
    return out


def permutation_orbit_sizes(gens: list[tuple[int, ...]], n: int) -> list[int]:
    unseen = set(range(n))
    sizes = []
    while unseen:
        start = next(iter(unseen))
        seen = {start}
        q = deque([start])
        while q:
            v = q.popleft()
            for g in gens:
                w = g[v]
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        sizes.append(len(seen))
        unseen -= seen
    return sorted(sizes)

def main() -> None:
    print(json.dumps({
        "module": "e7_projective_weyl_action",
        "role": "source-action helper",
        "entry_point": "scripts/e7_projective_source_channel_replay.py",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()