# Reproduce the S44 Remediation Candidate

The exact raw S42 distribution passed the single S43 fresh-copy replay summarized in `docs/S43_REPLAY_SUMMARY.md`. S44 then found blocking release defects. The current bytes are an S44 remediation candidate and have not yet passed S44H verification from a Git-normalized clone. Publication is not authorized.

## Python environment

Use Python 3.10 or newer and install the pinned environment:

```powershell
python -m pip install -r requirements.txt
```

The recorded S43 environment was Python 3.14.3, SymPy 1.14.0, and NumPy 2.4.2. SymPy supports the bounded signed Type-B/C route. NumPy is exercised only by the optional X05 full-census regeneration; the default verifier audits frozen X05 evidence.

## Bounded verifier

From the repository root, the short preflight is:

```powershell
python -B scripts/verify.py --static-only
```

The static preflight validates `SHA256SUMS.txt`, `RELEASE_SHA256.txt`, exact route coverage, required files, and artifact semantics before loading the route registry or executing a quantitative route. It took about 2 seconds in the reference environment and executes no quantitative route.

The full bounded command is:

```powershell
python -B scripts/verify.py --timeout 600
```

It covers exactly:

```text
X05, X15, X16, X18, X19, X20, X21, X22, X23, X24, X25, X26
```

X13 and `G-004/CPL-001` are human-proof/classical-source-lock rows and are intentionally outside the numerical replay count.

The single historical S43 run of the raw S42 bytes took 973.905 seconds (about 16.2 minutes) and passed 12/12 routes. That result does not certify the current remediation bytes. Do not launch a new full run until the S44 fixes, Git-normalized file set, manifest, and outer checksum are final and the S44H gate is ready. S45 remains an explicit owner-authorization gate after S44H; these commands do not authorize release or publication.

## Optional X05 full census

The default X05 command audits the frozen 1000+1000 census and bounded `lat565` evidence. Full regeneration is optional, takes about 26 minutes in the reference environment, writes to `m19_census/`, and is outside S43/S44H bounded replay:

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

The fourth total `pdflatex` invocation (the fifth command overall) is the label-stabilization pass. The recorded S43 build was 34 pages and byte-identical to its S42 source PDF, but the final S44H PDF hash must be recorded after all paper and bibliography repairs.

Expected candidate PDF:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

## Verify final hashes

`SHA256SUMS.txt` uses forward-slash paths and covers the distributed payload except the two checksum metadata files. `RELEASE_SHA256.txt` pins exactly `SHA256SUMS.txt` and the title PDF. The verifier validates both layers before loading any route. From the repository root, an independent GNU-compatible check is `sha256sum -c RELEASE_SHA256.txt` followed by `sha256sum -c SHA256SUMS.txt`. These checksums bind candidate bytes; they do not authorize S45, release, or publication.
