# Live Streaming Cheat Sheet

## Phase 1: ingest only

Use this to test the stream path before any model is involved.

```bash
dmdc live-replay --config configs/templates/live_replay_csv.toml
```

```bash
dmdc live-run --config configs/templates/live_csv_tail.toml
```

Outputs:

```text
raw_stream_log.csv
cleaned_stream_log.csv
live_warnings.csv
warnings.txt
live_buffer_summary.json
live_ingestion_summary.json
provenance.json
```

## Phase 2: replay or tail plus forecast

Train a model offline first. For nonuniform/adaptive time, prefer:

```bash
dmdc adaptive-fit --config configs/templates/adaptive_variable_dt_dmdc.toml
```

Then replay with forecasts:

```bash
dmdc live-replay-predict --config configs/templates/live_replay_predict.toml
```

Or tail a live logger:

```bash
dmdc live-run-predict --config configs/templates/live_csv_tail_predict.toml
```

Outputs added by Phase 2:

```text
live_state_estimates.csv
live_forecasts.csv
live_forecasts_wide.csv
live_prediction_summary.json
```

## Minimal CLI example

```bash
dmdc live-replay-predict \
  --data data/my_loop.csv \
  --model outputs/adaptive_fit/adaptive_model.pkl \
  --time-col time \
  --state-cols TP1 TP2 TP3 massFlowRate \
  --input-cols q_heater T_amb \
  --forecast-horizons-seconds 5 10 30 60 \
  --max-samples 100 \
  --outdir outputs/live_replay_prediction
```

## If using a discrete model

For `DMDcModel`, `RegularizedDMDcModel`, `PODDMDcPipeline`, or POD-ML, tell the predictor how many physical seconds one sample step represents:

```bash
--discrete-dt-seconds 0.5
```

or in TOML:

```toml
[forecast]
discrete_dt_seconds = 0.5
```

## Current limitations

Live Phase 2 does not yet do:

```text
Kalman filtering
state-estimation uncertainty
residual alerts
model-trust scoring
online retraining
operator dashboard
```

Those are intentionally separate future phases.

## Live Phase 3: filtered state estimation

Use this when the stream has only some sensors, but you have a saved POD-DMDc model for the full loop state.

```bash
dmdc live-replay-estimate \
  --data live_data/loop_log.csv \
  --model outputs/pod_dmdc/pod_dmdc_model.pkl \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --measurement-cols TP1 TP3 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --forecast-horizons-seconds 5 10 30 \
  --discrete-dt-seconds 0.5 \
  --outdir outputs/live_estimate
```

Key idea:

```text
measurement_cols = sensors actually present in the stream
state_cols       = full state expected by the saved model
```

Main outputs:

```text
live_state_estimates.csv      filtered full-state estimate
live_modal_estimates.csv      filtered POD coefficients
live_kalman_innovations.csv   measured - predicted measurement
live_estimate_covariance.csv  uncertainty proxy in modal space
live_forecasts.csv            optional forecasts from filtered state
```

First tuning knobs:

```toml
[estimator]
process_noise = 1.0e-6       # trust ROM less if larger
measurement_noise = 1.0e-3   # trust sensors less if larger
initial_covariance = 1.0     # first-sample uncertainty
```

## Phase 5 dashboard

Install the optional dashboard extras:

```bash
python -m pip install -e '.[dashboard]'
```

Launch the dashboard on a live monitoring folder:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring
```

Use a config:

```bash
dmdc live-dashboard --config configs/templates/live_dashboard.toml
```

Write a no-browser summary JSON:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --write-summary-only
```

For the best live update experience, run the monitor with `--save-every-batch` so CSV outputs are refreshed as rows arrive.

---

## Live Phase 6.1: bounded bias correction

Replay with adaptation:

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
```

Tail a live CSV logger with adaptation:

```bash
dmdc live-run-adapt --config configs/templates/live_csv_tail_adapt.toml
```

Open the dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_adaptation_replay
```

Bias correction is conservative: it adds a bounded forecast offset and records every accepted/skipped update. It does not retrain the saved ROM.

---

## Long-term archive commands

Archive a run folder:

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive --format parquet
```

Show the manifest:

```bash
dmdc archive-index --archive-root live_archive
```

Summarize the archive:

```bash
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
```

Make quicklook plots:

```bash
dmdc archive-quicklook --archive-root live_archive --window-label 60s
```

For an integrated replay/adaptation/archive demo:

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt_with_archive.toml
```

See also:

- `docs/live/archive_phase6_2.md`
- `docs/live/summaries_quicklooks_phase6_3.md`
- `docs/cheatsheets/live_archive_cheatsheet.md`


## Live Phase 6.4 — archive dashboard mode

For long live-loop campaigns, use archive dashboard mode instead of pointing the dashboard at one run folder:

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
dmdc archive-quicklook --archive-root live_archive --window-label 60s
dmdc live-dashboard --archive-root live_archive --mode archive --window-label 60s
```

Archive dashboard mode is summary-first. It reads the manifest, compact summary CSVs, and quicklook PNGs before opening raw partitions. See `docs/live/dashboard_archive_phase6_4.md` and `docs/cheatsheets/live_archive_dashboard_cheatsheet.md`.
