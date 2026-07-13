# ============================================================
# M19 CROSS-GRID CENSUS  (Google Colab, CPU-only)
# Question: is the M19 hidden-coset phenomenon isolated or a family?
#
# Per order-9 grid L (Sudoku solutions + non-Sudoku Latin squares):
#   1. Gamma_rank(L) = relabelings gamma in S9 whose CENTERED operator
#      drops rank on V_std (rank < 8).                [exact]
#   2. BLIND coset mining: pairwise-quotient histogram over Gamma_rank,
#      gap-detected plateau -> candidate stabilizer K_L; verify subgroup;
#      fingerprint (order, order-distribution, abelian, center, exponent).
#   3. PREDICATE mining (generalized, no middle-band/15 assumption):
#      for every row-band and column-band (stack), is there a target sum s
#      with constant band line-sums across the whole coset?
#   4. Magic flag: s == 15 (Lo Shu constant) and Lo-Shu-like group.
#   5. Classify Type 0-4.
#
# Falsifiable prediction: Sudoku grids show the phenomenon far more than
# generic Latin squares, and the coset is ~3^2:D4 with sum = 15.
# ============================================================

import itertools, json, time, random, math
from pathlib import Path
from collections import Counter
import numpy as np

# ---------------- CONFIG ----------------
N_SUDOKU      = 1000     # random Sudoku solution grids
N_LATIN       = 1000     # random non-Sudoku Latin squares (order 9)
N_M19_EQUIV   = 8        # Sudoku-symmetry equivalents of M19 (covariance control)
SEED          = 12345
BIG_COSET     = 12       # coset size >= BIG_COSET counts as "large"
CHECKPOINT_EVERY = 25    # save partial results every k grids
# ----------------------------------------

random.seed(SEED); np.random.seed(SEED)

try:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT = Path("/content/drive/MyDrive/m19_census")
except Exception:
    OUT = Path("./m19_census")
OUT.mkdir(parents=True, exist_ok=True)

PERMS = np.array(list(itertools.permutations(range(9))), dtype=np.int64)  # 362880 x 9, 0-based
NPERM = len(PERMS)

M19 = np.array([
 [2,6,3,8,1,5,4,7,9],[4,9,8,3,6,7,2,5,1],[7,5,1,4,9,2,3,6,8],
 [8,2,5,1,3,9,6,4,7],[6,4,7,5,2,8,1,9,3],[3,1,9,6,7,4,5,8,2],
 [5,7,4,2,8,1,9,3,6],[9,3,2,7,5,6,8,1,4],[1,8,6,9,4,3,7,2,5]], dtype=np.int64)

# ---------------- permutation utilities ----------------
IDENT = tuple(range(9))
COMPLEMENT = tuple(8 - i for i in range(9))            # v -> 10-v (0-based); always in K_L when Gamma_rank != []
def comp(p, q): return tuple(p[i] for i in q)          # (p o q)(i) = p[q[i]]
def inv(p):
    r = [0]*9
    for i, v in enumerate(p): r[v] = i
    return tuple(r)
def order(p):
    c, k = p, 1
    while c != IDENT: c = comp(p, c); k += 1
    return k

# ---------------- exact integer rank (fraction-free) ----------------
from fractions import Fraction
def exact_rank(mat):
    M = [[Fraction(int(x)) for x in row] for row in mat]
    rows, cols, pr = len(M), len(M[0]), 0
    for c in range(cols):
        piv = next((i for i in range(pr, rows) if M[i][c] != 0), None)
        if piv is None: continue
        M[pr], M[piv] = M[piv], M[pr]
        pv = M[pr][c]
        for i in range(rows):
            if i != pr and M[i][c] != 0:
                f = M[i][c]/pv
                M[i] = [M[i][k]-f*M[pr][k] for k in range(cols)]
        pr += 1
        if pr == rows: break
    return pr

