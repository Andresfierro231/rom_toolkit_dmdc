# QR/Q-DEIM Sensor Selection and POD Sparse Sensing

Sparse sensing asks: which measured variables are most informative for reconstructing the dominant state space?

## QR/Q-DEIM idea

Given POD modes

```math
\Phi_r \in \mathbb{R}^{n_x \times r},
```

we want to select rows of `\Phi_r`, which correspond to physical state variables or sensor locations. Pivoted QR is applied to

```math
\Phi_r^T.
```

The pivot order identifies state indices whose rows best span the retained POD subspace.

If

```math
\Phi_r^T P = Q R,
```

then the first pivots in `P` define the selected sensors.

## Sparse reconstruction

Let `C` be a row-selection matrix that keeps only selected sensors. The sparse measurement is

```math
y = C x.
```

Using the POD approximation

```math
x \approx \bar x + \Phi_r a,
```

we get

```math
y - C\bar x \approx C\Phi_r a.
```

Then estimate modal coefficients by least squares:

```math
a \approx (C\Phi_r)^\dagger (y - C\bar x).
```

Finally reconstruct the full state:

```math
\hat x = \bar x + \Phi_r a.
```

## Why this matters for loop data

For thermal-fluid loops, sparse sensing can help identify which thermocouples or wall-temperature locations carry the most information about the dominant dynamics. This is useful for sensor placement, digital twin state estimation, and interpreting spatial coupling.

## Where this is implemented

- `src/dmdc/sensor_selection.py`: generic SVD + QR state ranking.
- `src/dmdc/pod_sensors.py`: POD-specific sparse sensing and reconstruction.
- `src/dmdc/cli.py`: `dmdc select-sensors` and `dmdc pod-sensors`.

## Important caveat

QR-selected sensors are optimized to reconstruct the retained POD subspace, not necessarily to minimize future prediction error. For forecasting workflows, compare selected-sensor reconstructions against held-out trajectories and forecast-horizon errors.
