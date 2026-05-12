# Analysis Menu

Use this page to decide what to run.

| Goal | Command | Notes |
|---|---|---|
| Check whether data is usable | `dmdc inspect-data` | Start here for every new dataset. |
| Handle adaptive/nonuniform time | `dmdc adaptive-fit` | Learns `dx/dt = A_c x + B_c u` using actual `dt_k`. |
| Fit ordinary DMD/DMDc | `dmdc fit` | Good for sample-to-sample or fixed-step data. |
| Fit POD basis | `dmdc pod` | SVD/POD modes and coefficients. |
| Fit reduced POD-DMDc | `dmdc pod-dmdc` | Main linear ROM workflow. |
| Optional nonlinear reduced model | `dmdc pod-ml` | ML acts only on POD coefficients. |
| Validate on unseen cases | `dmdc validate` | Reports train/test error and generalization gap. |
| Compare models | `dmdc compare` | Baselines, DMDc, adaptive DMDc, ridge DMDc, POD-DMDc, POD-ML. |
| Sweep rank/delay/model choices | `dmdc sweep` | Produces dashboards and best-model recommendation. |
| Select important sensors | `dmdc pod-sensors` | POD/Q-DEIM sparse sensing. |
| Generate report | `dmdc report` | Writes a LaTeX report from an output folder. |

## Suggested first three commands

```bash
dmdc inspect-data --config my_study.toml
dmdc compare --config my_study.toml
dmdc report --run outputs/my_study
```

## Suggested model list for nonuniform thermal-loop data

```toml
[compare]
models = ["persistence", "mean", "adaptive_dmdc", "ridge_dmdc", "pod_dmdc"]
```

`adaptive_dmdc` is often the most honest first physics-time linear model when
your solver or experiment uses changing time steps.


## Live streaming / online workflows

Use these commands when a local workstation is receiving loop data row-by-row.

```bash
# Phase 1: stream/replay/tail and clean logs
dmdc live-replay --config configs/templates/live_replay_csv.toml
dmdc live-run --config configs/templates/live_csv_tail.toml

# Phase 2: forecast from the newest clean measured state
dmdc live-replay-predict --config configs/templates/live_replay_predict.toml
dmdc live-run-predict --config configs/templates/live_csv_tail_predict.toml

# Phase 3: POD-Kalman full-state estimation from sparse measurements
dmdc live-replay-estimate --config configs/templates/live_replay_estimate.toml
dmdc live-run-estimate --config configs/templates/live_csv_tail_estimate.toml
```

Current live phase: stream abstraction, forecasting, and POD-Kalman state estimation.
Residual alerts, trust scores, dashboards, and guarded online adaptation should plug into this layer later.

Read: `docs/live/streaming_phase1.md`, `docs/live/forecasting_phase2.md`, and `docs/live/state_estimation_phase3.md`.

## Live online adaptation

Use this when a validated live ROM is consistently offset from measurements but you do not want to retrain the dynamics online.

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
dmdc live-dashboard --run-dir outputs/live_adaptation_replay
```

Read:

```text
docs/live/adaptation_phase6.md
docs/cheatsheets/bias_correction_cheatsheet.md
```
