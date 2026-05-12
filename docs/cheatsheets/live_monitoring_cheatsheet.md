# Live Monitoring Cheat Sheet

## Replay old data with alerts

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml
```

## Tail a live CSV logger with alerts

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml
```

## Main files to inspect

```text
live_alerts.csv
live_alerts.txt
live_trust_score.csv
live_forecast_residuals.csv
live_kalman_innovations.csv
live_monitoring_summary.json
```

## Common tuning knobs

```toml
[monitor]
residual_abs_threshold = 5.0
innovation_abs_threshold = 5.0
forecast_match_tolerance_seconds = 0.3
operating_ranges = {q_heater = [0.0, 120.0]}
```

## Meaning of alerts

- `FORECAST_RESIDUAL_HIGH`: old forecast did not match later measurement.
- `KALMAN_INNOVATION_HIGH`: current measurement disagrees with model prediction before correction.
- `OPERATING_CONDITION_OUT_OF_RANGE`: input/control value is outside trusted envelope.
- `STATE_ESTIMATE_UNCERTAINTY_HIGH`: Kalman covariance is high.

## Safety note

This is an advisory monitoring system. It logs, forecasts, and warns. It does not control hardware.
