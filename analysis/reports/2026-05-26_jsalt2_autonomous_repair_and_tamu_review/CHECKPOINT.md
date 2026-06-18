# Checkpoint — 2026-05-26_jsalt2_autonomous_repair_and_tamu_review

Generated: 2026-05-26T08:24:40-05:00

## Date and campaign/task name

- Date: `2026-05-26`
- Task: repair the autonomous JSALT2 no-input workflow, enforce campaign failure exits, verify the repaired campaign end to end, and close the overnight TAMU/JSALT2 review loop.

## Research question

Can the JSALT2 autonomous/no-input campaign now run through `inspect` and complete locally, and what do the repaired run plus overnight sweep outputs imply about keeping `h` and about which TAMU cases deserve human validation review?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `src/dmdc/resampling.py`
- `src/dmdc/cli.py`
- `src/dmdc/config.py`
- `src/dmdc/campaign.py`
- `tests/test_adaptive_variable_dt.py`
- `tests/test_inspection_resampling.py`
- `tests/test_registry_campaign_archive_schema.py`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/campaign_step_index.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/adaptive_fit/adaptive_dmdc_summary.json`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/compare/model_comparison.csv`
- `outputs/overnight_sweeps/jsalt2_no_h_20260525/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_with_h_20260525/best_model_recommendation.txt`
- `outputs/tamu_validation_export/validation_export_summary.json`
- `outputs/tamu_validation_export_overnight_20260525/validation_export_summary.json`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_cases.csv`

## Commands run

- `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_adaptive_variable_dt.py tests/test_inspection_resampling.py tests/test_registry_campaign_archive_schema.py`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml --dry-run`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml`
- `diff -u outputs/tamu_validation_export/validation_export_summary.json outputs/tamu_validation_export_overnight_20260525/validation_export_summary.json`
- `diff -u outputs/tamu_validation_export/inventory_validation_candidates.csv outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`

## Inputs used

- Autonomous config: `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml`
- Overnight no-`h` sweep: `outputs/overnight_sweeps/jsalt2_no_h_20260525/`
- Overnight with-`h` sweep: `outputs/overnight_sweeps/jsalt2_with_h_20260525/`
- Daytime TAMU export: `outputs/tamu_validation_export/`
- Overnight TAMU export: `outputs/tamu_validation_export_overnight_20260525/`

## Outputs generated

### Code/test verification

- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T132232Z_66c4d1a2/`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T132240Z_39621eff/`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/`

### Report artifacts

- `analysis/reports/2026-05-26_jsalt2_autonomous_repair_and_tamu_review/CHECKPOINT.md`
- `analysis/reports/2026-05-26_jsalt2_autonomous_repair_and_tamu_review/MANIFEST.yaml`

## Key numerical results

- Targeted pytest slice: `17 passed`
- Repaired autonomous campaign run ID: `run_20260526T133003Z_5943a549`
- Repaired autonomous campaign completed steps: `5/5`
- Repaired autonomous compare best model: `pod_dmdc`
- Repaired autonomous compare best test rollout RMSE: `0.37289603980550534`
- Repaired autonomous compare `adaptive_dmdc` test rollout RMSE: `0.7727588071114045`
- Overnight stable no-`h` sweep recommendation: `dmdc`, `delay=4`, `pod_rank=2`, `test_rollout_rmse=0.17075270970574585`
- Overnight stable with-`h` sweep recommendation: `dmdc`, `delay=4`, `pod_rank=2`, `test_rollout_rmse=0.17407191740679362`
- TAMU daytime export counts: `54` inventory candidates, `8` normalized cases, `40` nearest-fit rows
- TAMU overnight export counts: `54` inventory candidates, `8` normalized cases, `40` nearest-fit rows

## Plots/tables generated

- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/campaign_step_index.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/adaptive_fit/adaptive_dmdc_summary.json`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/compare/model_comparison.csv`
- `outputs/overnight_sweeps/jsalt2_no_h_20260525/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_with_h_20260525/best_model_recommendation.txt`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`

## Interpretation

The three intended workflow fixes worked. `inspect-data` now tolerates `input_cols = []`, `dmdc campaign` now exits non-zero when a non-dry-run step fails, and `adaptive-fit` now honors the campaign-derived adaptive output directory. The autonomous JSALT2 campaign that failed on 2026-05-25 completed all five configured steps on 2026-05-26 with adaptive outputs written into the run-local `workflow_outputs/adaptive_fit/` directory.

The `h` decision is still nuanced rather than one-sided. On the default campaign compare path, the no-`h` autonomous rerun is weaker than the earlier with-`h` `pod_dmdc` run (`0.3729` vs `0.3308` test rollout RMSE). But on the broader overnight stable sweeps, the best filtered no-`h` model is slightly better than the best filtered with-`h` model (`0.17075` vs `0.17407`). Current evidence does not justify treating `h` as required for the best stable JSALT2 result; keep it as an optional modeling choice rather than a forced input.

The TAMU overnight export matches the daytime export structurally. The summary JSON diff changed only the output directory string, and the candidate inventory CSVs were byte-identical. That indicates no unexpected drift between the two runs.

## Limitations

- The TAMU nearest-fit table is still advisory only. Human review is still required before any case is promoted into a validation reference set.
- The no-`h` campaign compare result and the overnight sweep recommendation are not directly interchangeable because they evaluate different model-selection scopes.
- The repo worktree remained dirty throughout this checkpoint, with many unrelated in-progress changes already present before today’s edits.

## Bugs or anomalies

- Existing overnight log-path cleanup from the 2026-05-25 checkpoint remains unresolved; this turn did not revisit Slurm stdout/stderr placement.

## Follow-up tasks

1. Decide whether the default JSALT2 study config should keep `h`, drop `h`, or branch into two named study variants, now that the default compare and stable sweep evidence disagree.
2. Review TAMU candidate cases manually, prioritizing real folders rather than synthetic/example folders.
3. If a shortlist is needed immediately, start with salt cases `2024_05_04__2`, `2024_05_04__3`, `2024_05_04__4`, `2024_05_04__6` and water cases `2025_05_20__4`, `2025_03_19__4`, `2025_03_19__7`, `2025_03_19__2`.

## Exact files future agents should inspect first

- `analysis/reports/2026-05-26_jsalt2_autonomous_repair_and_tamu_review/MANIFEST.yaml`
- `analysis/reports/2026-05-26_jsalt2_autonomous_repair_and_tamu_review/CHECKPOINT.md`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/campaign_step_index.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/adaptive_fit/adaptive_dmdc_summary.json`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/compare/model_comparison.csv`
- `outputs/overnight_sweeps/jsalt2_no_h_20260525/best_model_recommendation.txt`
- `outputs/overnight_sweeps/jsalt2_with_h_20260525/best_model_recommendation.txt`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`
- `src/dmdc/resampling.py`
- `src/dmdc/cli.py`
- `src/dmdc/config.py`
