# Reproduce

This repository uses a standard LaTeX installation.  The paper is an interface package: it contains the manuscript source, compiled PDF, source manifest, and public boundary notes.  It does not include a standalone replay engine for every source row; those rows are cited public repositories or bounded companion artifacts summarized by the manifest.

## Python environment

No third-party Python package is required for this package.  `requirements.txt` is a no-op marker for automated environments.

## Build the paper

From `paper/`:

```powershell
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
bibtex A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
```

Expected PDF:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

## Inspect artifacts

The machine-readable source instance matrix is:

```text
artifacts/source_instance_manifest.json
```

The hash manifest is:

```text
SHA256SUMS.txt
```