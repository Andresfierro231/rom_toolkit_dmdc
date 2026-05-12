# DMDc / ROM Analysis Toolkit

**Release status:** `v0.1.0-alpha`

A research-grade ROM and live monitoring toolkit for DMD/DMDc/POD workflows, with live replay, dashboarding, archive support, and model registry scaffolding. This alpha release is intended for research and development workflows and is **not yet field-validated on live hardware**.

The project is designed for simulation and experimental time-series data, especially thermal-hydraulic loop data, SAM-like outputs, reduced-order modeling studies, and local-workstation live monitoring demos. It is intentionally config-driven so a study can be reproduced from one central TOML file.

**Safety and scope:** this repo is read-only/advisory for live systems. It can ingest data, estimate state, forecast, warn, archive, and visualize. It does **not** control hardware, replace safety systems, or make autonomous safety decisions.

**Fastest path:** copy a study template, edit one TOML file, and run modular campaign steps.

```bash
cp -r examples/real_data_onboarding studies/my_loop_study
cd studies/my_loop_study

# Preview commands and output folders first.
dmdc campaign --config study_config.toml --dry-run

# Run only what you need.
dmdc campaign --config study_config.toml --steps import inspect compare
dmdc campaign --config study_config.toml --steps live_replay_adapt dashboard operator_report
```

**Command discovery:**

```bash
dmdc guide
```

**Read these first:**

```text
WORKFLOWS.md                         # one-command workflow recipes
COMMANDS.md                          # command index and when to use each command
examples/real_data_onboarding/README.md
docs/navigation/workflow_map.md
docs/navigation/choose_your_path.md
```

The repo is intentionally modular. You can run only import/inspection, only offline comparison, only live replay, only archive summaries, or only dashboard/report generation. The central config is the study contract; individual commands read only the sections they need.

## Release-readiness files

This repository includes the basic files needed before the first GitHub/internal alpha release:

```text
LICENSE           # MIT license
CITATION.cff      # citation metadata for research use
.gitignore        # excludes generated outputs, archives, private data, and large files
TODO_TESTING_AND_ROADMAP.md
```

Treat the current version as an alpha: feature-rich, heavily scaffolded, and tested with examples, but still requiring real SAM/experimental-loop validation before operational use.

---

## Start here with your current data

Most real SAM outputs and experimental loop logs have **nonuniform/adaptive time steps**. The repo now treats changing time step as the normal real-data case, not as an error.

The fastest safe workflow is:

```bash
# 1. Inspect columns, cases, missing values, failed/short cases, and dt behavior.
dmdc inspect-data --config my_study.toml

# 2. Compare honest baselines and ROMs on held-out cases.
# Include adaptive_dmdc when time steps are nonuniform.
dmdc compare --config my_study.toml

# 3. Sweep ranks/delays/models to find a stable model that generalizes.
dmdc sweep --config my_study.toml

# 4. Generate a LaTeX report from any output folder.
dmdc report --run outputs/my_study
```

For a hands-on guide to connecting your own data, read:

```text
examples/real_data_onboarding/README.md
docs/tutorials/real_data_onboarding.md
docs/start_here_connect_your_data.md
docs/analysis_menu.md
docs/cheatsheets/time_handling_cheatsheet.md
```


---

## Current-data import quick start

Use `dmdc import-data` when your current data starts as Excel, a messy CSV, a folder of LabVIEW/DAQ chunks, or an EPICS PV snapshot. The importer writes a canonical table that every downstream command can read.

```bash
# Single CSV/Excel/Parquet file
dmdc import-data \
  --source data/raw/current_loop_export.xlsx \
  --source-type excel \
  --sheet Sheet1 \
  --rename-col TC01=TP1 TC02=TP2 Heater_W=q_heater \
  --out data/processed/current_loop.parquet

# Folder of DAQ/LabVIEW CSV chunks
dmdc import-data \
  --source data/raw/labview_chunks \
  --source-type labview_daq \
  --pattern "*.csv" \
  --case-from-filename \
  --out data/processed/labview_cases.parquet

# Config-first import
dmdc import-data --config configs/templates/import_csv_excel_folder.toml
```

After import, inspect the canonical output:

```bash
dmdc inspect-data \
  --data data/processed/current_loop.parquet \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/inspection
```

Importer docs and templates:

```text
docs/importers/README.md
configs/templates/import_csv_excel_folder.toml
configs/templates/import_epics_snapshot.toml
configs/templates/central_study_config.toml
```

### Should everything be in one central config file?

For serious studies, **yes**. A central TOML config should be the study contract: source importer, canonical column names, units, train/test split, ROM settings, live streaming settings, archive settings, and dashboard settings. Commands only read the sections they need, so the same file can drive `import-data`, `inspect-data`, `compare`, `live-replay-adapt`, `archive-summarize`, and `live-dashboard`.

For quick debugging, CLI flags are still useful. For anything you will show to others, use the central config and keep it under version control.

Helpful navigation:

```text
docs/navigation/choose_your_path.md
TODO_TESTING_AND_ROADMAP.md
```

### Time-step policy

| Your data situation | Recommended action |
|---|---|
| Adaptive/nonuniform `dt` and physical-time dynamics matter | Use `dmdc adaptive-fit` or include `adaptive_dmdc` in `compare`/`sweep`. |
| You intentionally want a fixed-step discrete map | Run `dmdc resample` explicitly, then run `fit` / `pod-dmdc`. |
| You only care about sample-to-sample prediction | `fit` / `pod-dmdc` are valid, but interpret `A` as a sample-index map. |

`adaptive-fit` learns

```math
\frac{dx}{dt} \approx A_c x + B_c u
```

from the actual transition sizes \(\Delta t_k\), then rolls out using each requested future \(\Delta t_k\).


---

## Live streaming quick start

The repo now has five online-data layers for a local workstation connected to a loop.

```text
Live Phase 1: ingest/replay/tail rows, validate them, maintain a rolling buffer, and log clean data.
Live Phase 2: load a saved offline ROM and produce live forecasts from the newest clean state/input sample.
Live Phase 3: estimate the current full state with a POD-Kalman filter, including sparse sensors.
Live Phase 4: monitor forecast residuals, innovations, operating envelope, uncertainty, alerts, and trust score.
Live Phase 5: launch a polished Streamlit dashboard for interactive live visualization.
Live Phase 6.1: apply bounded, auditable forecast-bias correction without modifying the saved ROM.
Live Phase 6.2: archive run outputs into partitioned CSV/Parquet storage with a manifest.
Live Phase 6.3: create compact summaries and quicklook plots for long-term archive browsing.
```

