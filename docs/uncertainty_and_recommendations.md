# Uncertainty Estimates and Best-Model Recommendations

## Bootstrap uncertainty

The repo now reports simple bootstrap confidence intervals where case-level errors are available.  For example, `uncertainty_summary.csv` may contain a confidence interval for mean held-out RMSE across cases.

This is not a substitute for a full uncertainty quantification study, but it is much better than reporting only one number.

## Operating-condition summaries

For validation on unseen cases, the repo writes `operating_condition_summary.csv` when input/condition columns are available.  This tells you whether held-out cases are interpolation or extrapolation.

Example warning:

```text
Test operating condition 'q_heater' is outside the training range.
Treat this as extrapolation.
```

## Best-model recommendation

`compare` and `sweep` write:

```text
best_model_recommendation.json
best_model_recommendation.txt
```

The recommendation is deliberately transparent.  It generally:

1. removes failed candidates,
2. optionally removes unstable candidates,
3. chooses the remaining model with the lowest held-out rollout error.

The recommendation should guide review, not replace engineering judgment.  Always inspect stability, forecast-horizon error, operating-condition extrapolation, and residuals.
