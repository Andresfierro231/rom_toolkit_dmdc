# Troubleshooting Guide

## The model predicts poorly

Possible causes:

1. The dynamics are strongly nonlinear over the data range.
2. Important inputs are missing.
3. The time step is nonuniform.
4. Rank is too low and discards relevant dynamics.
5. Rank is too high and overfits noise.
6. State variables have very different magnitudes and need `--scale`.
7. The data includes multiple regimes, such as startup and steady-state behavior, in one fit.

## The condition number is huge

The augmented matrix `Omega = [X; U]` may be ill-conditioned. Try:

```bash
--scale --rank 0.999
```

or remove redundant variables.

## Eigenvalues are outside the unit circle

This can mean:

- the system is genuinely unstable in the fitted regime,
- the fit is overfitting noise,
- rank is too high,
- the data does not sufficiently excite the dynamics,
- inputs are missing or incorrectly aligned.

## My controls are one row shorter than my states

That is allowed. If `X` has `m+1` rows, `U` may have `m` rows because each `u_k` maps `x_k` to `x_{k+1}`.

## I have nonuniform time steps

DMDc can still fit a sample-to-sample map, but `A` is no longer a fixed-duration propagator. Prefer `dmdc adaptive-fit` when physical time matters. Resample explicitly with `dmdc resample` only when a fixed-step map is desired and interpolation is justified.
