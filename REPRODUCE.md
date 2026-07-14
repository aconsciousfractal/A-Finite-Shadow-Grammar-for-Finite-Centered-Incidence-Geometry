# Reproduce the Public External-Review Candidate

The remediated payload at commit `a3cfafe3a3bb244ce9a293173a963e3cf6929a68` passed one complete S44H-R author replay from a new true Git clone. The later reviewer-preparation commit changes public governance/navigation, `artifacts/source_instance_manifest.json`, and checksum metadata only; the paper, PDF, quantitative scripts, route registry, and route artifacts are unchanged. That later commit is the S46 external-review target and is not itself covered by the author full-replay certificate.

## Python environment

Use Python 3.11 or newer and install the pinned environment:

```powershell
python -m pip install -r requirements.txt
```

The recorded S44H-R environment used Python 3.14.3, SymPy 1.14.0, and NumPy 2.4.2. SymPy supports the bounded signed Type-B/C route. NumPy is exercised only by the optional X05 full-census regeneration; the default verifier audits frozen X05 evidence.

## Short static gate

From the repository root:

```powershell
python -B scripts/verify.py --static-only --out ../p13_static_review.json
```

This standard-library-only preflight validates `SHA256SUMS.txt`, `RELEASE_SHA256.txt`, exact package coverage, the twelve-route contract, required files, and artifact semantics without executing a quantitative route.

Expected on the reviewer-preparation head: exit 0; schema 3; `PASS_PUBLIC_REPLAY_ENVELOPE`; `mode=static_only`; 12 routes evaluated, zero invoked; manifest 113/113; outer checksum 2/2; no `.verify` directory; clean tracked worktree.

## Full bounded verifier

Run once from a fresh clone of the exact review commit:

```powershell
python -B scripts/verify.py --timeout 600 --out ../p13_full_review.json
```

It covers exactly:

```text
X05, X15, X16, X18, X19, X20, X21, X22, X23, X24, X25, X26
```

X13 and `G-004/CPL-001` are human-proof/classical-source-lock rows and are intentionally outside the numerical replay count.

The S44H-R author run on `a3cfafe` completed in 783.885 seconds with exit 0: 12/12 routes, 86/86 route checks, 156/156 route-contract checks, 12/12 distributed artifacts immutable, manifest 112/112 pre/post, and outer checksum 2/2 pre/post. X15 validated an ignored verifier-owned runtime artifact and cleaned it. See `docs/S44HR_AUTHOR_REPLAY_SUMMARY.md`.

For the current reviewer-preparation head, the expected quantitative counts are unchanged and manifest coverage is 113/113. An independent successful run on that exact commit may be recorded as external reproduction; the author run alone may not.

After a full run:

```powershell
Test-Path artifacts/.verify
git status --short
Get-FileHash ../p13_full_review.json -Algorithm SHA256
```

Expected: `False`, no Git output, and a retained external envelope hash.

## Historical S43 replay

The exact raw S42 distribution passed the earlier S43 fresh-copy replay in 973.905 seconds with 12/12 routes and 60/60 checks. It remains historical evidence only; `docs/S43_REPLAY_SUMMARY.md` records it.

## Optional X05 full census

The default X05 command audits the frozen 1000+1000 census and bounded `lat565` evidence. Full regeneration is optional, takes about 26 minutes in the reference environment, writes to `m19_census/`, and is outside the bounded verifier:

```powershell
python -B scripts/x05_m19_census_full_regeneration.py
```

## Build the paper

From `paper/`, use the stabilization-complete sequence:

```powershell
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
bibtex A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
```

Expected PDF:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
35 pages
675797 bytes
SHA-256 36DA47522259F31924A4B679275901235E4842CB6139D2B8A01B94F7B635C26F
```

## Verify final hashes

`SHA256SUMS.txt` uses forward-slash paths and covers every distributed payload file except the two checksum metadata files. `RELEASE_SHA256.txt` pins exactly `SHA256SUMS.txt` and the title PDF.

An independent GNU-compatible check is:

```powershell
sha256sum -c RELEASE_SHA256.txt
sha256sum -c SHA256SUMS.txt
```

These checksums bind the reviewer target bytes. They do not establish a theorem, independent reproduction, a tag, a release, a DOI, or an arXiv deposit.