# ---------------- rank-drop locus of the centered operator ----------------
def gamma_rank(L0):
    """L0 = grid-1 (0-based values). Returns list of rank-deficient relabelings (tuples)."""
    cand = []
    for s in range(0, NPERM, 30000):
        p = PERMS[s:s+30000]; P = p[:, L0]                       # (chunk,9,9)
        A = (P[:,:8,:8]-P[:,:8,8:9]-P[:,8:9,:8]+P[:,8:9,8:9]).astype(np.float64)
        for k in np.where(np.abs(np.linalg.det(A)) < 0.5)[0]:    # float pre-filter (exact for det=0)
            cand.append(s+int(k))
    out = []
    for i in cand:
        p = PERMS[i]; P = p[L0]
        A = (P[:8,:8]-P[:8,8:9]-P[8:9,:8]+P[8,8])
        if exact_rank(A) < 8: out.append(tuple(p.tolist()))
    return out

# ---------------- blind coset mining ----------------
def blind_mine(Grank):
    """pairwise-quotient histogram -> PLATEAU SCAN -> largest valid subgroup K_L.

    Fix (2026-07-05): the old single gap-detected threshold silently returned a
    non-closed set whenever the top plateau was noisy (large |Gamma_rank| with a
    residual tail). is_subgroup then failed and analyze_grid mislabeled the grid
    as Type-1 "no coset" -- even when a real stabilizer (down to the guaranteed
    complement <c>) existed at a lower level. We now scan EVERY frequency level
    and keep the largest {q : freq>=thr} that is an actual subgroup."""
    if len(Grank) < 2: return None
    left = Counter()
    for g in Grank:
        ig = inv(g)
        for h in Grank: left[comp(h, ig)] += 1
    best = None
    for thr in sorted(set(left.values()), reverse=True):
        K = frozenset(q for q, c in left.items() if c >= thr)
        if len(K) > 400: break                         # noise-dominated; no clean stabilizer past here
        if IDENT in K and is_subgroup(K) and (best is None or len(K) > len(best)):
            if largest_coset_in(Grank, K) == len(K):   # K must actually tile a full coset of Grank
                best = K                                # (rejects high-freq subgroups that don't stabilize Grank)
    return best

def is_subgroup(K):
    if IDENT not in K: return False
    for x in K:
        if inv(x) not in K: return False
    for a in K:
        for b in K:
            if comp(a, b) not in K: return False
    return True

def group_fingerprint(K):
    Ks = set(K)
    od = dict(sorted(Counter(order(h) for h in K).items()))
    ab = all(comp(a, b) == comp(b, a) for a in K for b in K)
    center = sum(1 for z in K if all(comp(z, a) == comp(a, z) for a in K))
    exponent = 1
    for o in od: exponent = exponent*o//math.gcd(exponent, o)
    return {"order": len(K), "order_dist": od, "abelian": ab,
            "center": center, "exponent": exponent}

def largest_coset_in(Grank, K):
    """Grank as a union of left K-cosets; return size of the most-represented coset."""
    Gs = set(Grank); Kl = list(K); seen = set(); best = 0
    for g in Grank:
        if g in seen: continue
        coset = {comp(k, g) for k in Kl}
        seen |= (coset & Gs)
        best = max(best, len(coset & Gs))
    return best

# ---------------- canonical grid-affine group G0 (universal for coset-72 grids) ----------------
# Bootstrapped once as the order-72 stabilizer of M19; used to place each K in the
# ladder <c> < D4 < G0  vs. outside G0 (the lat565-type exceptions).
G0 = blind_mine(gamma_rank(M19 - 1))
assert G0 is not None and len(G0) == 72, "G0 bootstrap failed"

def k_containment(K):
    return {"has_complement": COMPLEMENT in K, "in_G0": K <= G0, "equals_G0": K == G0}

# ---------------- generalized predicate mining ----------------
def bands():
    for k in range(3): yield ("row", k, [3*k, 3*k+1, 3*k+2])
    for k in range(3): yield ("col", k, [3*k, 3*k+1, 3*k+2])

def line_sums(gamma, L0, kind, idx):
    # gamma(value) 1-based = perm[value-1]+1 = gamma[L0]+1
    if kind == "row":
        return [sum(gamma[L0[i, j]]+1 for i in idx) for j in range(9)]
    else:
        return [sum(gamma[L0[i, j]]+1 for j in idx) for i in range(9)]

def predicate_mine(coset, L0):
    """Return list of (kind, band_index, sum) that hold with a single constant across the whole coset."""
    hits = []
    for kind, k, idx in bands():
        common = None; ok = True
        for g in coset:
            ls = line_sums(g, L0, kind, idx)
            if len(set(ls)) != 1: ok = False; break
            if common is None: common = ls[0]
            elif ls[0] != common: ok = False; break
        if ok and common is not None:
            hits.append((kind, k, common))
    return hits

