# S44H-R Author Replay Summary

This path-free record summarizes the complete author-operated replay of the remediated public payload. It is not an independent external reproduction certificate.

## Certified baseline

- Commit: `a3cfafe3a3bb244ce9a293173a963e3cf6929a68`.
- Tree: `9acf53f8f5068872e0a0273139efac87dee224f2`.
- Clone method: new true Git clone with local-object reuse disabled.
- Command: `python -B scripts/verify.py --timeout 600`.
- Verifier invocations in the certifying task: exactly one.
- Runtime: 783.885 seconds.
- Exit code: 0.
- Envelope: schema 3, mode `replay`, `PASS_PUBLIC_REPLAY_ENVELOPE`.

## Replay result

- Routes declared, required, evaluated, invoked, and passed: 12/12.
- Route checks: 86/86.
- Route-contract checks: 156/156.
- Subprocesses exiting zero: 12/12.
- Semantic artifacts passing: 12/12.
- Distributed artifacts byte-immutable: 12/12.
- Manifest: 112/112 before and after; byte-identical pre/post.
- Outer checksum: 2/2 before and after; byte-identical pre/post.
- X15 verifier-owned runtime artifact: prepared, validated, and cleaned.
- `.verify` and lingering Python processes after completion: absent.
- Raw author-envelope SHA-256: `A974ACCD2ACF319EEAC28BDD07E6C77370FC41C250B6C9ADA599058BCD88A85F`.

The raw envelope is not distributed because captured subprocess output contains transient clone paths.

## Canonical paper rebuild

All five commands in the sequence `pdflatex`, `bibtex`, `pdflatex`, `pdflatex`, `pdflatex` exited 0 and produced a clean stabilized log.

- Pages: 35.
- Bytes: 675797.
- PDF SHA-256: `36DA47522259F31924A4B679275901235E4842CB6139D2B8A01B94F7B635C26F`.
- Result: byte-identical to the committed PDF.

## Post-run gates

- Static verifier: 12/12 evaluated, zero invoked.
- Fail-closed sentinel suite: 15/15.
- JSON parse: 38/38.
- Python in-memory compile: 34/34.
- UTF-8/LF text: 113/113; CR bytes zero.
- Private/local path hits: zero.
- Tracked clone: clean.

## Pinned baseline hashes

- `SHA256SUMS.txt`: `88EAA8DBB0D1C1B9C6B89BCE1F0C5F71ABB30D792EC24ADC500581F03149918C`.
- `RELEASE_SHA256.txt` file: `303EA71CAF0EA9361A024DE0AB29C34F90ABF3BF6823B80DF54ED2D0D4AFBBC1`.
- Title PDF: `36DA47522259F31924A4B679275901235E4842CB6139D2B8A01B94F7B635C26F`.

## Scope boundary

This author replay certifies exactly commit `a3cfafe` and tree `9acf53f8`. The later reviewer-preparation commit changes only public reviewer/governance documents, `artifacts/source_instance_manifest.json`, and checksum metadata; it leaves the paper, PDF, quantitative scripts, route registry, and route artifacts unchanged. Short gates may make that later commit reviewer-ready, but only an independent full replay on its exact commit can establish external reproduction.

S45 scoped review preparation is complete. S46 independent external red team is next. No tag, GitHub Release, DOI, arXiv deposit, or formal release is claimed.
