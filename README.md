# A Finite-Shadow Grammar for Finite Centered Incidence Geometry

This repository contains the public paper package for:

**A Finite-Shadow Grammar for Finite Centered Incidence Geometry**

The paper records a bounded interface grammar for finite centered incidence geometry.  It organizes finite incidence rows as tuples

```text
S = (n, X, I, rho, Phi)
```

where `X` is a finite subset of a symmetric group, or a source-locked finite shadow inside one; `I` is the incidence rule; `rho` is the representation or centered-operator channel; and `Phi` is a replayable fingerprint package.

## What This Paper Does

1. Defines a bounded finite-shadow grammar for current FCIG source rows.
2. Uses the elementary standard-block dictionary as an interface lens: position-value balance corresponds to vanishing of the standard Specht block.
3. Shows worked Type-A and signed Type-B/C finite evidence where the fingerprint package sees structure not determined by coarse cycle-type histograms.
4. Records why the fingerprint package is descriptive only: it is not a classifier, not a tiling oracle, and not a substitute for separate theorem routes.

## Repository Layout

```text
paper/       LaTeX source and compiled title-named PDF
docs/        Public claim boundary, source lock, and claim ledger
artifacts/   Machine-readable source instance manifest
scripts/     Placeholder note; this interface package has no standalone replay engine
```

## Companion Files

- `REPRODUCE.md` gives the paper build command.
- `README_REVIEWER.md` gives a short reviewer inspection path.
- `docs/CLAIM_BOUNDARY.md` states the public claim boundary.
- `docs/SOURCE_LOCK.md` records the source categories used by the paper.
- `docs/CLAIM_LEDGER.md` lists the public claims and their status.
- `SHA256SUMS.txt` records hashes for the exported package.

## Build The Paper

From `paper/`:

```text
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
bibtex A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
```

Expected PDF:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

## Public Boundary

This package does not claim a complete theory of FCIG, a classification theorem, a general Weyl-group theorem, a tiling criterion, a theorem-level bridge from the number `5568`, or a public theorem for the separate signed-reversal route.  The paper is a bounded grammar/interface paper.

## License

Code, scripts, artifacts, and repository documentation are released under the MIT License. The paper text and PDF under `paper/` are released under CC-BY-4.0; see `LICENSE`.