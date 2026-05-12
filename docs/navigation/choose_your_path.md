# Choose your path


## I have a real SAM/simple-loop dataset and want the whole workflow

Start from the copyable onboarding folder:

```bash
cp -r examples/real_data_onboarding studies/my_simple_loop_study
cd studies/my_simple_loop_study
```

Then edit `column_map.toml` and `study_config.toml`, and run the scripts in order.

See:

```text
examples/real_data_onboarding/README.md
docs/tutorials/real_data_onboarding.md
```

## I have a raw CSV/Excel/LabVIEW folder

1. `dmdc import-data --config configs/templates/import_csv_excel_folder.toml`
2. `dmdc inspect-data --config configs/templates/central_study_config.toml`
3. `dmdc compare --config configs/templates/central_study_config.toml`

See: `docs/importers/README.md`.

## I have EPICS PVs

Start with a snapshot import if you only need a quick test:

```bash
dmdc import-data --config configs/templates/import_epics_snapshot.toml
```

For continuous live monitoring, use the streaming adapter architecture in `src/dmdc/streaming.py`; an EPICS streaming adapter is planned as a plug-in.

## I want the best offline ROM

Run:

```bash
dmdc compare --config my_study.toml
dmdc sweep --config my_study.toml
dmdc recommend --table outputs/sweep/sweep_results.csv
```

## I want a live dashboard

Run a live/replay workflow first, then open the dashboard:

```bash
dmdc live-replay-adapt --config my_study.toml
dmdc live-dashboard --config my_study.toml --view operator
```

## I want a meeting-ready summary

```bash
dmdc live-operator-report --run-dir outputs/live_adaptation --outdir outputs/operator_report
```

## I have months of live data

Use archive mode:

```bash
dmdc archive-run --config my_study.toml
dmdc archive-summarize --config my_study.toml
dmdc archive-quicklook --config my_study.toml
dmdc live-dashboard --archive-root live_archive --mode archive --view operator
```

## I need to know what is still not production-hardened

Read `TODO_TESTING_AND_ROADMAP.md`.

## I need to demo or defend the live dashboard

Use the operator view with a geometry file:

```bash
dmdc live-dashboard \
  --run-dir outputs/live_adaptation_replay \
  --view operator \
  --geometry configs/templates/simple_loop_geometry.toml
```

Read: `docs/dashboard/operator_presentation_mode.md`.

## I need to understand archive performance

```bash
dmdc benchmark-archive --n-rows 1000000 --n-states 32 --format parquet
```

Read: `docs/benchmarks/archive_benchmarking.md`.

## I want to plan local vs HPC execution

```bash
dmdc hpc-plan --config configs/templates/central_campaign_config.toml
```

Read: `docs/hpc/batch_workflows.md`.
