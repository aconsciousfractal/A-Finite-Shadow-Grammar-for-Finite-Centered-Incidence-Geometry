# Scripts

This directory contains the bounded verifier and public evidence scripts. The exact raw S42 surface passed the single S43 replay, but S44 found verifier and repeatability defects. The current scripts are an S44 remediation candidate and have not yet passed S44H.

## Verifier contract

`verify.py` is required to validate `SHA256SUMS.txt`, `RELEASE_SHA256.txt`, and exact package coverage before route loading or execution, reject escaping registry paths/arguments, require exactly the twelve quantitative IDs, execute routes unless `--static-only` is used, and reject artifacts without explicit passing semantics.

```powershell
python -B scripts/verify.py --static-only
python -B scripts/verify.py --timeout 600
```

The first command is the short preflight. The second is the full bounded verifier and must not be run for S44H until the Git-normalized file set, final manifest, and outer checksum are sealed. Neither command authorizes S45 or publication.

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

Exact helpers, seeds, selected source files, certificates, bounded arguments, and support artifacts are declared in `artifacts/public_evidence_routes.json`. X15 recompute output must be verifier-owned/ignored so a run does not mutate a manifest-pinned distributed artifact.

## Noncomputational rows

- X13 uses the public manuscript proof and classical source lock; it is not a thirteenth replay.
- G-004/CPL-001 uses human proof and classical sources for the retained S36/S37 guardrail; it has no numerical replay, novelty claim, new X-ID, or imported descent/transfer theorem.

## Optional X05 regeneration

`x05_m19_census_full_regeneration.py` regenerates the full X05 census, uses NumPy, takes about 26 minutes in the reference environment, and writes `m19_census/`. It is not called by the default verifier and was excluded from S43.

These scripts are bounded evidence payloads. They are not general modular-representation, Coxeter/Weyl, root-system-matroid, classifier, tiling, source-coupling, or descent engines.
