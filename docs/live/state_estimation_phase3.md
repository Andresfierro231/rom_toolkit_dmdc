# Live Phase 3: POD-Kalman State Estimation

Live Phase 3 adds online **state estimation** to the streaming workflow. The goal is to use a saved, offline-validated POD-DMDc model together with live measurements to estimate the current full loop state.

This phase still does **not** do online retraining, residual alerts, autonomous control, or model-trust scoring. Those should remain separate phases.

## Why state estimation?

In a live thermal loop, you may not measure every state used by the ROM. For example, the model may contain

```text
TP1, TP2, TP3, TP4, TP5, TP6, massFlowRate
```

but the live stream might only contain

```text
TP1, TP3, TP6, q_heater
```

POD-Kalman estimation uses the reduced POD coordinates to infer the full state from the measured subset.

## Mathematical idea

The offline POD basis represents the full state as

\[
x_k \approx \bar{x} + \Phi_r a_k,
\]

or, when POD scaling is enabled,

\[
x_k \approx \bar{x} + D_s \Phi_r a_k,
\]

where:

- \(x_k\) is the full physical state,
- \(\bar{x}\) is the POD mean,
- \(D_s\) is the diagonal scale matrix,
- \(\Phi_r\) contains POD modes,
- \(a_k\) are reduced modal coefficients.

The POD-DMDc model evolves those coefficients:

\[
a_{k+1} = A_r a_k + B_r u_k + w_k.
\]

The live sensors measure a subset of full-state rows:

\[
y_k = Cx_k + v_k.
\]

Substituting the POD reconstruction gives the measurement model

\[
y_k = C\bar{x} + C D_s \Phi_r a_k + v_k.
\]

The Kalman filter estimates \(a_k\), then reconstructs the full state.

## Commands

Replay an existing CSV as if it were live:

```bash
dmdc live-replay-estimate --config configs/templates/live_replay_estimate.toml
```

Tail a CSV file being appended by a live logger:

```bash
dmdc live-run-estimate --config configs/templates/live_csv_tail_estimate.toml
```

Minimal command-line example:

```bash
dmdc live-replay-estimate \
  --data live_data/loop_stream.csv \
  --model outputs/pod_dmdc/pod_dmdc_model.pkl \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --measurement-cols TP1 TP3 TP6 \
  --input-cols q_heater T_amb \
  --forecast-horizons-seconds 5 10 30 \
  --discrete-dt-seconds 0.5 \
  --outdir outputs/live_estimate
```

## Outputs

```text
outputs/live_estimate/
├── raw_stream_log.csv
├── cleaned_stream_log.csv
├── live_state_estimates.csv
├── live_modal_estimates.csv
├── live_estimate_covariance.csv
├── live_kalman_innovations.csv
├── live_forecasts.csv
├── live_forecasts_wide.csv
├── live_estimation_summary.json
├── live_buffer_summary.json
├── live_warnings.csv
├── warnings.txt
├── provenance.json
└── config_used.toml
```

## How to choose noise values

The two most important settings are:

```toml
[estimator]
process_noise = 1.0e-6
measurement_noise = 1.0e-3
initial_covariance = 1.0
```

Interpretation:

- Larger `process_noise` means the filter trusts the ROM dynamics less.
- Larger `measurement_noise` means the filter trusts the sensors less.
- Larger `initial_covariance` means the first measurements can strongly correct the initial state estimate.

A practical starting point is to use small process noise and measurement noise comparable to expected sensor variance. For temperature sensors, if the standard deviation of noise is about 0.5 K, then a measurement variance around \(0.5^2 = 0.25\) may be reasonable.

## Current limitations

- Phase 3 currently supports POD-Kalman estimation from saved `PODDMDcPipeline` models.
- It does not retrain the model online.
- It logs innovations, but it does not yet issue residual alerts or trust-score decisions.
- For nonuniform live timestamps, the filter still uses the saved discrete POD-DMDc update per received sample. The forecast layer can map horizons to sample steps using `discrete_dt_seconds`.

## Recommended live workflow

```text
1. Train POD-DMDc offline.
2. Validate on unseen cases.
3. Run live-replay-estimate on historical data.
4. Check innovations and covariance traces.
5. Run live-run-estimate on the actual stream.
6. Add residual alerts later in Live Phase 4.
```