# ---------------- one grid ----------------
def analyze_grid(grid, gid, tag):
    L0 = grid - 1
    t0 = time.time()
    Grank = gamma_rank(L0)
    rec = {"grid_id": gid, "tag": tag, "grid": grid.tolist(),
           "Gamma_rank_size": len(Grank)}
    if len(Grank) == 0:
        rec.update({"type": 0, "coset_size": 0, "group": None,
                    "predicates": [], "magic": False, "secs": round(time.time()-t0, 2)})
        return rec
    K = blind_mine(Grank)
    coset_size = 0; fp = None; preds = []; magic = False; best_c = None
    if K is not None and is_subgroup(K) and len(K) > 1:
        fp = group_fingerprint(K)
        coset_size = largest_coset_in(Grank, K)
        # recover the largest coset explicitly for predicate mining
        Gs = set(Grank); Kl = list(K); best = 0
        for g in Grank:
            coset = {comp(k, g) for k in Kl} & Gs
            if len(coset) > best: best, best_c = len(coset), coset
        preds = predicate_mine(best_c, L0) if best_c else []
        magic = any(s == 15 for (_, _, s) in preds)
    # classification
    large = coset_size >= BIG_COSET
    if not (K and fp and coset_size > 1):
        typ = 1                                   # rank-drop but no coset
    elif large and preds and magic:
        typ = 4                                   # M19-like
    elif large and (not preds or not magic):
        typ = 3                                   # large coset, no magic predicate
    else:
        typ = 2                                   # small coset
    rec.update({"type": typ, "coset_size": coset_size, "group": fp,
                "k_class": k_containment(K) if fp else None,
                "predicates": preds, "magic": magic, "secs": round(time.time()-t0, 2)})
    if typ >= 3:                                   # keep full structure for interesting grids
        rec["group_elements"] = [list(x) for x in sorted(K)]
        rec["coset_elements"] = [list(x) for x in sorted(best_c)] if best_c else []
    return rec

