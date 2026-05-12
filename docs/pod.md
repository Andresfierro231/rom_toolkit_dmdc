# Proper Orthogonal Decomposition (POD)

POD is the SVD-based reduced-basis layer in this repository. It should be viewed as a projection method, not a forecasting model by itself.

Given snapshots

```math
X = [x_1, x_2, \ldots, x_m],
```

POD computes an SVD of the centered/scaled snapshot matrix:

```math
X \approx \Phi_r \Sigma_r V_r^T.
```

The columns of `Phi_r` are the retained POD modes. Each state can be approximated as

```math
x_k \approx \bar{x} + \Phi_r a_k,
```

where `a_k` is the vector of modal coefficients.

## CLI

```bash
dmdc pod \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --time-col time \
  --rank 0.999 \
  --center \
  --outdir outputs/example_pod \
  --plots
```

## Config

```toml
[data]
path = "data/example_timeseries.csv"
time_col = "time"
state_cols = ["x1", "x2"]

[pod]
rank = 0.999
center = true
scale = false

[output]
outdir = "outputs/example_pod"
plots = true
```

Run:

```bash
dmdc pod --config configs/example_pod.toml
```

## Outputs

```text
pod_basis.pkl
pod_summary.json
pod_coefficients.csv
pod_reconstruction.csv
pod_reconstruction_error.csv
reconstruction_error_vs_rank.csv
singular_values.pdf
cumulative_energy.pdf
reconstruction_error_vs_rank.pdf
coefficient_timeseries.pdf
```

## Python API

```python
from dmdc import PODBasis

pod = PODBasis(rank=0.999, center=True, scale=False)
pod.fit(X, state_names=["TP1", "TP2", "massFlowRate"])
A = pod.transform(X)
X_recon = pod.inverse_transform(A)
```

## Rank guidance

- Use a small integer rank when you want interpretability.
- Use an energy threshold such as `0.999` when you want a reconstruction-quality target.
- Compare `reconstruction_error_vs_rank.csv` before deciding the final rank.
- For thermal-hydraulic loops, a rank that reconstructs temperatures well may still be too low for rollout dynamics; later POD-DMDc validation on unseen cases should decide the final modeling rank.
