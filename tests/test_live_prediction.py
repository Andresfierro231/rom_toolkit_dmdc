from pathlib import Path

import pandas as pd

from dmdc import AdaptiveDMDcModel, LivePredictionConfig, run_live_prediction
from dmdc.cli import main


def _write_live_training_csv(path: Path, n: int = 12) -> pd.DataFrame:
    # Mildly nonuniform timestamps, one input, two states.  The pattern is simple
    # enough for an adaptive DMDc model to fit during tests but still exercises
    # the variable-dt path used by live prediction.
    t = [0.0]
    for i in range(1, n):
        t.append(t[-1] + 0.1 + 0.02 * (i % 3))
    x1 = [1.0]
    x2 = [2.0]
    u = [0.5 + 0.01 * i for i in range(n)]
    for k in range(n - 1):
        dt = t[k + 1] - t[k]
        x1.append(x1[-1] + dt * (-0.2 * x1[-1] + 0.1 * u[k]))
        x2.append(x2[-1] + dt * (-0.1 * x2[-1] + 0.05 * x1[-1]))
    df = pd.DataFrame({"time": t, "case_id": ["run_001"] * n, "x1": x1, "x2": x2, "u1": u})
    df.to_csv(path, index=False)
    return df


def _fit_adaptive_model(data: Path, model_path: Path) -> None:
    df = pd.read_csv(data)
    model = AdaptiveDMDcModel(alpha=1e-8)
    model.fit(
        df[["x1", "x2"]].to_numpy(),
        df[["u1"]].to_numpy(),
        time=df["time"].to_numpy(),
        state_names=["x1", "x2"],
        input_names=["u1"],
    )
    model.save(model_path)


def test_run_live_prediction_replay_writes_forecasts(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_live_training_csv(data)
    model_path = tmp_path / "adaptive_model.pkl"
    _fit_adaptive_model(data, model_path)
    out = tmp_path / "live_pred"
    cfg = LivePredictionConfig(
        stream_type="csv_replay",
        path=str(data),
        model_path=str(model_path),
        time_col="time",
        state_cols=["x1", "x2"],
        input_cols=["u1"],
        forecast_horizons_seconds=[0.1, 0.25],
        chunk_size=3,
        max_samples=6,
        outdir=str(out),
    )
    result = run_live_prediction(cfg)
    assert result.n_forecast_origins == 2
    assert result.n_forecast_rows == 2 * 2 * 2  # origins × horizons × states
    forecasts = pd.read_csv(out / "live_forecasts.csv")
    assert set(forecasts["state"]) == {"x1", "x2"}
    assert (out / "live_forecasts_wide.csv").exists()
    assert (out / "live_state_estimates.csv").exists()
    assert (out / "live_prediction_summary.json").exists()
    assert (out / "provenance.json").exists()


def test_live_replay_predict_cli_and_config(tmp_path: Path) -> None:
    data = tmp_path / "stream.csv"
    _write_live_training_csv(data)
    model_path = tmp_path / "adaptive_model.pkl"
    _fit_adaptive_model(data, model_path)
    out = tmp_path / "live_cli"
    cfg = tmp_path / "live_predict.toml"
    cfg.write_text(
        f'''
[stream]
type = "csv_replay"
path = "{data}"
chunk_size = 2

[data]
time_col = "time"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[model]
path = "{model_path}"

[forecast]
horizons_seconds = [0.1, 0.2]

[live]
max_samples = 4
outdir = "{out}"
''',
        encoding="utf-8",
    )
    main(["live-replay-predict", "--config", str(cfg)])
    forecasts = pd.read_csv(out / "live_forecasts.csv")
    assert not forecasts.empty
    assert set(forecasts["forecast_horizon_s"]) == {0.1, 0.2}
    assert (out / "cleaned_stream_log.csv").exists()


def test_live_run_predict_tail_mode_limited_polls(tmp_path: Path) -> None:
    data = tmp_path / "tail.csv"
    _write_live_training_csv(data, n=6)
    model_path = tmp_path / "adaptive_model.pkl"
    _fit_adaptive_model(data, model_path)
    out = tmp_path / "tail_pred"
    main(
        [
            "live-run-predict",
            "--data",
            str(data),
            "--model",
            str(model_path),
            "--time-col",
            "time",
            "--state-cols",
            "x1",
            "x2",
            "--input-cols",
            "u1",
            "--forecast-horizons-seconds",
            "0.1",
            "0.2",
            "--max-polls",
            "1",
            "--outdir",
            str(out),
        ]
    )
    forecasts = pd.read_csv(out / "live_forecasts.csv")
    assert len(forecasts) == 2 * 2  # one origin × two horizons × two states
