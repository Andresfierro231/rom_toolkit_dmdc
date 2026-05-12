# Mathematical Background: DMDc

## 1. Problem statement

Suppose we observe a dynamical system at discrete times:

```math
x_0, x_1, \ldots, x_m,
```

where each state vector satisfies

```math
x_k \in \mathbb{R}^n.
```

Suppose we also know the input/control vector

```math
u_k \in \mathbb{R}^p.
```

DMDc assumes the data can be approximated by a linear controlled discrete-time model

```math
x_{k+1} \approx A x_k + B u_k.
```

This can be exact for a linear time-invariant discrete system, or approximate for a nonlinear system near a regime of interest.

## 2. Snapshot matrices

Define

```math
X = \begin{bmatrix} x_0 & x_1 & \cdots & x_{m-1} \end{bmatrix},
```

```math
X' = \begin{bmatrix} x_1 & x_2 & \cdots & x_m \end{bmatrix},
```

and

```math
U = \begin{bmatrix} u_0 & u_1 & \cdots & u_{m-1} \end{bmatrix}.
```

Then the model equation becomes

```math
X' \approx A X + B U.
```

Equivalently,

```math
X' \approx \begin{bmatrix} A & B \end{bmatrix}
\begin{bmatrix} X \\ U \end{bmatrix}.
```

Let

```math
\Omega = \begin{bmatrix} X \\ U \end{bmatrix}.
```

Then

```math
X' \approx G \Omega,
```

where

```math
G = \begin{bmatrix} A & B \end{bmatrix}.
```

## 3. Least-squares solution

The formal least-squares solution is

```math
G = X' \Omega^\dagger,
```

where \(\Omega^\dagger\) is the Moore-Penrose pseudoinverse.

If

```math
\Omega = U_\Omega \Sigma_\Omega V_\Omega^*,
```

then the truncated pseudoinverse is

```math
\Omega_r^\dagger = V_r \Sigma_r^{-1} U_r^*.
```

Thus

```math
G_r = X' V_r \Sigma_r^{-1} U_r^*.
```

The first `n` columns of `G_r` are `A`; the remaining `p` columns are `B`.

## 4. Rank truncation

Rank truncation is important because experimental and simulation data often contain noise, redundant sensors, and poorly conditioned directions. Keeping every singular direction can overfit noise.

Common choices:

- `rank="full"`: keep all singular values.
- `rank="auto"`: use numerical matrix rank.
- `rank=10`: keep 10 modes.
- `rank=0.999`: keep enough modes to capture 99.9% singular-value energy.

## 5. Stability interpretation

The eigenvalues of `A` describe the autonomous discrete-time dynamics. A simple stability indicator is the spectral radius

```math
\rho(A) = \max_i |\lambda_i(A)|.
```

For a discrete-time autonomous linear system, if

```math
\rho(A) < 1,
```

then the homogeneous dynamics decay asymptotically. With inputs, the state may still be driven by `B u_k`.

## 6. Important caveats

DMDc learns a sample-to-sample map. If the time step changes across data points, `A` is not a single fixed-time operator. You can still fit a map, but interpretation becomes weaker. For strongly nonuniform time data, use `dmdc adaptive-fit` for a physical-time continuous generator, or resample explicitly only when a fixed-step map is desired.

---

## Expanded math guide

For a more complete, workflow-by-workflow mathematical description of the current repository, see:

```text
docs/math_index.md
```

That guide now includes separate files for data matrix notation, DMD/DMDc, delay embeddings, POD/SVD, POD-DMDc, optional POD-ML, POD sparse sensing, validation metrics, stability diagnostics, sweeps, and irregular time-step handling.
