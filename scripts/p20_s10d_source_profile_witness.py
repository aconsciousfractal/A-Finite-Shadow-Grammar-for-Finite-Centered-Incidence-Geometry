#!/usr/bin/env python3
"""P20-S10D ambient-conjugacy versus source-profile replay.

This replay is intentionally small.  It certifies the P20 instance of the general
lemma: two rows can be conjugate in the uncolored ambient symmetric group while
having different source-aware profiles.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

N = 12
SHORT = tuple(range(6))
LONG = tuple(range(6, 12))


def label(i: int) -> str:
    return f"S{i}" if i < 6 else f"L{i-6}"


def tau(a: int) -> tuple[int, ...]:
    p = [0] * N
    for i in range(6):
        p[i] = (a - i) % 6
        p[6 + i] = 6 + ((a - i - 1) % 6)
    return tuple(p)


def h_perm() -> tuple[int, ...]:
    p = [0] * N
    for i in range(6):
        p[i] = 6 + i          # h(S_i)=L_i
        p[6 + i] = (i + 1) % 6 # h(L_i)=S_{i+1}
    return tuple(p)


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(p[q[i]] for i in range(N))


def inv(p: tuple[int, ...]) -> tuple[int, ...]:
    q = [0] * N
    for i, v in enumerate(p):
        q[v] = i
    return tuple(q)


def conj(h: tuple[int, ...], p: tuple[int, ...]) -> tuple[int, ...]:
    return compose(compose(h, p), inv(h))


def cycle_type(p: tuple[int, ...]) -> tuple[int, ...]:
    seen = [False] * N
    lengths = []
    for i in range(N):
        if seen[i]:
            continue
        j = i
        l = 0
        while not seen[j]:
            seen[j] = True
            l += 1
            j = p[j]
        lengths.append(l)
    return tuple(sorted(lengths, reverse=True))


def fixed_profile(p: tuple[int, ...]) -> tuple[int, int]:
    return (
        sum(1 for i in SHORT if p[i] == i),
        sum(1 for i in LONG if p[i] == i),
    )


def multiset(items):
    d = {}
    for x in items:
        key = str(x)
        d[key] = d.get(key, 0) + 1
    return dict(sorted(d.items()))


def row_profile(row: set[tuple[int, ...]]) -> dict:
    return {
        "cycle_type_histogram": multiset(cycle_type(p) for p in row),
        "source_fixed_profile_histogram": multiset(fixed_profile(p) for p in row),
        "aggregate_fixed_short": sum(fixed_profile(p)[0] for p in row),
        "aggregate_fixed_long": sum(fixed_profile(p)[1] for p in row),
    }


def main() -> None:
    h = h_perm()
    taus = {a: tau(a) for a in range(6)}
    f_short = {taus[0], taus[2], taus[4]}
    f_long = {taus[1], taus[3], taus[5]}
    conj_table = {f"tau_{a}": f"tau_{(a+1)%6}" for a in range(6)}
    conj_images = {conj(h, taus[a]) for a in range(6)}
    row_image = {conj(h, p) for p in f_short}

    short_prof = row_profile(f_short)
    long_prof = row_profile(f_long)
    h_swaps_source_blocks = all(h[i] in LONG for i in SHORT) and all(h[i] in SHORT for i in LONG)
    h_is_source_preserving = all(h[i] in SHORT for i in SHORT) and all(h[i] in LONG for i in LONG)

    checks = {
        "h_swaps_source_blocks": h_swaps_source_blocks,
        "h_is_not_source_preserving": not h_is_source_preserving,
        "all_reflections_conjugated_to_reflections": conj_images == set(taus.values()),
        "h_F_short_h_inverse_equals_F_long": row_image == f_long,
        "ordinary_cycle_histograms_equal": short_prof["cycle_type_histogram"] == long_prof["cycle_type_histogram"],
        "source_profiles_differ": short_prof["source_fixed_profile_histogram"] != long_prof["source_fixed_profile_histogram"],
        "aggregate_source_profiles_differ": (short_prof["aggregate_fixed_short"], short_prof["aggregate_fixed_long"]) != (long_prof["aggregate_fixed_short"], long_prof["aggregate_fixed_long"]),
    }

    result = {
        "project": "P20_g2_hexagonal_weyl_shadows",
        "gate": "P20-S10D",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "conjugator": {
            "definition": "h(S_i)=L_i, h(L_i)=S_{i+1}",
            "label_map": {label(i): label(h[i]) for i in range(N)},
            "swaps_source_blocks": h_swaps_source_blocks,
            "is_source_preserving": h_is_source_preserving,
        },
        "conjugacy_table": conj_table,
        "rows": {
            "F_short_axis": short_prof,
            "F_long_axis": long_prof,
        },
        "checks": checks,
        "lemma_message": "Ambient conjugacy can preserve ordinary uncolored invariants while source-aware profiles distinguish rows.",
        "boundary": "Finite source-profile lemma only; no classifier, tiling, or general Weyl claim.",
        "next_gate": "P20-S10E projective quotient value test",
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "p20_s10d_source_profile_witness.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    lines = [
        "# P20-S10D Source-Profile Witness Summary",
        "",
        f"Status: {result['status']}",
        "",
        "## Checks",
        "",
        "| Check | Value |",
        "|---|---:|",
    ]
    for k, v in checks.items():
        lines.append(f"| `{k}` | {str(v).lower()} |")
    lines += [
        "",
        "## Profiles",
        "",
        "| Row | cycle histogram | source fixed profile | aggregate fixed short | aggregate fixed long |",
        "|---|---|---|---:|---:|",
        f"| `F_short_axis` | `{short_prof['cycle_type_histogram']}` | `{short_prof['source_fixed_profile_histogram']}` | {short_prof['aggregate_fixed_short']} | {short_prof['aggregate_fixed_long']} |",
        f"| `F_long_axis` | `{long_prof['cycle_type_histogram']}` | `{long_prof['source_fixed_profile_histogram']}` | {long_prof['aggregate_fixed_short']} | {long_prof['aggregate_fixed_long']} |",
        "",
        "Boundary: finite source-profile lemma only; no classifier, tiling, or general Weyl claim.",
        "",
        "Prossima task: P20-S10E projective quotient value test.",
    ]
    (RESULTS / "p20_s10d_source_profile_witness_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()