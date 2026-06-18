# JSALT2 Moose Mesh Convergence POC

This study is the proof-of-concept path for bringing recent external analysis
data into the `dmdc` workflow.

It targets the maintained external collection:

```text
../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs
```

The current source files already expose trajectory-level CSV outputs such as:

```text
jsalt2_moose_mesh_convergence_nm006_ord1/..._csv.csv
```

Those files are imported directly with `dmdc import-data --type folder`, then
inspected, fit with POD-DMDc, compared against DMDc and baselines, and finally
reported through the normal `dmdc report` flow.

## What this study assumes

- Commands are run from the repository root.
- The external analysis tree still exists at the relative path above.
- The current maintained collection fits inside `max_files = 11`, which presently spans the visible external case set.
- `h` is treated as the first candidate control/input column.

If inspection shows `h` is effectively constant or not useful across cases,
remove it from `[data].input_cols` in `study_config.toml` and rerun the POC as
an autonomous ROM comparison.

Current project policy for this study is:

- keep both with-`h` and no-`h` variants active
- treat the broader tuned sweep surface as authoritative for final JSALT2 model
  selection
- use the default delay-1 compare path as a baseline compare surface, not as
  the final tuned-model decision surface

## Fastest path

Dry-run the full workflow first:

```bash
dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --dry-run
```

Then run the POC steps:

```bash
dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --steps import inspect pod_dmdc compare
```

## Step scripts

The scripts under `scripts/` always resolve the study config and run from the
repo root, so they are safe to launch from anywhere:

```bash
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_01_campaign_dry_run.sh
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_02_import.sh
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_03_inspect.sh
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_04_pod_dmdc.sh
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_05_compare_and_report.sh
```

Or run the focused campaign end to end:

```bash
bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_06_campaign_poc.sh
```

## Outputs to open first

After import:

```text
data/processed/jsalt2_moose_mesh_convergence_poc.parquet
data/processed/import_metadata.json
data/processed/columns_summary.csv
```

After inspection:

```text
outputs/jsalt2_moose_mesh_convergence_poc/inspection/warnings.txt
outputs/jsalt2_moose_mesh_convergence_poc/inspection/dt_summary_by_case.csv
outputs/jsalt2_moose_mesh_convergence_poc/inspection/case_lengths.csv
```

After POD-DMDc:

```text
outputs/jsalt2_moose_mesh_convergence_poc/pod_dmdc/
```

After compare/report:

```text
outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/model_comparison.csv
outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/stability_dashboard.csv
outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/report/report.tex
```

After any campaign run:

```text
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_plan.md
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_step_index.csv
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/next_steps.md
```

## Current import scope

This config currently imports the full maintained JSALT2 collection:

```toml
max_files = 11
```

If additional cases are added under the external `outputs/` folder, raise or
remove that limit in `study_config.toml` before rerunning the proof-of-concept.
