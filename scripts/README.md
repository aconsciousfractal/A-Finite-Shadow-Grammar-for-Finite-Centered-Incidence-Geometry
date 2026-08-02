# Verification Scripts

This directory contains the fail-closed package verifier and the bounded evidence routes used by the paper.

`verify.py` validates `SHA256SUMS.txt`, `RELEASE_SHA256.txt`, exact tracked-file coverage, route-registry structure, required inputs, and artifact semantics before any subprocess is executed. In full mode it runs the twelve declared routes and repeats the integrity checks afterward.

Short review:

```powershell
python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
python -B scripts/verify.py --static-only --out ../finite_shadow_static_review.json
```

Full bounded replay:

```powershell
python -B scripts/verify.py --timeout 600 --out ../finite_shadow_full_review.json
```

The quantitative route registry is `artifacts/public_evidence_routes.json`. Exact helpers, seeds, selected source files, certificates, and bounded arguments are declared there.

The Type-A checker is read-only and separate from the twelve quantitative routes. Proof-only statements and classical source attributions are reviewed in the manuscript rather than converted into synthetic numerical routes.
