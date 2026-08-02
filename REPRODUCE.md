# Reproduce the Public Package

## Python environment

Use Python 3.11 or newer:

```powershell
python -m pip install -r requirements.txt
```

## Short integrity review

From the repository root:

```powershell
python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
python -B scripts/verify.py --static-only --out ../finite_shadow_static_review.json
```

Expected results:

```text
PASS_X13_TYPE_A_LATTICE_RANK_MASS_CERTIFICATE checks=61/61
PASS_PUBLIC_REPLAY_ENVELOPE
```

The static verifier checks exact package coverage, route declarations, artifact semantics, and both checksum layers without executing the twelve quantitative subprocesses.

## Fail-closed tests

```powershell
$env:FCIG_TEST_TMPDIR='C:\tmp'
python -B tests/test_verify_fail_closed.py -v
```

The legacy `P13_TEST_TMPDIR` variable remains accepted for compatibility with earlier automation but is no longer used in public instructions.

## Full bounded replay

```powershell
python -B scripts/verify.py --timeout 600 --out ../finite_shadow_full_review.json
```

The timeout is per route. The full verifier executes exactly the routes declared in `artifacts/public_evidence_routes.json`, verifies their expected semantics, and confirms that manifest-pinned files remain byte-identical.

The optional full centered-rank census is intentionally outside the bounded verifier because it takes substantially longer:

```powershell
python -B scripts/x05_m19_census_full_regeneration.py
```

## Build the paper

The committed PDF is generated from `paper/main.tex`. With a conventional TeX installation, run from `paper/`:

```powershell
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
bibtex A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
```

The output is:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

A portable Tectonic build is also supported. The fixed source epoch below is the
date of the current public package and keeps the generated PDF metadata stable:

```powershell
$env:SOURCE_DATE_EPOCH='1785628800'
tectonic -p --outdir . main.tex
Move-Item -Force main.pdf A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

The authoritative byte count and SHA-256 are recorded in `RELEASE_SHA256.txt`; they are not duplicated here, avoiding stale documentation after a paper rebuild.

## Checksum model

`SHA256SUMS.txt` covers every distributed payload except `SHA256SUMS.txt` and `RELEASE_SHA256.txt`. `RELEASE_SHA256.txt` pins the manifest itself and the paper PDF.
