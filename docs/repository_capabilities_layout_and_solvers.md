# Repository Capabilities, Layout, and Solver Overview

This document is the durable system-level description of the `dmdc-analysis`
repository. It is intended for future paper writing, onboarding, and technical
handoff.

## 1. Scope

`dmdc-analysis` is a config-driven Python toolkit for reduced-order modeling,
live replay/monitoring, archive summarization, and report generation for
multicase time-series data.

The repository is designed to work with:

- experimental thermal-loop data
- solver-generated trajectories from external tools such as MOOSE, SAM-like
  workflows, OpenFOAM-derived tables, or other tabular exports
- archived live/replay runs that need reproducible post-processing

The repository is **advisory/read-only** with respect to physical systems. It
can ingest, inspect, estimate, forecast, monitor, summarize, visualize, and
report. It does **not** control hardware, retrain a live plant model in an
unbounded way, or replace safety systems.

## 2. System Architecture

The dominant workflow pattern is:

```text
central study/campaign config
        -> dmdc CLI command or dmdc campaign
        -> reproducible outputs under outputs/
        -> optional analysis checkpointing under analysis/
        -> optional collaborator share-out via to_box/
```

The repository is organized around five functional layers.

### 2.1 Data connection and conditioning

This layer ingests raw or external data into canonical CSV/Parquet tables,
checks time-step behavior and case quality, and optionally resamples to a fixed
time grid.

Main commands:

- `dmdc import-data`
- `dmdc inspect-data`
- `dmdc resample`
- `dmdc tamu-inventory`
- `dmdc tamu-validation-export`

### 2.2 Offline ROM analysis and selection

This layer trains reduced-order models, evaluates held-out rollout error,
measures stability/generalization, and recommends candidate models.

Main commands:

- `dmdc fit`
- `dmdc adaptive-fit`
- `dmdc pod`
- `dmdc pod-dmdc`
- `dmdc pod-ml`
- `dmdc validate`
- `dmdc compare`
- `dmdc sweep`
- `dmdc recommend`
- `dmdc report`

### 2.3 Live digital-twin workflow

This layer replays or tails incoming data, estimates state, forecasts ahead,
computes trust/alert metrics, applies bounded bias correction, and presents the
results in dashboard/report form.

Main commands:

- `dmdc live-replay`, `dmdc live-run`
- `dmdc live-replay-predict`, `dmdc live-run-predict`
- `dmdc live-replay-estimate`, `dmdc live-run-estimate`
- `dmdc live-replay-monitor`, `dmdc live-run-monitor`
- `dmdc live-replay-adapt`, `dmdc live-run-adapt`
- `dmdc live-dashboard`
- `dmdc live-operator-report`

### 2.4 Archive and long-horizon review

This layer stores live/replay outputs in structured archive form, produces human
context tables, builds summaries/quicklooks, and supports archive dashboarding.

Main commands:

- `dmdc archive-run`
- `dmdc archive-summarize`
- `dmdc archive-quicklook`
- `dmdc archive-search`
- `dmdc validate-archive-schema`
- `dmdc archive-context`
- `dmdc benchmark-archive`

### 2.5 Campaign orchestration and execution planning

This layer turns a study config into a reproducible multi-step workflow with
recorded commands, output locations, and next-step prompts.

Main commands:

- `dmdc campaign`
- `dmdc hpc-plan`
- `dmdc resources`
- `dmdc guide`

## 3. Repository Layout

The repository is CLI-first and config-driven. The main top-level directories
have distinct roles.

| Path | Role |
|---|---|
| `src/dmdc/` | Python package implementing the CLI, model families, live stack, archive logic, and utilities. |
| `configs/templates/` | Canonical templates for central study, campaign, importer, live, archive, and sweep configuration shapes. |
| `examples/real_data_onboarding/` | Main real-data onboarding example. Use this first when adapting the repo to a new dataset. |
| `studies/` | Named study packages with repo-local configs and helper scripts. Current notable studies include the JSALT2 external-analysis POC and TAMU onboarding paths. |
| `outputs/` | Reproducible run products. Campaign run directories, compare/sweep outputs, archive summaries, and generated reports live here. |
| `analysis/` | Durable checkpoints, manifests, campaign journals, and report-ready progress notes. |
| `docs/` | User docs, workflow maps, math notes, live/archive docs, and now this system-level overview. |
| `scripts/workflows/` | Thin wrapper scripts around stable repo workflows rather than bespoke analysis logic. |
| `tools/` | Small wrappers/utilities for study setup, Box share-out, and reporting helpers. |
| `to_box/` | Staging area for lightweight collaborator-facing artifacts that may be uploaded to the separate Box outputs folder. |
| `tests/` | Pytest suite covering core workflows, time handling, campaign behavior, TAMU intake/export, and related regressions. |

