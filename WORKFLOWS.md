# One-Command Workflows

This repo is designed to be run from a **central TOML config**. You should not need to memorize dozens of commands. For most work, copy one config, edit the paths/columns, and run `dmdc campaign` with only the steps you need.

## The core idea

```text
central config file
        ↓
dmdc campaign --config <config> --steps <selected steps>
        ↓
separate output folders + campaign_plan.md + next_steps.md
```

Every campaign writes:

```text
campaign_plan.md        # commands, output folders, resource summary
campaign_step_index.csv # what ran, where it wrote, status
next_steps.md           # what to inspect or run next
resource_summary.json   # local/HPC resource snapshot
```

## Recommended first run with real data

```bash
cp -r examples/real_data_onboarding studies/my_loop_study
cd studies/my_loop_study

# Edit column_map.toml and study_config.toml first.
# Then preview the workflow without running expensive commands:
dmdc campaign --config study_config.toml --dry-run

# Run the first real-data pass:
dmdc campaign --config study_config.toml --steps import inspect compare
```

## TAMU raw data intake and validation prep

Use this when a new TAMU data drop arrives and you need an organized inventory before import or validation work:

```bash
dmdc tamu-inventory \
  --root ../tamu_loop_data/Loop\ Operational\ Data \
  --outdir outputs/tamu_inventory

dmdc tamu-validation-export \
  --inventory-root ../tamu_loop_data/Loop\ Operational\ Data \
  --source-tables \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv \
  --outdir outputs/tamu_validation_export
```

This path is documented in:

```text
docs/workflows/tamu_data_intake_and_validation.md
docs/workflows/tamu_loop_data_recovery.md
studies/tamu_loop_data_onboarding/README.md
```

If scratch is cleared and the sibling raw-data repo is missing, recreate it first:

```bash
python tools/studies/init_tamu_loop_data_repo.py --target-root ../tamu_loop_data
```

## External analysis proof of concept

If you already have trajectory CSVs in a maintained external analysis tree, use
the ready-made JSALT2 study instead of starting from a blank copy:

```bash
dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --dry-run

dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --steps import inspect pod_dmdc compare
```

This path is documented in:

```text
docs/workflows/jsalt2_external_analysis_poc.md
studies/jsalt2_moose_mesh_convergence_poc/README.md
```

## Common campaign recipes

### 1. Import and inspect only

Use this when connecting new data or checking column names.

```bash
dmdc campaign --config study_config.toml --steps import inspect
```

Look at:

```text
outputs/inspection/warnings.txt
outputs/inspection/case_quality_dashboard.csv
outputs/inspection/dt_summary_by_case.csv
```

### 2. Offline model comparison

Use this after the data imports cleanly.

```bash
dmdc campaign --config study_config.toml --steps inspect compare sweep
```

Look at:

```text
outputs/compare/model_comparison.csv
outputs/compare/stability_dashboard.csv
outputs/sweep/sweep_results.csv
```

### 3. Register and deploy the selected model

After a model is selected:

```bash
dmdc model-register \
  --model outputs/compare/best_model/model.pkl \
  --name simple_loop_pod_dmdc_v1 \
  --stage candidate \
  --metrics outputs/compare/model_comparison.csv

dmdc model-promote \
  --name simple_loop_pod_dmdc_v1 \
  --version <VERSION_FROM_REGISTER_OUTPUT> \
  --stage production
```

Then set the live config:

```toml
[model]
registry_name = "simple_loop_pod_dmdc_v1"
stage = "production"
registry_root = "models/registry"
```

### 4. Live replay, dashboard, and operator report

Use replay first before tailing a real logger.

```bash
dmdc campaign --config study_config.toml --steps live_replay_adapt dashboard operator_report
```

Look at:

```text
outputs/live_adaptation_replay/live_alerts.csv
outputs/live_adaptation_replay/live_trust_score.csv
outputs/live_adaptation_replay/live_bias_update_events.csv
outputs/operator_report/live_operator_report.html
```

### 5. Archive, summarize, validate schema, dashboard

Use this for long campaigns and repeated experiments.

```bash
dmdc campaign --config study_config.toml --steps archive_run archive_summarize archive_quicklook archive_schema dashboard
```

Look at:

```text
live_archive/manifest.csv
live_archive/context/archive_context_index.csv
live_archive/summaries/
live_archive/quicklooks/
live_archive/schema_validation/archive_schema_validation.md
```

### 6. Plan local/HPC batch execution

Local workstation remains the default. Use this only to create command plans and incomplete Slurm templates.

```bash
dmdc hpc-plan --config study_config.toml --steps inspect compare archive
```

The generated Slurm files contain `FIXME` fields for account, partition, modules, and environment setup.

## Command discovery

Use:

```bash
dmdc guide
```

or read:

```text
COMMANDS.md
docs/navigation/command_index.md
docs/navigation/choose_your_path.md
```

## Why not run everything every time?

The repo is intentionally modular. Typical examples:

```text
New raw file?                 import + inspect
Same data, new model idea?    compare + sweep
Already selected a model?     live_replay_adapt + dashboard
Long run finished?            archive_run + archive_summarize + archive_schema
Meeting tomorrow?             live-dashboard + live-operator-report
```

Do not treat the central config as a command that must run all sections. It is a study contract. Each workflow step reads only the sections it needs.
