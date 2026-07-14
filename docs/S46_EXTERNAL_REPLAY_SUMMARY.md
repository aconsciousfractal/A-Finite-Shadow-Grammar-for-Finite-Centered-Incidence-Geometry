# S46 Independent External Replay and Red-Team Summary

Date: 2026-07-14
Reviewed commit: `16be346502e754bd6282adb5216599bed26ab8d6`
Reviewed tree: `6fc2671f4b4c4d16ce4c51fb949da70840355aee`
S46 verdict: `MATHEMATICS_AND_REPLAY_HOLD__BOUNDED_SOURCE_GOVERNANCE_FIXES_REQUIRED`

## Independent replay

The exact public commit was cloned from the public remote into a new directory
and reviewed without modifying the source repository. Exactly one full bounded
verifier invocation was made.

- status: `PASS_PUBLIC_REPLAY_ENVELOPE`;
- runtime: 1256.112 seconds;
- routes: 12/12 declared, evaluated, invoked, and passed;
- route checks: 86/86;
- route-contract checks: 156/156;
- subprocess exits: 12/12 zero;
- semantic artifacts: 12/12 PASS;
- distributed route artifacts: 12/12 byte-immutable;
- manifest: 113/113 preflight and postflight;
- release checksum: 2/2 preflight and postflight;
- verifier-owned X15 runtime artifact: created, validated, and cleaned;
- external envelope SHA-256:
  `BB946A10C5264C30B9D64051AF8266F7C4CA3DED9D251E415C272FE59B22DDFD`.

The fail-closed sentinel suite passed 15/15 and all 34 Python files in the
reviewed commit parsed successfully. The canonical 35-page PDF at the reviewed
commit rebuilt byte-for-byte with SHA-256
`36DA47522259F31924A4B679275901235E4842CB6139D2B8A01B94F7B635C26F`.

## Red-team findings and S46H resolutions

1. The X15 all-`n` mirror-union proposition was outside the six-row numerical
   evidence boundary. S46H separates X15-001 (six-row replay) from X15-002
   (P13-owned self-contained elementary proof with P14 provenance).
2. The public package referred to a normative source-lock schema without
   distributing it. S46H publishes `docs/SOURCE_LOCK_SCHEMA.md` and aligns the
   manuscript with its distributed-record semantics.
3. X13 quoted Type-A rank-mass and Smith values without a public lattice/value
   certificate. S46H adds the manifest-pinned certificate and a read-only exact
   checker, while retaining exactly twelve quantitative routes.
4. The Latin companion citation pointed to the nonexistent
   `v1.0-submission` ref. S46H pins public commit
   `8984359d0f7fd66e4eaa7864a557d6b907e9f9ec`.
5. X10 nonimport wording conflicted across governance files. S46H fixes one
   controlling statement: P13 cites bounded P07/P33 results as context, imports
   neither theorem nor proof, and makes no all-`n` tiling claim.

## S46H bounded-replay inheritance

The S46H repair does not modify the existing verifier, fail-closed tests,
requirements, twelve-route registry, twelve route scripts, declared route
support files, or distributed route artifacts. The 75-file protected S46
quantitative surface has aggregate SHA-256
`D34456D1330F3B0A27BD47920679088803ECCFAC8E9DB37C40A6BC3546459C0E`.
The exact allowlist and LF/UTF-8 aggregation recipe are public in
`docs/PROTECTED_QUANTITATIVE_SURFACE.md`.
The only new executable is the read-only X13 static-certificate checker; it is
not registered as a quantitative route and writes no files.

The post-fix paper rebuild is 36 pages and 682382 bytes, with SHA-256
`545F206E9358047AC80CC3F27EEC243E5F40EE01067C6BCCB79398D93059C8E7`.
S46H short-gate verification is recorded by the package checksum layer and the
private closeout certificate. No tag, GitHub Release, DOI, arXiv deposit, or
formal release follows automatically from this review.
