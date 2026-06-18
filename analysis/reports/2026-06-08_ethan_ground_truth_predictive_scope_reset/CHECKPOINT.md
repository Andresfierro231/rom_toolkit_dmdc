# Checkpoint — 2026-06-08_ethan_ground_truth_predictive_scope_reset

Generated: `2026-06-08T12:24:00-05:00`

## Date and campaign/task name

- Date: `2026-06-08`
- Task: implement the Ethan-ground-truth predictive scope reset, add repo-native 2D and 1D study scaffolding, rebuild canonical Ethan tables, and execute the first compare and validate runs.

## Research question

If Ethan CFD is treated as the working ground-truth source for the next few months, what predictive workflows can be stood up immediately inside the existing `dmdc` CLI, what is already verified today, and what must still run before stronger predictive claims are ready?

## Repository state

- Branch: `main`
- Commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Dirty working tree: `True`

## Source files inspected

- `studies/ethan_ground_truth_predictive/README.md`
- `studies/ethan_ground_truth_predictive/study_config_2d.toml`
- `studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml`
- `studies/ethan_ground_truth_predictive/scripts/_common.sh`
- `studies/ethan_ground_truth_predictive/scripts/run_03_compare_2d.sh`
- `studies/ethan_ground_truth_predictive/scripts/run_04_validate_2d.sh`
- `studies/ethan_ground_truth_predictive/scripts/run_07_compare_1d.sh`
- `studies/ethan_ground_truth_predictive/scripts/run_08_validate_1d.sh`
- `tools/studies/build_ethan_ground_truth_tables.py`
- `.agents/tools/studies/build_ethan_ground_truth_tables.py`
- `../ethan_runs/reports/2026-06-04_ethan_transient_axial_package/all_salt_transient_timeseries.csv`
- `../ethan_runs/reports/2026-06-04_ethan_transient_axial_package/all_salt_axial_patch_heat_timeseries.csv`
- `../ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/case_inventory.csv`
- `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- `outputs/ethan_ground_truth_predictive/2d_inspection/case_quality_dashboard.csv`
- `outputs/ethan_ground_truth_predictive/2d_inspection/warnings.txt`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_inspection/case_quality_dashboard.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_inspection/warnings.txt`
- `outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/2d_compare/error_by_case.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/error_by_case.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/forecast_horizon_errors.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/forecast_horizon_errors.csv`
- `outputs/campaigns/ethan_ground_truth_predictive_2d/run_20260608T170452Z_da378d7c/campaign_plan.md`
- `outputs/campaigns/ethan_ground_truth_predictive_1d_axial_heat/run_20260608T170452Z_8eb5b180/campaign_plan.md`

## Commands run

- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `python tools/studies/build_ethan_ground_truth_tables.py`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli inspect-data --config studies/ethan_ground_truth_predictive/study_config_2d.toml`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli inspect-data --config studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config studies/ethan_ground_truth_predictive/study_config_2d.toml --dry-run`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml --dry-run`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli compare --config studies/ethan_ground_truth_predictive/study_config_2d.toml`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli compare --config studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli validate --config studies/ethan_ground_truth_predictive/study_config_2d.toml`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli validate --config studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml`

## Inputs used

- Ethan transient metrics: `../ethan_runs/reports/2026-06-04_ethan_transient_axial_package/all_salt_transient_timeseries.csv`
- Ethan axial heat metrics: `../ethan_runs/reports/2026-06-04_ethan_transient_axial_package/all_salt_axial_patch_heat_timeseries.csv`
- Ethan inventory: `../ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/case_inventory.csv`
- Ethan metadata fallback: `../ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`

## Outputs generated

