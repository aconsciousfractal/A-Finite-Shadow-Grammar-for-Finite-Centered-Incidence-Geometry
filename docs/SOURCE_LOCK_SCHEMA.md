# Normative Typed Source-Lock Schema

Schema version: 3
Public profile: bounded distributed-record profile

## Purpose and scope

A concrete mathematical row remains the five-slot datum
`S=(N,X,I,rho,Phi)`, with `X` a finite subset of `S_N`. The source lock is
normative provenance and interpretation metadata for that datum. It is not a
sixth mathematical slot and does not define a universal category of FCIG
objects.

This public profile is a **distributed-record schema**. A conforming record is
assembled from the canonical registry, the relevant manuscript row, its cited
source or bundled artifact, and (for quantitative routes) the route registry.
The package need not duplicate those values in one consolidated `L(S)` file.
`docs/SOURCE_LOCK_CROSSWALK.md` gives the authoritative field-to-surface
routing.

## Canonical types

| Field | Type | Rule |
|---|---|---|
| `family_id` | enum `X01`--`X26` | Identifies a source/family slot, never a concrete subset by itself. |
| `instance_id` | nonempty string | Required for an admitted concrete instance; not manufactured for a pointer or the X14 meta row. |
| `family_parameter` | scalar/string or `NA(reason)` | Distinct from the ambient degree `N`. |
| `ambient_degree` | positive integer | The concrete symmetric degree `N`. |
| `carrier` | finite-set specification | Includes the labelling convention when projective, signed, or source-coloured. |
| `ambient_action` | group-action specification | Names the acting group or finite shadow inside `S_N`. |
| `action_convention` | convention record | Fixes action side, composition order, and matrix convention when they affect interpretation. |
| `finite_row_X` | exact finite-row specification | Definition, explicit list, or immutable artifact locator. |
| `incidence_I` | exact incidence/selection rule | Defines membership in the row. |
| `channel_rho` | representation/operator specification | Includes domain, codomain, and centering/quotient convention when applicable. |
| `fingerprint_Phi` | bounded fingerprint specification | Names only the recorded ranks, Smith data, source splits, energies, or related fields. |
| `source_locator` | citation or bundled relative path | Must be public and immutable when used as authority. |
| `source_version` | version, tag, commit, or package checksum | Required whenever a source locator can move. |
| `admission` | enum | Exactly `admitted` or `not_admitted`. |
| `pointer_status` | enum | Exactly `not_applicable`, `future`, or `public_companion`; independent of `admission`. |
| `descriptive_role` | non-normative label | Human routing label such as `core_exhibit`, `prose`, `meta`, or `companion_pointer`. |
| `claim_owner` | owner identifier | P13 or the named companion project/source. |
| `verification_route` | route specification | Quantitative replay, static/human certificate, human proof, or cited classical source lock. |
| `import_boundary` | bounded statement | States exactly what P13 uses. |
| `nonimport_boundary` | exclusion statement | Prevents ownership transfer and family-wide, classification, or tiling inference. |

## Conditional fields and triggers

| Field | Trigger |
|---|---|
| `source_partition` | The carrier has mathematically active source colours or blocks. |
| `source_layer` | More than one admitted symmetry/incidence layer acts on the same carrier. |
| `coefficient_ring` | A claim depends on integral, rational, or modular coefficients. |
| `lattice_basis` | Any `SNF^L` value is quoted. |
| `characteristic` | A finite-field rank or reduction is quoted. |
| `centering_or_quotient` | The channel uses augmentation, a centered operator, or a quotient. |
| `coupling_class` | A source-quotient extension/coupling is discussed. |
| `placement_embedding` | The result depends on a specific ambient placement. |
| `decision_certificate` | A classification, tiling, non-tiling, or other decision claim is imported. |

A triggered conditional field must have an explicit value at the public locus
named by the crosswalk. An untriggered field is `NA(reason=not_triggered)` by
this schema and need not be copied into every row. Missing data at a triggered
locus is not interpreted as `NA`; it is a source-lock failure.

## Consistency rules

1. `admission` and `pointer_status` are independent. A future or companion
   pointer does not acquire a concrete five-slot instance merely from an X-ID.
2. An admitted concrete instance must expose all five mathematical slots and
   all required metadata fields through the routed public surfaces.
3. Every quoted Smith form must identify its integral lattice or basis.
4. A quantitative replay route must be declared in
   `artifacts/public_evidence_routes.json`; static/human certificates remain
   outside the twelve-route count and must be manifest-pinned.
5. A companion theorem remains companion-owned unless an explicit import
   statement names the theorem, source version, and proof boundary.
6. `Phi` is descriptive. It is never a classifier, tiling oracle, or decision
   certificate unless a separately owned decision theorem is explicitly
   imported.
7. Public source locators must resolve to an immutable version, tag, commit, or
   bundled manifest-pinned artifact.

## Authoritative public surfaces

- Canonical family/admission registry:
  `artifacts/source_instance_manifest.json#/registry_rows`.
- Quantitative route registry: `artifacts/public_evidence_routes.json`.
- Field routing: `docs/SOURCE_LOCK_CROSSWALK.md`.
- Claim scope and ownership: `docs/CLAIM_BOUNDARY.md` and
  `docs/CLAIM_LEDGER.md`.
- Concrete mathematical values: the relevant paper row and its declared
  source, artifact, or static/human certificate.
