# Phase 7: Optional POD-ML modal-coefficient dynamics

This repo is **not** an ML-first black-box ROM package. The core remains:

1. SVD/POD for basis construction.
2. DMD/DMDc for transparent linear dynamics.
3. Validation, stability checks, dashboards, and reports for trustworthiness.

Phase 7 adds an optional ML layer that acts only after POD projection.

## Mathematical idea

POD represents full states as

\[
x_k \approx \bar{x} + \Phi_r a_k,
\]

where \(\Phi_r\) is the SVD/POD basis and \(a_k\) are modal coefficients. The optional ML model learns

\[
[a_k, u_k] \mapsto a_{k+1},
\]

or, when no inputs are available,

\[
a_k \mapsto a_{k+1}.
\]

Then the predicted coefficients are reconstructed using the same POD basis:

\[
\hat{x}_k = \bar{x} + \Phi_r \hat{a}_k.
\]

ML does **not** replace POD. ML does **not** replace the DMDc implementation. It is an optional nonlinear reduced-coordinate dynamics experiment.

## CLI usage

```bash
dmdc pod-ml \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --pod-rank 0.999 \
  --model-type ridge \
  --center \
  --outdir outputs/example_pod_ml \
  --plots
```

Supported model types:

- `ridge`
- `random_forest`
- `gradient_boosting`
- `mlp`

Start with `ridge`. It is simple, fast, and much easier to debug. Use nonlinear models only after POD-DMDc and ridge POD-ML have been compared on held-out cases.

## Config usage

```bash
dmdc pod-ml --config configs/example_pod_ml.toml
```

Example TOML:

```toml
[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[pod]
rank = 0.999
center = true
scale = false

[ml]
model_type = "ridge"
recursive_rollout = true
outdir = "outputs/example_pod_ml"

[output]
plots = true
```

## Python API

```python
from dmdc import PODDynamicsRegressor

rom = PODDynamicsRegressor(
    pod_rank=0.999,
    model_type="ridge",
    center=True,
)

rom.fit_trajectories(X_cases, U_cases, state_names=state_cols, input_names=input_cols)
X_pred = rom.rollout(X_cases[0][0], U_future=U_cases[0][:-1])
```

## Outputs

A `pod-ml` run writes:

```text
pod_ml_model.pkl
pod_ml_summary.json
diagnostics.json
modal_coefficients.csv
modal_predictions.csv
reconstructed_predictions.csv
error_by_case.csv              # multi-case mode
error_by_state.csv             # multi-case mode
singular_values.pdf            # with --plots
cumulative_energy.pdf          # with --plots
true_vs_reconstructed*.pdf     # with --plots
modal_coefficients*.pdf        # with --plots
```

## How to use POD-ML responsibly

Recommended order:

1. Inspect and resample data if needed.
2. Fit POD and check reconstruction error.
3. Fit POD-DMDc and evaluate held-out cases.
4. Compare against persistence, mean, DMDc, and POD-DMDc.
5. Try POD-ML only as an optional nonlinear reduced-coordinate model.
6. Trust POD-ML only if it improves held-out rollout error and does not create worse residuals or unstable behavior.

Use:

```bash
dmdc compare --config configs/example_compare_with_pod_ml.toml
```

The comparison dashboard can include `pod_ml_ridge`, `pod_ml_random_forest`, `pod_ml_gradient_boosting`, or `pod_ml_mlp`.

## Thermal-hydraulic loop guidance

For SAM or experimental loop data, POD-ML can be useful when the reduced coefficients have nonlinear dynamics caused by changes in heater power, boundary conditions, thermal inertia, or transport delay. However, it can also overfit. Always evaluate on unseen cases, especially cases at different operating conditions.