The live system still does **not** retrain online, control hardware, or replace safety systems. It is an advisory digital-twin monitor that reads data, estimates state, forecasts, logs, alerts, visualizes, records bias correction, and archives long-term data.

### Ingestion-only replay

Recommended first test: replay an existing CSV as if it were live.

```bash
dmdc live-replay \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --case-col case_id \
  --case-id salt_test_1 \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --chunk-size 5 \
  --max-samples 50 \
  --outdir outputs/live_replay_demo
```

### Forecasting replay with a saved model

Train a model offline first, for example:

```bash
dmdc adaptive-fit --config configs/templates/adaptive_variable_dt_dmdc.toml
```

Then replay a stream and forecast from the latest clean sample:

```bash
dmdc live-replay-predict \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --model outputs/adaptive_fit/adaptive_model.pkl \
  --case-col case_id \
  --case-id salt_test_1 \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --forecast-horizons-seconds 5 10 30 60 \
  --max-samples 50 \
  --outdir outputs/live_replay_prediction_demo
```

### POD-Kalman state estimation replay

Train a POD-DMDc model offline first:

```bash
dmdc pod-dmdc --config configs/templates/pod_dmdc_validation.toml
```

Then replay a stream with only the measured sensors and reconstruct the full state:

```bash
dmdc live-replay-estimate \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --model outputs/pod_dmdc/pod_dmdc_model.pkl \
  --case-col case_id \
  --case-id salt_test_1 \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --measurement-cols TP1 TP3 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --forecast-horizons-seconds 5 10 30 \
  --discrete-dt-seconds 0.5 \
  --max-samples 50 \
  --outdir outputs/live_replay_estimate_demo
```

For a real logger that appends to a CSV file:

```bash
dmdc live-run-estimate \
  --data live_data/current_loop_log.csv \
  --model outputs/pod_dmdc/pod_dmdc_model.pkl \
  --time-col time \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --measurement-cols TP1 TP3 TP6 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --poll-seconds 0.5 \
  --buffer-seconds 300 \
  --forecast-horizons-seconds 5 10 30 \
  --discrete-dt-seconds 0.5 \
  --outdir outputs/live_run_estimate
```

### Streamlit dashboard for demos and live monitoring

Install optional dashboard dependencies:

```bash
python -m pip install -e '.[dashboard]'
```

Create monitoring outputs first:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml --save-every-batch
```

Then open the interactive dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --view operator
```

For a real live CSV logger, use:

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml --save-every-batch
dmdc live-dashboard --run-dir outputs/live_monitoring --view operator
```

The dashboard includes operator-friendly panels for current status, measured vs estimated state history, forecasts, residuals, alerts, trust score, Kalman innovations, covariance, and raw tables. For CI or a no-browser smoke test:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --write-summary-only
```

Read next:

```text
docs/live/dashboard_phase5.md
docs/cheatsheets/live_dashboard_cheatsheet.md
```

State-estimation outputs include:

```text
raw_stream_log.csv              # every row observed by the stream adapter
cleaned_stream_log.csv          # rows with valid required measurement/input/time values
live_state_estimates.csv        # filtered full-state estimates
live_modal_estimates.csv        # filtered POD modal coefficients
live_estimate_covariance.csv    # modal covariance trace/diagonal
live_kalman_innovations.csv     # measurement minus predicted-measurement innovations
live_forecasts.csv              # optional forecasts from filtered state
live_forecasts_wide.csv         # one row per origin/horizon, one column per state
live_warnings.csv               # structured warning table
warnings.txt                    # human-readable warning explanations
live_estimation_summary.json    # run-level state-estimation summary
provenance.json                 # version, command, config, platform, timestamp
```

Use these docs first:

```text
docs/live/streaming_phase1.md
docs/live/forecasting_phase2.md
docs/live/state_estimation_phase3.md
docs/cheatsheets/live_streaming_cheatsheet.md
configs/templates/live_replay_csv.toml
configs/templates/live_csv_tail.toml
configs/templates/live_replay_predict.toml
configs/templates/live_csv_tail_predict.toml
configs/templates/live_replay_estimate.toml
configs/templates/live_csv_tail_estimate.toml
```

Live timestamps are expected to be nonuniform/adaptive. Use an `AdaptiveDMDcModel` when physical forecast horizons matter. POD-Kalman Phase 3 currently uses a saved discrete POD-DMDc model for modal state estimation; set `--discrete-dt-seconds` or `[forecast].discrete_dt_seconds` when producing physical-time forecasts from that model.

---

## 1. What this repo does

Given time-series data, the repo can learn models such as

```math
x_{k+1} \approx A x_k
```

for ordinary DMD, or

```math
x_{k+1} \approx A x_k + B u_k
```

for DMDc, where:

- `x_k` is the state vector at time/sample `k`, for example temperatures, pressures, wall temperatures, or mass flow rate.
- `u_k` is the optional input/control vector, for example heater power, inlet temperature, ambient temperature, pump speed, or boundary-condition values.
- `A` describes state-to-state dynamics.
- `B` describes how known inputs drive the state.

It also supports reduced-coordinate workflows:

```math
x_k \approx \bar{x} + \Phi_r a_k,
```

where `Phi_r` is a POD/SVD basis and `a_k` is a vector of modal coefficients.

The repo can:

- Load CSV, Parquet, and NPZ time-series data.
- Inspect data quality before modeling.
- Detect missing values, duplicate times, non-monotone times, irregular time steps, and large gaps.
- Resample data explicitly when desired.
- Fit DMD when no inputs are available.
- Fit DMDc when inputs/control signals are available.
- Fit adaptive/variable-time-step DMDc when physical time steps are nonuniform.
- Fit multiple independent cases without creating fake transitions across case boundaries.
- Use delay embeddings for transport memory.
- Fit POD bases using SVD.
- Fit POD-DMDc reduced-order models.
- Fit optional POD-ML modal-coefficient dynamics.
- Select important sensors/states using QR/Q-DEIM-style methods.
- Reconstruct the full state from selected POD sensors.
- Validate on unseen cases.
- Compute train/test generalization gaps.
- Compute forecast-horizon errors.
- Compare against baseline models.
- Analyze stability using eigenvalues and spectral radius.
- Run rank, delay, POD-rank, and model sweeps.
- Generate CSV, Markdown, and LaTeX dashboards.
- Generate robust LaTeX reports.
- Replay historical CSV data as a live stream.
- Tail an append-only CSV logger into a rolling live buffer for future online ROM forecasting/state estimation.

