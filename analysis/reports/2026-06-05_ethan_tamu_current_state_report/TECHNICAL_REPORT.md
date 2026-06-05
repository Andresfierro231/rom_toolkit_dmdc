# Current Ethan Runs and TAMU Box Loop Data

Generated: `2026-06-05T10:40:13-05:00`

## Brief Summary

This report consolidates the current state of the sibling `ethan_runs/` CFD workspace and the refreshed `../tamu_box_loop_data/Loop Operational Data` mirror. The two sources are at different maturity levels. Ethan is already in a case-level validation and continuation-decision phase; TAMU is still primarily in an inventory and validation-onboarding phase.

The current evidence supports three practical conclusions.

1. Ethan Salt 2 remains the strongest current validation lane.
   The native continuation case `val_salt_test_2_coarse_mesh_laminar` is still the only active, already-justified continuation target and was confirmed `RUNNING` on job `3202708` during this report pass.

2. Ethan Salt 1 is still the weakest salt family.
   The Kirst Salt 1 row should no longer be treated as converged, and the broader salt-family synthesis still treats Salt 1 as the main exception because both current Salt 1 rows sit on a materially larger heat-balance residual floor.

3. TAMU is rich enough to guide case selection, but not yet strong enough to support automatic validation adoption.
   The refreshed inventory sees `53` case-like subfolders and `43` normalized candidate rows, but every candidate remains `metadata_only` and `ready_for_validation_export=False`.

## 1. Ethan Runs

### 1.1 Portfolio snapshot

Current cross-case counts from the latest available Ethan metadata package plus today's scheduler spot check:

| metric | value |
| --- | ---: |
| analyzable rows | 13 |
| running | 1 |
| completed | 2 |
| terminated | 10 |
| comparison candidates | 1 |
| convergence audit required | 12 |
| Jin rows | 4 |
| Kirst rows | 4 |
| Water rows | 4 |

Useful categories for the current Ethan state:

1. `Active continuation / highest manuscript value`
2. `Completed Kirst reference rows that are still not fully converged`
3. `Practically useful salt rows that still lack coded convergence`
4. `Salt rows that remain weak representatives`
5. `Water laminar diagnostics only`

### 1.2 Active continuation / highest manuscript value

#### `val_salt_test_2_coarse_mesh_laminar`

- What it is:
  Native Salt 2 validation/continuation case, distinct from the staged viscosity-screening Salt 2 Jin/Kirst variants.
- Current status:
  `run_status=running`, `comparison_ready=comparison_candidate`, confirmed live on Slurm job `3202708` at `2026-06-05`.
- Operating point / metadata:
  `heater_power_W=265.7`, `cooling_power_W=56.34`, `T_init_K=451.5`, laminar, `nprocs=64`.
- Evidence available:
  `latest_runtime_write=4066.0 s`; latest published QoI snapshot still reports `mdot_mean_abs_kg_s=0.0136162`, `probe_T_avg_K=452.58`, `exp_tp_rmse_k=2.57`, `exp_tw_rmse_k=6.26`, `exp_mdot_abs_error_pct=18.95`.
- Why it matters:
  This is still the strongest active validation case and the most defensible Salt 2 manuscript representative.
- Claim readiness:
  Strongest current candidate, but still not a clean converged claim because the continuation is active and the coded convergence monitor has not yet fired on the current row.
- Next action:
  Keep as the primary Salt 2 representative; refresh the QoI package after the next meaningful continuation checkpoint.

### 1.3 Completed Kirst reference rows that are still not fully converged

#### `viscosity_screening_salt_test_2_kirst_coarse_mesh`

- What it is:
  Completed Salt 2 Kirst variant for the same nominal heater/cooling target as the native Salt 2 row.
- Current status:
  `run_status=completed`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Operating point / metadata:
  `heater_power_W=265.7`, `cooling_power_W=56.34`.
- Evidence available:
  `final_time=586.56 s`, `mdot_mean_abs_kg_s=0.0122436`, `probe_T_avg_K=446.65`, `exp_tp_rmse_k=4.42`, `exp_tw_rmse_k=6.97`, `exp_mdot_abs_error_pct=27.12`.
- Why it matters:
  This is still the cleanest completed staged Salt 2 sensitivity row, but it should now be treated as a nonconverged reference against the native continuation lane rather than as a clean comparison candidate.
- Claim readiness:
  Diagnostic-only unless a later refresh shows stronger convergence evidence.
- Next action:
  Use as the first staged sensitivity benchmark against the native Salt 2 continuation.

