# Bias Correction Cheat Sheet

## Run replay adaptation

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
```

## Run live CSV-tail adaptation

```bash
dmdc live-run-adapt --config configs/templates/live_csv_tail_adapt.toml
```

## Open dashboard

```bash
dmdc live-dashboard --run-dir outputs/live_adaptation_replay
```

## Important config

```toml
[live_adaptation]
enabled = true
method = "horizon_state_bias"

[live_adaptation.bias]
learning_rate = 0.01
max_abs_bias = 10.0
max_update_step = 0.25
update_only_when_trust_above = 0.70
skip_when_outside_training_envelope = true
skip_on_alert_severity = ["critical"]
clip_residual_abs = 20.0
apply_bias_to_forecasts = true
```

## Main outputs

```text
live_bias_update_events.csv                 # every accepted/skipped update
live_bias_state_timeseries.csv              # bias over time by state
live_bias_horizon_timeseries.csv            # bias over time by state/horizon
live_bias_corrected_forecasts.csv           # raw forecast + applied bias + corrected forecast
live_bias_corrected_forecast_residuals.csv  # residuals after bias correction
live_bias_error_comparison.csv              # raw vs corrected residual summary
live_adaptation_summary.json                # machine-readable summary
live_bias_summary.txt                       # quick human summary
```

## Interpretation

Bias correction means:

```text
The ROM is fixed, but forecasts get a small learned offset.
```

Bias correction does not mean:

```text
The ROM is retrained online.
```

## Good starting values

```text
learning_rate = 0.01
max_update_step = 0.1 to 0.25
max_abs_bias = 5 to 10 K for temperatures
update_only_when_trust_above = 0.7
```

## What to inspect first

```text
1. live_bias_update_events.csv
2. live_bias_error_comparison.csv
3. dashboard Adaptation tab
4. skipped update reasons
```
