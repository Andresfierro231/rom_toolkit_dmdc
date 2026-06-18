# Checkpoint — 2026-05-22_jsalt2_external_analysis_poc

Generated: 2026-05-22T11:49:12-05:00

## Research question

Proof-of-concept onboarding of recent JSALT2 external analysis outputs into the dmdc import, inspection, POD-DMDc, DMDc comparison, and report workflow.

## Repository state

- Branch: `main`
- Commit: `93d9e59`
- Dirty working tree: `True`

## Files inspected / inputs

- `studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `studies/jsalt2_moose_mesh_convergence_poc/README.md`
- `docs/workflows/jsalt2_external_analysis_poc.md`
- `../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs`

## Validation or reference data

- None recorded.

## Commands recorded

- `.venv/bin/python -m py_compile src/dmdc/cli.py src/dmdc/campaign.py tools/_agents_bridge.py`
- `bash studies/jsalt2_moose_mesh_convergence_poc/scripts/run_01_campaign_dry_run.sh`
- `.venv/bin/python -m dmdc.cli campaign --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml --dry-run`
- `.venv/bin/python -m dmdc.cli import-data --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `.venv/bin/python -m dmdc.cli inspect-data --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `.venv/bin/python -m dmdc.cli pod-dmdc --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `.venv/bin/python -m dmdc.cli compare --config studies/jsalt2_moose_mesh_convergence_poc/study_config.toml`
- `.venv/bin/python -m dmdc.cli pod --data ../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs/jsalt2_meshconv_reference_nm032_ord2/jsalt2_meshconv_reference_nm032_ord2_csv.csv --state-cols TP1 TP2 TP3 TP6 massFlowRate --time-col time --rank 0.999 --center --scale --outdir outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_pod --plots`
- `.venv/bin/python -m dmdc.cli select-sensors --data ../physor2026_andrew/active_development/analysis/collections/jsalt2_moose_mesh_convergence/outputs/jsalt2_meshconv_reference_nm032_ord2/jsalt2_meshconv_reference_nm032_ord2_csv.csv --state-cols TP1 TP2 TP3 TP6 massFlowRate --time-col time --rank 0.999 --n-sensors 3 --center --scale --outdir outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_qr --plots`

## Scripts used

- `tools/studies/init_campaign.py`
- `tools/reporting/make_manifest.py`
- `tools/reporting/make_checkpoint.py`
- `studies/jsalt2_moose_mesh_convergence_poc/scripts/run_01_campaign_dry_run.sh`

## Outputs generated

### Reports

- `analysis/reports/2026-05-22_jsalt2_external_analysis_poc/CHECKPOINT.md`
- `analysis/reports/2026-05-22_jsalt2_external_analysis_poc/CHANGELOG.md`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_plan.md`
- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/next_steps.md`
- `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/report/report.tex`

### Figures

- `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/model_comparison.pdf`
- `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/report/model_comparison.pdf`
- `outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_pod/singular_values.pdf`
- `outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_qr/reconstruction_error_vs_sensors.pdf`

### Tables

- `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/campaign_step_index.csv`
- `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/model_comparison.csv`
- `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/stability_dashboard.csv`
- `outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_qr/sensor_ranking.csv`
- `outputs/jsalt2_moose_mesh_convergence_poc/representative_reference_qr/reconstruction_error_vs_sensors.csv`

## Key numerical results

- Imported rows: `9544`
- Imported cases: `11`
- Best held-out model: `pod_dmdc`
- Best-model test rollout RMSE: `0.33081936458561695`
- Best-model spectral radius: `0.9950743257826973`
- POD-DMDc direct fit used POD rank `4` and DMDc rank `5`
- Representative-run POD rank used for the centered/scaled SVD pass: `5`
- Representative QR-selected states: `TP2`, `TP3`, `massFlowRate`

## Interpretation

The imported JSALT2 mesh-convergence collection is usable for the intended
proof-of-concept workflow without manual cleanup. On the 11-case compare pass,
`pod_dmdc` was the strongest held-out model and remained spectrally stable.

The representative-run SVD/QR pass suggests that, for the chosen five-state
mixed temperature/flow basis under centering and scaling, `TP2`, `TP3`, and
`massFlowRate` span the dominant retained subspace best among three-sensor
choices.

## Limitations

- All 11 imported cases have nonuniform `dt`, so discrete compare results should
  be interpreted together with the adaptive-time warning.
- The representative QR ranking used centered and scaled states to balance the
  mixed temperature/flow magnitudes; a different preprocessing choice will
  change the ranking.

## Missing information

- The current checkpoint does not yet include an `adaptive-fit` baseline on the
  same 11-case collection.
- The usefulness of `h` as an input column still needs a domain decision beyond
  the numerical compare outputs.

## Next actions

- Inspect `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/stability_warnings.txt` and `uncertainty_summary.csv`.
- Decide whether to run `adaptive-fit` as the time-aware baseline for the same 11-case collection.
- Decide whether `h` remains in `input_cols` or whether an autonomous rerun with `input_cols = []` is more defensible.
- Compile `outputs/jsalt2_moose_mesh_convergence_poc/model_comparison/report/report.tex` if a local TeX toolchain is desired.

## Exact files future agents should inspect first

- `analysis/reports/2026-05-22_jsalt2_external_analysis_poc/MANIFEST.yaml`
- This checkpoint file
- Campaign config listed in the manifest
- Figure/table manifests under the report directory, if present
