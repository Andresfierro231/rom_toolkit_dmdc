# JSALT2 External-Analysis POC Workflow

This is the concrete proof-of-concept path for bringing recent external analysis
data into the repo's `dmdc` workflow without inventing a one-off script.

## Source data

Current target:

```text
../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs
```

The collection contains per-run trajectory CSV files named like:

```text
jsalt2_moose_mesh_convergence_nm006_ord1/..._csv.csv
```

Those are the correct inputs for `dmdc import-data --type folder`.

## Canonical study

Use:

```text
studies/jsalt2_moose_mesh_convergence_poc/study_config.toml
```

This study is intentionally smoke-sized first:

- `max_files = 11`
- `case_from_filename = true`
- `state_cols = ["TP1", "TP2", "TP3", "TP6", "massFlowRate"]`
- `input_cols = ["h"]`

If inspection shows `h` is not meaningful as an input, remove it and rerun the
study as an autonomous ROM comparison.

Current project policy for this study is:

- keep both with-`h` and no-`h` variants active
- use the broader tuned `dmdc sweep` surface as the authoritative selection
  surface for final JSALT2 model choice
- treat the narrower delay-1 `compare` surface as a baseline comparison view,
  not as the final tuned-model decision surface

## Exact workflow

1. Dry-run the campaign.

```bash
dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --dry-run
```

2. Import the recent external trajectories.

```bash
dmdc import-data \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml
```

3. Inspect the imported canonical table.

```bash
dmdc inspect-data \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml
```

Open these first:

```text
outputs/jsalt2_moose_mesh_convergence_poc/inspection/warnings.txt
outputs/jsalt2_moose_mesh_convergence_poc/inspection/dt_summary_by_case.csv
outputs/jsalt2_moose_mesh_convergence_poc/inspection/case_lengths.csv
```

4. Fit POD-DMDc.

```bash
dmdc pod-dmdc \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml
```

5. Compare DMDc, ridge DMDc, POD-DMDc, and baselines. This also writes the
report because `[report].enabled = true`.

```bash
dmdc compare \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml
```

Or run the focused campaign end to end:

```bash
dmdc campaign \
  --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml \
  --steps import inspect pod_dmdc compare
```

## Output truth

Treat these files as the execution truth:

```text
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_plan.md
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_step_index.csv
outputs/campaigns/jsalt2_moose_mesh_convergence_poc/next_steps.md
outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/model_comparison.csv
outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/report/report.tex
```

## Provenance follow-up

After the dry-run or execution pass:

1. initialize or update the analysis campaign under `analysis/campaigns/`
2. refresh `analysis/reports/<campaign_id>/MANIFEST.yaml`
3. regenerate `CHECKPOINT.md`

Use the root wrappers:

```bash
python tools/studies/init_campaign.py ...
python tools/reporting/make_manifest.py ...
python tools/reporting/make_checkpoint.py ...
```