Related sibling repositories matter operationally but are not part of the
analysis package itself.

| Sibling repo/path | Role |
|---|---|
| `../tamu_box_loop_data/` | Pull-only raw-data mirror from Box. Analysis outputs should not be published from there. |
| `../physor2026_andrew/.../jsalt2_moose_mesh_convergence/outputs` | External JSALT2 source collection imported by the current POC study. |
| `../ethan_runs/` | Separate CFD/runtime recovery workspace. It can inform interpretation but is not the `dmdc` source package. |

## 4. Source Package Layout

The source package is intentionally modular rather than notebook-centric.

### 4.1 CLI and workflow entrypoints

- `cli.py`: central command-line interface and command routing
- `campaign.py`: config rebasing, campaign plans, step execution, and run index
- `command_catalog.py`: compact command guide used by `dmdc guide`
- `config.py`: config loading, flattening, defaults, and validation helpers
- `hpc_workflows.py`: planning-only HPC workflow generation
- `resources.py`: local/Slurm resource summary utilities

### 4.2 Offline ROM/math modules

- `model.py`: core DMDc model
- `regularized.py`: ridge/regularized DMDc
- `adaptive.py`: variable-time-step DMDc in physical time
- `continuous.py`: continuous-time generator utilities
- `pod.py`: POD/SVD basis fitting
- `reduced.py`: POD-DMDc pipeline
- `ml.py`: optional POD-space machine-learning dynamics
- `delayed.py`: delay embedding helpers
- `validation.py`: unseen-case evaluation
- `sweeps.py`: rank/delay/model sweeps
- `baselines.py`: persistence/mean and common fit adapter layer
- `stability.py`, `uncertainty.py`, `recommendations.py`: model selection support

### 4.3 Data and preprocessing modules

- `data.py`: canonical data loading
- `resampling.py`: inspection and fixed-dt resampling helpers
- `preprocessing.py`, `time_windows.py`, `splits.py`: supporting dataset transforms
- `import_workflow.py` and `importers/`: importer adapters for CSV/Excel/folder/LabVIEW/EPICS-like inputs
- `case_quality.py`, `operating_conditions.py`, `warnings.py`: dataset diagnostics
- `tamu_data.py`: TAMU inventory and validation-export helpers

### 4.4 Live/online modules

- `live.py`, `live_buffer.py`, `streaming.py`: ingestion/buffering
- `live_forecast.py`, `live_predictor.py`: forward prediction
- `kalman.py`, `live_estimation.py`: state estimation
- `live_monitoring.py`: residuals, trust, alerts, envelope checks
- `live_adaptation.py`: bounded additive bias correction and audit records
- `live_dashboard.py`, `live_operator_report.py`: human-facing live views

### 4.5 Archive/report/presentation modules

- `live_archive.py`: manifest-indexed archive writing
- `live_summaries.py`, `live_quicklooks.py`, `archive_search.py`, `archive_schema.py`: archive browsing and validation
- `dashboards.py`, `plotting.py`, `reports.py`: plots, dashboards, LaTeX report generation
- `loop_geometry.py`, `operator_schematic.py`, `graph.py`: geometry- or presentation-oriented helpers
- `provenance.py`, `utils.py`, `metrics.py`, `diagnostics.py`: shared utilities and bookkeeping

## 5. Solver and Model Families

The repository does **not** contain a CFD or thermal-hydraulics PDE solver.
Instead, it ingests trajectory data from external solvers/experiments and fits
reduced models or monitoring layers around those trajectories.

### 5.1 Baseline and linear ROM families

| Family | Repo name / command surface | Purpose | When to use | Main notes |
|---|---|---|---|---|
| Persistence baseline | `persistence` in `compare`/`sweep` | Predict no change from current state. | Always include for honest comparison. | Sanity lower bound. |
| Mean baseline | `mean` in `compare`/`sweep` | Predict training-set mean state. | Always include for honest comparison. | Useful against biased datasets. |
| DMD / DMDc | `fit`, `compare`, `sweep` with `dmdc` | Linear discrete-time state/input model. | Fixed-step or sample-to-sample workflows. | Becomes no-input DMD when `input_cols` is empty. |
| Ridge DMDc | `ridge_dmdc` | Tikhonov-regularized DMDc. | Noisy or collinear-input datasets. | Same discrete-time framing as DMDc. |
| Continuous DMDc | `continuous` | Approximate continuous generator from discrete fit. | When a continuous-time view is needed after a discrete fit. | Utility/analysis layer, not the default workflow. |
| Adaptive / variable-dt DMDc | `adaptive-fit`, `adaptive_dmdc` | Learn `dx/dt = A_c x + B_c u` using actual `dt_k`. | Nonuniform or adaptive time-step data. | Physical-time model; stability still must be checked. |

