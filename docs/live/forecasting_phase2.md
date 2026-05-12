# Live Streaming Phase 2: Online Forecasting from a Saved ROM

Live Phase 2 adds the first prediction loop on top of the Phase 1 stream/buffer layer.
It is intentionally conservative:

```text
live/replayed rows
    -> rolling live buffer
    -> latest clean state/input sample
    -> saved offline ROM
    -> forecast table
```

It does **not** do Kalman filtering, model-residual alerting, or online retraining yet.
Those are later phases. This phase answers a narrower question:

> Can a saved, validated ROM be loaded on a local workstation and used quickly every time new loop data arrives?

## Recommended workflow

1. Train and validate a model offline.
2. Replay old data through the live predictor.
3. Tail a live CSV logger after replay works.
4. Inspect `live_forecasts.csv` and `live_forecasts_wide.csv`.

For nonuniform/adaptive timestamps, prefer an adaptive-time model:

```bash
dmdc adaptive-fit --config configs/templates/adaptive_variable_dt_dmdc.toml
```

Then replay with forecasts:

```bash
dmdc live-replay-predict --config configs/templates/live_replay_predict.toml
```

For an append-only CSV logger:

```bash
dmdc live-run-predict --config configs/templates/live_csv_tail_predict.toml
```

## Config anatomy

```toml
[stream]
type = "csv_replay"          # or csv_tail
path = "data/my_loop.csv"
chunk_size = 5

[data]
time_col = "time"
case_col = "case_id"
case_id = "run_001"
state_cols = ["TP1", "TP2", "TP3", "massFlowRate"]
input_cols = ["q_heater", "T_amb"]

[model]
path = "outputs/adaptive_fit/adaptive_model.pkl"

[forecast]
horizons_seconds = [5.0, 10.0, 30.0, 60.0]
# Only needed for discrete/sample-step models.
# discrete_dt_seconds = 0.5

[live]
max_samples = 100
buffer_seconds = 300.0
outdir = "outputs/live_prediction"
```

## Model support

Live Phase 2 can load saved objects from the existing offline workflows:

```text
AdaptiveDMDcModel       Recommended for nonuniform/adaptive physical timestamps.
DMDcModel               Discrete sample-to-sample model.
RegularizedDMDcModel    Ridge/Tikhonov DMDc.
PODDMDcPipeline         POD basis plus DMDc in modal coordinates.
PODDynamicsRegressor    Optional POD-ML modal dynamics, if ML dependencies are installed.
ContinuousDMDcModel     Continuous-time matrices derived from a fixed-step discrete model.
```

## Time handling

For `AdaptiveDMDcModel`, the requested horizons are physical seconds. The predictor uses the continuous generator directly:

```math
\frac{dx}{dt} = A_c x + B_c u.
```

For discrete models, the horizon is converted to an integer number of sample steps:

```math
n = \left\lceil \frac{h}{\Delta t_{\text{discrete}}} \right\rceil.
```

Therefore, if you use ordinary DMDc/POD-DMDc online, set:

```toml
[forecast]
discrete_dt_seconds = 0.5
```

If you do not set it, the predictor tries to read `metadata_.dt` from the model and otherwise falls back to `1.0` second. The output table always includes `effective_horizon_s` so this approximation is visible.

## Output files

```text
raw_stream_log.csv              every row observed by the stream adapter
cleaned_stream_log.csv          validated rows used by the live buffer
live_state_estimates.csv        latest measured states/inputs used as forecast origins
live_forecasts.csv              long-form origin × horizon × state predictions
live_forecasts_wide.csv         wide convenience version of the forecasts
live_warnings.csv               structured data-quality warnings
warnings.txt                    human-readable warnings
live_buffer_summary.json        dt/buffer summary
live_prediction_summary.json    model and run summary
provenance.json                 version, command, config, platform, timestamp
```

## Why forecasts use the measured state directly

Phase 2 uses:

```math
x_{\text{origin}} = x_{\text{latest measured}}.
```

This is simple and useful for testing the live prediction path. Phase 3 should replace that raw measured state with a filtered estimate, for example POD-space Kalman filtering:

```math
x_{\text{latest measured}} \quad \rightarrow \quad \hat{x}_{\text{Kalman}}.
```

## What comes next

The next online phases should add:

```text
Live Phase 3: Kalman/state-estimation layer.
Live Phase 4: residual alerts, model-trust score, and operating-envelope monitoring.
Live Phase 5: optional dashboard.
Live Phase 6: guarded online adaptation/bias correction.
```
