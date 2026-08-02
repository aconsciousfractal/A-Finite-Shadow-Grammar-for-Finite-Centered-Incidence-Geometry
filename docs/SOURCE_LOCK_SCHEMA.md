# Typed Source-Lock Schema

Schema version: 3

## Purpose

A concrete row remains the five-slot datum `S=(N,X,I,rho,Phi)`. The source lock supplies public provenance and interpretation metadata. A complete record is assembled from the instance registry, the relevant manuscript section, its cited source or bundled artifact, and the route registry when computation is used.

## Required fields

| Field | Type | Rule |
|---|---|---|
| `family_id` | `X01`-`X26` | source-family slot, never the finite subset by itself |
| `instance_id` | nonempty string | required for an admitted concrete instance |
| `family_parameter` | scalar, string, or `NA(reason)` | distinct from ambient degree `N` |
| `ambient_degree` | positive integer | concrete symmetric degree |
| `carrier` | finite-set specification | includes projective, signed, or source-colored labeling rules |
| `ambient_action` | group-action specification | acting group or finite shadow in `S_N` |
| `action_convention` | convention record | action side, composition order, and matrix convention when relevant |
| `finite_row_X` | exact finite-row specification | definition, explicit list, or immutable artifact |
| `incidence_I` | exact incidence or selection rule | defines membership in the row |
| `channel_rho` | representation or operator specification | includes domain, codomain, and centering convention |
| `fingerprint_Phi` | bounded fingerprint specification | only the ranks, Smith data, source splits, or related fields actually recorded |
| `source_locator` | citation or bundled path | public and immutable when used as authority |
| `source_version` | tag, commit, version, or package checksum | required for a movable source |
| `admission` | enum | `admitted` or `not_admitted` |
| `pointer_status` | enum | `not_applicable`, `future`, or `public_companion` |
| `descriptive_role` | non-normative label | routing aid, not a mathematical type |
| `claim_owner` | public work or this paper | identifies the source that owns the statement |
| `verification_route` | executable route, static certificate, proof, or classical source | must match the claim type |
| `import_boundary` | bounded statement | what this paper actually uses |
| `nonimport_boundary` | exclusion statement | prevents theorem-ownership transfer or family-wide inference |

## Conditional fields

| Field | Trigger |
|---|---|
| `source_partition` | mathematically active source colors or blocks |
| `source_layer` | multiple admitted symmetry or incidence layers on one carrier |
| `coefficient_ring` | integral, rational, or modular dependence |
| `lattice_basis` | a lattice-qualified Smith form is quoted |
| `characteristic` | a finite-field rank or reduction is quoted |
| `centering_or_quotient` | augmentation, centering, or quotient is used |
| `coupling_class` | a source-quotient extension is discussed |
| `placement_embedding` | the result depends on an ambient placement |
| `decision_certificate` | a classification or other decision claim is imported |

A triggered field must be explicit at the public locus named by the crosswalk. An untriggered field is `NA(reason=not_triggered)`.

## Consistency rules

1. Admission and pointer status are independent.
2. Every admitted concrete row exposes all five mathematical slots and all triggered metadata.
3. Every quoted Smith form identifies its integral lattice or basis.
4. Every quantitative replay is declared in `artifacts/public_evidence_routes.json`.
5. Static certificates and human proofs remain outside the twelve-route count.
6. Companion theorems remain companion-owned unless an explicit import statement names the theorem, source version, and proof boundary.
7. `Phi` remains descriptive unless a separately proved decision theorem is explicitly imported.
8. Public source locators resolve to an immutable version or a manifest-pinned artifact.
