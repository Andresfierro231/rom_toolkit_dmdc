# Live Phase 6.1 — Bias Correction and Adaptation Records

Live Phase 6.1 adds the first conservative online-adaptation layer to the live ROM workflow.

It is intentionally **not** online retraining.

The validated ROM, POD basis, DMDc matrices, and Kalman filter dynamics remain fixed. Phase 6.1 learns only a small additive forecast correction from matched forecast residuals:

```math
\hat{x}_{\text{corrected}}(t+h) = \hat{x}_{\text{ROM}}(t+h) + c(t)
```

or, in horizon-dependent form,

```math
\hat{x}_{\text{corrected},i}(t+h) = \hat{x}_{\text{ROM},i}(t+h) + c_i(h,t).
```

This is useful when the live loop is consistently offset from the offline model because of sensor calibration drift, heat-loss mismatch, imperfect boundary conditions, or small experimental differences.

---

## Recommended command

Replay mode:

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
```

Live CSV-tail mode:

```bash
dmdc live-run-adapt --config configs/templates/live_csv_tail_adapt.toml
```

Then open the dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_adaptation_replay
```

The dashboard includes an **Adaptation** tab with bias history, update records, and raw-vs-corrected residual comparisons.

---

## Where Phase 6.1 fits

```text
Live Phase 1: stream/replay/tail data
Live Phase 2: forecast from a saved ROM
Live Phase 3: POD-Kalman state estimation
Live Phase 4: residual alerts and trust score
Live Phase 5: Streamlit dashboard
Live Phase 6.1: bounded bias correction and adaptation records
```

Phase 6.1 depends on Phase 4 outputs:

```text
live_forecasts.csv
live_forecast_residuals.csv
live_alerts.csv
live_trust_score.csv
cleaned_stream_log.csv
```

It writes additional adaptation outputs.

---

## Bias modes

### `state_bias`

Learns one bias per state:

```math
c = [c_{TP1}, c_{TP2}, c_{TP3}, \ldots]^T.
```

Use this when you want the safest interpretation:

```text
TP4 is consistently about +2 K high relative to the model.
```

### `horizon_state_bias`

Learns one bias for each state and forecast horizon:

```math
c_i(h).
```

This is often better for forecasting because a 5-second forecast may have a different systematic error than a 60-second forecast.

Example:

```text
TP4, 5 s horizon:  +0.5 K
TP4, 30 s horizon: +2.1 K
TP4, 60 s horizon: +4.8 K
```

---

## Update rule

For each matched forecast residual,

```math
r_i(t,h) = x_{i,\text{measured}}(t+h) - \hat{x}_{i,\text{ROM}}(t+h),
```

the bias is updated by exponential smoothing:

```math
c_{k+1} = c_k + \alpha(r_k - c_k).
```

The update is bounded by:

```text
max_update_step
max_abs_bias
clip_residual_abs
trust-score threshold
alert-severity gate
operating-envelope gate
```

So Phase 6.1 is intentionally slow and reversible.

---

## Configuration

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

### Practical tuning

| Setting | Meaning | Conservative starting value |
|---|---|---:|
| `learning_rate` | How quickly bias follows residuals | `0.01` |
| `max_abs_bias` | Maximum allowed correction magnitude | `5–10 K` for temperatures |
| `max_update_step` | Maximum change from one residual event | `0.1–0.25 K` |
| `update_only_when_trust_above` | Skip learning when model trust is low | `0.7` |
| `clip_residual_abs` | Ignore extreme residual magnitude beyond this | `10–20 K` |

---

## Outputs

```text
live_bias_update_events.csv
live_bias_state_timeseries.csv
live_bias_horizon_timeseries.csv
live_bias_summary_by_state.csv
live_bias_summary_by_horizon.csv
live_bias_corrected_forecasts.csv
live_bias_corrected_forecast_residuals.csv
live_bias_error_comparison.csv
live_adaptation_summary.json
live_bias_summary.txt
```

### `live_bias_update_events.csv`

This is the most important audit file. It records every accepted and skipped update:

```text
time
state
forecast_horizon_s
old_bias
new_bias
delta_bias
raw_residual
residual_used
trust_score
accepted
rejection_reason
```

### `live_bias_corrected_forecasts.csv`

This preserves raw forecasts and adds correction columns:

```text
raw_predicted_value
applied_bias
bias_corrected_predicted_value
```

The raw `live_forecasts.csv` file is never overwritten.

### `live_bias_error_comparison.csv`

This table compares mean/max absolute residuals before and after bias correction by state and horizon.

---

## Safety and interpretation

Bias correction should be interpreted as:

```text
The saved model is fixed, but the live system appears to have a persistent offset.
```

It should **not** be interpreted as:

```text
The ROM has been retrained online.
```

Phase 6.1 does not change hardware, actuators, control logic, or safety systems.

---

## Common reasons updates are skipped

```text
trust_score_below_threshold
outside_training_or_operating_envelope
blocked_by_alert_severity_critical
```

Skipped updates are not failures. They are part of making the adaptation layer defensible.
