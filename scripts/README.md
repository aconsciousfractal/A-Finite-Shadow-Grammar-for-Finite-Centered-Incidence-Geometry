# Scripts

This directory contains the bounded verifier and public evidence scripts. Commit `16be346502e754bd6282adb5216599bed26ab8d6` passed one independent S46 replay from a fresh public clone. S46H leaves the twelve quantitative route scripts, route registry, and distributed route artifacts byte-identical and adds only the read-only X13 static-certificate checker.

## Verifier contract

`verify.py` validates `SHA256SUMS.txt`, `RELEASE_SHA256.txt`, and exact package coverage before route loading or execution; rejects escaping registry paths and arguments; requires exactly the twelve quantitative IDs; executes routes unless `--static-only` is used; validates explicit artifact semantics; and requires distributed artifacts and checksum layers to remain byte-immutable.

```powershell
python -B scripts/verify.py --static-only --out ../p13_static_review.json
python -B scripts/verify.py --timeout 600 --out ../p13_full_review.json
```

The first command is the standard-library-only short preflight and invokes zero quantitative routes. The second is the full bounded verifier intended for a fresh clone of the exact review commit. Expected full counts are 12/12 routes, 86/86 route checks, and 156/156 route-contract checks. X15 must prepare, validate, and clean its verifier-owned runtime artifact; `artifacts/.verify` must be absent afterward. Neither command authorizes a tag, release, DOI, arXiv deposit, or claim promotion.

## Quantitative routes

```text
x05_m19_lat565_evidence_check.py        X05 frozen M19/lat565 evidence audit
signed_type_bc_shadow_replay.py         X15 signed Type-B/C bounded recompute
modular_centered_channel_replay.py      X16 modular centered-channel replay
dihedral_vertex_shadow_replay.py        X18 dihedral vertex-shadow replay
g2_source_channel_replay.py             X19 G2 source-channel replay
f4_source_layer_replay.py               X20 F4 source-layer replay
h3_projective_source_channel_replay.py  X21 projective H3 source-channel replay
h4_projective_source_channel_replay.py  X22 projective H4 source-channel replay
d5_projective_source_channel_replay.py  X23 projective D5 source-channel replay
e6_projective_source_channel_replay.py  X24 projective E6 source-channel replay
e7_projective_source_channel_replay.py  X25 projective E7 source-channel replay
e8_projective_source_channel_replay.py  X26 projective E8 source-channel replay
```

Exact helpers, seeds, selected source files, certificates, bounded arguments, and support artifacts are declared in `artifacts/public_evidence_routes.json`. X15 recompute output is verifier-owned and ignored so a run cannot mutate a manifest-pinned distributed artifact.

## Static and human-proof rows outside the route count

- X13 uses the public proof, classical source lock, manifest-pinned certificate, and `x13_type_a_lattice_rank_mass_certificate_check.py`. The checker is read-only and is not a thirteenth route.
- X15-002 is the self-contained mirror-union human proof; X15-001 remains the six-row quantitative route.
- `G-004/CPL-001` uses human proof and classical sources for the retained S36/S37 guardrail; it has no numerical replay, novelty claim, new X-ID, or imported descent/transfer theorem.

## Optional X05 regeneration

`x05_m19_census_full_regeneration.py` regenerates the full X05 census, uses NumPy, takes about 26 minutes in the reference environment, and writes `m19_census/`. It is not called by the default verifier.

These scripts are bounded evidence payloads. They are not general modular-representation, Coxeter/Weyl, root-system-matroid, classifier, tiling, source-coupling, or descent engines.
