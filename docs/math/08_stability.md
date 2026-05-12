# Stability Diagnostics

For a discrete-time linear model

```math
x_{k+1} = A x_k,
```

or a reduced model

```math
a_{k+1} = A_r a_k,
```

rollout behavior is strongly affected by the eigenvalues of the transition matrix.

## Spectral radius

The spectral radius is

```math
\rho(A) = \max_i |\lambda_i(A)|.
```

For a discrete-time autonomous linear system:

- `rho(A) < 1`: asymptotically stable,
- `rho(A) ≈ 1`: marginal or slow decay/growth,
- `rho(A) > 1`: potentially unstable rollouts.

## DMDc and inputs

For DMDc,

```math
x_{k+1} = A x_k + B u_k,
```

stability diagnostics focus on the autonomous transition matrix `A`. Inputs can still force growth, but unstable eigenvalues in `A` are a clear warning that recursive prediction may diverge.

## Why one-step error can hide instability

A model can fit one-step transitions well and still have `rho(A) > 1`. Small one-step errors do not guarantee bounded rollouts. This is why the repo reports both eigenvalue diagnostics and multi-step validation errors.

## Where this is implemented

- `src/dmdc/stability.py`: eigenvalues, spectral radius, unstable count, status labels.
- `src/dmdc/baselines.py`: stability summaries in model comparison.
- `src/dmdc/reports.py`: LaTeX report stability section.
- `src/dmdc/plotting.py`: eigenvalue complex-plane plot.

## Friendly interpretation

An unstable warning is not automatically proof that the model is useless. It means the model should be judged by rollout error, forecast-horizon error, and test-case performance. Common fixes include lower rank, POD-DMDc instead of full-state DMDc, scaling, better inputs, or more training cases.