---

## 2. What this repo does not do

This is not an ML-first black-box framework.

The core modeling philosophy is:

1. Use transparent linear algebra first.
2. Use SVD/POD for basis construction.
3. Use DMD/DMDc/POD-DMDc for interpretable dynamics.
4. Use ML only as an optional reduced-coordinate layer.
5. Validate every model on unseen cases when possible.

POD-ML does **not** replace SVD/POD. It learns dynamics only after projection into POD coordinates:

```math
[a_k, u_k] \mapsto a_{k+1}.
```

---

## Known limitations and current boundaries

This repo is intentionally honest about what is and is not validated yet.

- **Not field-validated on live hardware yet.** Live streaming, dashboarding, bias correction, and archive tooling are implemented, but they still need testing with real loop instrumentation and actual operating procedures.
- **Read-only/advisory only.** The live tools do not actuate heaters, pumps, valves, or safety systems. Future advisory/control concepts are documented separately and should remain independent of hardware control until validated.
- **EPICS and LabVIEW/DAQ adapters are scaffolded.** CSV/Excel/folder workflows are usable now; EPICS/LabVIEW connectors need field testing with real PV names, timestamps, and logger behavior.
- **Large-data performance needs target-machine benchmarking.** Archive and summary tools are designed for large data, but true throughput and memory behavior must be measured on the workstation/HPC system that will run them.
- **Continuous-time DMDc is interpretive.** For nonuniform/adaptive time steps, `adaptive_dmdc` is preferred. Continuous-time matrices estimated from discrete data should be interpreted carefully and validated with rollouts.
- **Model recommendations are decision support.** The best-model tools rank models using configured metrics, but the user still needs engineering judgment, validation plots, stability checks, and operating-envelope checks.
- **No private/raw data should be committed.** Keep raw data, archives, model registries, and generated outputs outside Git or under ignored paths.

For more detail, see `docs/known_limitations.md` and `docs/future/advisory_control_mode.md`.

## 3. Installation

From inside the repository:

```bash
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e '.[dev]'
```

For Parquet support:

```bash
python -m pip install -e '.[parquet]'
```

For optional POD-ML support:

```bash
python -m pip install -e '.[ml]'
```

For everything:

```bash
python -m pip install -e '.[dev,parquet,ml]'
```

Run the test suite:

```bash
PYTHONPATH=src pytest -q
```

Expected result for this version:

```text
62 passed
```

---

## 4. Repository structure

```text
dmdc-analysis/
├── README.md
├── pyproject.toml
├── src/
│   └── dmdc/
│       ├── model.py             # DMD / DMDc core model
│       ├── adaptive.py          # variable-time-step continuous-generator DMDc
│       ├── regularized.py       # ridge/Tikhonov DMDc
│       ├── continuous.py        # fixed-dt discrete-to-continuous conversion
│       ├── data.py              # CSV/Parquet/NPZ loading and case-aware trajectory construction
│       ├── resampling.py        # data inspection and explicit time resampling
│       ├── case_quality.py      # failed/short-case and final-time summaries
│       ├── time_windows.py      # transient/steady-state time-window filtering
│       ├── operating_conditions.py # train/test operating-condition range checks
│       ├── warnings.py          # friendly, actionable warning records
│       ├── delayed.py           # delay-coordinate embeddings
│       ├── pod.py               # POD/SVD basis extraction and reconstruction
│       ├── reduced.py           # POD-DMDc reduced-order pipeline
│       ├── ml.py                # optional POD-ML modal dynamics
│       ├── kalman.py            # POD-space Kalman/state-estimation utilities
│       ├── loop_geometry.py     # optional physical loop position metadata and plots
│       ├── sensor_selection.py  # generic SVD + QR sensor/state ranking
│       ├── pod_sensors.py       # POD sparse sensing and reconstruction
│       ├── splits.py            # case-aware train/test splitting
│       ├── metrics.py           # RMSE, relative errors, state/case metrics
│       ├── uncertainty.py       # bootstrap uncertainty summaries
│       ├── recommendations.py   # best-model recommendation logic
│       ├── validation.py        # unseen-case validation and forecast-horizon errors
│       ├── stability.py         # eigenvalues, spectral radius, stability warnings
│       ├── baselines.py         # persistence, mean, adaptive, DMDc, POD-DMDc, POD-ML helpers
│       ├── sweeps.py            # rank/delay/model sweeps
│       ├── dashboards.py        # CSV/Markdown/LaTeX dashboard tables
│       ├── reports.py           # LaTeX report generation
│       ├── provenance.py        # version/config/command tracking in output folders
│       ├── streaming.py         # CSV replay/tail stream adapters for online workflows
│       ├── live_buffer.py       # rolling live-data buffer with warnings and dt summaries
│       ├── live.py              # high-level live ingestion/replay workflow
│       ├── live_predictor.py    # saved-model live forecast wrapper
│       ├── live_forecast.py     # live replay/tail prediction orchestration
│       ├── thermal_loop_example.py # synthetic tutorial dataset generator
│       ├── plotting.py          # matplotlib figures
│       ├── config.py            # TOML/JSON/YAML config support
│       └── cli.py               # command-line interface
├── configs/                     # runnable example TOML configs
├── data/                        # small example datasets
├── docs/                        # user docs
│   ├── math_index.md            # entry point for all math docs
│   └── math/                    # detailed math descriptions by workflow
├── examples/                    # Python API examples
└── tests/                       # pytest suite
```

---

## 5. Decision guide

Use this table to choose a workflow.

| Situation | Recommended workflow |
|---|---|
| No known forcing/input signal | DMD |
| Known inputs or boundary conditions, fixed/sample-step map | DMDc |
| Nonuniform/adaptive time steps with physical-time dynamics | Adaptive DMDc (`adaptive-fit`) |
| Many independent cases or parameter sweeps | Multi-trajectory DMDc/POD-DMDc with `--case-col` |
| Transport delay, thermal lag, or hidden memory | Delay-DMDc / delay POD-DMDc |
| Many state variables or full fields | POD |
| Need reduced linear dynamics | POD-DMDc |
| Linear reduced dynamics are insufficient | Optional POD-ML |
| Need to identify important sensors | QR/Q-DEIM sensor selection |
| Need to reconstruct full state from a few sensors | POD sparse sensing |
| Need honest predictive validation | `validate` on held-out cases |
| Need to choose rank/delay/model | `sweep` |
| Need meeting-ready output | dashboards and LaTeX report |

