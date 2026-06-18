# Checkpoint — 2026-06-02_jsalt2_tamu_followup

Generated: 2026-06-02T11:05:00-05:00

## Date and campaign/task name

- Date: `2026-06-02`
- Task: fix TAMU validation candidate filtering, re-stage collaborator-facing inventory artifacts, resolve the apparent JSALT2 compare-vs-sweep disagreement, and submit the full pytest guardrail from a valid login-node path.

## Research question

Can the TAMU candidate tables be cleaned so they stop surfacing example/pseudo rows, does the current raw-data mirror differ materially from the May 2026 inventory basis, and is the JSALT2 model-selection disagreement a real contradiction or just a wider hyperparameter search than the default compare path uses?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `src/dmdc/tamu_data.py`
- `tests/test_tamu_inventory_and_validation.py`
- `studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`
- `outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/compare/model_comparison.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/compare/model_comparison.csv`
- `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/best_model_recommendation.txt`
- `../tamu_box_loop_data/README.md`
- `../tamu_box_loop_data/Loop Operational Data`
- `../ethan_runs/journals/2026-06/2026-06-02_ethan_runs.md`
- `../ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/README.md`
- `../cfd-modeling-tools/AGENTS.md`

## Commands run

- `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_tamu_inventory_and_validation.py tests/test_tamu_study_workflow.py -q`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-inventory --root "../tamu_box_loop_data/Loop Operational Data" --outdir outputs/tamu_inventory_20260602_filtered`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-export --inventory-root "../tamu_box_loop_data/Loop Operational Data" --source-tables ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv --outdir outputs/tamu_validation_export_20260602_filtered`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli sweep --data outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet --state-cols TP1 TP2 TP3 TP6 massFlowRate --input-cols h --time-col time --case-col case_id --train-fraction 0.75 --models persistence mean dmdc ridge_dmdc pod_dmdc --pod-ranks 0.999 --dmdc-ranks full --n-delays 1 --center --outdir outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli sweep --data outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet --state-cols TP1 TP2 TP3 TP6 massFlowRate --time-col time --case-col case_id --train-fraction 0.75 --models persistence mean adaptive_dmdc dmdc ridge_dmdc pod_dmdc --pod-ranks 0.999 --dmdc-ranks full --n-delays 1 --center --outdir outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602`
- `sbatch -A ASC23046 -t 03:00:00 --parsable analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`
- `sacct -j 3202576 --format=JobID,JobName%24,State,Elapsed,ExitCode -P`
- `python tools/box/upload_to_tamu_flow_loop_box.py --dry-run --source-root to_box/flat_inventory_upload_2026-06-02_filtered`
- `python tools/box/upload_to_tamu_flow_loop_box.py --dry-run --source-root to_box/operational_data_inventory_2026-06-02_filtered`
- `python tools/box/upload_to_tamu_flow_loop_box.py --execute --source-root to_box/flat_inventory_upload_2026-06-02_filtered`
- `python tools/box/upload_to_tamu_flow_loop_box.py --execute --source-root to_box/operational_data_inventory_2026-06-02_filtered`

## Inputs used

- Current TAMU raw-data mirror root: `../tamu_box_loop_data/Loop Operational Data`
- Validation source tables:
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv`
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
- JSALT2 with-`h` import parquet: `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet`
- JSALT2 no-`h` import parquet: `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet`
- Slurm queue/account: partition `NuclearEnergy`, project `ASC23046`
- Box outputs destination: folder ID `385169164073`
- Raw-data Box source folder (not used for upload): folder ID `246873664013`

## Outputs generated

### Code/test verification

- Updated filter logic in `src/dmdc/tamu_data.py`
- Regression coverage in `tests/test_tamu_inventory_and_validation.py`
- Targeted TAMU pytest slice passed locally

### Filtered TAMU artifacts

- `outputs/tamu_inventory_20260602_filtered/`
- `outputs/tamu_validation_export_20260602_filtered/`

### JSALT2 apples-to-apples follow-up artifacts

- `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/`
- `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/`

### Box staging artifacts

- `to_box/flat_inventory_upload_2026-06-02_filtered/`
- `to_box/operational_data_inventory_2026-06-02_filtered/`

### Checkpoint artifacts

- `analysis/reports/2026-06-02_jsalt2_tamu_followup/CHECKPOINT.md`
- `analysis/reports/2026-06-02_jsalt2_tamu_followup/MANIFEST.yaml`
- `TODO_2026-06-02_jsalt2_tamu_followup.md`

## Key numerical results

