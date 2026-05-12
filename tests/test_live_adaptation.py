from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import LiveAdaptationConfig, PODDMDcPipeline, compute_bias_update_events, run_live_adaptation
from dmdc.live_adaptation import apply_bias_history_to_forecasts, build_live_adaptation_tables
from dmdc.cli import main


def _make_training_data(n: int = 36) -> pd.DataFrame:
    t = np.arange(n, dtype=float) * 0.2
    u = 0.4 + 0.05 * np.sin(0.4 * t)
    x = np.zeros((n, 2), dtype=float)
    x[0] = [1.0, -0.5]
    A = np.array([[0.91, 0.06], [-0.03, 0.89]])
    B = np.array([0.10, -0.025])
    for k in range(n - 1):
        x[k + 1] = A @ x[k] + B * u[k]
    return pd.DataFrame({"time": t, "case_id": ["run_001"] * n, "x1": x[:, 0], "x2": x[:, 1], "u1": u})


def _fit_model(df: pd.DataFrame, model_path: Path) -> None:
    model = PODDMDcPipeline(pod_rank="full", dmdc_rank="full", center=True)
    model.fit(df[["x1", "x2"]].to_numpy(), df[["u1"]].to_numpy(), state_names=["x1", "x2"], input_names=["u1"])
    model.save(model_path)


def test_bias_update_events_are_auditable_and_bounded() -> None:
    residuals = pd.DataFrame(
        {
            "origin_time": [0.0, 1.0, 2.0],
            "target_time": [1.0, 2.0, 3.0],
            "matched_time": [1.0, 2.0, 3.0],
            "forecast_horizon_s": [1.0, 1.0, 1.0],
            "state": ["TP4", "TP4", "TP4"],
            "measured_value": [10.0, 10.0, 10.0],
            "predicted_value": [8.0, 7.0, 6.0],
            "residual": [2.0, 3.0, 4.0],
            "abs_residual": [2.0, 3.0, 4.0],
        }
    )
    trust = pd.DataFrame({"time": [1.0, 2.0, 3.0], "trust_score": [1.0, 1.0, 1.0]})
    cfg = LiveAdaptationConfig(
        stream_type="csv_replay",
        path="unused.csv",
        model_path="unused.pkl",
        measurement_cols=["TP4"],
        time_col="time",
        adaptation_method="horizon_state_bias",
        bias_learning_rate=0.5,
        max_update_step=0.4,
        max_abs_bias=0.7,
        update_only_when_trust_above=0.5,
    )
    events = compute_bias_update_events(residuals=residuals, alerts=pd.DataFrame(), trust=trust, config=cfg)
    assert len(events) == 3
    assert events["accepted"].all()
    assert events["new_bias"].abs().max() <= 0.7 + 1e-12
    assert events["delta_bias"].abs().max() <= 0.4 + 1e-12


def test_apply_bias_history_uses_only_past_bias() -> None:
    forecasts = pd.DataFrame(
        {
            "origin_time": [0.0, 1.0, 2.0],
            "forecast_horizon_s": [1.0, 1.0, 1.0],
            "target_time": [1.0, 2.0, 3.0],
            "state": ["TP4", "TP4", "TP4"],
            "predicted_value": [100.0, 100.0, 100.0],
        }
    )
    events = pd.DataFrame(
        {
            "time": [1.5],
            "state": ["TP4"],
            "forecast_horizon_s": [1.0],
            "new_bias": [2.0],
            "accepted": [True],
        }
    )
    corrected = apply_bias_history_to_forecasts(forecasts, events, method="horizon_state_bias")
    assert float(corrected.loc[0, "applied_bias"]) == 0.0
    assert float(corrected.loc[1, "applied_bias"]) == 0.0
    assert float(corrected.loc[2, "applied_bias"]) == 2.0
    assert float(corrected.loc[2, "bias_corrected_predicted_value"]) == 102.0


def test_run_live_adaptation_writes_bias_outputs(tmp_path: Path) -> None:
    df = _make_training_data()
    stream = tmp_path / "stream.csv"
    stream_df = df[["time", "case_id", "x1", "u1"]].copy()
    # Persistent measurement offset makes the bias records nontrivial without
    # requiring any online change to the saved model.
    stream_df["x1"] += 0.15
    stream_df.to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_model(df, model_path)
    out = tmp_path / "adapt"
    cfg = LiveAdaptationConfig(
        stream_type="csv_replay",
        path=str(stream),
        model_path=str(model_path),
        state_cols=["x1", "x2"],
        measurement_cols=["x1"],
        input_cols=["u1"],
        time_col="time",
        chunk_size=1,
        max_samples=12,
        forecast_horizons_seconds=[0.2],
        discrete_dt_seconds=0.2,
        residual_abs_threshold=99.0,
        innovation_abs_threshold=99.0,
        adaptation_method="horizon_state_bias",
        bias_learning_rate=0.2,
        max_abs_bias=1.0,
        max_update_step=0.2,
        update_only_when_trust_above=0.0,
        outdir=str(out),
    )
    result = run_live_adaptation(cfg)
    assert result.n_bias_update_events > 0
    assert result.n_bias_updates_accepted > 0
    for filename in [
        "live_bias_update_events.csv",
        "live_bias_state_timeseries.csv",
        "live_bias_corrected_forecasts.csv",
        "live_bias_corrected_forecast_residuals.csv",
        "live_adaptation_summary.json",
    ]:
        assert (out / filename).exists()
    events = pd.read_csv(out / "live_bias_update_events.csv")
    assert {"old_bias", "new_bias", "accepted", "rejection_reason"}.issubset(events.columns)


def test_live_replay_adapt_cli_and_config(tmp_path: Path) -> None:
    df = _make_training_data()
    stream = tmp_path / "stream.csv"
    df[["time", "case_id", "x1", "u1"]].to_csv(stream, index=False)
    model_path = tmp_path / "pod_dmdc_model.pkl"
    _fit_model(df, model_path)
    out = tmp_path / "cli_adapt"
    cfg = tmp_path / "live_adapt.toml"
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
residual_abs_threshold = 99.0
innovation_abs_threshold = 99.0

[live_adaptation]
enabled = true
method = "state_bias"

[live_adaptation.bias]
learning_rate = 0.1
max_abs_bias = 1.0
max_update_step = 0.2
update_only_when_trust_above = 0.0
clip_residual_abs = 5.0

[live]
max_samples = 7
outdir = "{out}"
''',
        encoding="utf-8",
    )
    main(["live-replay-adapt", "--config", str(cfg)])
    assert (out / "live_adaptation_summary.json").exists()
    assert (out / "live_bias_update_events.csv").exists()
    assert (out / "live_bias_summary.txt").exists()
