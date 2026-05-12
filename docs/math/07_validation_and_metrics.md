# Validation, Unseen-Case Error, Residuals, and Metrics

A ROM is only useful if it predicts data that was not used to fit it. This repo therefore emphasizes held-out case validation.

## Train/test split by case

For multi-case data, the preferred split is

```text
train cases: run_001, run_002, run_003
test cases:  run_004, run_005
```

This measures whether the model generalizes across operating conditions. A random time-step split can be misleading because neighboring time samples are highly correlated.

## Rollout error

For a predicted trajectory `\hat X` and true trajectory `X`, the residual is

```math
R = X - \hat X.
```

The global RMSE is

```math
\mathrm{RMSE} = \sqrt{\frac{1}{n_x m} \sum_{i=1}^{n_x}\sum_{k=1}^{m} (x_{i,k} - \hat x_{i,k})^2 }.
```

Per-state RMSE is

```math
\mathrm{RMSE}_i = \sqrt{\frac{1}{m}\sum_{k=1}^{m} (x_{i,k} - \hat x_{i,k})^2 }.
```

Per-case RMSE is computed by applying the same formula to each trajectory independently.

## Generalization gap

The generalization gap is

```math
\Delta_{gen} = \mathrm{RMSE}_{test} - \mathrm{RMSE}_{train}.
```

The generalization ratio is

```math
\rho_{gen} = \frac{\mathrm{RMSE}_{test}}{\mathrm{RMSE}_{train}}.
```

Large gaps indicate overfitting, insufficient inputs, rank choices that do not generalize, or test cases outside the training envelope.

## Forecast horizon error

One-step error may be small while rollout predictions diverge. Forecast horizon error measures error after `h` recursive steps:

```math
e(h) = \|x_{k+h} - \hat x_{k+h}\|.
```

The repo computes horizon errors for user-selected horizons such as `1, 5, 10, 25, 50`.

## Where this is implemented

- `src/dmdc/metrics.py`: RMSE and related metrics.
- `src/dmdc/splits.py`: case-aware train/test splits.
- `src/dmdc/validation.py`: held-out validation, residuals, horizon metrics.
- `src/dmdc/cli.py`: `dmdc validate`.

## What to inspect first

- `validation_summary.json`
- `error_by_case.csv`
- `error_by_state.csv`
- `forecast_horizon_errors.csv`
- `residuals.csv`
