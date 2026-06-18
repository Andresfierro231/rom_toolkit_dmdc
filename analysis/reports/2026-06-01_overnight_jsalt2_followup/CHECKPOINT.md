# Checkpoint — 2026-06-01_overnight_jsalt2_followup

Generated: 2026-06-01T18:21:41-05:00

## Date and campaign/task name

- Date: `2026-06-01`
- Task: prepare and submit the next overnight JSALT2 follow-up jobs after the repaired autonomous/no-`h` campaign and today's Box cleanup.

## Research question

Which overnight jobs are ready now, and can they be submitted cleanly from the current repository state without inventing a new speculative queue?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/jsalt2_sweep_no_h.sbatch`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/jsalt2_sweep_with_h.sbatch`
- `analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/jobs/full_pytest_regression.sbatch`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/config/campaign_config.derived.json`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/import_summary.json`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/README.md`

## Commands run

- `bash -n analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `bash -n analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `bash -n analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`
- `ls -la outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet`
- `ssh -F /dev/null -o BatchMode=yes login3.ls6.tacc.utexas.edu 'hostname'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 03:00:00 --parsable /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 03:00:00 --parsable /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch'`
- `ssh -F /dev/null login3.ls6.tacc.utexas.edu 'sbatch -A ASC23046 -t 03:00:00 --parsable /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch'`

## Inputs used

- Repaired no-`h` import parquet: `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet`
- With-`h` comparison import parquet: `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet`
- Slurm queue/account target: partition `NuclearEnergy`, project `ASC23046`, submit host `login3.ls6.tacc.utexas.edu`

## Outputs generated

### Queue / planning artifacts

- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup.yaml`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/README.md`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`

### Checkpoint artifacts

- `analysis/reports/2026-06-01_overnight_jsalt2_followup/CHECKPOINT.md`
- `analysis/reports/2026-06-01_overnight_jsalt2_followup/MANIFEST.yaml`

## Key numerical results

- Sbatch scripts syntax-checked: `3/3`
- Sweep input parquet files verified present: `2/2`
- Slurm job IDs returned: `0`

## Interpretation

The overnight queue is technically prepared and defensible. The no-`h` sweep now uses the repaired autonomous campaign lineage from `2026-05-26`, the with-`h` sweep provides a direct comparison pair, and the pytest job is a reasonable guardrail because the repo remains dirty in `src/dmdc/` and campaign-facing code.

The only blocker is authentication, not job readiness. SSH reached the TACC login path, but interactive password and token prompts prevented unattended `sbatch` submission from this session.

## Limitations

- No jobs can be claimed as queued because no Slurm job IDs were returned.
- This checkpoint does not include runtime or result outputs because submission did not complete.

## Bugs or anomalies

- None in the prepared scripts or local inputs.
- External blocker: TACC MFA/password prompt required interactive authentication.

## Follow-up tasks

1. Re-run the three prepared `ssh ... sbatch ...` commands from an authenticated TACC session.
2. Once job IDs are returned, update this checkpoint with the submission results and monitor them with `sacct`.
3. If desired, add a fourth overnight job later only after deciding whether the TAMU inventory/export needs a rerun based on raw-data mirror changes.

## Exact files future agents should inspect first

- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/README.md`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/full_pytest_regression.sbatch`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet`
