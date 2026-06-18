# Overnight queue — 2026-05-25

This queue is intended to use the overnight window for:

1. one clean rerun of the current JSALT2 campaign using the append-only campaign
   layout
2. two JSALT2 follow-up variants that answer open modeling questions from the
   previous proof-of-concept
3. fresh TAMU inventory/export artifacts in unique output directories so today's
   outputs are preserved
4. a full regression suite run as a background guardrail

## Jobs prepared

| Order | Job name | Script | Purpose | Expected main outputs |
| --- | --- | --- | --- | --- |
| 1 | `dmdc_tamu_inv` | `jobs/tamu_inventory_refresh.sbatch` | Rebuild TAMU inventory in a unique overnight outdir. | `outputs/tamu_inventory_overnight_20260525/` |
| 2 | `dmdc_tamu_val` | `jobs/tamu_validation_export_refresh.sbatch` | Rebuild normalized and PHYSOR-style validation exports in a unique overnight outdir. | `outputs/tamu_validation_export_overnight_20260525/` |
| 3 | `dmdc_jsalt2_cur` | `jobs/jsalt2_current_campaign.sbatch` | Clean append-only rerun of the current JSALT2 POC campaign. | `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/<run_id>/` |
| 4 | `dmdc_jsalt2_adh` | `jobs/jsalt2_adaptive_with_h.sbatch` | JSALT2 variant with `h` retained and explicit adaptive-time outputs. | `outputs/campaigns/jsalt2_moose_mesh_convergence_adaptive_with_h/<run_id>/` |
| 5 | `dmdc_jsalt2_aut` | `jobs/jsalt2_autonomous_no_h.sbatch` | JSALT2 variant with `input_cols = []` to test the autonomous interpretation. | `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/<run_id>/` |
| 6 | `dmdc_pytest` | `jobs/full_pytest_regression.sbatch` | Full regression suite on the current dirty tree. | Slurm log plus any failing test traces |
| 7 | `dmdc_swph` | `jobs/jsalt2_sweep_with_h.sbatch` | Rank/delay/model sweep on the successful JSALT2 imported table with `h` included. | `outputs/overnight_sweeps/jsalt2_with_h_20260525/` |
| 8 | `dmdc_swno` | `jobs/jsalt2_sweep_no_h.sbatch` | Rank/delay/model sweep on the autonomous imported table with no input columns. | `outputs/overnight_sweeps/jsalt2_no_h_20260525/` |

## Notes

- The TAMU jobs write to unique overnight outdirs and do not overwrite the
  daytime `outputs/tamu_inventory` or `outputs/tamu_validation_export` trees.
- The JSALT2 jobs use `dmdc campaign`, so each run should materialize a unique
  run directory and update the campaign-level run index.
- The full `pytest` job is intentionally extra capacity use. It is not a data
  product, but it can catch an overnight regression while the cluster is idle.
- Queue/account used for submission: `NuclearEnergy` on project `ASC23046`.

## Submitted runs

| Job ID | Job name | Final state | Elapsed | Result note |
| --- | --- | --- | --- | --- |
| `3185496` | `dmdc_tamu_inv` | `COMPLETED` | `00:00:10` | Rebuilt `outputs/tamu_inventory_overnight_20260525/`; `metadata_failures.csv` contains header only. |
| `3185501` | `dmdc_tamu_val` | `COMPLETED` | `00:00:04` | Rebuilt `outputs/tamu_validation_export_overnight_20260525/`; 8 normalized cases and 40 nearest-fit suggestions. |
| `3185499` | `dmdc_jsalt2_cur` | `COMPLETED` | `00:00:20` | Current POC rerun succeeded under `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/`. |
| `3185500` | `dmdc_jsalt2_adh` | `COMPLETED` | `00:00:23` | Adaptive-with-`h` variant succeeded under `outputs/campaigns/jsalt2_moose_mesh_convergence_adaptive_with_h/run_20260525T230237Z_d2c7a1f2/`. |
| `3185498` | `dmdc_jsalt2_aut` | `COMPLETED` | `00:00:10` | Wrapper job completed, but the campaign stopped at `inspect`; see checkpoint for the `KeyError: 'variance'` failure signature. |
| `3185497` | `dmdc_pytest` | `COMPLETED` | `00:00:36` | Full regression job finished with exit code `0`. |

## Late additions

After the first queue completed, two more worthwhile jobs were submitted using
the already-imported JSALT2 tables so they can keep running tonight without
repeating import/inspect:

| Job ID | Job name | State at submission check | Purpose |
| --- | --- | --- | --- |
| `3185512` | `dmdc_swno` | `RUNNING` | Full rank/delay/model sweep on the autonomous JSALT2 import with no input columns. |
| `3185513` | `dmdc_swph` | `RUNNING` | Full rank/delay/model sweep on the successful JSALT2 import with `h` retained as an input. |
