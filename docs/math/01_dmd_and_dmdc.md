# DMD and DMDc

Dynamic Mode Decomposition with control, or DMDc, learns a discrete-time linear model

```math
x_{k+1} \approx A x_k + B u_k.
```

Here `A` describes autonomous state evolution and `B` describes how known inputs drive the state.

If no input vector is supplied, the method reduces to ordinary DMD:

```math
x_{k+1} \approx A x_k.
```

## DMDc least-squares problem

Given snapshot matrices `X`, `X'`, and `U`, DMDc solves

```math
X' \approx A X + B U.
```

Define the augmented matrix

```math
\Omega = \begin{bmatrix} X \\ U \end{bmatrix}.
```

Then the model can be written compactly as

```math
X' \approx G \Omega,
```

where

```math
G = \begin{bmatrix} A & B \end{bmatrix}.
```

The least-squares solution is

```math
G = X' \Omega^\dagger,
```

where `†` denotes the Moore-Penrose pseudoinverse.

## SVD-truncated pseudoinverse

The repository computes an SVD

```math
\Omega \approx W_r \Sigma_r V_r^T,
```

where `r` is the selected numerical rank. The truncated pseudoinverse is

```math
\Omega^\dagger \approx V_r \Sigma_r^{-1} W_r^T.
```

Therefore,

```math
G \approx X' V_r \Sigma_r^{-1} W_r^T.
```

The first `n_x` columns of `G` are `A`; the remaining columns are `B`.

## Why rank matters

Keeping every singular direction can overfit noisy data or produce unstable rollouts. Truncating the SVD discards weak directions associated with small singular values. In the CLI and config files, rank can be:

- `full`: keep all numerically available directions.
- an integer: keep exactly that many directions.
- a float in `(0, 1)`: keep enough singular directions to reach that cumulative energy level.

## DMD mode when no input is provided

If no `input_cols` are supplied, the model solves

```math
X' \approx A X.
```

This uses the same SVD pseudoinverse idea, but the augmented matrix is just `X`.

## Where this is implemented

- `src/dmdc/model.py`: `DMDcModel.fit`, `fit_trajectories`, `predict_one_step`, and `simulate`.
- `src/dmdc/diagnostics.py`: rollout and one-step diagnostics.
- `src/dmdc/plotting.py`: singular values, eigenvalues, and true-vs-predicted plots.

## Practical interpretation for loop data

If the state vector is

```math
x_k = [TP1, TP2, TP3, TP4, \dot m]^T,
```

then the learned `A` matrix encodes how each current measurement helps predict each future measurement. The entry `A[i, j]` is not automatically a causal physical law, but it is a useful linear influence measure after accounting for all included states and inputs.
