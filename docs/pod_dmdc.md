# POD-DMDc Reduced-Order Modeling

POD-DMDc combines two transparent linear-algebra steps:

1. **POD/SVD projection** learns a low-dimensional basis for the measured state data.
2. **DMD/DMDc in modal space** learns the dynamics of the POD coefficients.

This keeps SVD/POD as the reduced-basis backbone. ML is not part of this workflow and is not required.

## Mathematical idea

Given full-state snapshots

\[
x_k \in \mathbb{R}^{n},
\]

POD approximates them as

\[
x_k \approx \bar{x} + \Phi_r a_k,
\]

where:

- \(\bar{x}\) is the training mean,
- \(\Phi_r\) contains the first \(r\) POD modes,
- \(a_k\) are modal coefficients.

Then DMDc is fit in reduced coordinates:

\[
a_{k+1} \approx A_r a_k + B_r u_k.
\]

If no input columns are provided, the method reduces to POD-DMD:

\[
a_{k+1} \approx A_r a_k.
\]

## CLI usage

```bash
dmdc pod-dmdc \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --pod-rank 0.999 \
  --dmdc-rank full \
  --outdir outputs/example_pod_dmdc \
  --plots
```

## Config usage

```bash
dmdc pod-dmdc --config configs/example_pod_dmdc.toml
```

Example config:

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

[model]
dmdc_rank = "full"

[output]
outdir = "outputs/example_pod_dmdc"
plots = true
```

## Python API

```python
from dmdc import PODDMDcPipeline

pipeline = PODDMDcPipeline(pod_rank=0.999, dmdc_rank="full")
pipeline.fit_trajectories(X_cases, U_cases, state_names=state_cols, input_names=input_cols)

X_pred = pipeline.rollout(X_cases[0][0], U_future=U_cases[0][:-1])
```

## Outputs

A typical run produces:

```text
pod_dmdc_model.pkl
pod_dmdc_summary.json
diagnostics.json
modal_coefficients.csv
reconstructed_rollout_predictions.csv
error_by_case.csv
error_by_state.csv
singular_values.pdf
cumulative_energy.pdf
eigenvalues_reduced_A.pdf
true_vs_reconstructed_first_case.pdf
```

## Practical notes

- Use POD-DMDc when the full state has many variables or when full-state DMDc is ill-conditioned.
- Use `--pod-rank 0.999` as a reasonable first setting, then sweep rank later.
- Use `--input-cols` when you know forcing or boundary-condition variables.
- Omit `--input-cols` for autonomous POD-DMD.
