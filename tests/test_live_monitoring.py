from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import LiveMonitoringConfig, PODDMDcPipeline, compute_forecast_residuals, run_live_monitoring
from dmdc.cli import main


def _make_training_data(n: int = 30) -> pd.DataFrame:
    t = np.arange(n, dtype=float) * 0.2
    u = 0.4 + 0.05 * np.sin(0.3 * t)
    x = np.zeros((n, 2), dtype=float)
    x[0] = [1.0, -0.5]
    A = np.array([[0.92, 0.08], [-0.04, 0.88]])
    B = np.array([0.12, -0.03])
    for k in range(n - 1):
        x[k + 1] = A @ x[k] + B * u[k]
    return pd.DataFrame({"time": t, "case_id": ["run_001"] * n, "x1": x[:, 0], "x2": x[:, 1], "u1": u})


def _fit_model(df: pd.DataFrame, model_path: Path) -> None:
    model = PODDMDcPipeline(pod_rank="full", dmdc_rank="full", center=True)
    model.fit(df[["x1", "x2"]].to_numpy(), df[["u1"]].to_numpy(), state_names=["x1", "x2"], input_names=["u1"])
    model.save(model_path)


def test_compute_forecast_residuals_matches_target_times() -> None:
    clean = pd.DataFrame({"time": [0.0, 0.2, 0.4], "x1": [1.0, 1.1, 1.2]})
    forecasts = pd.DataFrame(
        {
            "origin_time": [0.0],
            "forecast_horizon_s": [0.2],
            "state": ["x1"],
            "predicted_value": [1.05],
        }
    )
    residuals = compute_forecast_residuals(clean, forecasts, time_col="time", measurement_cols=["x1"], tolerance_seconds=1e-9)
    assert len(residuals) == 1
    assert abs(float(residuals.iloc[0]["residual"]) - 0.05) < 1e-12


def test_run_live_monitoring_writes_alerts_and_trust(tmp_path: Path) -> None:
    df = _make_training_data()
    stream = tmp_path / "stream.csv"
    # Add a measurement glitch after the first forecast can be checked so the
    # monitor emits at least one alert in a deterministic way.
    stream_df = df[["time", "case_id", "x1", "u1"]].copy()
    stream_df.loc[4, "x1"] += 3.0
    stream_df.to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_model(df, model_path)
    out = tmp_path / "monitor"
    cfg = LiveMonitoringConfig(
        stream_type="csv_replay",
        path=str(stream),
        model_path=str(model_path),
        state_cols=["x1", "x2"],
        measurement_cols=["x1"],
        input_cols=["u1"],
        time_col="time",
        chunk_size=1,
        max_samples=8,
        forecast_horizons_seconds=[0.2],
        discrete_dt_seconds=0.2,
        residual_abs_threshold=0.1,
        innovation_abs_threshold=0.1,
        outdir=str(out),
    )
    result = run_live_monitoring(cfg)
    assert result.n_alerts > 0
    assert (out / "live_alerts.csv").exists()
    assert (out / "live_trust_score.csv").exists()
    assert (out / "live_forecast_residuals.csv").exists()
    alerts = pd.read_csv(out / "live_alerts.csv")
    assert {"FORECAST_RESIDUAL_HIGH", "KALMAN_INNOVATION_HIGH"}.intersection(set(alerts["code"]))
    trust = pd.read_csv(out / "live_trust_score.csv")
    assert float(trust["trust_score"].iloc[-1]) < 1.0


def test_live_replay_monitor_cli_and_config(tmp_path: Path) -> None:
    df = _make_training_data()
    stream = tmp_path / "stream.csv"
    df[["time", "case_id", "x1", "u1"]].to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_model(df, model_path)
    out = tmp_path / "cli_monitor"
    cfg = tmp_path / "live_monitor.toml"
    cfg.write_text(
        f'''
[stream]
type = "csv_replay"
path = "{stream}"
chunk_size = 1

[data]
time_col = "time"
state_cols = ["x1", "x2"]
measurement_cols = ["x1"]
input_cols = ["u1"]

[model]
path = "{model_path}"

[estimator]
process_noise = 1.0e-6
measurement_noise = 1.0e-3
initial_covariance = 1.0

[forecast]
horizons_seconds = [0.2]
discrete_dt_seconds = 0.2

[monitor]
residual_abs_threshold = 5.0
innovation_abs_threshold = 5.0
operating_ranges = {{u1 = [0.0, 1.0]}}

[live]
max_samples = 5
outdir = "{out}"
''',
        encoding="utf-8",
    )
    main(["live-replay-monitor", "--config", str(cfg)])
    assert (out / "live_monitoring_summary.json").exists()
    assert (out / "live_alerts.txt").exists()
    assert (out / "live_trust_score.csv").exists()