- `data/processed/ethan_ground_truth_predictive_2d.csv`
- `data/processed/ethan_ground_truth_predictive_1d_axial_heat.csv`
- `data/processed/ethan_ground_truth_predictive_manifest.json`
- `outputs/ethan_ground_truth_predictive/2d_inspection/`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_inspection/`
- `outputs/ethan_ground_truth_predictive/2d_compare/`
- `outputs/ethan_ground_truth_predictive/2d_validation/`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/`
- `outputs/campaigns/ethan_ground_truth_predictive_2d/run_20260608T170452Z_da378d7c/`
- `outputs/campaigns/ethan_ground_truth_predictive_1d_axial_heat/run_20260608T170452Z_8eb5b180/`
- `analysis/campaigns/2026-06-08_ethan_ground_truth_predictive_scope_reset.yaml`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/EXECUTIVE_SUMMARY.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/CHECKPOINT.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/MANIFEST.yaml`

## Key numerical results

- `2D` canonical table rows: `22,140`
- `1D axial heat` canonical table rows: `20,520`
- `2D` cases represented: `9`
- `1D axial heat` cases represented: `9`
- `2D` usable cases from inspection: `9 / 9`
- `1D axial heat` usable cases from inspection: `9 / 9`
- `2D` inspection warnings: `0`
- `1D axial heat` inspection warnings: `2`
- `2D compare` best held-out model: `persistence` with test RMSE `5.557706183000499`
- `1D compare` best held-out model: `persistence` with test RMSE `4.087636896404323`
- `2D pod_dmdc validate` train/test RMSE: `0.8985943775391863 / 156.8483948279097`
- `1D pod_dmdc validate` train/test RMSE: `0.35944261987520604 / 17.073730133234395`

## Plots/tables generated

- `data/processed/ethan_ground_truth_predictive_manifest.json`
- `outputs/ethan_ground_truth_predictive/2d_inspection/case_quality_dashboard.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_inspection/case_quality_dashboard.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_inspection/warnings.txt`
- `outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/2d_compare/error_by_case.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/error_by_case.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/forecast_horizon_errors.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/forecast_horizon_errors.csv`
- `outputs/campaigns/ethan_ground_truth_predictive_2d/run_20260608T170452Z_da378d7c/campaign_plan.md`
- `outputs/campaigns/ethan_ground_truth_predictive_2d/run_20260608T170452Z_da378d7c/campaign_step_index.csv`
- `outputs/campaigns/ethan_ground_truth_predictive_1d_axial_heat/run_20260608T170452Z_8eb5b180/campaign_plan.md`
- `outputs/campaigns/ethan_ground_truth_predictive_1d_axial_heat/run_20260608T170452Z_8eb5b180/campaign_step_index.csv`

## Interpretation

The Ethan-ground-truth scope reset is now implemented inside the existing repo workflow rather than as an external note. The repository now has a durable table-builder entrypoint, two study configs, reusable run scripts, refreshed inspections, refreshed campaign dry-run plans, and first actual compare and validate outputs for both the 2D and 1D lanes.

The measured result is not that the current ROMs are already predictive winners. The measured result is that the current explicit held-out split is baseline-dominated by `persistence`. The ROM families fit the training cases extremely well, but they fail badly on the native Salt 2 holdout while remaining low-error on the held-out Jin Salt 3 and Salt 4 cases. That points to a domain-shift or configuration-gap problem centered on the native Salt 2 case, not a uniform failure across all unseen test cases.

TAMU should now be treated as a future external-check track. It becomes a predictive unseen-case validation story only after canonical TAMU timeseries are imported, unseen TAMU cases are held out explicitly, and executed `compare` plus `validate` artifacts show case-level generalization.

## Limitations

- The `1D` study currently models axial heat aggregates, not a fuller axial temperature and transport state.
- Replay or real-time forecast outputs were not generated in this turn.
- The current compare surfaces are still narrow; no broader sweep was executed in this turn.

## Bugs or anomalies

- Sandbox Python execution repeatedly failed with namespace exhaustion (`bwrap ... ENOSPC`), so several Python verification and execution commands were rerun outside the sandbox.
- `apply_patch` encountered the same namespace-exhaustion issue during implementation, so a subset of file edits used a shell-writing fallback to complete the requested work.

## Follow-up tasks

1. Treat `persistence` as the current baseline claim in both lanes.
2. Build broader 2D and 1D Ethan-only search configs aimed at reducing the native Salt 2 holdout error.
3. Rerun validation only after a revised ROM candidate beats the persistence baseline.
4. Repair the zero-advance transport extraction so a fuller 1D axial state contract can replace the current heat-only contract.
5. After a ROM lane beats persistence on the explicit-case split, stage replay and throughput evaluation.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/EXECUTIVE_SUMMARY.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/MANIFEST.yaml`
- `analysis/campaigns/2026-06-08_ethan_ground_truth_predictive_scope_reset.yaml`
- `data/processed/ethan_ground_truth_predictive_manifest.json`
- `outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/validation_summary.csv`

## Missing information

- No broader sweep outputs exist yet for either Ethan lane.
- No replay or live-forecast throughput measurements exist yet.
- No TAMU canonical timeseries import package exists yet for a true unseen-case validation trial.
