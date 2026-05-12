# POD-DMDc Reduced-Order Modeling

POD-DMDc combines POD projection with DMDc dynamics. It is useful when the full state dimension is large or when full-state DMDc is poorly conditioned.

## Projection

Start with the POD approximation

```math
x_k \approx \bar x + \Phi_r a_k.
```

The modal coefficients are

```math
a_k = \Phi_r^T (x_k - \bar x).
```

## Reduced dynamics

Instead of learning dynamics in full state space,

```math
x_{k+1} \approx A x_k + B u_k,
```

POD-DMDc learns dynamics in modal space:

```math
a_{k+1} \approx A_r a_k + B_r u_k.
```

If no input is supplied, it learns POD-DMD:

```math
a_{k+1} \approx A_r a_k.
```

## Reconstruction

After rolling out modal coefficients,

```math
\hat a_0, \hat a_1, \ldots, \hat a_m,
```

the full state is reconstructed as

```math
\hat x_k = \bar x + \Phi_r \hat a_k.
```

## Why this is useful

If the full system has `n_x = 500` states and the POD rank is `r = 10`, then the state transition matrix shrinks from

```math
A \in \mathbb{R}^{500 \times 500}
```

to

```math
A_r \in \mathbb{R}^{10 \times 10}.
```

This usually improves conditioning, makes eigenvalue analysis easier, and reduces overfitting risk.

## Where this is implemented

- `src/dmdc/reduced.py`: `PODDMDcPipeline`.
- `src/dmdc/validation.py`: held-out evaluation of POD-DMDc.
- `src/dmdc/sweeps.py`: rank/delay sweeps including POD-DMDc.
- `src/dmdc/cli.py`: `dmdc pod-dmdc`.

## Important validation principle

A low reconstruction error from POD does not guarantee good forecast performance. The reduced dynamics must still be validated by rollout on held-out cases. This repo therefore separates:

1. POD reconstruction error.
2. One-step prediction error.
3. Multi-step rollout error.
4. Unseen-case generalization error.
