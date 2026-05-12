"""Synthetic thermal-loop example dataset and tutorial asset generator.

The generated data are intentionally *not* a validated SAM or TAMU dataset.  They
are a small, reproducible, SAM-like teaching dataset with columns and operating
conditions that resemble natural-circulation molten-salt loop studies: TP1--TP6,
wall temperatures, mass flow, heater power, ambient temperature, heat-transfer
coefficient, and independent case IDs.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


STATE_COLS = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TW1", "TW2", "TW3", "massFlowRate"]
INPUT_COLS = ["q_heater", "T_amb", "h_amb"]


def generate_thermal_loop_dataframe(*, n_time: int = 160, seed: int = 7) -> pd.DataFrame:
    """Generate a small multi-case synthetic thermal-loop time series."""

    rng = np.random.default_rng(seed)
    cases = [
        ("salt_test_1", 232.3, 31.7, 295.0, 7.5),
        ("salt_test_2", 268.0, 38.0, 296.0, 8.5),
        ("salt_test_3", 305.0, 46.0, 297.0, 9.5),
        ("salt_test_4", 337.6, 54.3, 298.0, 10.5),
        # A deliberately held-out/extrapolation-style case for validation examples.
        ("salt_test_5_unseen_hot", 365.0, 58.0, 299.0, 11.5),
    ]
    rows = []
    positions = np.array([0.0, 0.7, 1.4, 2.3, 3.2, 4.0])
    # Nonuniform/adaptive-like time grid: dense near startup, coarser near steady state.
    # This mirrors many SAM/adaptive solver outputs better than an exactly uniform grid.
    tau = np.linspace(0.0, 1.0, n_time)
    t_base = 850.0 * tau**1.45
    for case_id, q_heater, pr, T_amb, h_amb in cases:
        jitter = rng.normal(0.0, 0.015, size=n_time)
        jitter[0] = 0.0
        t = np.maximum.accumulate(t_base + np.cumsum(np.abs(jitter)))
        t = 850.0 * (t - t[0]) / (t[-1] - t[0])

        q_norm = (q_heater - 232.3) / (365.0 - 232.3)
        mdot_ss = 0.12 + 0.045 * np.sqrt(max(q_norm, 0.0) + 0.15)
        mdot = mdot_ss * (1 - np.exp(-t / (180.0 - 40.0 * q_norm)))
        mdot += 0.002 * np.sin(2 * np.pi * t / 300.0)
        base = 455.0 + 4.0 * q_norm
        delta_ss = 18.0 + 25.0 * q_norm
        transient = 1.0 - np.exp(-t / (120.0 + 30.0 * q_norm))
        # Traveling thermal wave; downstream sensors respond with position-dependent lag.
        tp = []
        for i, pos in enumerate(positions):
            lag = 18.0 * i
            shifted = np.clip(t - lag, 0.0, None)
            local_transient = 1.0 - np.exp(-shifted / (120.0 + 25.0 * q_norm))
            spatial_profile = np.sin(np.pi * pos / positions[-1])
            temp = base + delta_ss * spatial_profile * local_transient
            temp += 1.2 * np.sin(2 * np.pi * (t - lag) / 420.0) * transient
            temp += rng.normal(0.0, 0.08, size=t.size)
            tp.append(temp)
        tp = np.vstack(tp).T
        tw1 = tp[:, 1] + 2.5 + 3.0 * q_norm + rng.normal(0.0, 0.05, size=t.size)
        tw2 = tp[:, 3] + 3.0 + 2.0 * q_norm + rng.normal(0.0, 0.05, size=t.size)
        tw3 = tp[:, 4] + 1.5 + 1.5 * q_norm + rng.normal(0.0, 0.05, size=t.size)
        for k, time in enumerate(t):
            rows.append(
                {
                    "time": float(time),
                    "case_id": case_id,
                    "q_heater": q_heater,
                    "T_amb": T_amb,
                    "h_amb": h_amb,
                    "Pr": pr,
                    "air_flow_L_min": 37.0,
                    "TP1": tp[k, 0],
                    "TP2": tp[k, 1],
                    "TP3": tp[k, 2],
                    "TP4": tp[k, 3],
                    "TP5": tp[k, 4],
                    "TP6": tp[k, 5],
                    "TW1": tw1[k],
                    "TW2": tw2[k],
                    "TW3": tw3[k],
                    "massFlowRate": mdot[k],
                    "case_status": "success",
                }
            )
    return pd.DataFrame(rows)


def write_thermal_loop_example(outdir: str | Path, *, n_time: int = 160, seed: int = 7) -> dict[str, str]:
    """Write synthetic thermal-loop data, geometry, configs, and README."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    df = generate_thermal_loop_dataframe(n_time=n_time, seed=seed)
    data_path = out / "thermal_loop_synthetic.csv"
    df.to_csv(data_path, index=False)
    geometry_path = out / "loop_geometry.toml"
    geometry_path.write_text(
        '''description = "Synthetic one-dimensional positions around a natural-circulation loop."
[positions_m]
TP1 = 0.0
TP2 = 0.7
TP3 = 1.4
TP4 = 2.3
TP5 = 3.2
TP6 = 4.0
TW1 = 0.9
TW2 = 2.5
TW3 = 3.4
massFlowRate = 4.1
''',
        encoding="utf-8",
    )
    config_path = out / "thermal_loop_study.toml"
    config_path.write_text(
        f'''[data]
path = "{data_path.as_posix()}"
time_col = "time"
case_col = "case_id"
state_cols = {STATE_COLS!r}
input_cols = {INPUT_COLS!r}

[state_groups]
fluid_temperatures = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6"]
wall_temperatures = ["TW1", "TW2", "TW3"]
flow = ["massFlowRate"]

[split]
strategy = "explicit_case_lists"
train_cases = ["salt_test_1", "salt_test_2", "salt_test_3", "salt_test_4"]
test_cases = ["salt_test_5_unseen_hot"]

[pod]
rank = 0.999
center = true
scale = false

[model]
type = "pod_dmdc"
dmdc_rank = "full"

[adaptive]
alpha = 1.0e-8

[compare]
models = ["persistence", "mean", "adaptive_dmdc", "dmdc", "ridge_dmdc", "pod_dmdc"]

[validation]
forecast_horizons = [1, 5, 10, 25]

[output]
outdir = "{(out / 'outputs' / 'validation').as_posix()}"
plots = true

[geometry]
path = "{geometry_path.as_posix()}"
''',
        encoding="utf-8",
    )
    readme = out / "README.md"
    readme.write_text(
        f'''# End-to-End Thermal Loop ROM Tutorial

This folder contains a small synthetic TAMU/SAM-like natural-circulation loop dataset.
It is for software testing and tutorial use only; it is not validated experimental data.

## Files

- `thermal_loop_synthetic.csv`: multi-case time series with TP1--TP6, TW1--TW3, massFlowRate, and inputs.
- `loop_geometry.toml`: optional one-dimensional sensor positions around the loop.
- `thermal_loop_study.toml`: config for a POD-DMDc validation study.

## Suggested commands

```bash
python -m dmdc.cli inspect-data --config thermal_loop_study.toml
python -m dmdc.cli validate --config thermal_loop_study.toml
python -m dmdc.cli compare \
  --data {data_path.as_posix()} \
  --time-col time --case-col case_id \
  --state-cols {' '.join(STATE_COLS)} \
  --input-cols {' '.join(INPUT_COLS)} \
  --train-cases salt_test_1 salt_test_2 salt_test_3 salt_test_4 \
  --test-cases salt_test_5_unseen_hot \
  --models persistence mean adaptive_dmdc dmdc ridge_dmdc pod_dmdc \
  --outdir {out.as_posix()}/outputs/compare --plots --report
```

The synthetic time grid is intentionally nonuniform/adaptive-like, and the held-out case has a heater power above the training range on purpose.  The operating-condition summary should flag that as extrapolation.
''',
        encoding="utf-8",
    )
    return {"data": str(data_path), "geometry": str(geometry_path), "config": str(config_path), "readme": str(readme)}
