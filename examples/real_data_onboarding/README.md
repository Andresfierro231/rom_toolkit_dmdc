# Real Data Onboarding: SAM / Thermal-Loop Data to ROM Dashboard

This folder is the practical starting point when you have a real SAM simple-loop output folder, an experimental CSV/Excel export, a LabVIEW/DAQ folder drop, or a live-loop log and you want to connect it to this ROM toolkit.

The goal is to move from messy raw data to a canonical table, then to validated models, live replay, dashboard review, and an operator report.

> **Default assumption:** your time step is probably nonuniform or adaptive. This workflow starts with data inspection and adaptive-time modeling. Only resample if you intentionally want a fixed discrete-time map.

## Folder contents

```text
examples/real_data_onboarding/
├── README.md                         # This guide
├── column_map.toml                    # Raw-name -> canonical-name mapping template
├── study_config.toml                  # One central config for import/offline/live/dashboard workflows
├── notes.md                           # What to check after each step
└── scripts/
    ├── run_01_import.sh
    ├── run_02_inspect.sh
    ├── run_03_adaptive_fit.sh
    ├── run_04_pod_dmdc.sh
    ├── run_05_compare_models.sh
    ├── run_06_validate_unseen_cases.sh
    ├── run_07_live_replay_monitor.sh
    ├── run_08_live_replay_adapt.sh
    ├── run_09_live_dashboard.sh
    ├── run_10_operator_report.sh
    └── run_all_replay_demo.sh
```

## Quick start

1. Copy this folder for your study:

```bash
cp -r examples/real_data_onboarding studies/my_simple_loop_study
cd studies/my_simple_loop_study
```

2. Edit these two files:

```text
column_map.toml
study_config.toml
```

Replace every `TODO_...` path and column name with your actual data.

3. Run one step at a time:

```bash
bash scripts/run_01_import.sh
bash scripts/run_02_inspect.sh
bash scripts/run_03_adaptive_fit.sh
bash scripts/run_05_compare_models.sh
bash scripts/run_08_live_replay_adapt.sh
bash scripts/run_09_live_dashboard.sh
bash scripts/run_10_operator_report.sh
```

## Recommended order

### Step 1 — Import raw files into one canonical table

Use this for CSV, Excel, Parquet, folders of CSV chunks, LabVIEW/DAQ folder drops, or EPICS snapshots.

```bash
dmdc import-data --config study_config.toml
```

Output:

```text
data/processed/simple_loop_canonical.parquet
```

If Parquet support is unavailable, the importer can fall back to CSV unless strict mode is enabled.

### Step 2 — Inspect the canonical data

```bash
dmdc inspect-data --config study_config.toml
```

Check:

```text
outputs/real_data_onboarding/inspection/warnings.txt
outputs/real_data_onboarding/inspection/dt_summary_by_case.csv
outputs/real_data_onboarding/inspection/case_lengths.csv
```

This step tells you whether you have nonmonotone time, duplicated timestamps, missing values, short/failed cases, or highly nonuniform `dt`.

### Step 3 — Fit an adaptive-time model

Because SAM and live-loop data are often adaptive/nonuniform in time, start with:

```bash
dmdc adaptive-fit --config study_config.toml
```

This fits a physical-time model:

\[
\frac{dx}{dt} \approx A_c x + B_c u.
\]

### Step 4 — Fit POD-DMDc

POD-DMDc is useful when you have many sensors or want a low-dimensional ROM:

```bash
dmdc pod-dmdc --config study_config.toml
```

### Step 5 — Compare models on held-out cases

```bash
dmdc compare --config study_config.toml
```

This compares baselines, adaptive DMDc, regularized DMDc, and POD-DMDc. It produces dashboards, stability summaries, and error tables.

### Step 6 — Validate on unseen cases

```bash
dmdc validate --config study_config.toml
```

This is especially important when your test case is a different heater power, ambient condition, or loop operating regime.

### Step 7 — Live replay monitor/adapt

Replay your historical data as if it were live:

```bash
dmdc live-replay-monitor --config study_config.toml
```

Then run bias-corrected live replay:

```bash
dmdc live-replay-adapt --config study_config.toml
```

### Step 8 — Open dashboard

```bash
dmdc live-dashboard --config study_config.toml
```

Use the executive/operator view when showing others:

```bash
dmdc live-dashboard --config study_config.toml --view operator
```

### Step 9 — Generate operator report

```bash
dmdc live-operator-report --config study_config.toml
```

The report is meant for quick review: trust score, alerts, worst residuals, bias correction, and provenance.

## How to connect to current data

### CSV or Excel export

Set:

```toml
[importer]
type = "csv"       # or "excel"
source = "TODO/path/to/export.csv"
column_map = "column_map.toml"
```

### Folder of SAM outputs or DAQ chunks

Set:

```toml
[importer]
type = "folder"    # or "labview_daq"
source = "TODO/path/to/raw_folder"
pattern = "*.csv"
case_from_filename = true
column_map = "column_map.toml"
```

### EPICS snapshot

Set:

```toml
[importer]
type = "epics"

[importer.epics_pvs]
TP1 = "TODO:LOOP:TP1"
TP2 = "TODO:LOOP:TP2"
q_heater = "TODO:LOOP:HEATER:POWER"
```

Then install optional EPICS support:

```bash
python -m pip install -e '.[epics]'
```

## What to edit first

Most users only need to edit these blocks in `study_config.toml`:

```text
[importer]
[data]
[units]
[split]
[monitor]
[output]
```

The rest can stay close to the template for the first pass.

## Useful documentation links

- Main project guide: [`../../README.md`](../../README.md)
- Choose your path: [`../../docs/navigation/choose_your_path.md`](../../docs/navigation/choose_your_path.md)
- Importers: [`../../docs/importers/README.md`](../../docs/importers/README.md)
- Adaptive time: [`../../docs/math/13_adaptive_variable_dt_dmdc.md`](../../docs/math/13_adaptive_variable_dt_dmdc.md)
- Live streaming: [`../../docs/live/README.md`](../../docs/live/README.md)
- Bias correction: [`../../docs/live/adaptation_phase6.md`](../../docs/live/adaptation_phase6.md)
- Dashboard: [`../../docs/live/dashboard_phase5.md`](../../docs/live/dashboard_phase5.md)
- Archive dashboard: [`../../docs/live/dashboard_archive_phase6_4.md`](../../docs/live/dashboard_archive_phase6_4.md)
- Troubleshooting: [`../../docs/troubleshooting_decision_tree.md`](../../docs/troubleshooting_decision_tree.md)
- Testing and roadmap: [`../../TODO_TESTING_AND_ROADMAP.md`](../../TODO_TESTING_AND_ROADMAP.md)

## Important safety boundary

This repo is currently a read-only analysis, monitoring, and advisory toolkit. It can ingest data, estimate state, forecast, warn, archive, and report. It should not be connected to automatic loop control without a separate, validated controls/safety layer.
