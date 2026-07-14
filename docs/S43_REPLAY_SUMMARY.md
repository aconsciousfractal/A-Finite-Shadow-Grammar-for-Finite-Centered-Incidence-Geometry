# Sanitized S43 Replay Summary

This is the historical, path-free summary of the single S43 replay of the exact raw S42 distribution. It does not certify later remediation or reviewer-preparation bytes. The current author-replay record is `docs/S44HR_AUTHOR_REPLAY_SUMMARY.md`.

## Recorded result

- Source surface: 109 files declared by `SHA256SUMS.txt`, copied with the manifest into an isolated directory without `.git`.
- Historical S42 manifest SHA-256: `0E2E47BD05EE26AEDF7AA5FA540A94806BFAC9E8B8F3F5D70ACFC948DD90C5EA`.
- Verifier invocations: exactly one.
- Command: `python -B scripts/verify.py --timeout 600`.
- Runtime: 973.905 seconds.
- Exit code: 0.
- Envelope status: `PASS_PUBLIC_REPLAY_ENVELOPE`, mode `replay`.
- Quantitative routes: 12/12 PASS.
- Route subprocesses: 12/12 exit zero.
- Artifact semantics: 12/12 PASS.
- Route checks: 60/60 PASS.
- Optional full X05 census: not run.
- X13: human proof and classical source lock; no numerical replay.

The private raw S43 envelope has SHA-256 `76F1062442064076A150700C1195C02861217F49BF9BF84F5E6FF2721375290A`. It is not distributed because captured stdout includes the temporary replay path.

## Historical post-run delta

The raw S42 X15 route changed only its artifact mode from `frozen_result_audit` to `independent_recompute`; eleven other route-artifact hashes were unchanged. S44 correctly treated this as a repeatability defect. The later remediation moved X15 output to verifier-owned ignored storage and made distributed artifacts immutable.

## Superseding gate state

S44 found blocking release defects in the raw candidate. Those defects were remediated, and commit `a3cfafe` subsequently passed the S44H-R author replay from a true Git clone: 12/12 routes, 86/86 route checks, and 156/156 route-contract checks. The public origin is now an untagged external-review candidate. Independent external replay of the exact reviewer-preparation commit remains S46; no tag, release, DOI, or arXiv deposit is claimed.
