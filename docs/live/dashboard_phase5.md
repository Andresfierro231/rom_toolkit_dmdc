# Live Phase 5 — Streamlit Dashboard

Live Phase 5 adds a polished, read-only Streamlit dashboard for the live digital-twin outputs produced by the earlier phases.

The dashboard is designed for the audience that will not read every math file. It shows the live loop status, estimated states, forecasts, residuals, alerts, Kalman diagnostics, and trust score in interactive plots.

## Install dashboard dependencies

The core ROM package does not require Streamlit. Install the optional dashboard dependencies when you want the UI:

```bash
python -m pip install -e '.[dashboard]'
```

or, with the ML extras too:

```bash
python -m pip install -e '.[ml,dashboard]'
```

## Recommended workflow

First generate live monitoring outputs:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml
```

or for a CSV file that a local logger keeps appending to:

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml --save-every-batch
```

Then launch the dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring
```

For a config-driven launch:

```bash
dmdc live-dashboard --config configs/templates/live_dashboard.toml
```

## What the dashboard reads

The dashboard watches a live output folder and reads these files when available:

```text
cleaned_stream_log.csv
live_state_estimates.csv
live_modal_estimates.csv
live_estimate_covariance.csv
live_kalman_innovations.csv
live_forecasts.csv
live_forecast_residuals.csv
live_alerts.csv
live_trust_score.csv
live_warnings.csv
```

Missing files are okay. For example, a Phase-2 live prediction run may have forecasts but no Kalman innovations or trust score. The dashboard will show useful panels and clearly mark missing/not-yet-created tables.

## Main panels

### Overview

Shows the current live-run status, latest timestamp, number of clean samples, number of forecasts, alert counts, latest trust score, and available states.

### States

Interactive measured-vs-estimated state history. For sparse sensing, the measured stream may only include a few sensors, while `live_state_estimates.csv` can include the full POD-Kalman reconstructed state.

### Forecasts

Interactive forecast curves by state and horizon. This is the panel most useful for showing what the live ROM believes will happen next.

### Residuals

Forecast residuals are created by matching old forecasts to later measurements. This panel shows where the live loop is disagreeing with the ROM.

### Alerts & trust

Shows the trust-score timeline and the alert table. This is the operator-facing status panel.

### Kalman

Shows innovations and covariance diagnostics. Large innovations mean the live measurements disagree with the model-predicted measurement.

### Raw tables

Shows the raw CSV tables for debugging and transparency.

## Why this is read-only

The dashboard does not control hardware, change the model, retrain online, or write commands to the loop. It only visualizes logs. This is intentional: the first live digital-twin system should be advisory, auditable, and safe.

## Running remotely

On a workstation:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --port 8501
```

On a remote machine, bind to all interfaces if appropriate for your network/security setup:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --host 0.0.0.0 --port 8501
```

Then open the URL printed by Streamlit.

## CI / no-browser mode

To check that a live output folder is dashboard-readable without launching a web server:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --write-summary-only
```

This writes:

```text
live_dashboard_summary.json
```

## Practical advice for demos

For the prettiest dashboard during a replay demo, run the monitor with:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml --save-every-batch
```

Then open the dashboard on the same output folder. For true live use, the CSV-tail monitor should also use `--save-every-batch` so the dashboard updates as new rows arrive.

---

## Phase 6.1 adaptation tab

When the run folder contains outputs from:

```bash
dmdc live-replay-adapt ...
dmdc live-run-adapt ...
```

the dashboard also shows an **Adaptation** tab.

This tab visualizes:

```text
current bias by state
bias history over time
bias by forecast horizon
raw vs bias-corrected residual summaries
accepted and skipped update counts
full bias update audit log
```

The dashboard still remains read-only. It does not update the bias model itself; it only reads the CSV files written by the live adaptation command.
