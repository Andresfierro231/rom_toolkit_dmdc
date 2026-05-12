# Documentation Home

Start here when browsing the repository documentation.

## Fast navigation

| Need | Read |
|---|---|
| Minimal commands and one-command workflows | `../WORKFLOWS.md` |
| Command index | `../COMMANDS.md` or `navigation/command_index.md` |
| Which path should I take? | `navigation/choose_your_path.md` and `navigation/workflow_map.md` |
| Connect real SAM/loop data | `../examples/real_data_onboarding/README.md` and `tutorials/real_data_onboarding.md` |
| Offline ROM theory | `math/README.md` and `math_index.md` |
| Live streaming/digital twin | `live/README.md` |
| Importers/adapters | `importers/README.md` |
| Dashboard and operator view | `dashboard/operator_presentation_mode.md` |
| Model registry | `model_registry/README.md` |
| Archive validation/search/summaries | `archive/schema_validation.md`, `live/archive_phase6_2.md`, `live/summaries_quicklooks_phase6_3.md` |
| HPC/batch planning | `hpc/batch_workflows.md` |
| Known limitations and alpha boundaries | `known_limitations.md` |

## Recommended workflow

1. Use `dmdc guide` or read `COMMANDS.md`.
2. Copy `examples/real_data_onboarding/` into a study folder.
3. Edit `study_config.toml`.
4. Run `dmdc campaign --config study_config.toml --dry-run`.
5. Run selected steps with `--steps`.

---

# Documentation map

If you are new, start with:

```text
README.md
docs/navigation/choose_your_path.md
docs/start_here_connect_your_data.md
docs/analysis_menu.md
```


## Practical onboarding examples

- `examples/real_data_onboarding/` — copyable workflow for connecting a real SAM/simple-loop dataset to import, inspection, adaptive-fit, model comparison, live replay, dashboard, and operator report.
- `docs/tutorials/real_data_onboarding.md` — tutorial explaining how to use that example folder.

## Main folders

- `docs/importers/` — bringing CSV, Excel, EPICS, LabVIEW/DAQ data into canonical tables.
- `docs/live/` — live replay, forecasting, Kalman estimation, monitoring, dashboard, archive, and reports.
- `docs/math/` — math behind DMDc, POD, Kalman filtering, sparse sensing, and bias correction.
- `docs/cheatsheets/` — short command/config references.
- `docs/roadmaps/` — future production-hardening plans.
- `docs/testing/` — CI, unit tests, CLI checks, and performance testing plans.

## Most useful commands

```bash
dmdc import-data --config configs/templates/import_csv_excel_folder.toml
dmdc inspect-data --config configs/templates/central_study_config.toml
dmdc compare --config configs/templates/central_study_config.toml
dmdc live-replay-adapt --config configs/templates/central_study_config.toml
dmdc live-dashboard --config configs/templates/central_study_config.toml --view operator
dmdc live-operator-report --run-dir outputs/live_adaptation
```

## Recent operational additions

- Operator dashboard schematic: `docs/dashboard/operator_presentation_mode.md`
- Archive benchmark/performance metrics: `docs/benchmarks/archive_benchmarking.md`
- EPICS/LabVIEW field-adapter notes: `docs/adapters/field_ready_adapters.md`
- Local/HPC planning: `docs/hpc/batch_workflows.md`
- Future advisory/control boundary: `docs/future/advisory_control_mode.md`

Recommended operational path:

```text
real data import -> inspect -> compare/validate -> register/promote model ->
live replay/run -> dashboard/operator report -> archive -> summarize/search
```

For high-volume data, always prefer summary-first workflows: `archive-summarize`,
`archive-quicklook`, `archive-context`, and archive dashboard mode before opening
raw partitions.
