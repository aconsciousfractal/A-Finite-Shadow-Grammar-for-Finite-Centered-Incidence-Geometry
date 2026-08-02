# Independent Review Guide

This guide separates mathematical review, source review, and executable verification. Historical development labels are intentionally excluded: reviewers should evaluate the current committed package.

## Ten-minute review

1. Record the exact commit and confirm that the checkout is clean.

   ```powershell
   git rev-parse HEAD
   git status --short
   ```

2. Read the paper abstract and the sections defining the grammar, fingerprint channel, worked rows, limits, and future boundaries.

3. Compare the manuscript with:

   ```text
   docs/SOURCE_LOCK_SCHEMA.md
   docs/SOURCE_LOCK_CROSSWALK.md
   docs/CLAIM_BOUNDARY.md
   docs/CLAIM_LEDGER.md
   artifacts/source_instance_manifest.json
   artifacts/public_evidence_routes.json
   ```

4. Run the read-only Type-A certificate check and the static package verifier.

   ```powershell
   python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
   python -B scripts/verify.py --static-only --out ../finite_shadow_static_review.json
   ```

5. Expected result:

   ```text
   Type-A certificate: 61/61 checks pass
   Package status: PASS_PUBLIC_REPLAY_ENVELOPE
   Quantitative routes: 12 declared and 12 evaluated
   Quantitative subprocesses invoked in static mode: 0
   Manifest and release checksums: pass
   ```

The current PDF size and SHA-256 are recorded only in `RELEASE_SHA256.txt`, which is the authoritative public checksum record.

## Optional bounded replay

Install the pinned Python dependencies and invoke all twelve quantitative routes:

```powershell
python -m pip install -r requirements.txt
python -B scripts/verify.py --timeout 600 --out ../finite_shadow_full_review.json
```

The timeout is applied separately to each route. The full replay should leave distributed artifacts unchanged and should not leave an `artifacts/.verify` directory.

## Claim-to-evidence map

| Layer | Public evidence | Review method |
|---|---|---|
| Five-slot interface and mathematical claims | paper PDF and LaTeX source | mathematical review |
| Provenance and interpretation | source-lock schema, crosswalk, and instance registry | source and ownership audit |
| Quantitative rows | route registry, scripts, results, and artifacts | static verification or full bounded replay |
| Type-A exact values | manuscript proof, exact certificate, and 61-check script | read-only exact check |
| Integrity | `SHA256SUMS.txt` and `RELEASE_SHA256.txt` | independent SHA-256 comparison |

## Review boundaries

- `S=(N,X,I,rho,Phi)` is the mathematical core. Provenance metadata is not a sixth slot.
- `Phi` is descriptive and source-bounded; it is not a classifier, complete invariant, tiling oracle, or decision certificate.
- Companion papers retain ownership of their own theorems. Citation does not import a theorem or proof into this paper.
- The centered-rank census and every root-shadow computation are bounded finite exhibits, not family-wide classification results.
- The quotient and coupling discussion uses classical mechanisms and makes no novelty claim for quotient existence, spectral inheritance, or interlacing.
