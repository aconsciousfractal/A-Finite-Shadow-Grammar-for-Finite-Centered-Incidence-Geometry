# A Finite-Shadow Grammar for Finite Centered Incidence Geometry

This repository is the public external-review candidate for the paper **A Finite-Shadow Grammar for Finite Centered Incidence Geometry**.

> Gate status: the remediated payload at commit `a3cfafe` passed the S44H-R author replay from a true Git clone. The public origin is available on `master`; S45 scoped authorization is complete and S46 independent external red team is next. No tag, GitHub Release, DOI, arXiv deposit, or independent external reproduction is claimed.

## Interface

A concrete finite row is the five-slot datum

```text
S = (N, X, I, rho, Phi)
```

with `X` a finite subset of `S_N`. Here `N` is the ambient permutation degree. Canonical IDs `X01` through `X26` identify source/family slots, not individual subsets; a family parameter such as `n` is distinct from the concrete ambient degree `N`.

Admitted concrete rows are governed by the normative source-lock schema covering provenance, action conventions, channels, versions, verification, and import boundaries. The package does not assert that one consolidated `L(S)` object has already been published for every row. The schema-to-surface routing crosswalk is `docs/SOURCE_LOCK_CROSSWALK.md`; the canonical admission registry is `artifacts/source_instance_manifest.json`. Source-lock metadata is not a sixth mathematical slot and does not assert a universal category of FCIG objects.

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

The earlier S43 replay of the raw S42 surface remains historical evidence and is recorded in `docs/S43_REPLAY_SUMMARY.md`. The reviewer-preparation commit after `a3cfafe` changes only public governance/reviewer documentation, `artifacts/source_instance_manifest.json`, and checksum metadata; it does not change the paper, PDF, quantitative scripts, route registry, or route artifacts. It is reviewer-ready after static checks, but the S44H-R full replay certificate continues to bind exactly `a3cfafe`. Independent full replay of the public review head is the S46 gate.

X13 is intentionally noncomputational: its Fourier/Specht dictionary and `SNF^L` conventions are supported by the manuscript proof and classical source lock, not by a thirteenth numerical replay.

`G-004/CPL-001` is a second noncomputational governance row for the retained S36/S37 classical source-coupling/descent guardrail. It is supported by human proof and classical sources, creates no new X-ID or numerical route, claims no novelty, and imports no general descent or transfer theorem.

The default X05 route audits the frozen 1000+1000 census and the bounded `lat565` witness. The optional full X05 census regeneration takes about 26 minutes in the reference environment and was excluded from S43.

The H4 public wording is controlling: the row uses the same 60 projective points, equivalently 60 antipodal pairs of H4 roots, and distinguishes the flat-size and Gram-square channels without promoting a general H4 theorem.

## Repository layout

```text
paper/       LaTeX source and title-named candidate PDF
docs/        Claim boundary, source lock/crosswalk, claim ledger, and S43 summary
artifacts/   Canonical registry, route registry, inputs, and replay artifacts
scripts/     Fail-closed verifier and bounded replay scripts
```

See `README_REVIEWER.md` for the ten-minute and thirty-minute review paths, and `REPRODUCE.md` for the bounded verifier and paper-build commands.

## Ownership and nonimport boundaries

- X10 is a companion-owned P07/P33 pointer; P13 imports no all-`n` tiling theorem.
- X15 is the bounded P14 signed Type-B/C row. The separate P15 signed-reversal theorem is represented by the X17 companion pointer and is not imported.
- X11 is a version-neutral future P18 pointer and is not admitted; no release pin is required while it remains a nonimporting pointer.
- X12 is a future P17 pointer with `admission=not_admitted`; `pointer_status=future` is recorded separately.
- P28, P29, P30, P32, and P33 remain companion theorem or certificate routes. Their cited results are not reassigned to P13.

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
