# Checkpoint — 2026-05-25_overnight_tamu_jsalt2_queue

Generated: 2026-05-25T18:03:02-05:00

## Date and campaign/task name

- Date: `2026-05-25`
- Task: submit the overnight TAMU + JSALT2 queue, preserve what ran, and leave
  a restartable journal for tomorrow.

## Research question

What should run overnight to preserve the new TAMU workflow outputs, rerun the
main JSALT2 campaign under the append-only layout, and answer the next JSALT2
modeling questions before tomorrow?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `studies/tamu_loop_data_onboarding/study_config.toml`
- `studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `studies/jsalt2_moose_mesh_convergence_poc/README.md`
- `docs/hpc/batch_workflows.md`
- `src/dmdc/hpc_workflows.py`
- `src/dmdc/cli.py`
- `src/dmdc/resampling.py`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_adaptive_with_h.toml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/*.sbatch`
- `../tamu_loop_data_25_mayo/Loop Operational Data`
- `../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-05-25_workflow_journal.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-05-25_launch_submission_and_journaling_workflow.md`

## Commands run

- `bash -n analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/*.sbatch`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml --dry-run`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_adaptive_with_h.toml --dry-run`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --config analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml --dry-run`
- `ssh -F /dev/null -o BatchMode=yes login3.ls6.tacc.utexas.edu 'hostname'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 01:00:00 --parsable .../tamu_inventory_refresh.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 01:00:00 --parsable .../tamu_validation_export_refresh.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 04:00:00 --parsable .../jsalt2_current_campaign.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 04:00:00 --parsable .../jsalt2_adaptive_with_h.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 04:00:00 --parsable .../jsalt2_autonomous_no_h.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 03:00:00 --parsable .../full_pytest_regression.sbatch'`
- `sacct -j 3185496,3185497,3185498,3185499,3185500,3185501 --format=JobID,JobName%24,State,Elapsed,ExitCode -P`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli inspect-data --config outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260525T230234Z_166e14b8/config/campaign_config.derived.json`

## Inputs used

- Raw TAMU root: `../tamu_loop_data_25_mayo/Loop Operational Data`
- Fluid validation source tables:
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv`
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
- JSALT2 external analysis source:
  - `../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs`
- Slurm queue/account:
  - partition `NuclearEnergy`
  - project `ASC23046`
  - submit host `login3.ls6.tacc.utexas.edu`

## Outputs generated

### Queue / planning artifacts

- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue.yaml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/README.md`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_adaptive_with_h.toml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/configs/jsalt2_autonomous_no_h.toml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/*.sbatch`

### TAMU overnight outputs

- `outputs/tamu_inventory_overnight_20260525/TABLE_OF_CONTENTS.md`
- `outputs/tamu_inventory_overnight_20260525/folder_summaries.md`
- `outputs/tamu_inventory_overnight_20260525/case_inventory.csv`
- `outputs/tamu_inventory_overnight_20260525/metadata_failures.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_cases.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_data.csv`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_export_summary.json`

### JSALT2 overnight outputs

- current POC rerun:
  - `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/`
- adaptive-with-`h` rerun:
  - `outputs/campaigns/jsalt2_moose_mesh_convergence_adaptive_with_h/run_20260525T230237Z_d2c7a1f2/`
- autonomous/no-`h` rerun:
  - `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260525T230234Z_166e14b8/`

### Checkpoint artifacts

- `analysis/reports/2026-05-25_overnight_tamu_jsalt2_queue/MANIFEST.yaml`
- `analysis/reports/2026-05-25_overnight_tamu_jsalt2_queue/CHECKPOINT.md`

## Key numerical results

- Overnight TAMU inventory case rows: `54`
- Overnight TAMU metadata failure rows: `0`
- Overnight TAMU normalized validation cases: `8`
- Overnight TAMU nearest-fit rows: `40`
- JSALT2 current rerun best model: `pod_dmdc`
- JSALT2 current rerun best test rollout RMSE: `0.33081936458561695`
- JSALT2 adaptive-with-`h` rerun best model: `pod_dmdc`
- JSALT2 adaptive-with-`h` best test rollout RMSE: `0.33081936458561695`
- JSALT2 adaptive-with-`h` `adaptive_dmdc` test rollout RMSE: `0.7532141219005815`

## Plots/tables generated

- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/compare/model_comparison.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_adaptive_with_h/run_20260525T230237Z_d2c7a1f2/workflow_outputs/compare/model_comparison.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_cases.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_data.csv`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`

## Interpretation

The overnight queue did what it needed to do. The TAMU refresh jobs completed in
unique output directories, so the daytime outputs remain untouched. The
current JSALT2 campaign rerun and the adaptive-with-`h` variant both completed
cleanly under the append-only campaign layout and confirm the same headline
result as before: `pod_dmdc` remains the best held-out model on this 11-case
collection.

The extra autonomous/no-`h` run was useful because it exposed a real bug rather
than silently succeeding. `inspect-data` crashes when `input_cols = []`, so the
repo is not yet safe for autonomous studies even though that configuration is
otherwise meaningful.

## Limitations

- The overnight queue did not produce repo-local Slurm stdout/stderr files under
  the intended `analysis/campaigns/.../logs/` directory. The jobs completed,
  but log-path behavior still needs cleanup.
- The autonomous/no-`h` campaign produced only import outputs and no compare
  results because `inspect-data` failed before the later steps.
- The TAMU export still requires human review of nearest-fit suggestions before
  any cases are adopted as real validation references.

## Bugs or anomalies

- `inspect-data` with empty `input_cols` fails in `src/dmdc/resampling.py`
  because it assumes the input variance table contains a `variance` column:

```text
KeyError: 'variance'
```

- The `dmdc campaign` wrapper still let the autonomous Slurm job finish with
  wrapper exit code `0:0` even though the `inspect` step failed internally.
- LS6 submission from a compute node still returns the usual stub:
  `NOTIFICATION: sbatch not available on compute nodes. Use a login node.`
  The working path is SSH submission through `login3`.
- LS6 also required both of these at submission time:
  - explicit walltime via `sbatch -t`
  - explicit project via `-A ASC23046`

## Follow-up tasks

1. Review `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv` and `inventory_validation_candidates.csv` to choose actual validation cases.
2. Compare the overnight TAMU export against the daytime `outputs/tamu_validation_export/` outputs and confirm there is no unexpected drift.
3. Check Slurm jobs `3185512` and `3185513`, which were submitted after the main queue to run full JSALT2 sweeps without and with `h`, respectively.
4. Fix the empty-input inspect bug in `src/dmdc/resampling.py` so autonomous studies with `input_cols = []` work.
5. Fix `dmdc campaign` so a failed step returns a non-zero process status to Slurm or any other orchestrator.
6. Decide whether the `h` input adds enough value to keep it. On the current overnight rerun, `adaptive_dmdc` with `h` was still materially weaker than `pod_dmdc`.

## Exact files future agents should inspect first

- `analysis/reports/2026-05-25_overnight_tamu_jsalt2_queue/MANIFEST.yaml`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/README.md`
- `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_cases.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/compare/model_comparison.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_adaptive_with_h/run_20260525T230237Z_d2c7a1f2/workflow_outputs/compare/model_comparison.csv`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260525T230234Z_166e14b8/campaign_step_index.csv`
- `src/dmdc/resampling.py`
