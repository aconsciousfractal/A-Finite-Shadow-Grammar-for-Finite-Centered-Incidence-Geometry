# Verified Artifact Scope

The public verifier protects two related surfaces.

## Distributed package

`SHA256SUMS.txt` enumerates every tracked payload file except the checksum metadata files. The verifier fails closed on a missing file, an unexpected file, a duplicate entry, a malformed digest, or a digest mismatch.

`RELEASE_SHA256.txt` pins:

1. `SHA256SUMS.txt` itself;
2. the paper PDF.

## Quantitative routes

The route registry declares exactly twelve bounded routes:

```text
X05, X15, X16, X18, X19, X20, X21, X22, X23, X24, X25, X26
```

Before any route runs, the verifier validates registry structure, required files, canonical relative paths, and package checksums. After execution it repeats the integrity checks and requires every distributed artifact to remain unchanged.

The Type-A exact certificate is checked separately by `scripts/x13_type_a_lattice_rank_mass_certificate_check.py`. It performs 61 read-only exact checks and does not create or modify an artifact.

## Recomputing the scope

The checksum layer is regenerated only after an intentional public-package change. A successful final audit must then show:

- exact manifest coverage;
- valid release checksum entries;
- static package verification pass;
- Type-A certificate 61/61 pass;
- fail-closed test suite pass;
- clean repository status after commit.
