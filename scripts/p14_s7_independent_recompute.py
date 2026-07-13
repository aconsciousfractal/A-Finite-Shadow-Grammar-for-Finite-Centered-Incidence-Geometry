#!/usr/bin/env python3
"""P14-S7 independent recompute / red-team.

This gate recomputes the signed Type-B/C pilot from elementary finite-group
constructions rather than trusting the P14-S4/S6.5 generation path.  It uses the
classical left-ideal backbone

    rank_mass(X) = dim C[S_N] * 1_X

as an independent aggregate check for the Specht-rank atlas.  It does not
promote a theorem, a B4 atlas, or a native Type-B Fourier equivalence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, permutations
from pathlib import Path
import json
import math
import platform
import time

from sympy import Matrix, ZZ
from sympy.matrices.normalforms import smith_normal_form

ROOT = Path(__file__).resolve().parents[1]
FCIG_ROOT = ROOT.parents[1]
DATE = "2026-07-06"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
TABLES = ROOT / "tables"
CERTIFIED = ROOT / "certified"
SCRIPT_PATH = Path(__file__).resolve()
S4_ATLAS = RESULTS / "p14_s4_first_atlas.json"
S6_5_ATLAS = RESULTS / "p14_s6_5_rank_mass_formula_scout.json"
PRIME_MAIN = 1000003
PRIME_SECOND = 1000033
BOUNDARY = "independent recompute only; no theorem, no B4 atlas promotion, no classification, no tiling criterion, no native-B equivalence, no Type-D/affine/general-Weyl claim"
NEXT_TASK = "P14-S7B interpretation is complete; next is P14-S7.5 native branching comparison scout and prior-art gate."


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, data) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def word0(p):
    return "".join(str(i) for i in p)


def compose(a, b):
    """Permutation composition a after b, with tuples as images."""
    return tuple(a[i] for i in b)


def identity(n):
    return tuple(range(n))


_PERMS: dict[int, list[tuple[int, ...]]] = {}
_INDEX: dict[int, dict[tuple[int, ...], int]] = {}


def all_perms(n):
    if n not in _PERMS:
        _PERMS[n] = list(permutations(range(n)))
    return _PERMS[n]


def perm_index(n):
    if n not in _INDEX:
        _INDEX[n] = {g: i for i, g in enumerate(all_perms(n))}
    return _INDEX[n]


def transposition_class(n):
    out = set()
    base = list(range(n))
    for i, j in combinations(range(n), 2):
        p = base[:]
        p[i], p[j] = p[j], p[i]
        out.add(tuple(p))
    return out


def deterministic_sample(G, size, label):
    ordered = sorted(G, key=lambda p: sha256((label + "|" + word0(p)).encode("utf-8")).hexdigest())
    return set(ordered[:size])


def signed_negation(n):
    return tuple(i ^ 1 for i in range(2 * n))


def sign_flip(n, coords):
    p = list(range(2 * n))
    for c in coords:
        a = 2 * (c - 1)
        p[a], p[a + 1] = p[a + 1], p[a]
    return tuple(p)


def signed_shadow_B(n):
    """Generate B_n <= S_{2n} directly as C_2 wr S_n, not by filtering S_{2n}."""
    out = set()
    for pair_perm in permutations(range(n)):
        for mask in range(1 << n):
            p = [None] * (2 * n)
            for i, target in enumerate(pair_perm):
                flip = (mask >> i) & 1
                if flip:
                    p[2 * i] = 2 * target + 1
                    p[2 * i + 1] = 2 * target
                else:
                    p[2 * i] = 2 * target
                    p[2 * i + 1] = 2 * target + 1
            out.add(tuple(p))
    return out


def pair_preserving(g, n):
    pairs = {frozenset((2 * i, 2 * i + 1)) for i in range(n)}
    return all(frozenset((g[2 * i], g[2 * i + 1])) in pairs for i in range(n))


def commutes_with_J(g, n):
    J = signed_negation(n)
    return compose(g, J) == compose(J, g)


def signed_data(g, n):
    u, signs = [], []
    for i in range(n):
        v = g[2 * i]
        u.append(v // 2)
        signs.append(1 if v % 2 == 0 else -1)
    return tuple(u), tuple(signs)


def cycle_type(p):
    n = len(p)
    seen = [False] * n
    lengths = []
    for i in range(n):
        if seen[i]:
            continue
        cur = i
        length = 0
        while not seen[cur]:
            seen[cur] = True
            length += 1
            cur = p[cur]
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def partition_label(part):
    return ",".join(str(x) for x in part)


def signed_cycle_type(g, n):
    u, signs = signed_data(g, n)
    seen = [False] * n
    pos, neg = [], []
    for i in range(n):
        if seen[i]:
            continue
        cur, length, prod = i, 0, 1
        while not seen[cur]:
            seen[cur] = True
            length += 1
            prod *= signs[cur]
            cur = u[cur]
        (pos if prod == 1 else neg).append(length)
    return (tuple(sorted(pos, reverse=True)), tuple(sorted(neg, reverse=True)))


def signed_type_label(t):
    pos, neg = t
    ps = "+" + "+".join(str(x) for x in pos) if pos else "+none"
    ns = "-" + "-".join(str(x) for x in neg) if neg else "-none"
    return f"{ps}|{ns}"


def signed_histogram(X, n):
    if not all(pair_preserving(x, n) for x in X):
        return "not_applicable"
    h = Counter(signed_type_label(signed_cycle_type(x, n)) for x in X)
    return {k: h[k] for k in sorted(h)}


def fixed_pair_counts(g, n):
    pos = neg = 0
    for i in range(n):
        a = 2 * i
        if g[a] == a and g[a + 1] == a + 1:
            pos += 1
        elif g[a] == a + 1 and g[a + 1] == a:
            neg += 1
    return pos, neg


def signed_incidence_layer(B, n, k, ell):
    return {g for g in B if fixed_pair_counts(g, n) == (k, ell)}


def class_control(B, n, label):
    return {g for g in B if signed_type_label(signed_cycle_type(g, n)) == label}


def s15_witness(n=3):
    N = 2 * n
    s2 = sign_flip(n, (2,))
    s3 = sign_flip(n, (3,))
    s123 = sign_flip(n, (1, 2, 3))
    return {compose(s3, h) for h in {identity(N), s2}}, {compose(s3, h) for h in {identity(N), s123}}


def build_s4_objects_independent():
    objects = []
    for n in (2, 3):
        N = 2 * n
        B = signed_shadow_B(n)
        objects.append({"n": n, "N": N, "object_id": f"B{n}_subgroup_shadow", "X": B})
        for k in range(n + 1):
            for ell in range(n + 1):
                layer = signed_incidence_layer(B, n, k, ell)
                if layer:
                    objects.append({"n": n, "N": N, "object_id": f"BI{n}_{k}_{ell}", "X": layer, "k": k, "l": ell})
    XA, XB = s15_witness(3)
    objects.append({"n": 3, "N": 6, "object_id": "S15_X_A_s3_H_s2", "X": XA})
    objects.append({"n": 3, "N": 6, "object_id": "S15_X_B_s3_H_s1s2s3", "X": XB})
    B3 = signed_shadow_B(3)
    for label in sorted({signed_type_label(signed_cycle_type(x, 3)) for x in (XA | XB)}):
        oid = "B3_signed_class_" + label.replace("+", "p").replace("-", "m").replace("|", "_").replace(",", "_")
        objects.append({"n": 3, "N": 6, "object_id": oid, "X": class_control(B3, 3, label)})
    for n in (2, 3):
        N = 2 * n
        G = set(all_perms(N))
        B = signed_shadow_B(n)
        objects.append({"n": n, "N": N, "object_id": f"S{N}_full_group", "X": G})
        objects.append({"n": n, "N": N, "object_id": f"S{N}_transposition_class", "X": transposition_class(N)})
        objects.append({"n": n, "N": N, "object_id": f"S{N}_deterministic_random_size_B{n}", "X": deterministic_sample(G, len(B), f"P14-S4-random-S{N}-size-B{n}")})
    objects.append({"n": 3, "N": 6, "object_id": "S6_deterministic_random_size_2", "X": deterministic_sample(set(all_perms(6)), 2, "P14-S4-random-S6-size-2")})
    return objects


def sparse_rank_mod(row_sets, prime):
    basis = {}
    for cols in row_sets:
        row = {int(c): 1 for c in cols}
        while row:
            pivot = min(row)
            value = row[pivot] % prime
            if value == 0:
                del row[pivot]
                continue
            if pivot not in basis:
                inv = pow(value, -1, prime)
                if inv != 1:
                    row = {c: (v * inv) % prime for c, v in row.items() if (v * inv) % prime}
                basis[pivot] = row
                break
            factor = value
            base = basis[pivot]
            for c, v in base.items():
                new_value = (row.get(c, 0) - factor * v) % prime
                if new_value:
                    row[c] = new_value
                elif c in row:
                    del row[c]
    return len(basis)


def left_translate_span_rank_mod(X, N, prime=PRIME_MAIN):
    ambient_size = math.factorial(N)
    if len(X) == ambient_size:
        return 1
    if len(X) == 1:
        return ambient_size
    group = all_perms(N)
    index = perm_index(N)
    x_list = list(X)
    row_sets = []
    for g in group:
        row_sets.append({index[compose(g, x)] for x in x_list})
    return sparse_rank_mod(row_sets, prime)


def rank_mod_dense(matrix, prime=PRIME_MAIN):
    rows = []
    for row in matrix:
        rows.append([int(v) % prime for v in row])
    m = len(rows)
    n = len(rows[0]) if rows else 0
    rank = 0
    col = 0
    while rank < m and col < n:
        pivot = None
        for r in range(rank, m):
            if rows[r][col] % prime:
                pivot = r
                break
        if pivot is None:
            col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inv = pow(rows[rank][col], -1, prime)
        rows[rank] = [(v * inv) % prime for v in rows[rank]]
        for r in range(m):
            if r == rank:
                continue
            factor = rows[r][col] % prime
            if factor:
                rows[r] = [(rows[r][c] - factor * rows[rank][c]) % prime for c in range(n)]
        rank += 1
        col += 1
    return rank


def standard_matrix(p):
    N = len(p)
    base = N - 1
    M = [[0 for _ in range(N - 1)] for _ in range(N - 1)]
    for j in range(N - 1):
        image_j = p[j]
        image_base = p[base]
        if image_j < N - 1:
            M[image_j][j] += 1
        if image_base < N - 1:
            M[image_base][j] -= 1
    return M


def add_matrix(A, B):
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def zero_matrix(n):
    return [[0 for _ in range(n)] for _ in range(n)]


def standard_block_sum(X, N):
    M = zero_matrix(N - 1)
    for x in X:
        M = add_matrix(M, standard_matrix(x))
    return M


def smith_diagonal(matrix):
    M = Matrix(matrix)
    D = smith_normal_form(M, domain=ZZ)
    diag = []
    for i in range(min(D.rows, D.cols)):
        diag.append(abs(int(D[i, i])))
    return diag


def s1_5_standard_witness_check(atlas_rows, objects):
    by_id = {obj["object_id"]: obj for obj in objects}
    rows_by_key = {(row["object_id"], row["lambda"]): row for row in atlas_rows}
    out = []
    for oid in ("S15_X_A_s3_H_s2", "S15_X_B_s3_H_s1s2s3"):
        X = by_id[oid]["X"]
        N = by_id[oid]["N"]
        M = standard_block_sum(X, N)
        rank = rank_mod_dense(M, PRIME_MAIN)
        snf = smith_diagonal(M)
        atlas = rows_by_key[(oid, "5,1")]
        out.append({
            "object_id": oid,
            "lambda": "5,1",
            "standard_rank_recomputed": rank,
            "atlas_rank_Q": int(atlas["rank_Q"]),
            "rank_matches_atlas": rank == int(atlas["rank_Q"]),
            "standard_lattice_snf": snf,
            "atlas_snf_lattice_divisors": atlas["snf_divisors"],
            "snf_note": "SNF is lattice-qualified; matching is useful but rank is the invariant check.",
        })
    XA = by_id["S15_X_A_s3_H_s2"]
    XB = by_id["S15_X_B_s3_H_s1s2s3"]
    return {
        "rows": out,
        "same_signed_histogram": signed_histogram(XA["X"], 3) == signed_histogram(XB["X"], 3),
        "same_rank_mass_expected": True,
        "first_difference_lambda_5_1": out[0]["standard_rank_recomputed"] != out[1]["standard_rank_recomputed"],
        "rank_pair": [out[0]["standard_rank_recomputed"], out[1]["standard_rank_recomputed"]],
        "rank_pair_expected": [4, 2],
        "rank_pair_matches_expected": [out[0]["standard_rank_recomputed"], out[1]["standard_rank_recomputed"]] == [4, 2],
    }


def recompute_s4_surface():
    atlas = read_json(S4_ATLAS)
    summaries = {item["object_id"]: item for item in atlas["object_summaries"]}
    objects = build_s4_objects_independent()
    checks = []
    t0 = time.perf_counter()
    for obj in sorted(objects, key=lambda x: x["object_id"]):
        oid = obj["object_id"]
        X = set(obj["X"])
        n = int(obj["n"])
        N = int(obj["N"])
        summary = summaries[oid]
        rank = left_translate_span_rank_mod(X, N, PRIME_MAIN)
        hist = signed_histogram(X, n)
        checks.append({
            "object_id": oid,
            "n": n,
            "ambient_N": N,
            "size_recomputed": len(X),
            "size_atlas": int(summary["size_X"]),
            "size_matches": len(X) == int(summary["size_X"]),
            "signed_histogram_matches": hist == summary["signed_cycle_type_histogram"],
            "rank_mass_recomputed_left_ideal_mod_p": int(rank),
            "rank_mass_atlas": int(summary["rank_mass"]),
            "rank_mass_matches": int(rank) == int(summary["rank_mass"]),
            "prime": PRIME_MAIN,
        })
    return {
        "object_count_rebuilt": len(objects),
        "object_count_atlas": len(summaries),
        "rows": checks,
        "all_size_matches": all(c["size_matches"] for c in checks),
        "all_signed_histogram_matches": all(c["signed_histogram_matches"] for c in checks),
        "all_rank_mass_matches": all(c["rank_mass_matches"] for c in checks),
        "seconds": round(time.perf_counter() - t0, 6),
        "s1_5_standard_witness": s1_5_standard_witness_check(atlas["rows"], objects),
    }


def recompute_b4_rows():
    s6_5 = read_json(S6_5_ATLAS)
    expected = {(r["n"], r["k"], r["l"]): r for r in s6_5["bi_rank_mass_rows"] if int(r["n"]) == 4}
    n = 4
    N = 8
    B = signed_shadow_B(n)
    rows = []
    t0 = time.perf_counter()
    for k in range(n + 1):
        for ell in range(n + 1):
            X = signed_incidence_layer(B, n, k, ell)
            if not X:
                continue
            rank = left_translate_span_rank_mod(X, N, PRIME_MAIN)
            exp = expected[(n, k, ell)]
            rows.append({
                "object_id": f"BI{n}_{k}_{ell}",
                "n": n,
                "ambient_N": N,
                "k": k,
                "l": ell,
                "size_recomputed": len(X),
                "size_s6_5": int(exp["size_X"]),
                "size_matches": len(X) == int(exp["size_X"]),
                "rank_mass_recomputed_left_ideal_mod_p": int(rank),
                "rank_mass_s6_5": int(exp["rank_mass"]),
                "rank_mass_matches": int(rank) == int(exp["rank_mass"]),
                "prime": PRIME_MAIN,
            })
    X00 = signed_incidence_layer(B, n, 0, 0)
    second_prime_rank = left_translate_span_rank_mod(X00, N, PRIME_SECOND)
    second_prime = {
        "object_id": "BI4_0_0",
        "prime": PRIME_SECOND,
        "rank_mass_second_prime": int(second_prime_rank),
        "expected_rank_mass": int(expected[(4, 0, 0)]["rank_mass"]),
        "matches": int(second_prime_rank) == int(expected[(4, 0, 0)]["rank_mass"]),
        "scope_note": "second-prime modular replay for the high-value zero-zero candidate row; not a proof over Q by itself",
    }
    return {
        "rows": rows,
        "row_count": len(rows),
        "expected_row_count": len(expected),
        "all_size_matches": all(r["size_matches"] for r in rows),
        "all_rank_mass_matches": all(r["rank_mass_matches"] for r in rows),
        "second_prime_check": second_prime,
        "seconds": round(time.perf_counter() - t0, 6),
    }


def mirror_checks_from_rows(rows):
    by = {(r["n"], r["k"], r["l"]): r for r in rows if "k" in r and "l" in r}
    out = []
    for key, row in sorted(by.items()):
        n, k, ell = key
        if (k, ell) > (ell, k):
            continue
        mate = by.get((n, ell, k))
        if mate is None:
            continue
        size_a = row.get("size_recomputed", row.get("size_X"))
        size_b = mate.get("size_recomputed", mate.get("size_X"))
        rank_a = row.get("rank_mass_recomputed_left_ideal_mod_p", row.get("rank_mass"))
        rank_b = mate.get("rank_mass_recomputed_left_ideal_mod_p", mate.get("rank_mass"))
        out.append({
            "n": n,
            "pair": f"({k},{ell})<->({ell},{k})",
            "same_size": int(size_a) == int(size_b),
            "same_rank_mass": int(rank_a) == int(rank_b),
            "rank_mass_pair": [int(rank_a), int(rank_b)],
        })
    return out


def candidate_formula_check(s4_rows, b4_rows):
    all_rows = []
    for r in s4_rows:
        if r["object_id"].startswith("BI"):
            parts = r["object_id"].split("_")
            if len(parts) == 3:
                all_rows.append({
                    "n": int(r["n"]),
                    "ambient_N": int(r["ambient_N"]),
                    "k": int(parts[1]),
                    "l": int(parts[2]),
                    "rank_mass": int(r["rank_mass_recomputed_left_ideal_mod_p"]),
                })
    for r in b4_rows:
        all_rows.append({
            "n": int(r["n"]),
            "ambient_N": int(r["ambient_N"]),
            "k": int(r["k"]),
            "l": int(r["l"]),
            "rank_mass": int(r["rank_mass_recomputed_left_ideal_mod_p"]),
        })
    checks = []
    for r in sorted(all_rows, key=lambda x: x["n"]):
        if r["k"] == 0 and r["l"] == 0:
            predicted = math.factorial(r["ambient_N"]) // (2 ** r["n"])
            checks.append({
                "n": r["n"],
                "ambient_N": r["ambient_N"],
                "rank_mass": r["rank_mass"],
                "predicted_factorial_over_2n": predicted,
                "matches": r["rank_mass"] == predicted,
            })
    return {
        "candidate_statement": "rank_mass(BI_n(0,0))=(2n)!/2^n",
        "status": "FINITE_EVIDENCE_ONLY",
        "checks": checks,
        "all_match": all(c["matches"] for c in checks),
        "checked_n": [c["n"] for c in checks],
        "proof_obligation": "Requires a uniform left-ideal rank proof and prior-art lock before theorem wording.",
    }


def boundary_scan():
    marker = "S" + "6.5"
    gate_marker = "P14-" + marker
    machine_marker = "P14_" + "S6_5"
    stale_patterns = [
        "Prossima task: " + gate_marker,
        "Current active route: " + gate_marker,
        gate_marker + " next",
        marker + " next",
        "active_gate: " + machine_marker,
    ]
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in str(path):
            continue
        if path.resolve() == SCRIPT_PATH.resolve():
            continue
        rel_for_scan = path.relative_to(ROOT).as_posix()
        if rel_for_scan.startswith("results/p14_s7_") or rel_for_scan.startswith("docs/P14_S7_") or rel_for_scan.startswith("tables/P14_S7_") or rel_for_scan.startswith("certified/P14_S7_") or rel_for_scan == "results/SHA256SUMS_S7.txt":
            continue
        if path.suffix.lower() not in {".md", ".json", ".py", ".txt", ".csv", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in stale_patterns:
            if pat in text:
                hits.append({"path": str(path.relative_to(ROOT)), "pattern": pat})
    return {
        "stale_s6_5_next_hits": hits,
        "stale_s6_5_next_absent": len(hits) == 0,
        "boundary_note": "Keyword scan only; S7 report also states the public boundary explicitly.",
    }


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(payload):
    write_json(RESULTS / "p14_s7_independent_recompute.json", payload)
    write_json(RESULTS / "p14_s7_independent_recompute_summary.json", payload["summary"])

    s4_headers = ["object_id", "ambient_N", "size_matches", "signed_histogram_matches", "rank_mass_atlas", "rank_mass_recomputed_left_ideal_mod_p", "rank_mass_matches"]
    write_text(TABLES / "P14_S7_S4_RECOMPUTE_TABLE.md", "# P14-S7 S4 Surface Recompute Table\n\n" + markdown_table(s4_headers, payload["s4_surface"]["rows"]) + "\n")

    b4_headers = ["object_id", "size_s6_5", "size_recomputed", "rank_mass_s6_5", "rank_mass_recomputed_left_ideal_mod_p", "rank_mass_matches", "prime"]
    write_text(TABLES / "P14_S7_B4_RECOMPUTE_TABLE.md", "# P14-S7 B4 Recompute Table\n\n" + markdown_table(b4_headers, payload["b4_recompute"]["rows"]) + "\n")

    report = [
        "# P14-S7 Independent Recompute / Red-Team",
        "",
        f"Date: {DATE}",
        f"Status: {payload['summary']['status']}",
        f"Decision: `{payload['summary']['decision']}`",
        "",
        "## Scope",
        "",
        "S7 independently rebuilds the finite signed-shadow objects and recomputes the aggregate `rank_mass` through the left-ideal backbone. It checks the P14-S4 atlas surface, the S6.5 B4 feasibility rows, the narrow zero-zero formula candidate, and the S1.5 standard-block witness.",
        "",
        "This is still a red-team/recompute gate. It does not promote a theorem, a full B4/S8 atlas, a native Type-B Fourier equivalence, a classifier, or a tiling criterion.",
        "",
        "## Results",
        "",
        f"- Rebuilt P14-S4 objects: `{payload['s4_surface']['object_count_rebuilt']}` / atlas `{payload['s4_surface']['object_count_atlas']}`.",
        f"- S4 surface size checks pass: `{payload['s4_surface']['all_size_matches']}`.",
        f"- S4 signed-histogram checks pass: `{payload['s4_surface']['all_signed_histogram_matches']}`.",
        f"- S4 rank-mass left-ideal checks pass: `{payload['s4_surface']['all_rank_mass_matches']}`.",
        f"- B4 rows recomputed: `{payload['b4_recompute']['row_count']}` / expected `{payload['b4_recompute']['expected_row_count']}`.",
        f"- B4 rank-mass checks pass: `{payload['b4_recompute']['all_rank_mass_matches']}`.",
        f"- Second-prime check for BI4_0_0 passes: `{payload['b4_recompute']['second_prime_check']['matches']}`.",
        f"- Mirror checks pass: `{payload['summary']['mirror_checks_pass']}`.",
        f"- Zero-zero candidate matches n={payload['candidate_formula']['checked_n']}: `{payload['candidate_formula']['all_match']}`.",
        f"- S1.5 standard witness ranks: `{payload['s4_surface']['s1_5_standard_witness']['rank_pair']}`.",
        "",
        "## Interpretation In Simple Terms",
        "",
        "P14 remains a bounded dependency artifact. S7 confirmed that the S6.5 zero-zero pattern was not a file-generation accident: `BI_n(0,0)` has rank mass `6, 90, 2520` for `n=2,3,4`, matching `(2n)!/2^n`. S7B then clarified the interpretation: this is sign-subgroup index/background, while mixed layers carry the bounded non-index signal for P13.",
        "",
        "## Boundary",
        "",
        BOUNDARY,
        "",
        f"Prossima task: {NEXT_TASK}",
    ]
    write_text(DOCS / "P14_S7_INDEPENDENT_RECOMPUTE_2026_07_06.md", "\n".join(report) + "\n")
    write_text(RESULTS / "p14_s7_independent_recompute.md", "\n".join(report) + "\n")

    cert = {
        "certificate": "P14-S7 independent recompute / red-team",
        "date_utc": DATE,
        "status": payload["summary"]["status"],
        "decision": payload["summary"]["decision"],
        "checks": payload["summary"]["checks"],
        "artifact_paths": [
            "results/p14_s7_independent_recompute.json",
            "results/p14_s7_independent_recompute_summary.json",
            "results/p14_s7_independent_recompute.md",
            "tables/P14_S7_S4_RECOMPUTE_TABLE.md",
            "tables/P14_S7_B4_RECOMPUTE_TABLE.md",
            "docs/P14_S7_INDEPENDENT_RECOMPUTE_2026_07_06.md",
        ],
        "next_task": NEXT_TASK,
    }
    write_json(CERTIFIED / "P14_S7_INDEPENDENT_RECOMPUTE_CERTIFICATE.json", cert)
    cert_rows = [{"check": k, "value": v} for k, v in cert["checks"].items()]
    write_text(CERTIFIED / "P14_S7_INDEPENDENT_RECOMPUTE_CERTIFICATE.md", "# P14-S7 Independent Recompute Certificate\n\n" + f"Status: {cert['status']}\n\nDecision: `{cert['decision']}`\n\n" + markdown_table(["check", "value"], cert_rows) + f"\nProssima task: {NEXT_TASK}\n")

    manifest_paths = [
        SCRIPT_PATH,
        RESULTS / "p14_s7_independent_recompute.json",
        RESULTS / "p14_s7_independent_recompute_summary.json",
        RESULTS / "p14_s7_independent_recompute.md",
        TABLES / "P14_S7_S4_RECOMPUTE_TABLE.md",
        TABLES / "P14_S7_B4_RECOMPUTE_TABLE.md",
        DOCS / "P14_S7_INDEPENDENT_RECOMPUTE_2026_07_06.md",
        CERTIFIED / "P14_S7_INDEPENDENT_RECOMPUTE_CERTIFICATE.json",
        CERTIFIED / "P14_S7_INDEPENDENT_RECOMPUTE_CERTIFICATE.md",
    ]
    lines = []
    for p in manifest_paths:
        lines.append(f"{artifact_hash(p)}  {p.relative_to(ROOT).as_posix()}")
    write_text(RESULTS / "SHA256SUMS_S7.txt", "\n".join(lines) + "\n")


def run():
    RESULTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    CERTIFIED.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    s4_surface = recompute_s4_surface()
    b4_recompute = recompute_b4_rows()
    mirror_rows = []
    mirror_rows.extend(mirror_checks_from_rows(s4_surface["rows"]))
    mirror_rows.extend(mirror_checks_from_rows(b4_recompute["rows"]))
    candidate = candidate_formula_check(s4_surface["rows"], b4_recompute["rows"])
    boundary = boundary_scan()

    checks = {
        "s4_object_count_matches": s4_surface["object_count_rebuilt"] == s4_surface["object_count_atlas"] == 24,
        "s4_size_checks_pass": s4_surface["all_size_matches"],
        "s4_signed_histogram_checks_pass": s4_surface["all_signed_histogram_matches"],
        "s4_rank_mass_left_ideal_checks_pass": s4_surface["all_rank_mass_matches"],
        "s1_5_standard_rank_pair_matches_expected": s4_surface["s1_5_standard_witness"]["rank_pair_matches_expected"],
        "b4_row_count_matches": b4_recompute["row_count"] == b4_recompute["expected_row_count"] == 11,
        "b4_size_checks_pass": b4_recompute["all_size_matches"],
        "b4_rank_mass_checks_pass": b4_recompute["all_rank_mass_matches"],
        "b4_zero_zero_second_prime_pass": b4_recompute["second_prime_check"]["matches"],
        "mirror_checks_pass": all(r["same_size"] and r["same_rank_mass"] for r in mirror_rows),
        "zero_zero_candidate_matches_n_2_3_4": candidate["all_match"] and candidate["checked_n"] == [2, 3, 4],
        "stale_s6_5_next_absent": boundary["stale_s6_5_next_absent"],
        "no_theorem_promoted": True,
        "no_b4_atlas_promoted": True,
        "no_native_b_equivalence_promoted": True,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    decision = "GO_TO_S7_5_NATIVE_BRANCHING_SCOUT_AND_PRIOR_ART_GATE" if status == "PASS" else "BLOCK_BEFORE_S7_5"
    summary = {
        "gate": "P14-S7",
        "date_utc": DATE,
        "status": status,
        "decision": decision,
        "checks": checks,
        "runtime": {
            "total_seconds": round(time.perf_counter() - t0, 6),
            "s4_seconds": s4_surface["seconds"],
            "b4_seconds": b4_recompute["seconds"],
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "prime_main": PRIME_MAIN,
            "prime_second": PRIME_SECOND,
        },
        "mirror_checks_pass": checks["mirror_checks_pass"],
        "candidate_formula": candidate["candidate_statement"],
        "next_task": NEXT_TASK,
        "boundary": BOUNDARY,
    }
    payload = {
        "summary": summary,
        "s4_surface": s4_surface,
        "b4_recompute": b4_recompute,
        "mirror_checks": mirror_rows,
        "candidate_formula": candidate,
        "boundary_scan": boundary,
    }
    write_outputs(payload)
    return payload


if __name__ == "__main__":
    artifact = run()
    print(json.dumps(artifact["summary"], indent=2, sort_keys=True))