# Reviewer Guide

## Review status

Evidence status (2026-07-14): commit `a3cfafe3a3bb244ce9a293173a963e3cf6929a68` was checked by the authoring workflow in one complete replay from a new true Git clone. It passed 12/12 routes in 783.885 seconds, with 86/86 route checks, 156/156 route-contract checks, all distributed artifacts immutable, manifest 112/112 and outer checksum 2/2 identical pre/post. This is an author-operated replay, not independent external reproduction.

That certificate binds exactly commit `a3cfafe3a3bb244ce9a293173a963e3cf6929a68` and tree `9acf53f8f5068872e0a0273139efac87dee224f2`. The later reviewer-navigation/checksum commit is a new review target and is not covered by that full replay. It is labelled reviewer-ready only after its short gates pass.

The public origin is available on `master`. S45 scoped review preparation is complete; S46 independent external red team is next. No tag, GitHub Release, DOI, arXiv deposit, formal release, or independent external reproduction is claimed.

## Ten-minute path

1. Record the exact target and cleanliness:

   ```powershell
   git rev-parse HEAD
   git status --short
   ```

   The second command should print nothing. No tag exists, so `master` alone is not a stable review identifier.

2. Read:

   ```text
   paper/abstract.tex
   paper/sections/02_finite_shadow_grammar.tex
   paper/sections/03_fingerprint_channel.tex
   paper/sections/03b_modular_centered_channels.tex
   paper/sections/16_value_and_limits_of_phi.tex
   paper/sections/17_boundaries_and_future_routes.tex
   docs/CLAIM_BOUNDARY.md
   docs/CLAIM_LEDGER.md
   docs/S44HR_AUTHOR_REPLAY_SUMMARY.md
   ```

3. Inspect `artifacts/source_instance_manifest.json` and `artifacts/public_evidence_routes.json`. Check the independent `admission`/`pointer_status` typing and the exact twelve-route surface.

4. Run the standard-library-only static gate from the repository root:

   ```powershell
   python -B scripts/verify.py --static-only --out ../p13_static_review.json
   ```

5. Expected: exit 0; schema 3; `PASS_PUBLIC_REPLAY_ENVELOPE`; `mode=static_only`; 12 declared, required, and evaluated routes; zero invoked routes; manifest 113/113; outer checksum 2/2; every global check true. A final `git status --short` should still print nothing.

## Thirty-minute replay path

The reference author replay took 783.885 seconds. The thirty-minute estimate excludes first-time network installation and TeX provisioning.

1. Clone the exact review commit into a new directory. Record the commit, clean status, Python, SymPy, and NumPy versions. Python 3.11 or newer is required.

2. Install and preflight:

   ```powershell
   python -m pip install -r requirements.txt
   python -B scripts/verify.py --static-only --out ../p13_static_review.json
   ```

3. Run the bounded verifier once:

   ```powershell
   python -B scripts/verify.py --timeout 600 --out ../p13_full_review.json
   ```

4. Expected: exit 0; schema-3 replay PASS; 12/12 declared, required, evaluated, invoked, and passed routes; 12/12 zero subprocess exits; 12/12 semantic artifacts; 12/12 distributed artifacts immutable; 86/86 route checks; 156/156 route-contract checks; manifest 113/113 and outer checksum 2/2 identical pre/post; X15 runtime output prepared, validated, and cleaned.

5. Check cleanup and retain the envelope outside the repository:

   ```powershell
   Test-Path artifacts/.verify
   git status --short
   Get-FileHash ../p13_full_review.json -Algorithm SHA256
   ```

   Expected: `False`, then no Git output.

The canonical LaTeX rebuild is a separate extended lane. Its expected PDF is 35 pages, 675797 bytes, SHA-256 `36DA47522259F31924A4B679275901235E4842CB6139D2B8A01B94F7B635C26F`.

## Claim-to-artifact map

| Layer | Main public artifacts | Review or replay path | Current status |
|---|---|---|---|
| Interface and bounded mathematical prose | title PDF; sections 02, 03/03b, 16, 17 | human mathematical review | bounded claims only |
| Public boundary and claim status | `docs/CLAIM_BOUNDARY.md`; `docs/CLAIM_LEDGER.md` | compare wording, scope, and status columns | reviewer-ready after the exact head passes its static gate |
| Admission and source lock | `artifacts/source_instance_manifest.json`; `docs/SOURCE_LOCK.md`; `docs/SOURCE_LOCK_CROSSWALK.md` | human audit plus static checksum gate | typed and manifest-covered |
| Executable contract | `artifacts/public_evidence_routes.json`; `scripts/verify.py` | static gate checks the exact registry; full gate executes exactly twelve routes | author-replayed at `a3cfafe` |
| Quantitative evidence | X05, X15, X16, X18-X26 artifacts named by the route registry | full bounded verifier | author-replayed; external replay pending |
| Noncomputational evidence | X13 and `G-004/CPL-001` in the manuscript and classical anchors in `docs/SOURCE_LOCK.md` | human proof/source audit | intentionally no thirteenth replay |
| Author replay record | `docs/S44HR_AUTHOR_REPLAY_SUMMARY.md` | verify commit/tree, counts, hashes, and scope | author-replayed at `a3cfafe` |
| Integrity | `SHA256SUMS.txt`; `RELEASE_SHA256.txt` | static gate or independent SHA-256 check | current reviewer head covered |

## Review boundaries

- The core row is `S=(N,X,I,rho,Phi)`. Source-lock metadata is not a sixth slot or a universal object category.
- H4 uses the same 60 projective points, equivalently 60 antipodal pairs of H4 roots.
- X10 is P07/P33-owned; X15 is the bounded P14 replay; P15 owns the separate X17 signed-reversal theorem.
- X11 and X12 remain nonadmitted future pointers. P28, P29, P30, P32, and P33 remain companion-owned.
- X13 and `G-004/CPL-001` are human-proof/classical-source-lock rows, not numerical routes.
- `Phi` is descriptive only: it is not a classifier, tiling oracle, complete invariant, or decision certificate.

## Known limits

- No independent external full replay has yet been recorded.
- The author replay certificate binds `a3cfafe`, not the later reviewer-navigation/checksum commit.
- The raw author envelope is not distributed because captured output contains transient clone paths; its SHA-256 is public in the sanitized summary.
- Optional full X05 census regeneration takes about 26 minutes, writes `m19_census/`, and is excluded from the bounded verifier.
- X13 and `G-004/CPL-001` require human proof and source review.
- The thirty-minute estimate excludes network and TeX setup.
- There is no tag, GitHub Release, DOI, arXiv deposit, or formal release.
- All bounded claims, nonimports, ownership rules, and explicit nonclaims remain controlling.

## External red-team handoff

Review the exact commit supplied by the maintainer, not a moving branch name. Follow the supplied external red-team protocol, list every file read, record the environment and every command, hash the external envelope, report findings in severity order, and keep suggestions separate from findings. Do not approve publication or promote claims. The requested next decision is whether the exact public review commit holds for external reproduction and paper/repository coherence.
