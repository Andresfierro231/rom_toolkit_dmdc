# POD and SVD Reduced Bases

Proper Orthogonal Decomposition, or POD, constructs a low-dimensional basis for high-dimensional state snapshots. In this repository POD is computed using the singular value decomposition.

Given a snapshot matrix

```math
X = \begin{bmatrix} | & | & & | \\
 x_1 & x_2 & \cdots & x_m \\
 | & | & & |
\end{bmatrix},
```

the centered form is

```math
\tilde X = X - \bar x \mathbf{1}^T,
```

where `\bar x` is the mean state.

The SVD is

```math
\tilde X = \Phi \Sigma V^T.
```

The columns of `\Phi` are POD modes. Keeping the first `r` modes gives

```math
\Phi_r \in \mathbb{R}^{n_x \times r}.
```

## Modal coefficients

The reduced coordinates, also called modal coefficients or basis weights, are

```math
a_k = \Phi_r^T (x_k - \bar x).
```

For all snapshots,

```math
A_{coef} = \Phi_r^T \tilde X.
```

The reconstruction is

```math
\hat x_k = \bar x + \Phi_r a_k.
```

or, for all snapshots,

```math
\hat X = \bar x \mathbf{1}^T + \Phi_r A_{coef}.
```

## Energy criterion

The singular values measure captured variance/energy. The fraction of energy captured by the first `r` modes is

```math
E_r = \frac{\sum_{i=1}^{r} \sigma_i^2}{\sum_{i=1}^{q} \sigma_i^2}.
```

This lets the user choose a rank such as `0.999`, meaning keep enough modes to capture 99.9% of snapshot energy.

## Scaling caution

If one state is in Kelvin and another is a small flow rate, the largest-magnitude variable may dominate the POD energy. The repo supports optional centering and scaling, but scaling should be a deliberate modeling choice. Scaling changes the inner product in which the POD basis is optimal.

## Where this is implemented

- `src/dmdc/pod.py`: `PODBasis.fit`, `transform`, `inverse_transform`, `reconstruction_error`.
- `src/dmdc/plotting.py`: POD singular value and cumulative energy plots.
- `src/dmdc/cli.py`: `dmdc pod`.

## Outputs to inspect

- `pod_summary.json`: rank, energy, state names, centering/scaling choices.
- `pod_coefficients.csv`: modal coefficients over snapshots.
- `pod_reconstruction.csv`: reconstructed states.
- `pod_reconstruction_error.csv`: per-state reconstruction errors.
- `cumulative_energy.pdf`: rank selection visual.
