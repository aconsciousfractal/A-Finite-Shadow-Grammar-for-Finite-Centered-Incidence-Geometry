# Reviewer Guide

## Review status

Evidence status (2026-07-14): exact public commit
`16be346502e754bd6282adb5216599bed26ab8d6` passed one independent S46 replay
from a new public clone in 1256.112 seconds: 12/12 routes, 86/86 route checks,
156/156 route-contract checks, all distributed route artifacts immutable,
manifest 113/113 and outer checksum 2/2 pre/post. The external envelope
SHA-256 is
`BB946A10C5264C30B9D64051AF8266F7C4CA3DED9D251E415C272FE59B22DDFD`.

S46 found five bounded source/governance defects but no mathematical or replay
failure. S46H closes them by publishing the normative schema, adding the X13
static certificate/checker, giving a complete X15-002 proof, repairing the
Latin source pin, and unifying X10 nonimport wording. The existing verifier,
route registry, quantitative route scripts, support files, and distributed
route artifacts remain byte-identical. No tag, GitHub Release, DOI, arXiv
deposit, or formal release is claimed.

## Ten-minute path

1. Record the exact target and cleanliness:

   ```powershell
   git rev-parse HEAD
   git status --short
   ```

2. Read:

   ```text
   paper/abstract.tex
   paper/sections/02_finite_shadow_grammar.tex
   paper/sections/03_fingerprint_channel.tex
   paper/sections/04_type_a_source_rows.tex
   paper/sections/05_signed_type_bc_source_rows.tex
   paper/sections/16_value_and_limits_of_phi.tex
   paper/sections/17_boundaries_and_future_routes.tex
   docs/SOURCE_LOCK_SCHEMA.md
   docs/SOURCE_LOCK_CROSSWALK.md
   docs/CLAIM_BOUNDARY.md
   docs/CLAIM_LEDGER.md
   docs/S46_EXTERNAL_REPLAY_SUMMARY.md
   ```

3. Inspect `artifacts/source_instance_manifest.json`,
   `artifacts/public_evidence_routes.json`, and the X13 static certificate.
   Check the independent `admission`/`pointer_status` typing and the exact
   twelve-route surface.

4. Run the X13 checker and standard-library-only static gate:

   ```powershell
   python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
   python -B scripts/verify.py --static-only --out ../p13_static_review.json
   ```

5. Expected: X13 `61/61`; static exit 0; schema 3;
   `PASS_PUBLIC_REPLAY_ENVELOPE`; `mode=static_only`; 12 declared, required,
   and evaluated routes; zero invoked routes; manifest 118/118; outer checksum
   2/2; every global check true. A final `git status --short` should print
   nothing in a committed clone.

## Optional full replay path

The S46 independent replay already exercised the unchanged quantitative
surface. A second replay is not required for the bounded S46H delta, but a
reviewer may run it once from a fresh clone:

```powershell
python -m pip install -r requirements.txt
python -B scripts/verify.py --static-only --out ../p13_static_review.json
python -B scripts/verify.py --timeout 600 --out ../p13_full_review.json
```

`--timeout 600` is a per-route timeout. Expected full counts remain 12/12
routes, 86/86 route checks, 156/156 route-contract checks, 12/12 immutable
distributed artifacts, manifest 118/118 pre/post, and outer checksum 2/2.
Afterward `Test-Path artifacts/.verify` must be `False` and `git status
--short` must be empty.

The canonical S46H PDF is 36 pages, 682382 bytes, SHA-256
`545F206E9358047AC80CC3F27EEC243E5F40EE01067C6BCCB79398D93059C8E7`.

## Claim-to-artifact map

| Layer | Main public artifacts | Review path | Current status |
|---|---|---|---|
| Interface and bounded mathematical prose | title PDF; sections 02--05, 16, 17 | human mathematical review | bounded claims only |
| Normative source lock | `docs/SOURCE_LOCK_SCHEMA.md`; crosswalk; canonical registry | type and locus audit | public distributed-record schema |
| Public boundary and claim status | claim boundary and ledger | compare wording, scope, and ownership | S46H aligned |
| Executable contract | route registry and `scripts/verify.py` | static/full verifier | independent S46 PASS on `16be346` |
| Quantitative evidence | X05, X15-001, X16, X18--X26 route artifacts | full bounded verifier | independent S46 PASS |
| Static/human evidence | X13 certificate/checker; X15-002 proof; G-004/CPL-001 proof/sources | short exact check and human proof audit | outside twelve-route count |
| Integrity | `SHA256SUMS.txt`; `RELEASE_SHA256.txt` | static gate or independent SHA-256 | S46H bytes covered |

## Review boundaries

- The core row is `S=(N,X,I,rho,Phi)`; source-lock metadata is not a sixth slot.
- X10 is P07/P33 context only: neither theorem nor proof is imported and no
  all-`n` tiling claim is made.
- X15-001 is the six-row replay; X15-002 is the self-contained P13 proof; P15
  owns the separate signed-reversal theorem.
- X11 and X12 remain nonadmitted future pointers. P28, P29, P30, P32, and P33
  remain companion-owned.
- `Phi` is descriptive only: it is not a classifier, tiling oracle, complete
  invariant, or decision certificate.

## Known limits

- The S46 replay binds exact commit `16be346`; S46H inherits it only because
  the protected quantitative surface is byte-identical and the delta passes
  the short gates. The exact 75-path allowlist and digest recipe are in
  `docs/PROTECTED_QUANTITATIVE_SURFACE.md`.
- Optional full X05 census regeneration takes about 26 minutes and is excluded
  from the bounded verifier.
- The X13 checker is a static certificate check, not a thirteenth route.
- There is no tag, GitHub Release, DOI, arXiv deposit, or formal release.
