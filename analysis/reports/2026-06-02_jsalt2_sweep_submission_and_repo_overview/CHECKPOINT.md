# Checkpoint — 2026-06-02_jsalt2_sweep_submission_and_repo_overview

Generated: 2026-06-02T11:20:00-05:00

## Date and campaign/task name

- Date: `2026-06-02`
- Task: submit the authoritative broader JSALT2 tuned sweeps and write a durable repo/system overview for future paper use.

## Research question

Can the broader JSALT2 tuned search surface be formally queued under Slurm as the active selection workflow, and can the repository's capabilities, layout, and solver/model coverage be documented in a paper-ready way grounded in the current codebase?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `src/dmdc/cli.py`
- `src/dmdc/campaign.py`
- `src/dmdc/command_catalog.py`
- `src/dmdc/baselines.py`
- `src/dmdc/import_workflow.py`
- `src/dmdc/live_adaptation.py`
- `README.md`
- `WORKFLOWS.md`
- `docs/navigation/workflow_map.md`
- `docs/analysis_menu.md`
- `docs/sweeps.md`
- `docs/live/README.md`
- `docs/archive/schema_validation.md`
- `docs/workflows/jsalt2_external_analysis_poc.md`
- `studies/jsalt2_moose_mesh_convergence_poc/README.md`

## Commands run

- `bash -n analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `bash -n analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `sbatch -A ASC23046 -t 03:00:00 --parsable analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `sbatch -A ASC23046 -t 03:00:00 --parsable analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- `sacct -j 3202984,3202985 --format=JobID,JobName%24,State,Elapsed,ExitCode -P`

## Inputs used

- No-`h` tuned sweep script: `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- With-`h` tuned sweep script: `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
- Slurm queue/account: partition `NuclearEnergy`, project `ASC23046`

## Outputs generated

### Submitted jobs

- broader no-`h` tuned sweep job ID: `3202984`
- broader with-`h` tuned sweep job ID: `3202985`

### Documentation outputs

- `docs/repository_capabilities_layout_and_solvers.md`
- updated `README.md`
- updated `docs/navigation/workflow_map.md`
- updated `docs/workflows/jsalt2_external_analysis_poc.md`
- updated `studies/jsalt2_moose_mesh_convergence_poc/README.md`

### Checkpoint artifacts

- `analysis/reports/2026-06-02_jsalt2_sweep_submission_and_repo_overview/CHECKPOINT.md`
- `analysis/reports/2026-06-02_jsalt2_sweep_submission_and_repo_overview/MANIFEST.yaml`

## Key numerical results

- Submitted no-`h` tuned sweep job ID: `3202984`
- Submitted with-`h` tuned sweep job ID: `3202985`
- Initial scheduler state for both jobs at checkpoint time: `PENDING`
- The tuned sweep surface used by both jobs includes:
  - models: `persistence`, `mean`, `adaptive_dmdc`, `dmdc`, `ridge_dmdc`, `pod_dmdc`
  - POD ranks: `2`, `3`, `4`, `0.999`
  - DMDc ranks: `full`, `2`, `3`, `4`
  - delays: `1`, `2`, `4`

## Plots/tables generated

- None yet from this turn; this checkpoint covers submission and documentation, not job completion.

## Interpretation

The broader JSALT2 tuned sweep surface is now formally queued under Slurm as the active model-selection workflow. This matters because the project has chosen the broader tuned sweep surface, not the narrower default delay-1 compare surface, as the authoritative selection policy. Keeping both with-`h` and no-`h` variants active preserves the current modeling fork while avoiding accidental policy drift back to a single implicit input treatment.

The new `docs/repository_capabilities_layout_and_solvers.md` file turns the repository from a collection of task-oriented user docs into something closer to a reusable system description. It explains the repo as a config-driven ROM/live-monitor/archive/reporting toolkit, clarifies that it is not itself a CFD/PDE solver, and organizes capabilities, layout, and model families in a way that is much closer to future paper prose.

The JSALT2 workflow docs now also reflect current reality better than before:

- they no longer describe the study as an outdated `max_files = 8` smoke pass
- they now state that the broader tuned sweep surface is authoritative for final JSALT2 model selection
- they preserve the with-`h` / no-`h` variant split explicitly

## Limitations

- This turn submitted the tuned sweeps but did not wait for completion.
- This turn focused on documentation and policy capture; it did not change core solver/model code paths.
- The overview doc is a system description for this repo, not a replacement for method-specific math docs in `docs/math/`.

## Bugs or anomalies

- None discovered in the prepared sweep scripts during this turn.

## Follow-up tasks

1. Monitor jobs `3202984` and `3202985` to completion and capture the final Slurm states plus the resulting sweep outputs.
2. If the broader tuned sweep surface remains the long-term policy, consider surfacing that more directly in the main JSALT2 study config comments or a dedicated study note.
3. Reuse `docs/repository_capabilities_layout_and_solvers.md` as the seed for any future paper methods/system-overview section.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-02_jsalt2_sweep_submission_and_repo_overview/CHECKPOINT.md`
- `docs/repository_capabilities_layout_and_solvers.md`
- `docs/workflows/jsalt2_external_analysis_poc.md`
- `studies/jsalt2_moose_mesh_convergence_poc/README.md`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_no_h_repaired.sbatch`
- `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/jobs/jsalt2_sweep_with_h_pair.sbatch`