---

## 6. Mathematical guide

The math documentation is intentionally separated from the README so the repository is easier to audit.

Start here:

```text
docs/math_index.md
```

Detailed files:

```text
docs/math/00_data_matrices_and_notation.md
docs/math/01_dmd_and_dmdc.md
docs/math/02_delay_embeddings.md
docs/math/03_pod_and_svd.md
docs/math/04_pod_dmdc.md
docs/math/05_pod_ml.md
docs/math/06_sparse_sensing.md
docs/math/07_validation_and_metrics.md
docs/math/08_stability.md
docs/math/09_sweeps.md
docs/math/10_irregular_time_and_resampling.md
docs/math/11_regularized_and_continuous_dmdc.md
docs/math/12_kalman_filtering.md
docs/math/13_adaptive_variable_dt_dmdc.md
```

These files describe matrix shapes, SVD truncation, POD projection, POD-DMDc dynamics, optional POD-ML, sparse sensing, validation metrics, stability diagnostics, sweeps, and irregular time-step assumptions.

---

## 7. Data format

A single-case CSV can look like this:

```csv
time,TP1,TP2,TP3,massFlowRate,q_heater,T_amb
0.0,450.0,449.5,449.0,0.18,37.0,300.0
1.0,451.0,450.1,449.3,0.18,37.0,300.0
2.0,452.0,451.0,450.2,0.18,37.0,300.0
```

A multi-case CSV should include a case column:

```csv
case_id,time,TP1,TP2,TP3,massFlowRate,q_heater,T_amb
run_001,0.0,450.0,449.5,449.0,0.18,37.0,300.0
run_001,1.0,451.0,450.1,449.3,0.18,37.0,300.0
run_002,0.0,460.0,459.5,459.0,0.20,45.0,300.0
run_002,1.0,461.0,460.2,459.4,0.20,45.0,300.0
```

Important rules:

- State columns are predicted quantities.
- Input columns are known controls, forcings, or boundary conditions.
- `case_id` separates independent trajectories.
- The repo never forms transitions across different `case_id` values.
- Time should be monotone within each case. It does **not** have to be uniform; nonuniform/adaptive time steps are expected for many real datasets.

---

## 8. Inspect data before modeling

Run inspection before fitting any ROM:

```bash
dmdc inspect-data \
  --data data/example_multicase_timeseries.csv \
  --time-col time \
  --case-col case_id \
  --state-cols x1 x2 \
  --input-cols u1 \
  --outdir outputs/inspection
```

Config-driven version:

```bash
dmdc inspect-data --config configs/example_inspect_data.toml
```

Outputs:

```text
inspection_summary.json
columns_summary.csv
missing_values.csv
dt_summary_by_case.csv
case_lengths.csv
state_variance.csv
input_variance.csv
large_time_gaps.csv
warnings.txt
inspection_report.tex
```

Read `warnings.txt` first. It is designed to be actionable rather than cryptic.

---

## 9. Explicit resampling

DMD/DMDc learns a discrete-time map. If time steps are irregular, inspect the data first. Prefer `adaptive-fit` when physical time matters; resample only when you intentionally choose a fixed time grid and interpolation is physically defensible.

```bash
dmdc resample \
  --data data/example_multicase_timeseries.csv \
  --time-col time \
  --case-col case_id \
  --columns x1 x2 u1 \
  --dt 0.1 \
  --out outputs/resampled_data.csv
```

Config version:

```bash
dmdc resample --config configs/example_resampling.toml
```

The repo does not silently resample.

---

## 10. DMD / DMDc quick start

Single trajectory with inputs:

```bash
dmdc fit \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --input-cols u1 \
  --time-col time \
  --rank full \
  --outdir outputs/example_fit \
  --plots
```

No input columns means ordinary DMD:

```bash
dmdc fit \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --time-col time \
  --rank full \
  --outdir outputs/example_dmd \
  --plots
```

Multi-case DMDc:

```bash
dmdc fit \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --state-cols x1 x2 \
  --input-cols u1 \
  --time-col time \
  --rank full \
  --outdir outputs/example_multicase_fit \
  --plots
```

Config-driven DMDc:

```bash
dmdc fit --config configs/example_fit.toml
```

---

## 11. Delay-DMDc

Use delays when transport memory matters:

```bash
dmdc fit \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --input-cols u1 \
  --time-col time \
  --n-delays 3 \
  --rank 0.999 \
  --outdir outputs/example_delay_fit \
  --plots
```

Delay embedding creates columns such as:

```text
x1__lag0, x2__lag0, x1__lag1, x2__lag1, ...
```

Interpret `lag0` as the current-time state and later lags as memory coordinates.

---

## 12. POD quick start

Fit a POD/SVD reduced basis:

```bash
dmdc pod \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --time-col time \
  --rank 0.999 \
  --center \
  --outdir outputs/example_pod \
  --plots
```

Config version:

```bash
dmdc pod --config configs/example_pod.toml
```

Outputs:

```text
pod_basis.pkl
pod_summary.json
pod_coefficients.csv
pod_reconstruction.csv
pod_reconstruction_error.csv
reconstruction_error_vs_rank.csv
singular_values.pdf
cumulative_energy.pdf
reconstruction_error_vs_rank.pdf
coefficient_timeseries.pdf
```

Python API:

```python
from dmdc import PODBasis

pod = PODBasis(rank=0.999, center=True, scale=False)
pod.fit(X, state_names=["TP1", "TP2", "massFlowRate"])
A_modal = pod.transform(X)
X_reconstructed = pod.inverse_transform(A_modal)
```

---

## 13. POD-DMDc quick start

POD-DMDc fits DMDc in POD coefficient space:

```math
a_{k+1} \approx A_r a_k + B_r u_k.
```

CLI:

```bash
dmdc pod-dmdc \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --pod-rank 0.999 \
  --dmdc-rank full \
  --outdir outputs/example_pod_dmdc \
  --plots
```

Config:

```bash
dmdc pod-dmdc --config configs/example_pod_dmdc.toml
```

Outputs:

