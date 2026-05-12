# Rank, Delay, and Model Sweeps

The `dmdc sweep` command is the recommended way to choose ROM settings without fooling yourself with training error.

## Why sweeps matter

DMD/DMDc/POD-DMDc models can look excellent in one-step prediction and still fail during rollout. They can also fit training cases well while generalizing poorly to unseen operating conditions. Sweeps make model selection explicit by comparing candidate configurations on held-out cases.

A sweep can vary:

- model family: `persistence`, `dmdc`, `pod_dmdc`, `pod_ml_ridge`, etc.
- POD rank
- DMDc rank
- number of delay blocks
- POD centering/scaling choices

## Basic command

```bash
dmdc sweep --config configs/example_rank_delay_sweep.toml
```

## Important outputs

```text
sweep_results.csv       all candidates
best_models.csv         top candidates by test rollout RMSE
rank_vs_error.pdf       visual rank comparison
delay_vs_error.pdf      visual delay comparison
stability_vs_error.pdf  spectral-radius/error comparison
runs/*/                 per-candidate metadata and case errors
```

## Suggested thermal-loop sweep

Start small:

```toml
[sweep]
models = ["persistence", "dmdc", "pod_dmdc"]
pod_ranks = [2, 4, 6, 0.999]
dmdc_ranks = ["full"]
n_delays = [1, 2, 4]
```

Then add POD-ML only after the linear ROMs are understood:

```toml
[sweep]
models = ["pod_dmdc", "pod_ml_ridge"]
```

## Interpreting the dashboard

Prefer candidates with low `test_rollout_rmse`, small `generalization_gap`, and reasonable `spectral_radius`. A slightly less accurate but stable low-rank model may be more useful than a high-rank model that is unstable.

## Delay-embedding caveat

When `n_delays > 1`, the model sees an embedded state:

```text
[x_k, x_{k-1}, ..., x_{k-d+1}]
```

The reported sweep error is over that embedded state. This is useful for comparing delay settings, but final physical plots should focus on the current-time `lag0` states.
