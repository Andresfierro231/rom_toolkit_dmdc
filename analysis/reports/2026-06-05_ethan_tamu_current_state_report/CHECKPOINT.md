# Checkpoint — 2026-06-05_ethan_tamu_current_state_report

Generated: `2026-06-05T10:40:13-05:00`

## Date and campaign/task name

- Date: `2026-06-05`
- Task: write a combined current-state report on `ethan_runs` and `tamu_box_loop_data`, refresh lightweight source artifacts, and rank the first cases/subfolders for deeper follow-on analysis.

## Research question

What do the current Ethan CFD runs and the refreshed TAMU raw-data mirror support today, what is already paper-useful versus still only diagnostic, and which items should be analyzed first?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `studies/tamu_loop_data_onboarding/README.md`
- `studies/tamu_loop_data_onboarding/scripts/run_01_inventory.sh`
- `studies/tamu_loop_data_onboarding/scripts/run_02_export_validation_cases.sh`
- `docs/workflows/tamu_data_intake_and_validation.md`
- `analysis/reports/2026-06-02_jsalt2_tamu_followup/CHECKPOINT.md`
- `analysis/reports/2026-05-26_tamu_loop_data_inventory_report/CHECKPOINT.md`
- `outputs/tamu_inventory_20260605_current/inventory_summary.json`
- `outputs/tamu_inventory_20260605_current/EXECUTIVE_SUMMARY.md`
- `outputs/tamu_validation_export_20260605_current/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_20260605_current/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_20260605_current/validation_cases.csv`
- `../ethan_runs/README.md`
- `../ethan_runs/journals/2026-06/2026-06-02_ethan_runs.md`
- `../ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/README.md`
- `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md`
- `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.json`
- `../ethan_runs/reports/2026-06-04_all_salt_behavior_package/README.md`
- `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit/README.md`
- `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit/water_laminar_claim_audit.csv`
- `../ethan_runs/work_products/campaigns/2026-06-01_modern_runs_first_batch/qoi_availability.csv`

## Commands run

- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short`
- `bash studies/tamu_loop_data_onboarding/scripts/run_01_inventory.sh ../tamu_box_loop_data/Loop\ Operational\ Data outputs/tamu_inventory_20260605_current`
- `bash studies/tamu_loop_data_onboarding/scripts/run_02_export_validation_cases.sh ../tamu_box_loop_data/Loop\ Operational\ Data outputs/tamu_validation_export_20260605_current ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
- `python ../ethan_runs/tools/analyze/build_ethan_report_package.py`
- `python ../ethan_runs/tools/analyze/build_all_salt_behavior_package.py`
- `python ../ethan_runs/tools/analyze/build_water_laminar_claim_audit.py --report-slug 2026-06-05_water_laminar_claim_audit`
- `squeue -j 3202708`
- multiple read-only `python -c` summary extractions against refreshed TAMU CSVs and Ethan report tables

## Inputs used

- TAMU raw-data mirror root: `../tamu_box_loop_data/Loop Operational Data`
- TAMU salt validation source: `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv`
- TAMU water validation source: `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
- Ethan metadata package root: `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index`
- Ethan all-salt synthesis root: `../ethan_runs/reports/2026-06-04_all_salt_behavior_package`
- Ethan refreshed water audit root: `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit`

## Outputs generated

- `outputs/tamu_inventory_20260605_current/`
- `outputs/tamu_validation_export_20260605_current/`
- `../ethan_runs/reports/2026-06-04_all_salt_behavior_package/` refreshed in-place
- `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit/`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/EXECUTIVE_SUMMARY.md`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/TECHNICAL_REPORT.md`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/priority_queue.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/ethan_priority_metrics.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/tamu_priority_subfolders.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/CHECKPOINT.md`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/MANIFEST.yaml`

## Key numerical results

- TAMU top-level items: `23`
- TAMU directories indexed: `65`
- TAMU case-like subfolders: `53`
- TAMU metadata failures: `0`
- TAMU normalized candidate rows: `43`
- TAMU auto-ready validation rows: `0`
- TAMU largest candidate family: `2025_06_19` with `17` rows
- Ethan analyzable rows: `13`
- Ethan comparison candidates: `1`
- Ethan convergence-audit-required rows: `12`
- Ethan running/completed/terminated split: `1 / 2 / 10`
- Active Salt 2 continuation job: `3202708`
- Active Salt 2 scheduler state at check time: `RUNNING`

## Plots/tables generated or referenced

- `outputs/tamu_inventory_20260605_current/folder_comparison.csv`
- `outputs/tamu_inventory_20260605_current/case_inventory.csv`
- `outputs/tamu_validation_export_20260605_current/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_20260605_current/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_20260605_current/validation_cases.csv`
- `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- `../ethan_runs/reports/2026-06-04_all_salt_behavior_package/all_salt_case_status.csv`
- `../ethan_runs/reports/2026-06-04_all_salt_behavior_package/representative_case_selection.csv`
- `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit/water_laminar_claim_audit.csv`

## Interpretation

The current Ethan workspace is already in a manuscript-triage phase, while TAMU is still in a case-selection phase. Salt 2 remains the strongest current Ethan validation case. Salt 3 and much of Salt 4 are technically useful despite lacking coded convergence, while Salt 1 remains the weakest salt family. TAMU is structurally well indexed and now includes recognized salt-case mapping for `2024_05_04`, but the validation-export lane is still metadata-only and should not yet be promoted into automatic validation adoption.

## Limitations

- `python ../ethan_runs/tools/analyze/build_ethan_report_package.py` did not emit a clean completion line during this turn, and the Ethan metadata package timestamp remained `2026-06-04`. This report therefore uses those June 4 Ethan per-case tables plus a fresh June 5 live scheduler check for Salt 2.
- The TAMU candidate table remains `metadata_only` across all rows.
- No expensive CFD reruns or TAMU raw-data renormalization beyond the existing CLI workflows were performed.

## Bugs or anomalies

- Local sandbox execution remained intermittently blocked by namespace exhaustion (`bwrap ... ENOSPC`), so several refresh and inspection commands were rerun outside the sandbox.
- The Ethan metadata refresh command appears to have hung or stalled without updating its output timestamps.

## Follow-up tasks

1. Refresh Ethan QoI extraction for `val_salt_test_2_coarse_mesh_laminar` after the next meaningful continuation checkpoint.
2. Diagnose why `build_ethan_report_package.py` did not exit cleanly during this pass.
3. Promote TAMU beyond `metadata_only` by reviewing whether the refreshed recognized salt mappings can safely drive a narrower validation-ready shortlist.
4. Revisit `2025_06_19` as the main exploratory TAMU family once deeper normalization or figure extraction is requested.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/TECHNICAL_REPORT.md`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/priority_queue.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/ethan_priority_metrics.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/tamu_priority_subfolders.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/MANIFEST.yaml`
- `outputs/tamu_inventory_20260605_current/EXECUTIVE_SUMMARY.md`
- `outputs/tamu_validation_export_20260605_current/nearest_fit_suggestions.csv`
- `../ethan_runs/reports/2026-06-04_all_salt_behavior_package/README.md`
- `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- `../ethan_runs/reports/2026-06-05_water_laminar_claim_audit/README.md`
