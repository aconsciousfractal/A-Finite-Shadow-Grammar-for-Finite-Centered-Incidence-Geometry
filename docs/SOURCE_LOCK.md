# Source Lock

## Mathematical core

Every admitted concrete row uses

```text
S = (N, X, I, rho, Phi)
```

The source lock records how those five slots are to be interpreted: carrier, action convention, source version, coefficient ring or quotient when relevant, verification route, ownership, and import boundary. It is provenance metadata, not an additional mathematical slot.

The normative field definitions are in `SOURCE_LOCK_SCHEMA.md`; `SOURCE_LOCK_CROSSWALK.md` identifies where each value is published. The canonical family and admission data are in `artifacts/source_instance_manifest.json`.

## Quantitative evidence

The public route registry declares twelve bounded computations:

```text
X05, X15, X16, X18, X19, X20, X21, X22, X23, X24, X25, X26
```

Each route declares its script, arguments, required files, and result artifacts. `scripts/verify.py` checks exact coverage and artifact semantics before executing any route, then confirms that distributed files remain unchanged.

The Type-A exact certificate and its 61-check reader are deliberately outside this route count because they verify a fixed public certificate rather than regenerate a quantitative artifact.

## Classical sources

The standard-block dictionary, Smith-form statements, quotient mechanism, interlacing context, Sylvester-equation criterion, coprime splitting result, and Green-Klein/Littlewood-Richardson background are attributed to their published sources in `paper/refs.bib`. The paper does not claim novelty for those classical mechanisms.

## Companion sources

When a result belongs to a companion paper, the bibliography records its public title and immutable GitHub tag or commit. Citation is contextual unless the manuscript explicitly states an imported theorem and its proof boundary.

## Integrity

`SHA256SUMS.txt` covers every distributed payload except the checksum metadata files. `RELEASE_SHA256.txt` pins the manifest and the title PDF. The current verification record is summarized in `REPRODUCIBILITY_RECORD.md`.
