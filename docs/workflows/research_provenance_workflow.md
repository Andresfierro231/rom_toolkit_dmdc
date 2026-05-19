# Research Provenance Workflow

This repository already has an active execution workflow built around central TOML configs and the `dmdc` CLI. The root `tools/` directory added here does not replace that workflow. It adds a provenance-first layer for research checkpoints, manifests, and reusable analysis notes.

## Active execution workflow

Use these files as the main run-time sources of truth:

- `README.md`
- `WORKFLOWS.md`
- `COMMANDS.md`
- `configs/templates/central_campaign_config.toml`
- `configs/templates/central_study_config.toml`
- `examples/real_data_onboarding/study_config.toml`
- `scripts/workflows/run_campaign_local.sh`
- `src/dmdc/cli.py`
- `src/dmdc/campaign.py`

The normal path is:

```bash
dmdc campaign --config studies/<study>/study_config.toml --dry-run
dmdc campaign --config studies/<study>/study_config.toml --steps import inspect compare
```

The `dmdc campaign` outputs live under `outputs/campaigns/<campaign_name>/` and record the plan, step index, next steps, and resource summary.

## Root research workflow wrappers

The root `tools/` scripts are thin wrappers that delegate to the generic starter utilities stored in `.agents/tools/`.

Use them for:

- initializing provenance-first campaigns in `analysis/campaigns/`
- creating report/checkpoint files in `analysis/reports/`
- validating manifests and hashing inputs without changing the main `dmdc` runtime path

This separation keeps the repo's active modeling workflow stable while still giving future agents a durable analysis notebook equivalent on disk.

## Typical repo-adapted workflow

1. Pick or copy a central study config.
2. Dry-run the `dmdc campaign` workflow first.
3. Run only the needed steps.
4. Initialize or update an `analysis/` campaign to record provenance.
5. Regenerate a checkpoint from the campaign manifest after changes or runs.

Example:

```bash
python -m pip install -r requirements-codex-tools.txt
python -m py_compile $(find tools -name "*.py")
python tools/studies/init_campaign.py \
  --name workflow_adaptation_smoke_test \
  --question "Tailor the Codex research workflow to this repository."
python -m dmdc.cli campaign \
  --config configs/templates/one_command_local_workflow.toml \
  --dry-run \
  --steps inspect compare
```

## What goes where

- `configs/templates/` and `studies/<study>/`: run definitions and study contracts
- `outputs/`: command outputs, model results, reports, dashboards, archives
- `outputs/campaigns/`: campaign plans and step indexes from `dmdc campaign`
- `analysis/campaigns/`: provenance-first YAML campaign records
- `analysis/reports/`: checkpoints, manifests, figures, tables, and report notes
- `tools/`: root wrappers for the generic provenance and reporting utilities

## Dry-run and safety policy

- Prefer `--dry-run` for campaign planning before large or expensive runs.
- Treat HPC plans and Slurm templates as incomplete until a user fills in cluster-specific fields.
- Use example datasets for smoke tests when real data or credentials are unavailable.
- Record any unverified steps explicitly in `MANIFEST.yaml` and `CHECKPOINT.md`.