### 5.2 Reduced-order and nonlinear reduced families

| Family | Repo name / command surface | Purpose | When to use | Main notes |
|---|---|---|---|---|
| POD / SVD | `pod` | Compute low-rank basis and modal coefficients. | Basis inspection, compression, sensor design. | Not a forecast model by itself. |
| POD-DMDc | `pod-dmdc`, `pod_dmdc` | Project to POD space, then fit linear dynamics there. | Main reduced linear ROM path. | Current default winner on the JSALT2 delay-1 compare surface. |
| POD-ML | `pod-ml`, `pod_ml_*` | Learn POD-coefficient dynamics with ML in reduced space. | After linear ROM baselines are understood. | Optional extension, not first-line evidence. |
| Delay-embedded variants | `n_delays > 1` in `fit`/`sweep` | Use history-augmented state vectors. | When memory effects improve rollout/generalization. | Final physical interpretation should focus on lag-0 states. |

### 5.3 Estimation and sparse-sensing families

| Family | Command surface | Purpose | Notes |
|---|---|---|---|
| QR/POD sensor selection | `select-sensors`, `pod-sensors` | Rank candidate measurements and reconstruct state from sparse observations. | Bridges offline POD structure to deployable sensing layouts. |
| POD-Kalman estimation | live estimation stack | Estimate full state from sparse/partial live measurements. | Used in live Phases 3+. |

### 5.4 Live monitoring and adaptation layers

| Layer | Command surface | Purpose | Notes |
|---|---|---|---|
| Forecasting | `live-replay-predict`, `live-run-predict` | Roll saved ROMs forward from newest measurements. | Uses validated offline models. |
| Monitoring | `live-replay-monitor`, `live-run-monitor` | Residual alerts, trust score, operating-envelope checks. | Advisory only. |
| Bias correction / adaptation | `live-replay-adapt`, `live-run-adapt` | Add bounded additive forecast corrections. | Does not retrain the saved ROM online. |

## 6. Current JSALT2 POC Policy

The JSALT2 external-analysis study is a proof-of-concept for importing external
trajectory CSV collections into the `dmdc` workflow.

Current working policy for that study:

- keep both with-`h` and no-`h` variants in play
- treat the **broader tuned sweep surface** as the selection authority rather
  than the narrower default delay-1 compare surface
- continue to report the delay-1 compare result, but only as the baseline
  compare surface, not as the final tuned model-selection answer

At the time of writing:

- the default delay-1 compare-equivalent surface still selects `pod_dmdc`
- the broader stable tuned sweep surface can select delay-embedded `dmdc`
  instead

This is a policy choice about the authoritative search surface, not evidence
that the `compare` command is malfunctioning.

## 7. Provenance, Outputs, and Share-Out

The repository expects engineering provenance rather than notebook-only state.

Primary execution truth sources:

- `outputs/campaigns/<campaign_name>/campaign_plan.md`
- `outputs/campaigns/<campaign_name>/campaign_step_index.csv`
- `outputs/campaigns/<campaign_name>/next_steps.md`
- run-local `workflow_outputs/...` directories
- `analysis/reports/<checkpoint_id>/CHECKPOINT.md`
- `analysis/reports/<checkpoint_id>/MANIFEST.yaml`

Share-out model:

- raw-data Box folder -> mirrored into the sibling raw-data repo only
- analysis artifacts -> staged under `to_box/`
- collaborator-facing uploads -> separate Box outputs folder

The repository is explicit that `to_box/` uploads must **never** target the raw
TAMU data source folder.

## 8. What This Repository Is Not

To avoid overclaiming in papers or reports, the following boundaries matter.

This repository is not:

- a CFD solver
- a MOOSE/SAM/OpenFOAM runtime manager
- a hardware control system
- a safety system
- an online unconstrained retraining framework
- a substitute for case-aware validation on unseen operating conditions

It is best described as a reproducible ROM, live-monitoring, archive, and
reporting toolkit for multicase time-series data.

## 9. Recommended Citation Context

If this repository is described in a paper, the cleanest framing is:

1. external solvers/experiments generate trajectories
2. `dmdc-analysis` imports and standardizes those trajectories
3. the repository fits and compares reduced-order models
4. the repository supports replay/monitor/archive/report workflows around the
   selected reduced models
5. provenance and campaign artifacts make each study replayable

That framing is faithful to the codebase and avoids overstating the scope.
