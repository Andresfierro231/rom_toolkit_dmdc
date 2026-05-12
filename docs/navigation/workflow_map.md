# Workflow Map

Use this file when you know what you want to accomplish but not which command to run.

| Goal | Recommended command | Main docs |
|---|---|---|
| See the command guide | `dmdc guide` | `COMMANDS.md` |
| Run a modular workflow | `dmdc campaign --config study_config.toml --steps ...` | `WORKFLOWS.md`, `docs/workflows/campaign_workflows.md` |
| Connect CSV/Excel/folder/LabVIEW/EPICS-style data | `dmdc import-data --config study_config.toml` | `docs/importers/README.md` |
| Check whether data is usable | `dmdc inspect-data --config study_config.toml` | `docs/data_inspection_resampling.md` |
| Handle nonuniform/adaptive time steps | `dmdc adaptive-fit` or include `adaptive_dmdc` in `compare` | `docs/math/13_adaptive_variable_dt_dmdc.md` |
| Compare candidate models | `dmdc compare --config study_config.toml` | `docs/analysis_menu.md` |
| Sweep ranks/delays/models | `dmdc sweep --config study_config.toml` | `docs/sweeps.md` |
| Register a model for live use | `dmdc model-register` then `dmdc model-promote` | `docs/model_registry/README.md` |
| Replay a live workflow from old data | `dmdc live-replay-adapt --config study_config.toml` | `docs/live/README.md` |
| Open operator dashboard | `dmdc live-dashboard --config study_config.toml` | `docs/dashboard/operator_presentation_mode.md` |
| Generate an operator report | `dmdc live-operator-report --config study_config.toml` | `docs/live/operator_report.md` |
| Archive a live run | `dmdc archive-run --config study_config.toml` | `docs/live/archive_phase6_2.md` |
| Browse months of archived data | `dmdc archive-summarize`, `archive-quicklook`, `live-dashboard --mode archive` | `docs/live/dashboard_archive_phase6_4.md` |
| Validate archive schema | `dmdc validate-archive-schema --config study_config.toml` | `docs/archive/schema_validation.md` |
| Benchmark large-data performance | `dmdc benchmark-archive` | `docs/benchmarks/archive_benchmarking.md` |
| Plan HPC/batch execution | `dmdc hpc-plan --config study_config.toml` | `docs/hpc/batch_workflows.md` |

## Recommended reading order

1. `README.md`
2. `WORKFLOWS.md`
3. `COMMANDS.md`
4. `examples/real_data_onboarding/README.md`
5. `docs/navigation/choose_your_path.md`
6. The focused doc for your command.
