# Start Here: Connect the Repo to Your Current Data

This page is the practical entry point for real SAM or experimental loop data.
The repo assumes your data will often have **nonuniform/adaptive time steps**.
That is normal. The first decision is whether you want a sample-to-sample model,
a fixed-step discrete model, or a physical-time model.

## 1. Minimum table format

Your CSV or Parquet table should contain:

```text
case_id,time,TP1,TP2,TP3,TP4,TP5,TP6,massFlowRate,q_heater,T_amb,h_amb
run_001,0.000,450.0,449.8,...,0.18,37.0,300.0,8.0
run_001,0.014,450.1,449.9,...,0.18,37.0,300.0,8.0
run_001,0.052,450.4,450.1,...,0.18,37.0,300.0,8.0
run_002,0.000,455.0,454.6,...,0.20,55.0,300.0,8.0
```

Use:

- `case_id` for independent runs, experiments, or SAM cases.
- `time` for physical time. It does **not** need to be uniformly spaced.
- `state_cols` for quantities you want the ROM to predict.
- `input_cols` for known forcings, controls, or boundary conditions.

## 2. Inspect first

```bash
dmdc inspect-data \
  --data path/to/my_data.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/inspection_my_data
```

Read these first:

```text
outputs/inspection_my_data/warnings.txt
outputs/inspection_my_data/dt_summary_by_case.csv
outputs/inspection_my_data/case_lengths.csv
```

## 3. Choose time handling

### Default real-data expectation: adaptive/nonuniform time

For SAM and experimental logs, use this when `dt` changes substantially:

```bash
dmdc adaptive-fit \
  --data path/to/my_data.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/adaptive_fit_my_data \
  --plots
```

This learns

\[
\frac{dx}{dt} \approx A_c x + B_c u
\]

using each actual interval \(\Delta t_k = t_{k+1}-t_k\).

### Fixed-step discrete map

Use this when your data is already nearly uniform, or after you explicitly resample:

```bash
dmdc fit \
  --data path/to/my_data.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/dmdc_my_data \
  --plots
```

This learns

\[
x_{k+1} \approx A x_k + B u_k.
\]

### Explicit resampling

Only resample when interpolation is physically defensible:

```bash
dmdc resample \
  --data path/to/my_data.csv \
  --time-col time \
  --case-col case_id \
  --columns TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate q_heater T_amb h_amb \
  --dt 0.1 \
  --out outputs/my_data_resampled_dt0p1.csv
```

## 4. Recommended first full study

After inspection, use a config template:

```bash
cp configs/templates/full_thermal_loop_study.toml my_study.toml
```

Edit:

```toml
[data]
path = "path/to/my_data.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "massFlowRate"]
input_cols = ["q_heater", "T_amb", "h_amb"]
```

Then run:

```bash
dmdc inspect-data --config my_study.toml
dmdc compare --config my_study.toml
dmdc sweep --config my_study.toml
dmdc report --run outputs/thermal_loop_study
```

## 5. Where outputs go

Every analysis folder should contain:

```text
provenance.json              # command, version, Python, config path
warnings.txt                 # actionable warnings when available
*_summary.json               # machine-readable model/data summary
*.csv / *.tex / *.md          # tables and dashboards
*.pdf                         # plots
report/report.tex             # LaTeX report when generated
```


## Connecting live data

If your loop logger writes rows continuously to a CSV file, start with the ingestion-only live layer:

```bash
dmdc live-run --config configs/templates/live_csv_tail.toml
```

Before connecting hardware, replay a historical CSV:

```bash
dmdc live-replay --config configs/templates/live_replay_csv.toml
```

After you have a saved offline model, move to Live Phase 2 forecasting:

```bash
dmdc live-replay-predict --config configs/templates/live_replay_predict.toml
dmdc live-run-predict --config configs/templates/live_csv_tail_predict.toml
```

If you have a saved POD-DMDc model and want filtered full-state estimates from only a subset of measured sensors, use Live Phase 3:

```bash
dmdc live-replay-estimate --config configs/templates/live_replay_estimate.toml
dmdc live-run-estimate --config configs/templates/live_csv_tail_estimate.toml
```

This writes raw and cleaned stream logs, filtered full-state estimates, modal estimates, Kalman innovations, covariance traces, optional forecasts, warnings, dt summaries, and provenance. It still does not perform online retraining or residual alerting; those remain later online-digital-twin phases.

## Optional live dashboard for current loop data

After you have a trained model and a live monitoring folder, the most operator-friendly way to inspect the live twin is the Streamlit dashboard.

Install the optional dashboard dependencies:

```bash
python -m pip install -e '.[dashboard]'
```

For replay/demo data:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml --save-every-batch
dmdc live-dashboard --run-dir outputs/live_monitoring
```

For a local workstation where a logger appends rows to a CSV file:

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml --save-every-batch
dmdc live-dashboard --run-dir outputs/live_monitoring
```

The dashboard is read-only. It shows state estimates, measurements, forecasts, forecast residuals, alerts, trust score, Kalman innovations, covariance, and raw tables. It does not control hardware or retrain the ROM.

Read:

```text
docs/live/dashboard_phase5.md
docs/cheatsheets/live_dashboard_cheatsheet.md
```

---

## Live archives for long-running loop data

If you are connecting the repo to a live loop, treat the run folder as the
short-term working area and the archive as the long-term record.

Recommended live workflow:

```bash
# 1. Run live monitoring/adaptation. This writes the current run folder.
dmdc live-replay-adapt --config configs/templates/live_replay_adapt_with_archive.toml

# 2. Inspect the manifest.
dmdc archive-index --archive-root live_archive

# 3. Build compact summaries.
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600

# 4. Generate small quicklook plots.
dmdc archive-quicklook --archive-root live_archive --window-label 60s
```

Read:

- `docs/live/archive_phase6_2.md`
- `docs/live/summaries_quicklooks_phase6_3.md`
- `docs/cheatsheets/live_archive_cheatsheet.md`

The key principle is: **summary first, raw data second**. Open quicklooks and
summary CSVs first; only load raw partition files around time windows that matter.


## Live Phase 6.4 — archive dashboard mode

For long live-loop campaigns, use archive dashboard mode instead of pointing the dashboard at one run folder:

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
dmdc archive-quicklook --archive-root live_archive --window-label 60s
dmdc live-dashboard --archive-root live_archive --mode archive --window-label 60s
```

Archive dashboard mode is summary-first. It reads the manifest, compact summary CSVs, and quicklook PNGs before opening raw partitions. See `docs/live/dashboard_archive_phase6_4.md` and `docs/cheatsheets/live_archive_dashboard_cheatsheet.md`.
