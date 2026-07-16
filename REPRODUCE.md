# Reproduce the Public Post-Review Candidate

Exact commit `16be346502e754bd6282adb5216599bed26ab8d6` passed one
independent S46 replay from a fresh public clone. S46H changes only the bounded
paper/source-governance allowlist, the title PDF, and a new read-only X13
certificate checker. The existing twelve-route quantitative surface remains
byte-identical.

## Python environment

Use Python 3.11 or newer and install the pinned environment:

```powershell
python -m pip install -r requirements.txt
```

The S46 environment used Python 3.14.3, SymPy 1.14.0, and NumPy 2.4.2.

## Short S46H gate

From the repository root:

```powershell
python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
python -B scripts/verify.py --static-only --out ../p13_static_review.json
```

Expected: X13 `61/61`; static exit 0; schema 3;
`PASS_PUBLIC_REPLAY_ENVELOPE`; `mode=static_only`; 12 routes evaluated, zero
invoked; manifest 118/118; outer checksum 2/2; no `.verify` directory.

The existing fail-closed sentinel suite is:

```powershell
$env:P13_TEST_TMPDIR='C:\tmp'
python -B tests/test_verify_fail_closed.py -v
```

Expected: 15/15 PASS.

## Full bounded verifier

The independent S46 run on `16be346` completed in 1256.112 seconds with exit
0: 12/12 routes, 86/86 route checks, 156/156 route-contract checks, 12/12
distributed artifacts immutable, manifest 113/113 pre/post, and outer checksum
2/2 pre/post. Its envelope SHA-256 is
`BB946A10C5264C30B9D64051AF8266F7C4CA3DED9D251E415C272FE59B22DDFD`.

Because S46H leaves that protected quantitative surface byte-identical, no
second long replay is required for the bounded repair. A reviewer may still run
one from a fresh clone:

```powershell
python -B scripts/verify.py --timeout 600 --out ../p13_full_review.json
```

The timeout is per route. The route set remains exactly:

```text
X05, X15, X16, X18, X19, X20, X21, X22, X23, X24, X25, X26
```

X13 uses its static certificate/checker, X15-002 its self-contained proof, and
G-004/CPL-001 its human proof/classical source lock. None is a thirteenth
quantitative route.

## Optional X05 full census

The default X05 command audits frozen evidence. Full regeneration remains
optional, takes about 26 minutes, writes to `m19_census/`, and is outside the
bounded verifier:

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
36 pages
683807 bytes
SHA-256 6C6207818A03BBE43B7E341198ECB95AAE3BCEDE6F2181C51B5EA88C1C9B4BC2
```

## Verify final hashes

`SHA256SUMS.txt` covers every distributed payload file except the two checksum
metadata files. `RELEASE_SHA256.txt` pins exactly `SHA256SUMS.txt` and the title
PDF. These checksums bind bytes; they do not authorize a tag, release, DOI, or
deposit.