```text
pod_dmdc_model.pkl
pod_dmdc_summary.json
diagnostics.json
modal_coefficients.csv
reconstructed_rollout_predictions.csv
error_by_case.csv
error_by_state.csv
singular_values.pdf
cumulative_energy.pdf
eigenvalues_reduced_A.pdf
true_vs_reconstructed_first_case.pdf
```

---

## 14. Optional POD-ML quick start

Install optional ML dependencies:

```bash
python -m pip install -e '.[ml]'
```

Fit a POD-ML model:

```bash
dmdc pod-ml \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --pod-rank 0.999 \
  --model-type ridge \
  --center \
  --outdir outputs/example_pod_ml \
  --plots
```

Config:

```bash
dmdc pod-ml --config configs/example_pod_ml.toml
```

Supported model types:

```text
ridge
random_forest
gradient_boosting
mlp
```

POD-ML learns modal dynamics:

```math
[a_k, u_k] \mapsto a_{k+1}.
```

It does not replace the POD basis.

---

## 15. POD sparse sensing

Use POD sparse sensing to select informative state/sensor locations and reconstruct the full state from only those measurements.

```bash
dmdc pod-sensors \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --rank full \
  --n-sensors 2 \
  --center \
  --outdir outputs/example_pod_sensors \
  --plots
```

Config:

```bash
dmdc pod-sensors --config configs/example_pod_sensors.toml
```

Outputs:

```text
pod_basis.pkl
pod_summary.json
pod_sensor_summary.json
selected_sensors.csv
selected_sensors.txt
sparse_sensor_measurements.csv
sparse_sensor_coefficients.csv
sparse_sensor_reconstruction.csv
sparse_sensor_reconstruction_error.csv
reconstruction_error_vs_sensors.csv
reconstruction_error_vs_sensors.pdf
```

---

## 16. Validate on unseen cases

Validation should be case-aware when possible.

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

Config:

```bash
dmdc validate --config configs/example_validate_unseen_cases.toml
```

Outputs:

```text
validation_summary.json
validation_summary.csv
error_by_case.csv
error_by_state.csv
forecast_horizon_errors.csv
residuals.csv
warnings.txt
forecast_error_vs_horizon.pdf
error_by_case.pdf
true_vs_pred_first_test_case.pdf
```

Important metrics:

```text
train_rollout_rmse
test_rollout_rmse
generalization_gap_rmse
generalization_gap_ratio
```

---

## 17. Compare models and baselines

Compare ROMs against simple baselines:

```bash
dmdc compare \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --train-cases run_001 run_002 \
  --test-cases run_003 \
  --models persistence mean dmdc pod_dmdc pod_ml_ridge \
  --outdir outputs/model_comparison \
  --plots \
  --report
```

Config:

```bash
dmdc compare --config configs/example_compare_with_pod_ml.toml
```

Outputs:

```text
model_comparison.csv
model_comparison.md
model_comparison.tex
error_by_case.csv
error_by_state.csv
stability_dashboard.csv
comparison_summary.json
stability_summary.json
stability_warnings.txt
model_comparison.pdf
eigenvalues.csv
eigenvalues_complex_plane.pdf
report/report.tex
```

---

## 18. Stability diagnostics

For linear models, the repo computes eigenvalues and spectral radius:

```math
\rho(A) = \max_i |\lambda_i(A)|.
```

Interpretation for discrete-time models:

```text
rho(A) < 1      usually stable
rho(A) ≈ 1      marginal / slow growth or decay
rho(A) > 1      potentially unstable rollout
```

The repo saves stability warnings instead of silently modifying models. Optional stabilization should be explicit and documented if added later.

---

## 19. Rank / delay / model sweeps

Run a sweep to choose model type, POD rank, DMDc rank, and delay length:

```bash
dmdc sweep \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --train-cases run_001 run_002 \
  --test-cases run_003 \
  --models persistence dmdc pod_dmdc pod_ml_ridge \
  --pod-ranks full 0.999 \
  --dmdc-ranks full \
  --n-delays 1 2 \
  --center \
  --outdir outputs/example_rank_delay_sweep \
  --plots \
  --report
```

Config:

```bash
dmdc sweep --config configs/example_rank_delay_sweep.toml
```

Outputs:

```text
sweep_results.csv
sweep_results.md
sweep_results.tex
best_models.csv
best_models.md
best_models.tex
sweep_summary.json
rank_vs_error.pdf
delay_vs_error.pdf
stability_vs_error.pdf
runs/<candidate>/candidate_summary.json
report/report.tex
```

---

## 20. LaTeX reports

Generate a report from an existing run directory:

```bash
dmdc report --run outputs/model_comparison
```

Attempt PDF compilation if LaTeX is available:

```bash
dmdc report --run outputs/model_comparison --compile-pdf
```

The report generator is intentionally robust. If optional artifacts are missing, it skips those sections and still writes `report.tex`.

---

## 21. Config-first workflow

Every major command supports TOML configs. This is the recommended workflow for repeatable research.

Example:

```toml
[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[pod]
rank = 0.999
center = true
scale = false

[model]
type = "pod_dmdc"
dmdc_rank = "full"

[split]
strategy = "explicit_case_lists"
train_cases = ["run_001", "run_002"]
test_cases = ["run_003"]

[validation]
forecast_horizons = [1, 2, 5]

[output]
outdir = "outputs/my_study"
plots = true
```

Useful configs included:

```text
configs/example_fit.toml
configs/example_inspect_data.toml
configs/example_resampling.toml
configs/example_pod.toml
configs/example_pod_dmdc.toml
configs/example_pod_ml.toml
configs/example_pod_sensors.toml
configs/example_validate_unseen_cases.toml
configs/example_compare_models.toml
configs/example_compare_with_pod_ml.toml
configs/example_rank_delay_sweep.toml
configs/example_latex_report.toml
```

---

## 22. Python API examples

DMDc:

```python
from dmdc import DMDcModel

model = DMDcModel(rank="full", center=False, scale=False)
model.fit(X, U, state_names=["TP1", "TP2"], input_names=["q_heater"])
X_pred = model.simulate(X[0], U_future=U_future)
```

POD:

```python
from dmdc import PODBasis

pod = PODBasis(rank=0.999, center=True)
pod.fit(X, state_names=["TP1", "TP2", "massFlowRate"])
coeffs = pod.transform(X)
X_hat = pod.inverse_transform(coeffs)
```

POD-DMDc:

