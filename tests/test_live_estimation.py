from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import LiveEstimationConfig, PODDMDcPipeline, run_live_estimation
from dmdc.cli import main


def _make_pod_dmdc_training_data(n: int = 30) -> pd.DataFrame:
    t = np.arange(n, dtype=float) * 0.2
    u = 0.4 + 0.05 * np.sin(0.3 * t)
    x = np.zeros((n, 2), dtype=float)
    x[0] = [1.0, -0.5]
    A = np.array([[0.92, 0.08], [-0.04, 0.88]])
    B = np.array([0.12, -0.03])
    for k in range(n - 1):
        x[k + 1] = A @ x[k] + B * u[k]
    return pd.DataFrame({"time": t, "case_id": ["run_001"] * n, "x1": x[:, 0], "x2": x[:, 1], "u1": u})


def _fit_pod_dmdc_model(df: pd.DataFrame, model_path: Path) -> None:
    model = PODDMDcPipeline(pod_rank="full", dmdc_rank="full", center=True)
    model.fit(df[["x1", "x2"]].to_numpy(), df[["u1"]].to_numpy(), state_names=["x1", "x2"], input_names=["u1"])
    model.save(model_path)


def test_run_live_estimation_replay_sparse_measurement(tmp_path: Path) -> None:
    df = _make_pod_dmdc_training_data()
    stream = tmp_path / "stream.csv"
    # The live stream only includes x1, not x2. The estimator reconstructs x2.
    df[["time", "case_id", "x1", "u1"]].to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_pod_dmdc_model(df, model_path)
    out = tmp_path / "live_estimate"
    cfg = LiveEstimationConfig(
        stream_type="csv_replay",
        path=str(stream),
        model_path=str(model_path),
        state_cols=["x1", "x2"],
        measurement_cols=["x1"],
        input_cols=["u1"],
        time_col="time",
        chunk_size=3,
        max_samples=9,
        forecast_horizons_seconds=[0.2, 0.4],
        discrete_dt_seconds=0.2,
        outdir=str(out),
    )
    result = run_live_estimation(cfg)
    assert result.n_estimate_updates == 3
    assert result.n_forecast_rows == 3 * 2 * 2
    states = pd.read_csv(out / "live_state_estimates.csv")
    assert {"x1", "x2", "covariance_trace", "innovation_norm"}.issubset(states.columns)
    assert len(states) == 3
    assert (out / "live_modal_estimates.csv").exists()
    assert (out / "live_estimate_covariance.csv").exists()
    innovations = pd.read_csv(out / "live_kalman_innovations.csv")
    assert set(innovations["measurement"]) == {"x1"}
    forecasts = pd.read_csv(out / "live_forecasts.csv")
    assert set(forecasts["state"]) == {"x1", "x2"}
    assert (out / "live_estimation_summary.json").exists()
    assert (out / "provenance.json").exists()


def test_live_replay_estimate_cli_and_config(tmp_path: Path) -> None:
    df = _make_pod_dmdc_training_data()
    stream = tmp_path / "stream.csv"
    df[["time", "case_id", "x1", "u1"]].to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_pod_dmdc_model(df, model_path)
    out = tmp_path / "cli_estimate"
    cfg = tmp_path / "live_estimate.toml"
    cfg.write_text(
        f'''
[stream]
type = "csv_replay"
path = "{stream}"
chunk_size = 2

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

[live]
max_samples = 4
outdir = "{out}"
''',
        encoding="utf-8",
    )
    main(["live-replay-estimate", "--config", str(cfg)])
    states = pd.read_csv(out / "live_state_estimates.csv")
    assert not states.empty
    assert "x2" in states.columns
    forecasts = pd.read_csv(out / "live_forecasts.csv")
    assert not forecasts.empty


def test_live_run_estimate_tail_mode_limited_polls(tmp_path: Path) -> None:
    df = _make_pod_dmdc_training_data(n=10)
    stream = tmp_path / "tail.csv"
    df[["time", "case_id", "x1", "u1"]].to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_pod_dmdc_model(df, model_path)
    out = tmp_path / "tail_estimate"
    main(
        [
            "live-run-estimate",
            "--data",
            str(stream),
            "--model",
            str(model_path),
            "--time-col",
            "time",
            "--state-cols",
            "x1",
            "x2",
            "--measurement-cols",
            "x1",
            "--input-cols",
            "u1",
            "--max-polls",
            "1",
            "--outdir",
            str(out),
        ]
    )
    states = pd.read_csv(out / "live_state_estimates.csv")
    assert len(states) == 1
    assert (out / "live_kalman_innovations.csv").exists()
