# Data Matrices, Cases, and Notation

This repository treats a time series as a sequence of state vectors and optional input vectors. At sample index `k`, the state is

```math
x_k \in \mathbb{R}^{n_x},
```

and the input/control vector is

```math
u_k \in \mathbb{R}^{n_u}.
```

For a thermal-hydraulic loop, `x_k` might contain thermocouple temperatures, wall temperatures, pressures, and mass flow rate. The input vector `u_k` might contain heater power, pump speed, inlet temperature, ambient temperature, heat transfer coefficient, or any known boundary condition.

## Snapshot matrices

For one trajectory with samples `0, 1, ..., m`, the code forms transition matrices

```math
X = \begin{bmatrix} | & | & & | \\
 x_0 & x_1 & \cdots & x_{m-1} \\
 | & | & & |
\end{bmatrix}
\in \mathbb{R}^{n_x \times m},
```

```math
X' = \begin{bmatrix} | & | & & | \\
 x_1 & x_2 & \cdots & x_m \\
 | & | & & |
\end{bmatrix}
\in \mathbb{R}^{n_x \times m},
```

and, if inputs exist,

```math
U = \begin{bmatrix} | & | & & | \\
 u_0 & u_1 & \cdots & u_{m-1} \\
 | & | & & |
\end{bmatrix}
\in \mathbb{R}^{n_u \times m}.
```

The convention used in the code is **states by snapshots**, not snapshots by states. Dataframes have rows as time samples, but the linear algebra functions transpose those arrays into state-by-snapshot matrices internally.

## Multi-case data

When a file contains multiple independent cases, the repository does not create transitions across case boundaries. For example, the valid transitions are

```text
run_001: x0 -> x1 -> x2 -> ...
run_002: x0 -> x1 -> x2 -> ...
```

The invalid transition

```text
last state of run_001 -> first state of run_002
```

is never used when a `case_col` is supplied.

This is essential for parameter sweeps, SAM runs, and experiments. Different cases are separate trajectories, not one long physical transient.

## Where this is implemented

- `src/dmdc/data.py`: loading CSV/Parquet/NPZ and building trajectory objects.
- `src/dmdc/model.py`: DMD/DMDc fitting from snapshot matrices and trajectory lists.
- `src/dmdc/reduced.py`: POD-DMDc fitting from full-state trajectories.
- `src/dmdc/validation.py`: train/test evaluation using held-out cases.

## Common shape mistakes

The most common bug in ROM code is mixing conventions. This repo uses:

```text
X.shape == (n_states, n_snapshots)
U.shape == (n_inputs, n_snapshots)
```

If you start from a pandas dataframe, the raw values usually have shape:

```text
raw_state_values.shape == (n_snapshots, n_states)
```

The repo transposes before fitting.