```python
from dmdc import PODDMDcPipeline

rom = PODDMDcPipeline(pod_rank=0.999, dmdc_rank="full", center=True)
rom.fit_trajectories(X_cases, U_cases, state_names=state_names, input_names=input_names)
X_rollout = rom.rollout(X_cases[0][0], U_future=U_cases[0][:-1])
```

POD sparse sensing:

```python
from dmdc import PODBasis, select_pod_sensors, reconstruct_from_sensors

pod = PODBasis(rank=0.999, center=True).fit(X, state_names=state_names)
selection = select_pod_sensors(pod, n_sensors=6)
X_recon = reconstruct_from_sensors(X[:, selection.selected_indices], pod, selection.selected_indices)
```

---

## 23. Thermal-hydraulic loop recommendations

A good workflow for SAM or experimental loop data:

1. Create a clean table with `case_id`, `time`, state columns, and input columns.
2. Run `inspect-data`.
3. Decide whether resampling is justified.
4. Fit a simple DMD/DMDc baseline.
5. Fit POD and inspect cumulative energy.
6. Fit POD-DMDc.
7. Validate on unseen cases.
8. Compare against persistence and mean baselines.
9. Run a rank/delay sweep.
10. Use POD sparse sensing to identify informative sensor locations.
11. Generate dashboards and a LaTeX report.

Suggested state groups:

```toml
[state_groups]
fluid_temperatures = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6"]
wall_temperatures = ["TW1", "TW2", "TW3", "TW4"]
flow = ["massFlowRate"]
pressure = ["P1", "P2"]
```

Suggested input columns:

```text
q_heater
T_inlet
T_amb
h_amb
pump_speed
inlet_mass_flow
insulation_thickness
```

---

## 24. Common mistakes

### Mistake 1: Treating many cases as one long transient

Use `--case-col`. The repo will then avoid fake transitions across case boundaries.

### Mistake 2: Judging only one-step error

Always check rollout error and forecast-horizon error.

### Mistake 3: Choosing rank only by training error

Use held-out cases and sweeps. High rank can overfit.

### Mistake 4: Ignoring irregular time steps

Run `inspect-data`. Resample explicitly if needed.

### Mistake 5: Interpreting ML as the core model

POD-ML is optional. The core repo is SVD/POD/DMD/DMDc.

### Mistake 6: Ignoring state scaling

Temperature, pressure, and flow variables may have different magnitudes. Decide deliberately whether to scale.

---

## 25. Development commands

Run tests:

```bash
PYTHONPATH=src pytest -q
```

Run key smoke workflows:

```bash
PYTHONPATH=src python -m dmdc.cli inspect-data --config configs/example_inspect_data.toml
PYTHONPATH=src python -m dmdc.cli pod --config configs/example_pod.toml
PYTHONPATH=src python -m dmdc.cli pod-dmdc --config configs/example_pod_dmdc.toml
PYTHONPATH=src python -m dmdc.cli validate --config configs/example_validate_unseen_cases.toml
PYTHONPATH=src python -m dmdc.cli compare --config configs/example_compare_with_pod_ml.toml
PYTHONPATH=src python -m dmdc.cli sweep --config configs/example_rank_delay_sweep.toml
PYTHONPATH=src python -m dmdc.cli pod-sensors --config configs/example_pod_sensors.toml
```

---

## 26. Current caveats

- Delay-DMDc outputs embedded-state columns; use `lag0` columns for current-time interpretation.
- POD-ML is optional but currently included in several example workflows. Install `.[ml]` to run those examples in a fresh environment.
- LaTeX report PDF compilation requires a LaTeX distribution. The repo still writes `report.tex` if PDF compilation is unavailable.
- The graph-constrained tools are intentionally lightweight and should be validated carefully before being used as physical constraints.

---

## 27. Mental model

Use the repo like this:

```text
Inspect data
    ↓
Clean/resample only if justified
    ↓
Fit simple baselines
    ↓
Fit DMD/DMDc
    ↓
Fit POD and POD-DMDc
    ↓
Validate on unseen cases
    ↓
Run rank/delay/model sweeps
    ↓
Use sparse sensing for sensor insight
    ↓
Generate dashboards and LaTeX reports
```

The strongest model is not necessarily the one with the smallest training error. Prefer models that are accurate, stable, simple, and validated on unseen cases.

---

# Research-Readiness Additions

This version adds a practical layer for using the repo on real thermal-hydraulic ROM studies, especially SAM/simple-loop datasets and experimental loop time series.

## Thermal-loop example

Create a realistic tutorial scaffold:

```bash
dmdc make-thermal-loop-example --outdir examples/end_to_end_thermal_loop_study
```

This writes a synthetic multi-case loop dataset with:

```text
TP1--TP6, TW1--TW3, massFlowRate, q_heater, T_amb, h_amb, case_id, time
```

The example is inspired by the simple natural-circulation SAM loop / Salt Test workflow we discussed: multiple salt-like cases, heater-power variation, fixed airflow metadata, and a hotter held-out case for unseen validation. It is not validated experimental data; it is a teaching and software smoke-test dataset.

See:

```text
docs/tutorials/end_to_end_thermal_loop_study.md
docs/thermal_loop_example.md
```

## Failed/short-case handling

`inspect-data` now writes:

```text
case_quality_dashboard.csv
```

This identifies cases that are too short, contain missing values, have duplicate/nonmonotonic time, or miss an expected final time:

```bash
dmdc inspect-data \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --expected-final-time 850 \
  --outdir outputs/thermal_loop/inspection
```

## Operating-condition summaries

`validate` and `compare` now save `operating_condition_summary.csv` when input columns are available. This reports whether test cases are interpolation or extrapolation in known operating conditions such as heater power, ambient temperature, or heat-transfer coefficient.

This matters because a held-out case outside the training heater-power range should not be interpreted the same way as a held-out case inside the training envelope.

## Uncertainty estimates

Where case-level error tables are available, the repo now writes:

```text
uncertainty_summary.csv
uncertainty_summary.md
uncertainty_summary.tex
```

These use simple bootstrap confidence intervals from case-level errors. They are intentionally lightweight but make reports more honest than a single RMSE value.

## Best-model recommendation

`compare` and `sweep` now write:

```text
best_model_recommendation.json
best_model_recommendation.txt
```

The recommendation is transparent: it filters failed/unstable candidates where possible, then selects the model with the lowest held-out rollout error. It is a review aid, not a substitute for engineering judgment.

You can also run it manually:

