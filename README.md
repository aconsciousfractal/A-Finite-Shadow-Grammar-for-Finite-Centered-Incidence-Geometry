# A Finite-Shadow Grammar for Finite Centered Incidence Geometry

This repository contains the paper, LaTeX source, exact computational evidence, and reproducibility tools for **A Finite-Shadow Grammar for Finite Centered Incidence Geometry** by Oleksiy Babanskyy.

The paper introduces a bounded five-slot interface

```text
S = (N, X, I, rho, Phi)
```

for source-locked finite rows. Here `N` is the ambient permutation degree, `X` is a finite subset of `S_N`, `I` is the incidence or selection rule, `rho` is the representation or centered-operator channel, and `Phi` is the recorded fingerprint package. The interface is applied to Type-A, signed Type-B/C, dihedral, `G2`, projective `F4`, `H3`, `H4`, `D5`, `E6`, `E7`, and `E8` rows, together with centered-operator examples.

The central point is deliberately limited: coarse data such as rational rank, an uncolored carrier, or a conjugacy-class histogram can erase structure that remains visible in a source-aware channel. The fingerprint is descriptive; it is not a complete invariant, a classifier, or a tiling oracle.

## Read the work

- [Paper PDF](paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf)
- [LaTeX source](paper/)
- [Independent review guide](README_REVIEWER.md)
- [Reproducibility instructions](REPRODUCE.md)
- [Public claim boundary](docs/CLAIM_BOUNDARY.md)
- [Source-lock specification](docs/SOURCE_LOCK.md)
- [Author website](https://oleksiybabanskyy.com/)

## Evidence package

The route registry in `artifacts/public_evidence_routes.json` declares twelve bounded quantitative checks. They cover the centered-rank census, signed Type-B/C rows, modular centered channels, dihedral shadows, and the selected `G2`, `F4`, `H3`, `H4`, `D5`, `E6`, `E7`, and `E8` source rows.

The Type-A Fourier/Specht dictionary is supported separately by a manifest-pinned exact certificate and a read-only 61-check verifier. It is intentionally not counted as an additional quantitative route.

Run the short integrity review from the repository root:

```powershell
python -B scripts/x13_type_a_lattice_rank_mass_certificate_check.py
python -B scripts/verify.py --static-only --out ../finite_shadow_static_review.json
```

Expected status:

```text
PASS_X13_TYPE_A_LATTICE_RANK_MASS_CERTIFICATE checks=61/61
PASS_PUBLIC_REPLAY_ENVELOPE
```

`SHA256SUMS.txt` covers every distributed payload except the checksum metadata files. `RELEASE_SHA256.txt` pins the manifest and the paper PDF.

## Repository layout

```text
paper/       Paper PDF and LaTeX source
docs/        Public scope, source-lock, claim, and reproducibility records
artifacts/   Canonical registries and immutable evidence
results/     Bounded numerical outputs used by the replay routes
scripts/     Verification and replay programs
tests/       Fail-closed integrity tests
```

## Related public work

The paper cites companion results by their public titles and immutable GitHub references. Important related packages include:

- [Finite Centered Incidence Geometry on the Type-A Standard Space](https://github.com/aconsciousfractal/Finite-Centered-Incidence-Geometry-Type-A-Standard-Space/tree/v1.0.0)
- [Type-A Poset Cones and Extension Tilers](https://github.com/aconsciousfractal/type-a-poset-cones-and-extension-tilers/tree/v0.2-public-release)
- [Linear-Extension Sets and Subgroup Rows in S4](https://github.com/aconsciousfractal/Linear-Extension-Sets-and-Subgroup-Rows-in-S4-A-Finite-Witness-Separation/tree/v1.0.1)
- [Determinant Divisibility of Centered Latin Squares](https://github.com/aconsciousfractal/Determinant-Divisibility-of-Centered-Latin-Squares/tree/8984359d0f7fd66e4eaa7864a557d6b907e9f9ec)
- [Odd-Rank Loci and Box-Induced Symmetries of Centered Sudoku Operators](https://github.com/aconsciousfractal/Odd-Rank-Loci-and-Box-Induced-Symmetries-of-Centered-Sudoku-Operators/tree/4af472a8235732aa8f6e75371f23225f0b6a2b23)

The complete bibliography and all companion-source pins are in `paper/refs.bib`.

## Scope

This repository does not claim a universal FCIG theory, a general Coxeter or Weyl theorem, a root-subsystem classification, a modular Specht novelty theorem, a new quotient-transfer theorem, or a classification or tiling criterion derived from `Phi`.

## Citation and license

Citation metadata is provided in `CITATION.cff`.

Code, scripts, artifacts, and repository documentation are MIT-licensed. The paper text and PDF under `paper/` are CC BY 4.0; see `LICENSE`.
