# Reviewer Guide

> Candidate status: the exact raw S42 distribution passed one S43 fresh-copy replay. S44 then identified blocking release defects. The current worktree is an S44 remediation candidate; S44H verification and S45 owner publication remain pending.

## Inspect first

```text
paper/main.tex
paper/sections/02_finite_shadow_grammar.tex
paper/sections/03_fingerprint_channel.tex
paper/sections/03b_modular_centered_channels.tex
paper/sections/04_type_a_source_rows.tex
paper/sections/05_signed_type_bc_source_rows.tex
paper/sections/06_dihedral_vertex_shadows.tex
paper/sections/07_g2_length_colored_root_shadow.tex
paper/sections/08_f4_projective_root_shadow.tex
paper/sections/09_h3_projective_source_channel.tex
paper/sections/10_h4_projective_source_channel.tex
paper/sections/11_d5_projective_root_shadow_control.tex
paper/sections/12_e6_projective_root_shadow_control.tex
paper/sections/13_e7_projective_root_shadow_control.tex
paper/sections/14_e8_projective_root_shadow_subsystem_separator.tex
paper/sections/15_abd_grammar_contrast.tex
paper/sections/16_value_and_limits_of_phi.tex
paper/sections/17_boundaries_and_future_routes.tex
paper/appendices/A_source_instance_manifest.tex
docs/CLAIM_BOUNDARY.md
docs/SOURCE_LOCK.md
docs/SOURCE_LOCK_CROSSWALK.md
docs/CLAIM_LEDGER.md
docs/S43_REPLAY_SUMMARY.md
artifacts/source_instance_manifest.json
artifacts/public_evidence_routes.json
```

The core row is `S=(N,X,I,rho,Phi)`. The X-ID is a family/source label, while a concrete instance has its own ambient degree `N`. Admitted concrete rows are governed by the typed source-lock schema and its schema-to-surface routing crosswalk; this package does not claim one consolidated `L(S)` object for every row. The wrapper is metadata, not a sixth slot or universal object category.

## Verification posture

The sanitized S43 summary records one replay of the exact raw S42 bytes: 12/12 quantitative routes, 12/12 zero subprocess exits, 12/12 passing artifacts, and 60/60 route checks in 973.905 seconds. It is historical evidence, not certification of the changed remediation worktree.

After the S44 remediation bytes and checksum layers are final, S44H must verify a Git-normalized clone. The bounded command surface is:

```powershell
python -m pip install -r requirements.txt
python -B scripts/verify.py --static-only
python -B scripts/verify.py
```

Do not treat those commands or the historical S43 result as publication authorization. The optional `scripts/x05_m19_census_full_regeneration.py` route is outside the bounded verifier.

## Review boundaries

- H4 wording must describe the same 60 projective points, equivalently 60 antipodal pairs of H4 roots.
- The canonical registry types `admission` separately from `pointer_status`.
- X10 is owned by P07/P33; X11 is a version-neutral future P18 pointer; X12 is a future P17 pointer and is not admitted.
- X13 is public human-proof/classical-source-lock evidence; X15, X19, and X20 have public bounded routes.
- X15 is the bounded P14 replay. P15 owns the separate signed-reversal theorem represented by X17; P13 imports no proof.
- `G-004/CPL-001` records the S36/S37 classical guardrail with no new X-ID, numerical replay, novelty claim, or imported descent/transfer theorem.
- P28, P29, P30, P32, and P33 remain companion pointers and do not become P13 theorem claims.
- `Phi` is descriptive only: no classifier, tiling oracle, or completeness claim follows.

The next verification gate is S44H. S45 remains the explicit owner decision; publication is not authorized.