#### `viscosity_screening_salt_test_1_kirst_coarse_mesh`

- What it is:
  Completed Salt 1 Kirst staged sensitivity row.
- Current status:
  `run_status=completed`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Operating point / metadata:
  `heater_power_W=232.3`, `cooling_power_W=55.58`.
- Evidence available:
  `final_time=3279.16 s`, `mdot_mean_abs_kg_s=0.0109321`, `probe_T_avg_K=429.48`, `exp_tp_rmse_k=17.33`, `exp_tw_rmse_k=17.69`, `exp_mdot_abs_error_pct=30.81`, `final_total_wall_heat_abs_w=9.48783`.
- Why it matters:
  It is one of only two completed staged Kirst rows, but it is also the clearest example of why completion alone is not enough by itself.
- Claim readiness:
  Limited. The row should not be treated as converged, and the all-salt package still flags Salt 1 as the main exception because the family retains a larger heat-balance residual floor.
- Next action:
  Keep in the report as an important cautionary example, not as a preferred Salt 1 manuscript representative.

### 1.4 Practically useful salt rows that still lack coded convergence

#### `viscosity_screening_salt_test_4_jin_coarse_mesh`

- What it is:
  Salt 4 Jin staged sensitivity row and current user-facing manuscript sensitivity representative for Salt 4.
- Current status:
  `run_status=terminated`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Operating point / metadata:
  `heater_power_W=337.6`, `cooling_power_W=65.98`.
- Evidence available:
  `final_time=2083.0 s`, `mdot_mean_abs_kg_s=0.0169851`, `probe_T_avg_K=477.38`, `exp_tp_rmse_k=1.69`, `exp_tw_rmse_k=7.56`, `exp_mdot_abs_error_pct=15.50`.
- Why it matters:
  Despite terminated status, it is quantitatively one of the better salt rows and has already been selected as the current Salt 4 manuscript sensitivity representative.
- Claim readiness:
  Diagnostic/manuscript-sensitivity useful, but not a clean validation claim.
- Next action:
  Track its continuation-improvement path, but use with explicit caveats.

#### `viscosity_screening_salt_test_3_jin_coarse_mesh`

- What it is:
  Salt 3 Jin staged sensitivity row.
- Current status:
  `run_status=terminated`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Operating point / metadata:
  `heater_power_W=297.5`, `cooling_power_W=60.55`.
- Evidence available:
  `final_time=2515.0 s`, `mdot_mean_abs_kg_s=0.0149255`, `probe_T_avg_K=461.27`, `exp_tp_rmse_k=2.13`, `exp_tw_rmse_k=6.90`, `exp_mdot_abs_error_pct=14.71`.
- Why it matters:
  The all-salt package currently prefers Salt 3 Jin as the manuscript representative because it remains practically steady and has better mass-flow agreement than the Kirst row.
- Claim readiness:
  Useful for manuscript interpretation with explicit audit caveats; not yet a clean validation claim.
- Next action:
  Keep ahead of the Salt 3 Kirst row in the priority queue unless a future refresh materially changes the steadiness audit.

#### `viscosity_screening_salt_test_4_kirst_coarse_mesh`

- What it is:
  Salt 4 Kirst staged sensitivity row.
- Current status:
  `run_status=terminated`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Operating point / metadata:
  Same Salt 4 target as the Jin row: `heater_power_W=337.6`, `cooling_power_W=65.98`.
- Evidence available:
  `final_time=2984.0 s`, `mdot_mean_abs_kg_s=0.0158792`, `probe_T_avg_K=477.21`, `exp_tp_rmse_k=2.22`, `exp_tw_rmse_k=7.27`, `exp_mdot_abs_error_pct=21.00`.
- Why it matters:
  The all-salt package treats it as the steadier current Salt 4 reference even though the Jin row remains the chosen manuscript sensitivity representative.
- Claim readiness:
  Better as a steady-reference diagnostic row than as the main manuscript row.
- Next action:
  Keep paired with Salt 4 Jin so the report preserves the Jin-vs-Kirst tradeoff explicitly.

### 1.5 Salt rows that remain weak representatives

#### `viscosity_screening_salt_test_1_jin_coarse_mesh`

- What it is:
  Salt 1 Jin staged sensitivity row.
- Current status:
  `run_status=terminated`, `convergence_reached=False`, `comparison_ready=convergence_audit_required`.
- Why it matters:
  The all-salt package still prefers this row over Salt 1 Kirst as the future continuation candidate, but not because it is already strong. It is preferred only because Salt 1 has no clean representative yet.
