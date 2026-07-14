# Normative Source-Lock Crosswalk

This crosswalk routes the fields of the normative public schema in
`docs/SOURCE_LOCK_SCHEMA.md`.  Admitted concrete rows are **governed by** that
schema; the package does not claim that one standalone, consolidated `L(S)`
object has already been published for every row.

It identifies the authoritative public evidence surface for each field and
family.  Triggered conditional fields must be explicit at the routed locus;
untriggered fields follow the schema's `NA(reason=not_triggered)` rule without
requiring a duplicated consolidated record.

The single canonical post-S44 admission registry is
`artifacts/source_instance_manifest.json` (`registry_rows`).  Its `admission` field
is typed independently from `pointer_status`:

- `admission` is either `admitted` or `not_admitted`;
- `pointer_status` is `not_applicable`, `future`, or `public_companion`;
- a future or companion pointer does not receive a filled five-slot instance
  merely because it has an X-ID.

The registry content at `a3cfafe` is part of the S44H-R author-replayed
baseline.  Commit `16be346502e754bd6282adb5216599bed26ab8d6` passed the
independent S46 replay.  S46H changes only the bounded source/governance and
paper surfaces declared in its allowlist; the existing quantitative route
surface remains byte-identical.

## Required-field crosswalk

| Schema field | Authoritative public locus | Scope rule |
|---|---|---|
| `family_id` | `artifacts/source_instance_manifest.json` (`registry_rows[].id`) | Exactly one of X01-X26. |
| `instance_id` | Paper row labels/tables in `paper/sections/04_*` through `paper/sections/14_*`, Appendix A, and the declared route artifacts | Required for an admitted concrete instance; not manufactured for pointers or the X14 meta row. |
| `family_parameter` | The relevant paper row plus Appendix A | Distinct from ambient `N`; use `NA(reason)` when the family is not parameterized. |
| `ambient_degree` | The relevant paper row, Appendix A, and bounded artifact payload | Concrete `N`, not the family rank symbol. |
| `carrier` | The relevant paper row and its declared source/artifact | Includes the labelling rule when the carrier is projective or source-coloured. |
| `ambient_action` | `paper/sections/02_finite_shadow_grammar.tex` plus the relevant row section/artifact | Records the acting group or subgroup in `S_N`. |
| `action_convention` | `paper/sections/02_finite_shadow_grammar.tex`, the relevant row section, and source script where computation is used | Left/right and composition details remain source-scoped. |
| `finite_row_X` | The relevant row section and exact bundled artifact or companion locator | Identifies the concrete finite subset; the X-ID alone is never used as that subset. |
| `incidence_I` | `paper/sections/02_finite_shadow_grammar.tex` and the relevant row section/artifact | Exact incidence rule for the concrete row. |
| `channel_rho` | `paper/sections/03_fingerprint_channel.tex`, `paper/sections/03b_modular_centered_channels.tex`, and the relevant row section | Includes domain/codomain or centered operator. |
| `fingerprint_Phi` | The channel sections, relevant row section, and replay artifact where quantitative | Includes basis/lattice qualification when used. |
| `source_locator` | `paper/refs.bib`, the registry `verification` field, and `artifacts/public_evidence_routes.json` | Primary citation or exact bundled path. |
| `source_version` | Registry `verification`, bibliographic locator, Git source pin where cited, and the package checksum layer | S44H-R binds `a3cfafe`; independent S46 binds `16be346`; S46H files are pinned by the regenerated package manifest. |
| `admission` | Registry `admission` | Typed only as `admitted` or `not_admitted`. |
| `pointer_status` | Registry `pointer_status` | Typed independently as `not_applicable`, `future`, or `public_companion`. |
| `descriptive_role` | Registry `role` and Appendix A | Routing label only; not an admission value. |
| `claim_owner` | Registry `owner` | P13 or the named companion owner. |
| `verification_route` | Registry `verification` plus `artifacts/public_evidence_routes.json` for the twelve quantitative routes | X13 uses a static certificate/checker, X15-002 a self-contained proof, and G-004/CPL-001 human proof/classical sources; none is a thirteenth route. |
| `import_boundary` | Registry `boundary`, relevant paper row, and `docs/CLAIM_BOUNDARY.md` | States the bounded material actually used by P13. |
| `nonimport_boundary` | Registry `boundary`, relevant paper row, and `docs/CLAIM_BOUNDARY.md` | Blocks theorem ownership transfer, classification, tiling, and family-wide inference. |

## Conditional-field crosswalk

