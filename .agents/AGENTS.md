# AGENTS.md

## Repository role

This repository is a Python research toolkit for DMD/DMDc/POD analysis, live replay and monitoring, archive summarization, dashboards, and report generation.

The active workflow is config-driven and CLI-first:

- central study or campaign TOML in `configs/templates/` or `studies/<study>/study_config.toml`
- execution through `python -m dmdc.cli ...` or the installed `dmdc` entrypoint
- reproducible outputs under `outputs/`
- optional research checkpointing under `analysis/`

## Active workflow sources of truth

- Entry points: `src/dmdc/cli.py`
- Campaign runner: `src/dmdc/campaign.py`
- Local workflow wrapper: `scripts/workflows/run_campaign_local.sh`
- Campaign config templates: `configs/templates/central_campaign_config.toml`, `configs/templates/one_command_local_workflow.toml`
- Study config template: `configs/templates/central_study_config.toml`
- Real-data example study: `examples/real_data_onboarding/study_config.toml`
- Workflow docs: `README.md`, `WORKFLOWS.md`, `COMMANDS.md`, `docs/workflows/campaign_workflows.md`

## Repository-specific rules

- Preserve the existing `dmdc` CLI workflow. Do not replace it with one-off scripts.
- Prefer adding thin wrappers under `tools/` that delegate to stable repo commands or starter workflow utilities.
- Treat `examples/real_data_onboarding/` as the main onboarding example for real studies.
- Treat `configs/templates/` as the canonical source for campaign and study configuration shapes.
- Treat `outputs/campaigns/<campaign_name>/campaign_plan.md` and `campaign_step_index.csv` as the source of truth for what a `dmdc campaign` run planned or executed.
- Treat `data/example_timeseries.csv`, `data/example_multicase_timeseries.csv`, and `examples/end_to_end_thermal_loop_study/` as smoke-test and tutorial data, not validated experimental truth.
- Treat `scripts/slurm/*.sbatch.template` and `dmdc hpc-plan` outputs as planning artifacts only until a user explicitly fills in cluster details.
- When verifying workflow changes, prefer dry-run commands and small example datasets before anything expensive.

## Provenance expectations

For research workflow tasks, record:

- git branch, commit, and dirty status
- files inspected
- exact commands run
- generated outputs and their paths
- unresolved issues and next actions

Use the root `tools/` wrappers together with `analysis/campaigns/` and `analysis/reports/` for durable checkpoints. Use `dmdc report` for run-specific LaTeX reporting under `outputs/.../report/`.

## Reporting and validation

- Validation on unseen cases should follow case-aware splits; prefer the documented `validate` and `compare` workflows.
- Figures and tables should come from saved CSV/JSON/model outputs, not notebook-only state.
- If a run is only dry-run or planning-only, label it that way.
- Do not present synthetic example outputs as field-validated results.