- Interpretation:
  Salt 1 is still the family to describe as unresolved rather than merely incomplete.

### 1.6 Water laminar diagnostics only

All four water laminar rows remain `needs_convergence_audit` in the refreshed `2026-06-05_water_laminar_claim_audit`.

| case | status | final time (s) | mdot mean abs (kg/s) | avg probe T (K) | claim status |
| --- | --- | ---: | ---: | ---: | --- |
| `water_test_1` | terminated | 3195 | 0.006506 | 315.28 | needs_convergence_audit |
| `water_test_2` | terminated | 2436 | 0.007834 | 320.61 | needs_convergence_audit |
| `water_test_3` | terminated | 2254 | 0.008933 | 324.77 | needs_convergence_audit |
| `water_test_4` | terminated | 1468 | 0.010871 | 334.89 | needs_convergence_audit |

Interpretation:
- Water rows are useful for trend inspection only.
- `water_test_4` is the weakest of the four because it combines the shortest runtime with no recorded convergence marker.

### 1.7 Ethan trend summary

Useful cross-case trends:

1. Salt 2 is still the best validation lane.
   It combines the best live continuation story with strong direct TP error and a clear manuscript role.

2. Salt 3 and much of Salt 4 are more useful than their terminated status alone suggests.
   Their temperature and mass-flow errors are materially better than Salt 1, so they remain valuable for paper narrative with explicit caveats.

3. Jin vs Kirst affects mass-flow more than ambient-loss.
   The all-salt synthesis reads this as evidence that the dominant ambient-loss error is shared wall-loss model bias, not only viscosity-branch choice.

4. Water remains structurally behind salt.
   Current water rows are best treated as diagnostic context, not as accepted validation claims.

## 2. TAMU Box Loop Data

### 2.1 Portfolio snapshot

Current refreshed inventory and validation-export counts:

| metric | value |
| --- | ---: |
| top-level items | 23 |
| indexed directories | 65 |
| case-like subfolders | 53 |
| metadata parse failures | 0 |
| normalized candidate rows | 43 |
| auto-ready validation rows | 0 |

Candidate distribution by top-level folder:

| top-level folder | candidate rows |
| --- | ---: |
| `2025_06_19` | 17 |
| `2024_05_04` | 7 |
| `2025_03_19` | 7 |
| `2025_12_30` | 5 |
| `2025_05_20` | 4 |
| `2024_03_13` | 3 |

Useful categories for TAMU:

1. `Collaborator-confirmed salt anchors`
2. `Advisory water-side nearest-fit anchors`
3. `Largest recent acquisition family`
4. `Metadata-only candidates not yet ready for validation export`

### 2.2 Collaborator-confirmed salt anchors

The refreshed nearest-fit table is stronger than the prior June 2 snapshot because it now uses recognized-case mapping for the key `2024_05_04` salt subfolders:

| target case | case_dir | heater W | air flow Lpm | test-section power W | review status |
| --- | --- | ---: | ---: | ---: | --- |
| `Salt 1` | `2024_05_04/2` | 258 | 37 | 44.8 | known_case_subfolder |
| `Salt 2` | `2024_05_04/3` | 295 | 37 | 44.8 | known_case_subfolder |
| `Salt 3` | `2024_05_04/4` | 362 | 37 | 44.8 | known_case_subfolder |
| `Salt 4` | `2024_05_04/6` | 395 | 37 | 44.8 | known_case_subfolder |

These are the highest-value TAMU subfolders because:
- they are directly recognized rather than only inferred by nearest-fit distance
- they are compact and consistent, with repaired metadata and the same six-file structure
- they are the cleanest bridge between the raw mirror and the salt validation case family

### 2.3 Advisory water-side nearest-fit anchors

The water-side mappings are still weaker and remain advisory-only.

| target case | case_dir | heater W | air flow Lpm | test-section power W | distance score |
| --- | --- | ---: | ---: | ---: | ---: |
| `Water 1` | `2025_05_20/4` | 325 | 75 | 22.08 | 0.5327 |
| `Water 2` | `2025_03_19/4` | 150 | 200 | 0.0 | 0.517556 |
| `Water 3` | `2024_05_04/1` | 201 | 37 | 44.8 | 0.46077 |
| `Water 4` | `2025_03_19/4` | 150 | 200 | 0.0 | 0.398333 |