```bash
dmdc recommend --table outputs/model_comparison/model_comparison.csv --outdir outputs/recommendation
```

## Regularized DMDc

Use `ridge_dmdc` in comparison and sweep workflows:

```bash
dmdc compare \
  --models persistence mean dmdc ridge_dmdc pod_dmdc \
  ...
```

Ridge DMDc is useful for noisy experimental data or collinear inputs. It solves a Tikhonov-regularized least-squares problem instead of pure least squares.

## Continuous-time interpretation

Discrete sampled data can be converted to an approximate continuous-time generator if the time step is uniform:

```bash
dmdc continuous \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --case-id salt_test_1 \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/thermal_loop/continuous
```

This computes:

```math
A_c = \frac{1}{\Delta t}\log(A_d)
```

Use this for interpreting decay rates, growth rates, and oscillation frequencies. Prediction/validation remains safest in discrete time unless a continuous ODE simulator is added.

## Kalman filtering and state estimation

The repo now includes a beginner-friendly Kalman filtering module for POD-space state estimation:

```python
from dmdc.kalman import LinearKalmanFilter, estimate_pod_state_with_kalman
```

Use it when only a few sensors are available but you want to estimate the full POD state:

```math
a_{k+1} = A_r a_k + B_r u_k + w_k
```

```math
y_k = C\Phi_r a_k + v_k
```

See:

```text
docs/math/12_kalman_filtering.md
examples/kalman_state_estimation/example_kalman_pod_state_estimation.py
```

## Optional loop geometry and better physical plots

The module `dmdc.loop_geometry` lets you map sensors to loop positions and create physical plots:

```python
from dmdc.loop_geometry import LoopGeometry, plot_pod_modes_vs_geometry

geometry = LoopGeometry.load("loop_geometry.toml")
plot_pod_modes_vs_geometry(pod.modes_, state_names, geometry, "pod_modes_vs_geometry.pdf")
```

This is useful for plotting POD modes, errors, and selected sensors versus physical loop position.

## Steady-state and transient windows

Use `dmdc.time_windows` when you want to exclude startup or isolate steady-state behavior:

```python
from dmdc.time_windows import filter_time_window, split_transient_steady_windows

steady_df = filter_time_window(df, time_col="time", t_min=300.0)
windows = split_transient_steady_windows(df, time_col="time", steady_start=300.0, case_col="case_id")
```

## Reproducibility and provenance

Major commands now write:

```text
provenance.json
```

This captures package version, Python version, command/config path, platform, and git commit when available.

## Config templates and cheat sheets

Useful starting points now live in:

```text
configs/templates/
docs/cheatsheets/cli_cheatsheet.md
docs/cheatsheets/config_cheatsheet.md
docs/troubleshooting_decision_tree.md
```

## CI

A GitHub Actions workflow has been added:

```text
.github/workflows/ci.yml
```

It installs the package with dev/ML extras, runs tests, and checks the most important `--help` entry points.

---

## Live Phase 4 and 5: monitoring plus dashboard

The live stack now has five layers:

```text
Phase 1: stream/replay/tail data and maintain a clean rolling buffer
Phase 2: load a validated offline ROM and forecast from live samples
Phase 3: estimate the full state with POD-Kalman filtering, including sparse sensors
Phase 4: monitor residuals, innovations, operating envelope, uncertainty, and trust score
Phase 5: visualize the live run with a polished Streamlit dashboard
```

Use Phase 4 and 5 when you want the repo to act as an advisory live digital-twin monitor. It still does **not** retrain online, control hardware, or replace safety systems.

Replay a previous log with monitoring:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml
```

Tail a CSV file written by a live logger:

```bash
dmdc live-run-monitor --config configs/templates/live_csv_tail_monitor.toml
```

The most important outputs are:

```text
live_forecast_residuals.csv   # old forecasts matched to later measurements
live_alerts.csv               # machine-readable alerts
live_alerts.txt               # human-readable alert log
live_trust_score.csv          # advisory trust-score timeline
live_monitoring_summary.json  # summary for reports/dashboards
```

The main monitor thresholds live in the `[monitor]` config section:

```toml
[monitor]
residual_abs_threshold = 5.0
innovation_abs_threshold = 5.0
innovation_norm_threshold = 12.0
covariance_trace_threshold = 10.0
forecast_match_tolerance_seconds = 0.3
operating_ranges = {q_heater = [0.0, 120.0], T_amb = [280.0, 330.0]}
```

Read these guides next:

```text
docs/live/monitoring_phase4.md
docs/cheatsheets/live_monitoring_cheatsheet.md
```

Launch the Phase-5 dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --view operator
```

No-browser summary check:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --write-summary-only
```

Dashboard docs:

```text
docs/live/dashboard_phase5.md
docs/cheatsheets/live_dashboard_cheatsheet.md
```

---

## Live Phase 6.1: bounded bias correction

Live Phase 6.1 adds conservative online adaptation through **bias correction**.

It does **not** retrain the ROM, modify POD modes, change DMDc matrices, change Kalman matrices, or control hardware. It only learns a bounded additive correction to live forecasts and records every update decision.

```math
\hat{x}_{\text{corrected}}(t+h) = \hat{x}_{\text{ROM}}(t+h) + c(t)
```

or, with horizon-dependent corrections,

```math
\hat{x}_{i,\text{corrected}}(t+h) = \hat{x}_{i,\text{ROM}}(t+h) + c_i(h,t).
```

### Replay demo

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
```

### Live CSV-tail run

```bash
dmdc live-run-adapt --config configs/templates/live_csv_tail_adapt.toml
```

### Dashboard

```bash
dmdc live-dashboard --run-dir outputs/live_adaptation_replay
```

The dashboard includes an **Adaptation** tab showing bias history, raw-vs-corrected residual summaries, skipped-update reasons, and the full audit log.

### Main bias-correction outputs

```text
live_bias_update_events.csv
live_bias_state_timeseries.csv
live_bias_horizon_timeseries.csv
live_bias_summary_by_state.csv
live_bias_summary_by_horizon.csv
live_bias_corrected_forecasts.csv
live_bias_corrected_forecast_residuals.csv
live_bias_error_comparison.csv
live_adaptation_summary.json
live_bias_summary.txt
```

### Documentation

```text
docs/live/adaptation_phase6.md
docs/math/14_bias_correction_and_online_adaptation.md
docs/cheatsheets/bias_correction_cheatsheet.md
```

