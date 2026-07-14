# Protected Quantitative Surface

Status: `S46H_PUBLIC_REPLAY_INHERITANCE_RECIPE`.

Baseline commit: `16be346502e754bd6282adb5216599bed26ab8d6`.

This file makes the S46H replay-inheritance claim reproducible. The protected
surface is exactly the 75 baseline paths listed below. It consists of every
baseline Python file under `scripts/`, every baseline file under `tests/` and
`results/`, every baseline file under `artifacts/` except the separately
governed `artifacts/source_instance_manifest.json`, plus `.gitattributes`,
`.gitignore`, and `requirements.txt`.

The S46H X13 checker is intentionally absent: it is a new read-only static
certificate checker, not one of the twelve replay routes. Manuscript,
governance, checksum, and source-instance-manifest files are also outside this
quantitative protected set.

## Exact digest recipe

From the repository root in PowerShell:

```powershell
$base = '16be346502e754bd6282adb5216599bed26ab8d6'
$scripts = @(git ls-tree -r --name-only $base -- scripts |
  Where-Object { $_ -like '*.py' })
$tests = @(git ls-tree -r --name-only $base -- tests)
$results = @(git ls-tree -r --name-only $base -- results)
$artifacts = @(git ls-tree -r --name-only $base -- artifacts |
  Where-Object { $_ -ne 'artifacts/source_instance_manifest.json' })
$fixed = @('.gitattributes', '.gitignore', 'requirements.txt')
$protected = [Collections.Generic.HashSet[string]]::new(
  [StringComparer]::Ordinal)
@($scripts + $tests + $results + $artifacts + $fixed) |
  ForEach-Object { [void]$protected.Add($_) }
$lines = @(Get-Content SHA256SUMS.txt | Where-Object {
  $parts = $_ -split '  ', 2
  $parts.Count -eq 2 -and $protected.Contains($parts[1])
})
if ($protected.Count -ne 75 -or $lines.Count -ne 75) { throw 'surface mismatch' }
$bytes = [Text.UTF8Encoding]::new($false).GetBytes(
  ($lines -join "`n") + "`n")
$sha = [Security.Cryptography.SHA256]::Create()
([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '')
```

The order is the order inherited from `SHA256SUMS.txt`; separators and the
single final terminator are LF, encoded as UTF-8 without BOM. Expected digest:

`D34456D1330F3B0A27BD47920679088803ECCFAC8E9DB37C40A6BC3546459C0E`.

## Exact 75-path allowlist

```text`n.gitattributes
.gitignore
artifacts/d5_projective_source_channel_replay.json
artifacts/dihedral_vertex_shadow_replay.json
artifacts/e6_projective_source_channel_replay.json
artifacts/e7_projective_source_channel_replay.json
artifacts/e8_projective_automorphism_transcript.txt
artifacts/e8_projective_source_channel_replay.json
artifacts/e8_standard_parabolic_fusion_certificate.json
artifacts/e8_subsystem_separator_witnesses.json
artifacts/f4_source_layer_replay.json
artifacts/g2_source_channel_replay.json
artifacts/h3_projective_source_channel_replay.json
artifacts/h3_projective_source_channel_replay_seed.json
artifacts/h4_projective_source_channel_replay.json
artifacts/h4_projective_source_channel_replay_seed.json
artifacts/modular_centered_channel_replay.json
artifacts/public_evidence_routes.json
artifacts/signed_type_bc_shadow_replay.json
artifacts/x05/census_rows1000_v2.json
artifacts/x05/census_summary1000_v2.json
artifacts/x05/lat565_global_linearization_check.json
artifacts/x05/lat565_global_rankdrop_linearization.json
artifacts/x05/lat565_pair_dependency_verification.json
artifacts/x05_m19_lat565_evidence_check.json
artifacts/x15/P14_S7_INDEPENDENT_RECOMPUTE_CERTIFICATE.json
requirements.txt
results/p14_s4_first_atlas.json
results/p14_s6_5_rank_mass_formula_scout.json
results/p14_s7_independent_recompute.json
results/p14_s7_independent_recompute_summary.json
results/p20_s10d_source_profile_witness.json
results/p20_s3_channel_engine.json
results/p20_s4_length_defect_certificate.json
results/p20_s5_orbit_centered_balance.json
results/p20_s6_two_mirror_transfer.json
results/p21_s1_s3_projective_root_engine_replay.json
results/p21_s14_block_triality_true_witness_hunt_replay.json
results/p21_s15_flat_invariant_beyond_length_replay.json
results/p21_s4_length_line_theorem_replay.json
results/p21_s5_matroid_source_generator_lock_replay.json
scripts/d5_projective_source_channel_replay.py
scripts/dihedral_vertex_shadow_replay.py
scripts/e6_projective_root_engine.py
scripts/e6_projective_source_channel_replay.py
scripts/e6_projective_source_rows.py
scripts/e7_projective_flat_channel.py
scripts/e7_projective_root_engine.py
scripts/e7_projective_source_channel_replay.py
scripts/e7_projective_source_rows.py
scripts/e7_projective_weyl_action.py
scripts/e8_projective_source_channel_replay.py
scripts/f4_source_layer_replay.py
scripts/g2_source_channel_replay.py
scripts/h3_projective_source_channel_replay.py
scripts/h4_projective_source_channel_replay.py
scripts/modular_centered_channel_replay.py
scripts/p14_s7_independent_recompute.py
scripts/p20_s10d_source_profile_witness.py
scripts/p20_s3_channel_engine.py
scripts/p20_s4_length_defect_certificate.py
scripts/p20_s5_orbit_centered_balance.py
scripts/p20_s6_two_mirror_transfer.py
scripts/p21_f4_projective_root_engine.py
scripts/p21_s14_block_triality_true_witness_hunt.py
scripts/p21_s15_flat_invariant_beyond_length.py
scripts/p21_s4_length_line_theorem.py
scripts/p21_s5_matroid_source_generator_lock.py
scripts/p21_s6_block_triality_channel_scout.py
scripts/p21_s7_flat_incidence_profile_scout.py
scripts/signed_type_bc_shadow_replay.py
scripts/verify.py
scripts/x05_m19_census_full_regeneration.py
scripts/x05_m19_lat565_evidence_check.py
tests/test_verify_fail_closed.py
```

A change to any listed file invalidates replay inheritance and requires a new
full replay. Changes outside the list still require the package-specific
short gates and regenerated integrity files.
