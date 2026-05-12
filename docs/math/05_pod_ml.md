# Optional POD-ML Modal Dynamics

POD-ML is optional in this repository. It does not replace POD, SVD, DMD, or DMDc. Instead, it learns dynamics only after the state has been projected into POD coordinates.

## Reduced-coordinate task

After POD projection,

```math
x_k \approx \bar x + \Phi_r a_k.
```

A POD-ML model learns either

```math
[a_k, u_k] \mapsto a_{k+1},
```

or, when no inputs are supplied,

```math
a_k \mapsto a_{k+1}.
```

The full state prediction is reconstructed by

```math
\hat x_k = \bar x + \Phi_r \hat a_k.
```

## Why ML is optional

DMDc is linear in the reduced coordinates. Some systems have nonlinear reduced-coordinate dynamics, especially across broad operating ranges. POD-ML gives an optional way to model that nonlinearity while preserving an SVD/POD basis.

This repo intentionally avoids replacing the basis with an autoencoder or other black-box encoder. That may be useful in future work, but it is a different modeling philosophy.

## Supported model types

The code supports scikit-learn style regressors:

- ridge regression,
- random forest,
- gradient boosting,
- multilayer perceptron.

If scikit-learn is not installed, POD-ML fails gracefully with an actionable message.

## Rollout caution

A regressor trained for one-step modal prediction may still drift during recursive rollout. This is why the repo evaluates both one-step and multi-step errors, and why comparison against DMDc and simple baselines is encouraged.

## Where this is implemented

- `src/dmdc/ml.py`: `PODDynamicsRegressor`.
- `src/dmdc/baselines.py`: comparison integration.
- `src/dmdc/sweeps.py`: optional POD-ML candidates in sweeps.
- `src/dmdc/cli.py`: `dmdc pod-ml`.