Interpretation:
- `2025_03_19/4` is the single most useful current water-side exploratory anchor because it appears as the best current advisory match for multiple Water targets.
- `2025_05_20/4` is the best current Water 1 candidate, but it is still only metadata-based.
- No water-side TAMU subfolder should yet be described as a confirmed validation-case match.

### 2.4 Largest recent acquisition family

`2025_06_19` remains the largest and most important exploratory family:

- `17` candidate rows
- heater range from roughly `200` to `402` W
- air-flow range from roughly `30` to `45` L/min
- shared test-section power of `22.8` W across most rows

Representative central row chosen for first-pass analysis:

| case_dir | heater W | air flow Lpm | test-section power W | file count | note |
| --- | ---: | ---: | ---: | ---: | --- |
| `2025_06_19/16` | 300 | 35 | 22.8 | 7 | includes both transient and fiber-optic workspaces |

Why `2025_06_19/16` matters:
- it is near the middle of the dominant June-family operating range
- it includes richer file structure than the six-file minimal subfolders
- it is a better exploratory family representative than choosing an edge case

### 2.5 Metadata-only limitation

The refreshed TAMU export still shows:

- all `43` candidate rows are `review_status=metadata_only`
- all `43` have `ready_for_validation_export=False`

That means the current TAMU mirror is ready for:
- case selection
- family trend mapping
- paper planning for which experimental subfolders to prioritize next

It is not yet ready for:
- automatic validation adoption
- strong quantitative case matching claims without additional human review or deeper normalization

### 2.6 TAMU trend summary

Useful TAMU trends:

1. `2024_05_04` is the most paper-useful salt-side family right now.
   It has the strongest recognized mapping to named Salt cases.

2. `2025_03_19` is the most useful current water-side family.
   In particular, `/4` is the strongest advisory anchor across several Water targets.

3. `2025_06_19` is the most important exploratory family.
   It is the largest, spans a useful heater/airflow ladder, and includes at least one richer mixed-workspace row.

4. The overall bottleneck is not missing files but missing promotion from metadata-only status into validation-ready status.

## 3. First Four and Next Priority Order

### 3.1 First four analyzed first

1. `val_salt_test_2_coarse_mesh_laminar`
   Chosen because it is the strongest current Ethan manuscript lane, is still actively running, and should be anchored to the latest written continuation step.

2. `viscosity_screening_salt_test_4_jin_coarse_mesh`
   Chosen because it is one of the strongest practically useful salt rows even without a clean convergence claim.

3. `2024_05_04/3`
   Chosen because it is the collaborator-confirmed refreshed TAMU Salt 2 anchor and the cleanest raw-data mirror bridge to the Salt 2 experimental family.

4. `2025_03_19/4`
   Chosen because it is the strongest current water-side advisory anchor and therefore the most useful TAMU water-family planning case.

### 3.2 Next order of priority

5. `viscosity_screening_salt_test_3_jin_coarse_mesh`
6. `2024_05_04/2`
7. `2024_05_04/4`
8. `2024_05_04/6`
9. `viscosity_screening_salt_test_1_kirst_coarse_mesh`
10. `2025_06_19/16`
11. `2025_05_20/4`
12. `2024_05_04/1`
13. `viscosity_screening_salt_test_4_kirst_coarse_mesh`
14. `viscosity_screening_salt_test_3_kirst_coarse_mesh`
15. `viscosity_screening_salt_test_2_kirst_coarse_mesh`
16. `viscosity_screening_salt_test_2_jin_coarse_mesh`
17. `viscosity_screening_salt_test_1_jin_coarse_mesh`
18. Water laminar rows in descending urgency: `water_test_4`, `water_test_3`, `water_test_2`, `water_test_1`

## 4. Limitations and Paper-Use Cautions

1. The Ethan metadata package itself did not regenerate cleanly during this turn.
   The package remained at the June 4 artifact timestamp, so this report uses those June 4 per-case tables plus a fresh June 5 Slurm status check for the active Salt 2 continuation.

2. The refreshed TAMU export is still metadata-only.
   It supports prioritization and case-family interpretation, but not strong validation claims.

3. Several Ethan salt rows are practically useful before they are coded-converged.
   That is useful for technical narrative, but it must be stated explicitly in any paper draft to avoid overclaiming.

4. Water-side conclusions are weaker than salt-side conclusions on both sources.
   Ethan water CFD rows are still audit-only, and TAMU water-side subfolder mapping is still advisory-only.


## 5. Appendix Tables

For downstream reuse, the report package also carries machine-readable appendix tables:

- `priority_queue.csv`
- `ethan_priority_metrics.csv`
- `tamu_priority_subfolders.csv`
