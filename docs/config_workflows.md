# Config-Driven Workflows

The command line is useful for quick experiments, but a research workflow becomes easier to
reproduce when the important choices live in a version-controlled config file.

This repo supports JSON, TOML, and optionally YAML config files.

- JSON is always supported.
- TOML is supported on Python 3.11+ through the standard library.
- YAML works only if you install `PyYAML`.

## 1. Single fit config

Example: `configs/example_fit.toml`

```toml
[data]
path = "data/example_timeseries.csv"
time_col = "time"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[model]
rank = "full"
n_delays = 1

[preprocessing]
center = false
scale = false

[output]
outdir = "outputs/config_example_fit"
plots = true
```

Run it with:

```bash
dmdc fit --config configs/example_fit.toml
```

CLI values override config values. For example:

```bash
dmdc fit --config configs/example_fit.toml --rank 0.999 --outdir outputs/rank_999
```

## 2. Multi-case workflow config

Example: `configs/example_workflow.toml`

```toml
[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[model]
rank = "full"
n_delays = 1

[output]
root = "outputs/configured_cases"
plots = true

[[cases]]
name = "all_cases_together"
# No case_id means one model is fit across all trajectories, while respecting case boundaries.

[[cases]]
name = "only_run_001"
case_id = "run_001"

[[cases]]
name = "only_run_002_custom_folder"
case_id = "run_002"
outdir = "outputs/my_custom_folder/run_002"
```

Run all configured jobs with:

```bash
dmdc workflow --config configs/example_workflow.toml
```

This produces one output folder per configured case. If `outdir` is not specified for a case,
the folder is generated from `output.root` and the case `name`.

## 3. Recommended folder strategy

For simulation sweeps, use stable run names and one folder per model fit:

```text
outputs/
└── my_study/
    ├── all_cases_together/
    ├── jsalt1_only/
    ├── jsalt2_only/
    ├── rank_sweep_r04/
    ├── rank_sweep_r08/
    └── delay_sweep_d04/
```

This makes it easy to compare diagnostics later without overwriting prior runs.

## 4. Sensor selection config

Example: `configs/example_sensor_selection.toml`

```toml
[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]

[model]
rank = "full"

[preprocessing]
center = true
scale = true

[output]
plots = true

[sensor_selection]
n_sensors = 2
outdir = "outputs/config_sensor_selection"
```

Run it with:

```bash
dmdc select-sensors --config configs/example_sensor_selection.toml
```

## 5. Practical thermal-hydraulic example

For loop data, a realistic config might look like:

```toml
[data]
path = "analysis/loop_timeseries.csv"
time_col = "time"
case_col = "run_id"
state_cols = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "massFlowRate"]
input_cols = ["q_net", "T_amb", "h_amb"]

[model]
rank = 8
n_delays = 5

[preprocessing]
center = true
scale = true

[output]
root = "outputs/loop_dmdc_study"
plots = true

[[cases]]
name = "all_runs_delay5_rank8"

[[cases]]
name = "jsalt1_only"
case_id = "jsalt1"

[[cases]]
name = "jsalt2_only"
case_id = "jsalt2"
```

This lets you keep column definitions and modeling choices in one place, which is much less
error-prone than retyping long commands.
