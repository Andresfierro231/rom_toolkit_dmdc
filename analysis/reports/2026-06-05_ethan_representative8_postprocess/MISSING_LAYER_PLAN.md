# Missing-Layer Plan

## Bottom Line

Yes, we can probably get the missing layer without a full new physics campaign.

The fastest path is not to restart all 8 runs immediately. The first move should be a zero-advance postprocessing pass on the latest written state for one salt case and one water case. The existing Ethan cases already define `wallHeatFlux` and a coded `Nu` field in `system/functions`, so the likely blocker is downstream extraction from the parallel case, not absence of the underlying field definitions.

For the currently running salt continuations, adding function objects and waiting for one more accepted step is technically feasible because:
- `controlDict` uses `runTimeModifiable true`
- `controlDict` includes `system/functions`
- the active jobs are still running as of June 5, 2026: `3202708`, `3210231`, `3210760`, `3210761`

But I would treat live modification as fallback, not first choice. Offline `reconstructPar` + `foamPostProcess` on the latest written time is safer and should answer most of the capability question.

## Prescribed HTC

If by "prescribed HTC" you mean the boundary-condition heat-transfer coefficients used in the 3D cases, we already have them. They are metadata, not a derived postprocessing quantity. They are now summarized in `prescribed_htc_table.csv`.

What we do not yet have is a consolidated table of derived effective HTCs, meaning quantities backed out from `q_w`, `T_w`, and `T_bulk`.

## Target Outputs For The Same 8

For the representative 8, the missing layer should be defined as these concrete products:

1. `axial_wall_patch_table.csv`
- One row per wall patch per case.
- Columns: `source_id`, `patch_name`, `leg_group`, `section_progress_0to1`, `areaAverage_T_w_k`, `areaAverage_Nu`, `areaAverage_wallHeatFlux_w_m2`, `q_total_w`.

2. `axial_bulk_station_table.csv`
- One row per internal station per case.
- Columns: `source_id`, `station_name`, `leg_group`, `section_progress_0to1`, `areaAverage_T_bulk_k`, `mdot_kg_s`, `areaAverage_p_rgh_pa`.

3. `axial_joined_profile_table.csv`
- One joined profile table mapping each wall patch to its nearest internal bulk station.
- Columns: `source_id`, `patch_name`, `station_name`, `T_w_k`, `T_bulk_k`, `deltaT_fw_k`, `wallHeatFlux_w_m2`, `h_internal_w_m2k`, `Nu_internal`.

4. `section_resistance_table.csv`
- One row per major section per case.
- Columns: `source_id`, `section_name`, `Q_section_w`, `T_bulk_section_k`, `T_wall_section_k`, `T_amb_section_k`, `R_fluid_to_wall_K_per_W`, `R_wall_to_ambient_K_per_W`, `R_fluid_to_ambient_K_per_W`, `abs_delta_p_rgh_pa` when available.

5. `thermal_circuit_table.csv`
- First reduced network per case.
- At minimum: heater branch, lower transport, test section, upper transport/cooler branch, downcomer, junction lump.

6. `representative8_postprocess_readiness.csv`
- Pass/fail table showing which of the above were populated for each case.

## Recommended Technical Route

### Phase 1: Zero-Advance Extraction Test

