# Live Phase 4: Monitoring, Residual Alerts, and Trust Scoring

Live Phase 4 turns the streaming/forecasting/state-estimation pipeline into an advisory monitoring workflow. It still does **not** retrain the ROM online, does **not** control hardware, and does **not** replace independent safety systems.

The workflow is:

```text
live stream or replay CSV
        ↓
RollingLiveBuffer validation
        ↓
POD-Kalman state estimate
        ↓
forecast from filtered state
        ↓
match old forecasts to new measurements
        ↓
residual, innovation, range, covariance alerts
        ↓
trust-score timeline and CSV logs
```

## Commands

Replay historical data as if it were live:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml
```

Tail a CSV logger that is being appended by a DAQ/workstation:

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml
```

## Important outputs

```text
live_state_estimates.csv          Filtered full-state estimates
live_modal_estimates.csv          POD modal-coordinate estimates
live_kalman_innovations.csv       Measurement mismatch before correction
live_forecasts.csv                Forecasts from each live origin
live_forecast_residuals.csv       Matched forecast-vs-measurement residuals
live_alerts.csv                   Unified alert table
live_alerts.txt                   Human-readable alert log
live_trust_score.csv              Advisory trust-score timeline
live_monitoring_summary.json      Machine-readable run summary
```

## Alert types

### `FORECAST_RESIDUAL_HIGH`

A past forecast was matched against a later measurement and the absolute residual exceeded the configured threshold:

\[
r(t) = y_{\text{measured}}(t) - \hat{y}(t \mid t-h).
\]

This can indicate model drift, sensor drift, a disturbance, or operation outside the training envelope.

### `KALMAN_INNOVATION_HIGH`

The current measurement disagrees with the model-predicted measurement before Kalman correction:

\[
\nu_k = y_k - \hat{y}_{k|k-1}.
\]

Large innovations are often the fastest signal that the live loop and the validated model are diverging.

### `OPERATING_CONDITION_OUT_OF_RANGE`

An input/control value is outside the configured training/validation envelope. Forecasts in this regime should be treated as extrapolations.

### `STATE_ESTIMATE_UNCERTAINTY_HIGH`

The trace of the POD modal covariance exceeded the configured threshold. This means the filter has high uncertainty about the reduced state.

## Trust score

The trust score is a simple advisory heuristic in `[0, 1]`. It starts at 1 and decreases as alerts accumulate. It is meant to make logs easy to scan; it is not a safety interlock and should not be used directly for autonomous control.

## Configuration

```toml
[monitor]
residual_abs_threshold = 5.0
innovation_abs_threshold = 5.0
innovation_norm_threshold = 12.0
covariance_trace_threshold = 10.0
forecast_match_tolerance_seconds = 0.3
operating_ranges = {q_heater = [0.0, 120.0], T_amb = [280.0, 330.0]}
```

Use thresholds based on the validation report. For example, if held-out-case TP errors are typically below 2 K, a 5 K residual threshold is a reasonable first warning level.

## Recommended use

1. Train and validate offline.
2. Pick a stable model with good held-out performance.
3. Run `live-replay-monitor` on old logs first.
4. Tune thresholds until alerts are meaningful.
5. Use `live-run-monitor` on a live CSV logger.
6. Treat alerts as advisory; do not use this as autonomous safety logic.
