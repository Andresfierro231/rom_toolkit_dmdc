# Rank, Delay, and Model Sweeps

Sweeps automate model selection by trying multiple configurations and comparing held-out performance.

A sweep candidate may vary:

- model type: persistence, mean, DMDc, POD-DMDc, POD-ML,
- POD rank,
- DMDc rank,
- number of delays,
- centering/scaling choices.

## Objective

For each candidate, the repo fits on training cases and evaluates on test cases. The most important metric is usually held-out rollout error:

```math
\mathrm{RMSE}_{test, rollout}.
```

The sweep also records generalization gap,

```math
\mathrm{RMSE}_{test} - \mathrm{RMSE}_{train},
```

and stability indicators such as spectral radius.

## Why sweeps matter

Rank and delay choices are modeling decisions, not just numerical settings. A high rank can reduce training error but worsen test error. More delays can capture memory but increase dimension and instability risk. Sweeps make these tradeoffs visible.

## Where this is implemented

- `src/dmdc/sweeps.py`: sweep candidate execution and summary tables.
- `src/dmdc/dashboards.py`: CSV/Markdown/LaTeX dashboards.
- `src/dmdc/reports.py`: LaTeX report generation from sweep outputs.
- `src/dmdc/cli.py`: `dmdc sweep`.

## Recommended practice

Start with a small sweep:

```text
pod_ranks = [2, 4, 6, 0.999]
n_delays = [1, 2, 4]
models = [persistence, dmdc, pod_dmdc]
```

Then expand only after the basic results make sense.
