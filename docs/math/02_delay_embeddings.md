# Delay Embeddings and Loop Memory

Thermal-fluid loops often have transport delay. A temperature perturbation at an upstream thermocouple may not affect a downstream thermocouple until several samples later. A memoryless model

```math
x_{k+1} \approx A x_k + B u_k
```

may miss that effect.

Delay embedding augments the state with previous values:

```math
z_k = \begin{bmatrix}
x_k \\
x_{k-1} \\
x_{k-2} \\
\vdots \\
x_{k-d+1}
\end{bmatrix}.
```

Then the model learns

```math
z_{k+1} \approx A_z z_k + B_z u_k.
```

The original current-time variables are the `lag0` block of `z_k`; older samples appear as `lag1`, `lag2`, and so on.

## Why this helps

Delay embedding gives a linear model access to finite memory. This is especially useful when the underlying physics includes:

- advection around a loop,
- wall thermal inertia,
- sensor response lag,
- actuator delay,
- hidden states not directly measured.

## Cost of delay embedding

If the original state dimension is `n_x` and the number of delays is `d`, the embedded state dimension is

```math
n_z = d n_x.
```

This can improve accuracy but may worsen conditioning, require more snapshots, and increase risk of unstable rollouts. This is why the repo provides sweep tools for testing `n_delays = 1, 2, 4, ...` against held-out data.

## Where this is implemented

- `src/dmdc/delayed.py`: delay embedding construction.
- `src/dmdc/cli.py`: `--n-delays` in `fit` and sweep workflows.
- `src/dmdc/sweeps.py`: model selection over delay choices.

## Practical guidance

Use delay embedding when one-step errors are acceptable but rollout predictions lag, smear, or miss transported temperature waves. Start small, for example `n_delays = 2` or `3`, then validate on held-out cases.
