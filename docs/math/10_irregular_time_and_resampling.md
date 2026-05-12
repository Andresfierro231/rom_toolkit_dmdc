# Irregular Time Steps, Adaptive Solvers, and Resampling

Real SAM outputs and experimental logs often have **nonuniform time steps**. The
repo treats this as the default real-data expectation. Nonuniform time is not an
error; it simply determines which model interpretation is safest.

## Discrete sample-to-sample maps

Standard DMD/DMDc learns

```math
x_{k+1} \approx A_d x_k + B_d u_k.
```

This is a map from sample index `k` to sample index `k+1`. It is easiest to
interpret physically when every transition has the same duration \(\Delta t\).
When \(\Delta t_k\) changes, one learned \(A_d\) is an average sample-to-sample
operator over mixed time intervals.

That can still be useful for prediction by sample index, but the eigenvalues are
not one fixed-time propagator.

## Adaptive / variable-time-step DMDc

When the physical time interval matters, use the adaptive model described in
[`13_adaptive_variable_dt_dmdc.md`](13_adaptive_variable_dt_dmdc.md). It learns

```math
\frac{dx}{dt} \approx A_c x + B_c u
```

from finite-difference slopes using each actual \(\Delta t_k\).

Recommended command:

```bash
dmdc adaptive-fit --config configs/templates/adaptive_variable_dt_dmdc.toml
```

Or include it in comparisons:

```toml
[compare]
models = ["persistence", "mean", "adaptive_dmdc", "ridge_dmdc", "pod_dmdc"]
```

## Diagnostics

For each case, `inspect-data` checks:

- duplicate times,
- non-monotonic time,
- median time step,
- min/max time step,
- standard deviation of positive time steps,
- large gaps relative to the median time step,
- whether the case is approximately uniform.

## Resampling

When resampling is explicitly enabled, the repo creates a uniform time grid and
interpolates selected columns. For one scalar signal `x(t)`, linear interpolation
produces values

```math
x(t_*) \approx x(t_i) + \frac{t_* - t_i}{t_{i+1} - t_i}\left[x(t_{i+1}) - x(t_i)\right].
```

This is done case by case so independent trajectories remain independent.

## Important policy

The repo never silently resamples data. Resampling changes the data and can hide
gaps or measurement issues. The user must call `dmdc resample` or enable
resampling explicitly in a config.

## Recommended workflow

1. Run `dmdc inspect-data` on raw data.
2. Read `warnings.txt` and `dt_summary_by_case.csv`.
3. If time is highly nonuniform and physical time matters, run `adaptive-fit` or
   include `adaptive_dmdc` in model comparisons.
4. If a fixed-step discrete map is needed, resample explicitly and save the
   resampled CSV.
5. Fit ROMs only after the time-step assumptions are clear.

## Where this is implemented

- `src/dmdc/resampling.py`: inspection and resampling utilities.
- `src/dmdc/adaptive.py`: variable-time-step continuous-generator DMDc.
- `src/dmdc/warnings.py`: friendly warnings.
- `src/dmdc/cli.py`: `inspect-data`, `resample`, and `adaptive-fit` commands.
