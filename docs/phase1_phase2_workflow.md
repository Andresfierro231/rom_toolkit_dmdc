# Phase 1--2 Workflow

The first two ROM phases added to the repo are:

1. Data inspection, warnings, and resampling foundations.
2. POD basis extraction and POD diagnostics.

Recommended first workflow:

```bash
# 1. Inspect the raw table
dmdc inspect-data --config configs/example_inspect_data.toml

# 2. Resample only if inspection shows irregular dt and interpolation is appropriate
dmdc resample --config configs/example_resampling.toml

# 3. Fit a POD basis
dmdc pod --config configs/example_pod.toml
```

For SAM or experimental loop data, inspect first. Do not start by fitting a model until you know whether the data has missing values, duplicate times, large gaps, or wildly different variable scales.