| Conditional field | Public locus when triggered |
|---|---|
| `source_partition` | X19/G2 in `paper/sections/07_g2_length_colored_root_shadow.tex` and its route artifact; source-coloured exceptional rows in their row sections/artifacts. |
| `source_layer` | X20/F4 in `paper/sections/08_f4_projective_root_shadow.tex` and `artifacts/f4_source_layer_replay.json`; analogous root-shadow layers in their row sections. |
| `coefficient_ring` | X16 in `paper/sections/03b_modular_centered_channels.tex`; integral/lattice-qualified rows in their sections and artifacts. |
| `lattice_basis` | X13/X18 and any quoted `SNF^L` value in the channel/row text and artifact. |
| `characteristic` | X16 modular row and `artifacts/modular_centered_channel_replay.json`. |
| `centering_or_quotient` | X05/X16 and G-004/CPL-001 in the relevant paper section and source artifact/proof. |
| `coupling_class` | G-004/CPL-001 in `paper/sections/16_value_and_limits_of_phi.tex`; no new X-ID or numerical route is created. |
| `placement_embedding` | Rows whose result depends on ambient placement, especially the bounded E7/E8 controls, in their row sections and artifacts. |
| `decision_certificate` | `NA(reason=not_triggered)` for the nonimporting X10/P33 pointer. This field is triggered only if P13 imports a classification, tiling, non-tiling, or other decision claim. |

## Family-to-locus crosswalk

| ID | Admission | Pointer status | Primary public row or pointer locus | Verification locus |
|---|---|---|---|---|
| X01 | admitted | not_applicable | `paper/sections/04_type_a_source_rows.tex`; Appendix A | pinned public sources in `paper/refs.bib` |
| X02 | admitted | not_applicable | Type-A material in section 04 and the contrast/limits sections | cited companion certificates where used |
| X03 | admitted | not_applicable | section 04; Appendix A | bounded public dependency artifacts |
| X04 | admitted | not_applicable | section 04; Appendix A | pinned P03 witness source |
| X05 | admitted | not_applicable | section 04; Appendix A | X05 route and `artifacts/x05/` |
| X06 | admitted | not_applicable | section 04 and cited Latin companion context | companion commit `8984359d0f7fd66e4eaa7864a557d6b907e9f9ec` |
| X07 | not_admitted | future | `paper/sections/17_boundaries_and_future_routes.tex` | no current P13 replay |
| X08 | admitted | not_applicable | section 04; Appendix A | pinned P11/P12 sources |
| X09 | admitted | not_applicable | section 04 provenance/contrast prose | P01/P03 provenance |
| X10 | not_admitted | public_companion | section 04 and section 17 pointer prose | bounded P07/P33 context only; neither theorem nor proof imported; no all-`n` claim |
| X11 | not_admitted | future | section 17 future pointer | version-neutral P18 pointer; no release pin required while nonimporting |
| X12 | not_admitted | future | section 17 future pointer | P17 context only; no admitted row or theorem import |
| X13 | admitted | not_applicable | sections 02, 03, 04, and 16; Appendix A | public proof, classical lock, and `artifacts/x13_type_a_lattice_rank_mass_certificate.json` plus read-only checker |
| X14 | admitted | not_applicable | grammar/contrast/limits prose | definitions and governance; meta row, not a concrete instance |
| X15 | admitted | not_applicable | `paper/sections/05_signed_type_bc_source_rows.tex`; Appendix A | X15-001 six-row replay plus X15-002 self-contained proof; P15 theorem/proof excluded |
| X16 | admitted | not_applicable | modular channel section; Appendix A | public X16 replay |
| X17 | not_admitted | public_companion | contrast and future-route pointer prose | public P15 companion; no proof import |
| X18 | admitted | not_applicable | `paper/sections/06_dihedral_vertex_shadows.tex`; Appendix A | public X18 replay |
| X19 | admitted | not_applicable | `paper/sections/07_g2_length_colored_root_shadow.tex`; Appendix A | exported public X19 replay |
| X20 | admitted | not_applicable | `paper/sections/08_f4_projective_root_shadow.tex`; Appendix A | exported public X20 replay |
| X21 | admitted | not_applicable | `paper/sections/09_h3_projective_source_channel.tex`; Appendix A | public X21 replay |
| X22 | admitted | not_applicable | `paper/sections/10_h4_projective_source_channel.tex`; Appendix A | public X22 replay |
| X23 | admitted | not_applicable | `paper/sections/11_d5_projective_root_shadow_control.tex`; Appendix A | public X23 replay |
| X24 | admitted | not_applicable | `paper/sections/12_e6_projective_root_shadow_control.tex`; Appendix A | public X24 replay |
| X25 | admitted | not_applicable | `paper/sections/13_e7_projective_root_shadow_control.tex`; Appendix A | public X25 replay |
| X26 | admitted | not_applicable | `paper/sections/14_e8_projective_root_shadow_subsystem_separator.tex`; Appendix A | public X26 replay |

## Non-X classical guardrail

`G-004/CPL-001` records the retained S36/S37 source-coupling/descent
guardrail.  Its locus is `paper/sections/16_value_and_limits_of_phi.tex`; its
verification route is human proof plus classical sources.  It has no numerical
replay, no novelty claim, no new X-ID, and imports no general descent or
transfer theorem.
