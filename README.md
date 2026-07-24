# A Finite-Shadow Grammar for Finite Centered Incidence Geometry

This repository is the public external-review candidate for the paper **A Finite-Shadow Grammar for Finite Centered Incidence Geometry**.

> Gate status: commit `16be346502e754bd6282adb5216599bed26ab8d6` passed the independent S46 replay and mathematical red team. This S47 public review candidate includes the five bounded S46H source/governance remediations; their short gates pass with the pre-existing quantitative surface byte-identical. No tag, GitHub Release, DOI, arXiv deposit, or formal release is claimed.

## Interface

A concrete finite row is the five-slot datum

```text
S = (N, X, I, rho, Phi)
```

with `X` a finite subset of `S_N`. Here `N` is the ambient permutation degree. Canonical IDs `X01` through `X26` identify source/family slots, not individual subsets; a family parameter such as `n` is distinct from the concrete ambient degree `N`.

Admitted concrete rows are governed by the public normative schema `docs/SOURCE_LOCK_SCHEMA.md`, covering provenance, action conventions, channels, versions, verification, and import boundaries. The package does not assert that one consolidated `L(S)` object has already been published for every row. The field-routing map is `docs/SOURCE_LOCK_CROSSWALK.md`; the canonical admission registry is `artifacts/source_instance_manifest.json`. Source-lock metadata is not a sixth mathematical slot and does not assert a universal category of FCIG objects.

The paper uses the standard-block balance dictionary as an interface lens, records characteristic- and lattice-sensitive centered channels, and compares bounded source-aware fingerprints. `Phi` is descriptive: it is not a classifier, a tiling oracle, or a substitute for a separately owned theorem.

## Recorded evidence and review state

The route registry `artifacts/public_evidence_routes.json` contains exactly twelve quantitative routes:

```text
X05  frozen M19/lat565 evidence audit
X15  signed Type-B/C bounded replay
X16  modular centered-channel replay
X18  dihedral vertex-shadow replay
X19  G2 source-channel replay
X20  F4 source-layer replay
X21  H3 projective source-channel replay
X22  H4 projective source-channel replay
X23  D5 projective source-channel replay
X24  E6 projective source-channel replay
X25  E7 projective source-channel replay
X26  E8 projective source-channel replay
```

The remediated payload at commit `a3cfafe3a3bb244ce9a293173a963e3cf6929a68` and tree `9acf53f8f5068872e0a0273139efac87dee224f2` passed one S44H-R author replay from a new true Git clone in 783.885 seconds: 12/12 routes, 86/86 route checks, 156/156 route-contract checks, manifest 112/112 pre/post, outer checksum 2/2 pre/post, and 12/12 distributed artifacts byte-immutable. The canonical build reproduced the 35-page PDF byte-for-byte. See the path-free `docs/S44HR_AUTHOR_REPLAY_SUMMARY.md`.

The earlier S43 replay remains historical evidence. The exact public review commit `16be346502e754bd6282adb5216599bed26ab8d6` passed the independent S46 replay in 1256.112 seconds with 12/12 routes, 86/86 route checks, 156/156 route-contract checks, manifest 113/113, outer checksum 2/2, and immutable distributed artifacts. See `docs/S46_EXTERNAL_REPLAY_SUMMARY.md`. S46H changes only the bounded paper/source-governance allowlist and adds the read-only X13 checker; the existing quantitative surface remains byte-identical.

X13 is outside the quantitative route count: its Fourier/Specht dictionary, Type-A rank masses, lattice, block matrices, and `SNF^L` values are supported by the manuscript proof, classical source lock, a manifest-pinned certificate, and a read-only 61-check exact checker. It is not a thirteenth route.

`G-004/CPL-001` is a human-proof/classical-source-lock row for the retained S36/S37 source-coupling/descent guardrail. X15-002 is the separate self-contained mirror-union human proof, while X15-001 remains the six-row quantitative route. Neither creates a thirteenth route or imports a general descent, transfer, or P15 theorem.

The default X05 route audits the frozen 1000+1000 census and the bounded `lat565` witness. The optional full X05 census regeneration takes about 26 minutes in the reference environment and was excluded from S43.

The H4 public wording is controlling: the row uses the same 60 projective points, equivalently 60 antipodal pairs of H4 roots, and distinguishes the flat-size and Gram-square channels without promoting a general H4 theorem.

## Repository layout

```text
paper/       LaTeX source and title-named candidate PDF
docs/        Normative schema/crosswalk, claim boundary/ledger, and replay summaries
artifacts/   Canonical registry, route registry, inputs, and replay artifacts
scripts/     Fail-closed verifier and bounded replay scripts
```

See `README_REVIEWER.md` for the ten-minute and optional full-replay review paths, and `REPRODUCE.md` for the bounded verifier and paper-build commands.

## Ownership and nonimport boundaries

- X10 is a companion-owned P07/P33 pointer; P13 cites bounded results as context, imports neither theorem nor proof, and makes no all-`n` tiling claim.
- X15-001 is the bounded P14 six-row replay; X15-002 is the P13-owned elementary mirror-union proof with P14 provenance. The separate P15 signed-reversal theorem/proof is not imported.
- X11 is a version-neutral future P18 pointer and is not admitted; no release pin is required while it remains a nonimporting pointer.
- X12 is a future P17 pointer with `admission=not_admitted`; `pointer_status=future` is recorded separately.
- P28, P29, P30, P32, and P33 remain companion theorem or certificate routes. Their cited results are not reassigned to P13.
- The two P39-derived packages (`FCIG-Higher-Star-Defect-Design-Lattice`; `FCIG-Common-Marked-Lattice-Designs`, both published untagged 2026-07-24) are companion routes on design incidence lattices. Design incidence lattices are not admitted X-rows; no X-ID is created and no theorem is imported into P13.

The package does not claim a complete FCIG theory, a general Coxeter/Weyl or Type-E theorem, a root-subsystem classification, a modular Specht novelty theorem, a new coupling/descent theorem, a `5568` bridge, or any classification or tiling criterion derived from `Phi`.

## Build the paper

From `paper/`:

```powershell
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
bibtex A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
pdflatex -jobname=A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry -interaction=nonstopmode -halt-on-error main.tex
```

Expected candidate PDF:

```text
paper/A_Finite-Shadow_Grammar_for_Finite_Centered_Incidence_Geometry.pdf
```

## License

Code, scripts, artifacts, and repository documentation are MIT-licensed. The paper text and PDF under `paper/` are CC-BY-4.0; see `LICENSE`.
