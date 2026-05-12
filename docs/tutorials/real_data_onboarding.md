# Tutorial: Onboard Real SAM / Thermal-Loop Data

This tutorial points to the practical starter folder:

```text
examples/real_data_onboarding/
```

Use it when you have an actual SAM simple-loop folder, an experimental loop CSV/Excel export, a LabVIEW/DAQ folder drop, or a current live-loop CSV log and want to connect it to the ROM workflow.

## One-page workflow

```bash
cp -r examples/real_data_onboarding studies/my_simple_loop_study
cd studies/my_simple_loop_study

# Edit paths and columns first.
$EDITOR column_map.toml
$EDITOR study_config.toml

# Then run incrementally.
bash scripts/run_01_import.sh
bash scripts/run_02_inspect.sh
bash scripts/run_03_adaptive_fit.sh
bash scripts/run_05_compare_models.sh
bash scripts/run_08_live_replay_adapt.sh
bash scripts/run_09_live_dashboard.sh
bash scripts/run_10_operator_report.sh
```

## Why this tutorial exists

Most docs explain one command at a time. Real data onboarding is different because it requires connecting many pieces:

```text
raw files
  -> importer/column map
  -> canonical table
  -> inspection and time-step diagnostics
  -> adaptive-time or POD-DMDc model
  -> held-out validation and comparison
  -> live replay
  -> dashboard
  -> operator report
```

The example folder provides a central `study_config.toml`, shell scripts, and notes/checklists for each step.

## Default time assumption

Assume your data has nonuniform or adaptive timestamps unless inspection proves otherwise. Start with:

```bash
dmdc inspect-data --config study_config.toml
dmdc adaptive-fit --config study_config.toml
```

Only use `dmdc resample` when you intentionally want a fixed-grid discrete-time model.

## Related docs

- Importers: `docs/importers/README.md`
- Connect current data: `docs/start_here_connect_your_data.md`
- Time handling: `docs/cheatsheets/time_handling_cheatsheet.md`
- Adaptive DMDc math: `docs/math/13_adaptive_variable_dt_dmdc.md`
- Live dashboard: `docs/live/dashboard_phase5.md`
- Bias correction: `docs/live/adaptation_phase6.md`
- Troubleshooting: `docs/troubleshooting_decision_tree.md`