Bias correction should be used as a small, auditable live offset. Guarded recursive least-squares updates to the dynamics can be added later, but they should remain experimental and opt-in.


## Live Phase 6.4 — archive dashboard mode

For long live-loop campaigns, use archive dashboard mode instead of pointing the dashboard at one run folder:

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
dmdc archive-quicklook --archive-root live_archive --window-label 60s
dmdc live-dashboard --archive-root live_archive --mode archive --window-label 60s
```

Archive dashboard mode is summary-first. It reads the manifest, compact summary CSVs, and quicklook PNGs before opening raw partitions. See `docs/live/dashboard_archive_phase6_4.md` and `docs/cheatsheets/live_archive_dashboard_cheatsheet.md`.

---

## Executive dashboard and operator report

The dashboard now has an operator/executive view designed for scrutiny in meetings:

```bash
dmdc live-dashboard --run-dir outputs/live_adaptation_replay --view operator
dmdc live-dashboard --archive-root live_archive --mode archive --view operator
```

It emphasizes status, trust score, alerts, forecast residuals, bias-correction effect, and archive health before showing detailed technical tables.

For a short meeting-ready report:

```bash
dmdc live-operator-report --run-dir outputs/live_adaptation_replay --outdir outputs/operator_report
dmdc live-operator-report --archive-root live_archive --window-label 60s --outdir outputs/operator_archive_report
```

Docs:

```text
docs/live/operator_report.md
docs/live/dashboard_phase5.md
docs/live/dashboard_archive_phase6_4.md
```

---

## What still needs testing and hardening

Read the roadmap/TODO before treating the repo as operational infrastructure:

```text
TODO_TESTING_AND_ROADMAP.md
docs/testing/ci_and_testing_plan.md
docs/roadmaps/model_deployment_and_provenance.md
docs/hpc_workflow.md
```

Important pending work includes real-data import tests, EPICS/LabVIEW adapter hardening, large-data performance benchmarks, model registry/deployment, schema validation, stronger CI checks, and future HPC/batch workflows. Advisory/control ideas are documented as a future direction only; the current live system is read-only and advisory.

---

## Modular campaigns, model registry, and archive validation

For serious studies, prefer a central campaign config:

```bash
dmdc campaign --config configs/templates/central_campaign_config.toml --dry-run
```

Run only selected steps:

```bash
dmdc campaign --config studies/my_loop/study_config.toml --steps inspect compare dashboard
```

Register a validated model for live deployment:

```bash
dmdc model-register --model outputs/pod_dmdc/pod_dmdc_model.pkl --name simple_loop_pod_dmdc_v1 --stage candidate

dmdc model-promote --name simple_loop_pod_dmdc_v1 --version <VERSION> --stage production
```

Live configs can then use:

```toml
[model]
registry_name = "simple_loop_pod_dmdc_v1"
stage = "production"
registry_root = "models/registry"
```

Validate long-term archives and create human-readable context tables:

```bash
dmdc validate-archive-schema --archive-root live_archive

dmdc archive-context --archive-root live_archive
```

Useful docs:

- `docs/workflows/campaign_workflows.md`
- `docs/model_registry/README.md`
- `docs/archive/schema_validation.md`
- `docs/testing/smoke_tests_and_large_data_plan.md`
- `TODO_TESTING_AND_ROADMAP.md`

---

## Presentation-grade operator dashboard

For demos, reviews, and live-loop monitoring, use the operator view:

```bash
dmdc live-dashboard \
  --run-dir outputs/live_adaptation_replay \
  --view operator \
  --geometry configs/templates/simple_loop_geometry.toml \
  --residual-warning-threshold 2.0 \
  --residual-critical-threshold 5.0
```

The operator view shows:

```text
status banner
live model registry name/stage/version
trust score
alert counts
bias-correction activity
loop schematic with sensors colored by latest forecast residual
largest residuals
bias-correction effect
```

Sensor color convention:

```text
green  = nominal residual
amber  = warning residual
red    = critical residual
gray   = no matched residual yet
```

See:

```text
docs/dashboard/operator_presentation_mode.md
configs/templates/simple_loop_geometry.toml
configs/templates/live_dashboard_presentation.toml
```

---

## Archive benchmark and performance metrics

Use this when you want evidence about archive throughput and summary cost on a
local workstation:

```bash
dmdc benchmark-archive \
  --n-rows 1000000 \
  --n-states 32 \
  --format parquet \
  --outdir outputs/archive_benchmark
```

For a quick smoke test:

```bash
dmdc benchmark-archive --n-rows 10000 --format csv --no-quicklooks
```

The benchmark records:

```text
archive write MB/sec
summary rows/sec
summary generation time
quicklook generation time
peak memory MB
archive size
provenance
```

See:

```text
docs/benchmarks/archive_benchmarking.md
```

---

## Local/HPC campaign planning

Local workstation is the default. HPC is a later/batch execution mode for large
sweeps or archive summaries.

```bash
dmdc hpc-plan \
  --config configs/templates/central_campaign_config.toml \
  --outdir outputs/hpc_plan
```

This writes a local runner and incomplete Slurm templates with `FIXME` account,
partition, module, and environment fields.

See:

```text
docs/hpc/batch_workflows.md
```

---

## Field adapters

The importer/streaming layer is intentionally modular. Current supported or
scaffolded adapters include:

```text
CSV / Excel / Parquet imports
folder imports
LabVIEW/DAQ folder-drop imports
CSV replay stream
CSV tail stream
EPICS PV snapshot import
EPICS polling stream scaffold
```

See:

```text
docs/adapters/field_ready_adapters.md
docs/importers/README.md
docs/live/streaming_phase1.md
```

Future adapters such as MQTT, ZeroMQ, OPC UA, and vendor-specific DAQ readers
should implement the same small importer or stream adapter contracts.

## Testing status and hardening

The repo includes a broad pytest suite covering offline ROM math, configs, imports, live streaming, forecasting, Kalman estimation, monitoring, bias correction, archiving, dashboards, model registry, campaign workflows, and HPC planning.

Run the normal suite with:

```bash
pytest
```

Run the new hardening-focused tests with:

```bash
pytest tests/test_hardening_*.py
```

Large benchmark plumbing tests are opt-in:

```bash
pytest -m large
```

See [`docs/testing/test_hardening_added.md`](docs/testing/test_hardening_added.md) and [`docs/testing/ci_and_testing_plan.md`](docs/testing/ci_and_testing_plan.md).