Do this first on 3 cases:
- `val_salt_test_2_coarse_mesh_laminar`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`
- `val_water_test_1_coarse_mesh_laminar`

Goal:
- confirm whether `T`, `Nu`, and `wallHeatFlux` can be reconstructed and sampled from the latest written state without advancing the solver.

Method:
- copy or symlink each runtime into a disposable temp case under `../ethan_runs/tmp_extract/`
- `reconstructPar -time <latest> -fields '(T Nu wallHeatFlux p_rgh phi)'`
- for `val_salt_test_2_coarse_mesh_laminar`, always use the actual latest processor time/write, not the older probe-history horizon
- run a custom `foamPostProcess` dictionary that samples:
  - wall patches: `areaAverage(T Nu wallHeatFlux)`
  - internal bulk stations: `areaAverage(T p_rgh)` plus `sum(phi)` and `sum(phi*T)` on face zones

Success criterion:
- at least one salt case and one water case produce nonblank `T_w`, `Nu`, and bulk-station `T_bulk` rows.

If Phase 1 succeeds, do not touch the live jobs.

### Phase 2: Harden The Extraction Path

If Phase 1 works, generalize it to all 8 with a new reusable Ethan-side builder, for example:
- `../ethan_runs/tools/analyze/build_ethan_representative8_transport_package.py`

That builder should:
- read the current representative-8 list from the existing convergence package
- create disposable extract cases
- reconstruct only the latest written time
- run the sampling dicts
- publish the 6 tables listed above

### Phase 3: Fallback To Live/Short Continuation Only If Needed

Only do this if Phase 1 fails because the latest written state does not contain the fields we need or reconstructs unreliably.

For the active salt jobs:
- `val_salt_test_2_coarse_mesh_laminar`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `viscosity_screening_salt_test_1_jin_coarse_mesh`

we can append new function objects and wait for one accepted step because the runs are live and `runTimeModifiable` is enabled.

Important detail:
- the new postprocessors must use `writeControl timeStep; writeInterval 1;`
- do not rely on `outputTime`, since that may require too much additional physical runtime

For the terminated representative rows:
- `viscosity_screening_salt_test_3_jin_coarse_mesh`
- `val_water_test_1_coarse_mesh_laminar`
- `val_water_test_2_coarse_mesh_laminar`
- `val_water_test_3_coarse_mesh_laminar`
- `val_water_test_4_coarse_mesh_laminar`

prefer short continuation clones rather than modifying the source trees in place.

## What Needs To Be Added

### A. Wall-patch sampling dict

Use the existing ordered wall patches and sample:
- `T`
- `Nu`
- `wallHeatFlux`
- optionally `wallShearStress`

This gives us:
- `T_w(x)`
- `Nu(x)`
- `q_w(x)`

### B. Bulk-station sampling dict

We need internal stations for `T_bulk(x)`.

Best first-pass definition:
- reuse existing mdot face zones where available
- add a small number of new face zones per leg if needed through `topoSetDict`
- compute bulk temperature as mass-flux-weighted temperature:
  - `T_bulk = sum(phi*T) / sum(phi)`

This is the most important new missing quantity.

### C. Join logic between wall patches and bulk stations

For the first package, do not chase exact arc-length registration.
Use:
- existing `leg_group`
- existing ordered `section_progress_0to1`
- nearest station in the same leg

That is good enough for a first thermal-circuit table.

## How To Compute The New Quantities

### Internal HTC

For each wall patch or section:
- `h_internal = |q_w| / max(|T_w - T_bulk|, eps)`

### Internal Nusselt

For each wall patch or section:
- `Nu_internal = h_internal * D_h / k(T_bulk)`

Use the same local conductivity law already embedded in the Ethan function objects.

### Fluid-to-wall resistance

For each section:
- `R_fluid_to_wall = |T_bulk - T_w| / max(|Q_section|, eps)`

### Wall-to-ambient resistance

For each section with ambient loss:
- `R_wall_to_ambient = |T_w - T_amb,BC| / max(|Q_ambient_section|, eps)`

### Total fluid-to-ambient resistance

For each section:
- `R_fluid_to_ambient = |T_bulk - T_amb,BC| / max(|Q_ambient_section|, eps)`

### Heater and cooler branch entries

For heater and cooler sections, keep the sign convention explicit and also publish absolute-value magnitudes.

## Case Priority

Do the 8 in this order:

1. `val_salt_test_2_coarse_mesh_laminar`
2. `viscosity_screening_salt_test_4_jin_coarse_mesh`
3. `viscosity_screening_salt_test_3_jin_coarse_mesh`
4. `viscosity_screening_salt_test_1_kirst_coarse_mesh`
5. `val_water_test_1_coarse_mesh_laminar`
6. `val_water_test_2_coarse_mesh_laminar`
7. `val_water_test_3_coarse_mesh_laminar`
8. `val_water_test_4_coarse_mesh_laminar`

Rationale:
- Salt 2 is the best current representative and active continuation.
- Salt 4 is a manuscript-priority salt case.
- Salt 3 is the strongest terminated salt comparison row.
- Salt 1 remains physically important but still has a residual-floor problem.
- Water 1-4 complete the 8-run representative set.

## Recommended Execution Decision

Recommended path:
- yes, build the missing layer for the representative 8
- no, do not start by editing all live runs
- first run an offline zero-advance extraction test on Salt 2, Salt 3, and Water 1
- only if that fails, add timeStep-based postprocessors to the active salt jobs and create short continuation clones for the nonrunning rows

## Expected Effort

If Phase 1 works:
- 0 queue-risk for most cases
- mostly scripting and extraction hardening

If Phase 3 is needed:
- low queue-risk for the active salt jobs
- moderate operational overhead for short continuation clones of Salt 3 and Water 1-4
