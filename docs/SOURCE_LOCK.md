# Source Lock

This file records provenance and verification discipline for the S44 remediation candidate. The exact raw S42 distribution passed S43; the changed remediation bytes still require S44H verification. Publication is not authorized.

## Five-slot core and bounded normative wrapper

A concrete row remains

`S=(N,X,I,rho,Phi)`, with `X` a finite subset of `S_N`.

An X-ID identifies a family/source slot; each concrete instance fixes its own ambient degree `N`. A separate parameter such as `n` may index a family.

Admitted concrete rows are governed by the normative typed source-lock schema. The public package does **not** assert that a single consolidated `L(S)` record has already been materialized for every row. Instead:

- `artifacts/source_instance_manifest.json#/registry_rows` is the single canonical post-S44 admission registry;
- `admission` is typed independently from `pointer_status`;
- `docs/SOURCE_LOCK_CROSSWALK.md` routes every required and conditional schema field to its public evidence surface without claiming consolidated field-level values;
- row-specific values remain in the manuscript row, appendix, cited source, and declared artifact rather than being duplicated into a potentially divergent registry.

The wrapper types provenance and interpretation. It is not a sixth mathematical slot and does not define a universal category of FCIG objects.

## Quantitative route lock

`artifacts/public_evidence_routes.json` is the executable route registry. It declares exactly these twelve quantitative routes:

| ID | Script | Default posture |
|---|---|---|
| X05 | `scripts/x05_m19_lat565_evidence_check.py` | audit frozen evidence |
| X15 | `scripts/signed_type_bc_shadow_replay.py` | bounded recompute to verifier-owned output |
| X16 | `scripts/modular_centered_channel_replay.py` | bounded replay |
| X18 | `scripts/dihedral_vertex_shadow_replay.py` | bounded replay |
| X19 | `scripts/g2_source_channel_replay.py` | bounded exported replay |
| X20 | `scripts/f4_source_layer_replay.py` | bounded exported replay |
| X21 | `scripts/h3_projective_source_channel_replay.py` | bounded replay |
| X22 | `scripts/h4_projective_source_channel_replay.py` | bounded replay |
| X23 | `scripts/d5_projective_source_channel_replay.py` | bounded replay |
| X24 | `scripts/e6_projective_source_channel_replay.py` | bounded replay |
| X25 | `scripts/e7_projective_source_channel_replay.py` | bounded replay |
| X26 | `scripts/e8_projective_source_channel_replay.py` | bounded replay |

The raw S42 route surface passed one S43 run in 973.905 seconds: 12/12 routes, 12/12 subprocess exits, 12/12 artifact semantics, and 60/60 route checks. Its historical manifest SHA-256 is `0E2E47BD05EE26AEDF7AA5FA540A94806BFAC9E8B8F3F5D70ACFC948DD90C5EA`; the private raw-envelope SHA-256 is `76F1062442064076A150700C1195C02861217F49BF9BF84F5E6FF2721375290A`. See `docs/S43_REPLAY_SUMMARY.md`.

Those hashes identify the raw S42 evidence only. They must not be reused as release hashes after S44 edits. The remediation manifest and outer checksum are S44H inputs and become certification evidence only after verification from the final Git-normalized clone.

X05 defaults to a deterministic audit of frozen census rows, summary, and `lat565` evidence. The optional full census generator was not run in S43 and remains outside the bounded verifier.

## Noncomputational locks

- X13: public manuscript proof and classical source lock for the Fourier/Specht dictionary, rank mass, and lattice-qualified `SNF^L`; no numerical replay and no thirteenth quantitative route.
- G-004/CPL-001: human proof and classical sources for the retained S36/S37 source-coupling/descent guardrail; no numerical replay, no novelty, no new X-ID, and no imported descent or transfer theorem.

## Classical source anchors

| Source | Exact public anchor | Locked role |
|---|---|---|
| Higman (1970) | `https://www.numdam.org/item/RSMUP_1970__44__1_0/`, Section 6 p. 11 and Section 8 Eq. (8.1) p. 20 | commutative-ring coefficient statement and unnormalised quotient |
| Godsil (2010) | `https://www.math.uwaterloo.ca/~cgodsil/pdfs/assoc2.pdf`, Section 5.1, Eq. (5.1.1), Lemma 5.1.2 | association-scheme quotient/intersection-number background |
| Haemers (1995) | `https://doi.org/10.1016/0024-3795(95)00199-2`, Section 2 | interlacing background |
| Roth (1952); Gustafson (1979) | `https://doi.org/10.1090/S0002-9939-1952-0047598-3`; `https://doi.org/10.1016/0024-3795(79)90106-X` | splitting and Sylvester-equation background |
| Newman (1974) | `https://doi.org/10.6028/jres.078B.002`, Theorem 2; Theorem 3 for the multiblock form | integral matrix-equivalence anchor |
| T. Klein (1968) | `https://doi.org/10.1112/jlms/s1-43.1.280` | source name retained as `T. Klein`; initial not expanded |
| Schmidmeier (2007) | `https://arxiv.org/abs/0709.2920`, Theorems 4.1-4.2 | Green-Klein/Littlewood-Richardson background |
| Bao et al. (2011) | *Congressus Numerantium* 207, 141-160; `https://arxiv.org/abs/1005.5492` | published spelling `Friedman-Gerlicz`; arXiv metadata spelling remains source metadata only |

The detailed field and source loci for X13 and G-004/CPL-001 are in `docs/SOURCE_LOCK_CROSSWALK.md`.

## Admission, ownership, and companion locks

- X10: `admission=not_admitted`, `pointer_status=public_companion`; P07/P33 retain ownership.
- X11: `admission=not_admitted`, `pointer_status=future`; the P18 pointer is version-neutral and requires no release pin while it remains nonimporting.
- X12: `admission=not_admitted`, `pointer_status=future`; P17 context only, with no current row or theorem import.
- X13: admitted and publicly supported by human proof/classical sources; no private-dependency label remains.
- X15: admitted bounded P14 row with a public replay; the P15 theorem is not its proof source.
- X17: `admission=not_admitted`, `pointer_status=public_companion`; theorem ownership remains with P15.
- X19 and X20: admitted bounded rows with exported public replay routes.
- X20 and the other root-shadow rows may cite P28/P29/P30/P32 refinements or limits, but those remain nonimport companion routes.
- P33 is an exact-certificate companion and does not turn `Phi` into a tiling oracle.

For every quantitative claim, the required evidence chain is:

`claim -> source -> version -> artifact -> command -> expected result -> SHA-256`.

If no immutable public source or bundled verification route exists, the quantity must be downgraded or removed. The current next gate is S44H post-fix verification. S45 remains an explicit owner action and cannot open from this remediation state.
