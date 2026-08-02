# Reproducibility Record

## Independent bounded replay

On 2026-07-14, an independent replay from a fresh public clone of commit `16be346502e754bd6282adb5216599bed26ab8d6` completed successfully:

- 12/12 quantitative routes passed;
- 86/86 route checks passed;
- 156/156 route-contract checks passed;
- 12/12 distributed route artifacts remained byte-identical;
- all subprocesses exited successfully;
- the package manifest and outer checksum passed before and after execution.

The replay identified documentation and source-attribution issues but no mathematical or quantitative-replay failure. Those editorial issues were subsequently corrected.

## Current-package verification

The current package is validated against its regenerated checksum layer with:

```powershell
python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
python -B scripts/verify.py --static-only --out ../finite_shadow_static_review.json
python -B tests/test_verify_fail_closed.py -v
```

The authoritative PDF and manifest hashes are stored in `RELEASE_SHA256.txt`. This record intentionally does not duplicate mutable byte counts or hashes.

Historical development-stage reports remain available through Git history but are not part of the current reader-facing documentation.
