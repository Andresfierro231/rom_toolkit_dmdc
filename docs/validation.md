# Validation on Unseen Cases

One-step training error is not enough for ROM work. A model can fit training trajectories well and still fail on an unseen operating condition.

This repo now supports case-aware validation for POD-DMDc workflows.

## Why case-aware validation matters

For simulation sweeps or experiments, each `case_id` usually represents one independent trajectory. You should avoid random row splitting because it can place nearly identical adjacent time samples in both train and test sets.

Instead, use:

```text
Train cases: run_001, run_002
Test cases:  run_003
```

This asks a more honest question:

> Can the ROM generalize to a trajectory it did not see during fitting?

## CLI usage

```bash
dmdc validate \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --train-cases run_001 run_002 \
  --test-cases run_003 \
  --pod-rank 0.999 \
  --dmdc-rank full \
  --forecast-horizons 1 2 5 \
  --outdir outputs/example_validation \
  --plots
```

## Config usage

```bash
dmdc validate --config configs/example_validate_unseen_cases.toml
```

## Metrics produced

The validation workflow saves:

```text
validation_summary.json
validation_summary.csv
error_by_case.csv
error_by_state.csv
forecast_horizon_errors.csv
residuals.csv
warnings.txt
```

If plots are enabled, it also saves:

```text
forecast_error_vs_horizon.pdf
error_by_case.pdf
true_vs_pred_first_test_case.pdf
```

## Generalization gap

The summary includes:

```text
generalization_gap_rmse = test_rollout_rmse - train_rollout_rmse
generalization_gap_ratio = test_rollout_rmse / train_rollout_rmse
```

A large generalization gap suggests the model is not transferring well to unseen conditions.

Possible causes:

- POD rank is too high or too low.
- Important input columns are missing.
- Test cases are outside the training parameter range.
- The model is unstable during rollout.
- State variables have incompatible scales.
- The data needs resampling or cleaning.

## Forecast horizon errors

The validation command also computes errors at specified horizons, such as 1, 5, 10, or 50 steps. This is important because a model can have small one-step error but drift or diverge during recursive rollout.