# ---------------- grid generators ----------------
def _fill(order_boxes):
    """Backtracking fill of a 9x9 with row/col (+box if order_boxes) constraints; random order."""
    grid = np.zeros((9, 9), dtype=np.int64)
    def box(i, j): return (i//3)*3 + j//3
    rowmask = [set() for _ in range(9)]
    colmask = [set() for _ in range(9)]
    boxmask = [set() for _ in range(9)]
    cells = [(i, j) for i in range(9) for j in range(9)]
    def bt(idx):
        if idx == 81: return True
        i, j = cells[idx]
        opts = list(range(1, 10)); random.shuffle(opts)
        for v in opts:
            if v in rowmask[i] or v in colmask[j]: continue
            if order_boxes and v in boxmask[box(i, j)]: continue
            grid[i, j] = v; rowmask[i].add(v); colmask[j].add(v); boxmask[box(i, j)].add(v)
            if bt(idx+1): return True
            grid[i, j] = 0; rowmask[i].discard(v); colmask[j].discard(v); boxmask[box(i, j)].discard(v)
        return False
    ok = bt(0)
    return grid if ok else None

def random_sudoku():
    for _ in range(50):
        g = _fill(True)
        if g is not None: return g
    raise RuntimeError("sudoku gen failed")

def is_sudoku(grid):
    for bi in range(3):
        for bj in range(3):
            blk = grid[3*bi:3*bi+3, 3*bj:3*bj+3].ravel()
            if len(set(blk.tolist())) != 9: return False
    return True

def random_latin_nonsudoku():
    for _ in range(200):
        g = _fill(False)
        if g is not None and not is_sudoku(g): return g
    raise RuntimeError("latin gen failed")

# Sudoku-preserving symmetries (for the M19 covariance control)
def sudoku_symmetry(grid):
    g = grid.copy()
    for bi in range(3):                                  # rows within band
        rows = [3*bi+r for r in np.random.permutation(3)]
        g[3*bi:3*bi+3, :] = g[rows, :]
    for bj in range(3):                                  # cols within stack
        cols = [3*bj+c for c in np.random.permutation(3)]
        g[:, 3*bj:3*bj+3] = g[:, cols]
    bp = np.random.permutation(3); g = np.vstack([g[3*b:3*b+3, :] for b in bp])
    sp = np.random.permutation(3); g = np.hstack([g[:, 3*s:3*s+3] for s in sp])
    if random.random() < 0.5: g = g.T
    relab = np.random.permutation(9) + 1                 # relabel symbols
    g = relab[g-1]
    return g

# ---------------- negative control ----------------
def negative_control(n_trials=20):
    worst = 0
    for _ in range(n_trials):
        R = [tuple(PERMS[i].tolist()) for i in random.sample(range(NPERM), 100)]
        K = blind_mine(R)
        if K is not None and is_subgroup(K):
            worst = max(worst, len(K) if len(K) > 1 else 0)
    return worst

# ---------------- driver ----------------
def run():
    t0 = time.time(); rows = []
    def checkpoint():
        with open(OUT/"census_rows.json", "w") as f: json.dump(rows, f)
        import csv
        with open(OUT/"census.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(
                ["grid_id","tag","type","Gamma_rank_size","coset_size","group_order",
                 "order_dist","abelian","center","in_G0","predicates","magic","secs"])
            for r in rows:
                g = r["group"] or {}; kc = r.get("k_class") or {}
                w.writerow([r["grid_id"], r["tag"], r["type"], r["Gamma_rank_size"],
                    r["coset_size"], g.get("order"), g.get("order_dist"), g.get("abelian"),
                    g.get("center"), kc.get("in_G0"), r["predicates"], r["magic"], r["secs"]])

    print("=== M19 positive control ===")
    r = analyze_grid(M19, "M19", "m19"); rows.append(r)
    print(f"  M19 -> Type {r['type']}, |Gamma_rank|={r['Gamma_rank_size']}, coset={r['coset_size']}, "
          f"magic={r['magic']}, preds={r['predicates']}")

    print(f"=== {N_M19_EQUIV} M19 Sudoku-equivalents (covariance control) ===")
    for e in range(N_M19_EQUIV):
        g = sudoku_symmetry(M19); r = analyze_grid(g, f"M19eq{e}", "m19_equiv"); rows.append(r)
        print(f"  eq{e}: Type {r['type']}, coset={r['coset_size']}, magic={r['magic']}")
        if (e+1) % CHECKPOINT_EVERY == 0: checkpoint()

    print(f"=== {N_SUDOKU} random Sudoku ===")
    for k in range(N_SUDOKU):
        g = random_sudoku(); r = analyze_grid(g, f"sud{k}", "sudoku"); rows.append(r)
        if (k+1) % 10 == 0:
            print(f"  sudoku {k+1}/{N_SUDOKU}  (last: Type {r['type']}, coset {r['coset_size']})")
        if (k+1) % CHECKPOINT_EVERY == 0: checkpoint()

    print(f"=== {N_LATIN} random non-Sudoku Latin ===")
    for k in range(N_LATIN):
        g = random_latin_nonsudoku(); r = analyze_grid(g, f"lat{k}", "latin"); rows.append(r)
        if (k+1) % 10 == 0:
            print(f"  latin {k+1}/{N_LATIN}  (last: Type {r['type']}, coset {r['coset_size']})")
        if (k+1) % CHECKPOINT_EVERY == 0: checkpoint()

    print("=== negative control (random 100-subsets) ===")
    nc = negative_control(); print(f"  worst spurious subgroup from random 100-subset: {nc} (expect 0)")

    checkpoint()
    # summary
    def summarize(tag):
        sub = [r for r in rows if r["tag"] == tag]
        types = Counter(r["type"] for r in sub)
        return {"n": len(sub), "type_dist": dict(sorted(types.items())),
                "type4_frac": round(types.get(4, 0)/max(len(sub), 1), 4)}
    summary = {"seed": SEED, "negative_control": nc,
               "sudoku": summarize("sudoku"), "latin": summarize("latin"),
               "m19_equiv": summarize("m19_equiv"),
               "elapsed_min": round((time.time()-t0)/60, 1)}
    with open(OUT/"census_summary.json", "w") as f: json.dump(summary, f, indent=2)
    print("\n=== SUMMARY ==="); print(json.dumps(summary, indent=2))
    print("Saved to", OUT)

if __name__ == "__main__":
    run()
