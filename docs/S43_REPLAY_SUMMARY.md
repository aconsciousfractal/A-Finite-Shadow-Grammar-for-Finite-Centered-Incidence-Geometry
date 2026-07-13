# Sanitized S43 Replay Summary

This is a public, path-free summary of the single S43 replay of the exact raw
S42 distribution.  It does not certify the later S44 remediation bytes.

## Recorded result

- Source surface: 109 files declared by `SHA256SUMS.txt`, copied with the
  manifest into an isolated directory without `.git`.
- Historical S42 manifest SHA-256:
  `0E2E47BD05EE26AEDF7AA5FA540A94806BFAC9E8B8F3F5D70ACFC948DD90C5EA`.
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

The private raw envelope has SHA-256
`76F1062442064076A150700C1195C02861217F49BF9BF84F5E6FF2721375290A`.
It is not distributed here because captured stdout includes the temporary
replay path.

## Historical post-run delta

The raw S42 X15 route changed only its artifact mode from
`frozen_result_audit` to `independent_recompute`; eleven other route-artifact
hashes were unchanged and no unexpected distributed delta occurred.  S44
identified this as a repeatability defect and required an immutable-output
repair.  That repair belongs to the S44 remediation candidate and does not
retroactively invalidate the bounded mathematical result recorded above.

## Gate boundary

S44 found blocking release defects in the raw candidate.  The current
worktree is being remediated and still requires S44H verification from final
Git-normalized bytes.  S45 remains an explicit owner decision.  This summary
does not authorize release or publication.