- Targeted TAMU pytest slice: `6 passed`
- Submitted full pytest guardrail job: `3202576`
- Guardrail final state: `COMPLETED`
- Guardrail elapsed time: `00:02:22`
- Guardrail exit code: `0:0`
- Filtered TAMU inventory summary: `23` top-level items, `65` directories indexed, `53` case directories, `0` metadata failures
- Filtered TAMU validation export: `43` inventory candidates, `8` normalized validation cases, `40` nearest-fit rows
- Prior overnight candidate-table size: `54` rows including example/demo, pseudo, and `Jadyn_runs` metadata-only entries
- New candidate-table size: `43` rows
- Candidate-row reduction after filtering: `11`
- Compare-equivalent with-`h` best candidate: `pod_dmdc`, `pod_rank=0.999`, `dmdc_rank=full`, `n_delays=1`, `test_rollout_rmse=0.3308193645862872`
- Compare-equivalent no-`h` best candidate: `pod_dmdc`, `pod_rank=0.999`, `dmdc_rank=full`, `n_delays=1`, `test_rollout_rmse=0.37289603980526714`
- Broader stable filtered sweep winner, no-`h`: `dmdc`, `pod_rank=2`, `n_delays=4`, `test_rollout_rmse=0.17075270970574585`
- Broader stable filtered sweep winner, with-`h`: `dmdc`, `pod_rank=2`, `n_delays=4`, `test_rollout_rmse=0.17407191740679362`
- Box upload execute summaries:
  - flat filtered staging upload: `8` new files
  - nested filtered staging upload: `9` new files

## Plots/tables generated

- `outputs/tamu_validation_export_20260602_filtered/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_20260602_filtered/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_20260602_filtered/validation_cases.csv`
- `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/sweep_results.csv`
- `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/best_model_recommendation.txt`
- `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/sweep_results.csv`
- `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/best_model_recommendation.txt`

## Interpretation

The TAMU candidate-table fix worked. The regenerated `inventory_validation_candidates.csv` and `nearest_fit_suggestions.csv` no longer include the obvious example-folder rows, the empty pseudo-row `2025_06_19`, or the metadata-only `Jadyn_runs` rows that were not actually usable for nearest-fit matching. The collaborator-facing filtered tables were then staged through `to_box/` and uploaded to the Box outputs folder, not the raw-data source folder.

The raw-data mirror did change operationally since the May 2026 checkpoint, but as a path/layout change rather than a visible content refresh. The old sibling path `../tamu_loop_data_25_mayo` is no longer the active mirror root in this workspace; the current mirror is `../tamu_box_loop_data`. The visible `Loop Operational Data/` contents and top-level mtimes still look unchanged relative to the May 25 inventory basis, so there is no evidence in this pass of a new raw-data drop inside the mirror contents themselves.

The JSALT2 compare-vs-sweep disagreement is now explained rather than unresolved. When the sweep is constrained to the same hyperparameters the default compare path actually uses (`pod_rank=0.999`, `dmdc_rank=full`, `n_delays=1`, same train fraction, same imported tables), the winner is `pod_dmdc` in both with-`h` and no-`h` variants and the RMSEs match the existing compare outputs to machine precision. The apparent contradiction only appears when the broader sweep is allowed to search a larger space that the default compare command does not cover, especially `n_delays=4` for `dmdc`.

Current implication: the open decision is not whether `compare` is wrong. The real decision is whether the project wants the narrower default compare path or the broader sweep search space to be the authoritative model-selection surface for JSALT2.

## Limitations

- This turn did not clean or commit the broader dirty worktree because many unrelated in-progress changes were already present.
- This turn did not change the core `compare` command behavior; it only ran compare-equivalent sweep follow-ups to explain the existing disagreement.
- Box upload success is based on uploader execution summaries in this repo session; this checkpoint does not include a separate post-upload remote folder listing.
- The JSALT2 external-analysis import scope still depends on the current maintained external collection layout.

## Bugs or anomalies

- Local sandbox tooling intermittently failed with namespace exhaustion (`bwrap ... ENOSPC`), which blocked `apply_patch` and some ordinary local file-copy commands. Edits, regenerations, and staging work were completed through the escalated shell path instead.
- `squeue -j 3202576` returned `Invalid job id specified` after submission; `sacct` provided the reliable final status.

## Follow-up tasks

1. Decide whether JSALT2 final model selection should be based on the default compare surface or on the broader sweep surface that includes delay search.
2. If broader sweep selection is the policy, document that explicitly and consider a named study variant or workflow note so users do not mistake delay-1 compare results for final tuned-model results.
3. For future JSALT2 sweeps, prioritize split robustness and search-surface design over simply repeating the same pair:
   - repeated/alternative case splits or leave-one-case-out style checks
   - `n_delays` extension for delay-capable linear models, e.g. `1, 2, 4, 8`
   - `pod_rank` sensitivity around both integer ranks and energy thresholds
   - `center` / `scale` toggles
   - with-`h` vs no-`h` as named variants, not an implicit silent toggle
4. Revisit the JSALT2 collection scope only when the external analysis tree gains more case CSVs. The current visible collection still appears to be `11` named case directories, so `max_files = 11` already spans the current collection.
5. If collaborator review of the new TAMU filtered tables reveals any remaining nuisance rows, tighten the filter with another regression test before regenerating Box artifacts.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-02_jsalt2_tamu_followup/CHECKPOINT.md`
- `TODO_2026-06-02_jsalt2_tamu_followup.md`
- `src/dmdc/tamu_data.py`
- `tests/test_tamu_inventory_and_validation.py`
- `outputs/tamu_validation_export_20260602_filtered/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_20260602_filtered/nearest_fit_suggestions.csv`
- `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/best_model_recommendation.txt`
- `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/best_model_recommendation.txt`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`
- `../tamu_box_loop_data/README.md`
