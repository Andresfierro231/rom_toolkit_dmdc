"""Live Phase-2: stream/replay data and forecast with a saved ROM.

This module builds on Phase-1 streaming.  It does not perform Kalman filtering,
residual alerting, or online retraining yet.  Each time new clean samples arrive,
it uses the newest clean state and input values as the forecast origin, calls a
saved offline ROM through :class:`dmdc.live_predictor.LivePredictor`, and appends
long-form forecast rows to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import shutil

import pandas as pd

from .live_buffer import RollingLiveBuffer
from .live_predictor import ForecastSettings, LivePredictor, forecast_frame_to_wide
from .provenance import write_provenance
from .streaming import make_stream_adapter, run_stream_until_done


@dataclass
class LivePredictionConfig:
    """Configuration for live replay/tail prediction.

    The stream/data fields mirror :class:`dmdc.live.LiveIngestionConfig`, with
    additional model and forecast settings.
    """

    stream_type: str
    path: str
    state_cols: list[str]
    input_cols: list[str]
    model_path: str
    time_col: str | None = None
    case_col: str | None = None
    case_id: str | int | float | None = None
    outdir: str = "outputs/live_prediction"
    chunk_size: int = 1
    poll_seconds: float = 0.0
    max_samples: int | None = None
    max_polls: int | None = None
    buffer_seconds: float | None = None
    buffer_max_samples: int | None = None
    start_at_end: bool = False
    save_every_batch: bool = False
    forecast_horizons_seconds: list[float] | None = None
    discrete_dt_seconds: float | None = None


@dataclass
class LivePredictionResult:
    """Summary returned by :func:`run_live_prediction`."""

    outdir: str
    n_batches: int
    n_samples_seen: int
    n_clean_samples_buffered: int
    n_forecast_origins: int
    n_forecast_rows: int
    n_warnings: int
    stream_type: str
    model_type: str


def run_live_prediction(config: LivePredictionConfig, *, config_path: str | Path | None = None) -> LivePredictionResult:
    """Run live/replay ingestion plus saved-model forecasting.

    Forecasts are written in two forms:

    ``live_forecasts.csv``
        Long-form table with one row per ``origin × horizon × state``.
    ``live_forecasts_wide.csv``
        Convenience table with one row per ``origin × horizon`` and one column
        per state.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if config_path is not None:
        try:
            shutil.copyfile(config_path, outdir / "config_used.toml")
        except OSError:
            pass

    adapter = make_stream_adapter(
        stream_type=config.stream_type,
        path=config.path,
        chunk_size=config.chunk_size,
        start_at_end=config.start_at_end,
        case_col=config.case_col,
        case_id=config.case_id,
        time_col=config.time_col,
    )
    buffer = RollingLiveBuffer(
        state_cols=config.state_cols,
        input_cols=config.input_cols,
        time_col=config.time_col,
        case_col=config.case_col,
        buffer_seconds=config.buffer_seconds,
        max_samples=config.buffer_max_samples,
    )
    predictor = LivePredictor.load(config.model_path, discrete_dt_seconds=config.discrete_dt_seconds)
    settings = ForecastSettings(
        horizons_seconds=list(config.forecast_horizons_seconds or [5.0, 10.0, 30.0, 60.0]),
        discrete_dt_seconds=config.discrete_dt_seconds,
    )

    forecast_frames: list[pd.DataFrame] = []
    state_estimate_records: list[dict[str, Any]] = []
    n_batches = 0
    n_samples_seen = 0
    last_forecasted_row_index: int | None = None

    for batch in run_stream_until_done(
        adapter,
        max_samples=config.max_samples,
        max_polls=config.max_polls,
        poll_seconds=config.poll_seconds,
    ):
        n_batches += 1
        n_samples_seen += len(batch)
        buffer.append(batch)
        clean = buffer.clean_frame
        if not clean.empty:
            latest = clean.iloc[-1].to_dict()
            row_index = latest.get("_stream_row_index")
            # Forecast once per newest source row.  If a tail poll returns no new
            # clean sample, avoid duplicating forecasts for the same origin.
            forecast_key = int(row_index) if row_index is not None else len(clean)
            if forecast_key != last_forecasted_row_index:
                x = buffer.latest_state()
                u = buffer.latest_input()
                if x is not None:
                    origin_time = float(latest[config.time_col]) if config.time_col and latest.get(config.time_col) is not None else None
                    forecast = predictor.forecast(
                        x,
                        u,
                        settings,
                        origin_time=origin_time,
                        origin_row_index=None if row_index is None else int(row_index),
                        received_utc=latest.get("_received_utc"),
                    )
                    forecast_frames.append(forecast.forecast_frame)
                    state_record = {
                        "origin_time": origin_time,
                        "origin_row_index": None if row_index is None else int(row_index),
                        "received_utc": latest.get("_received_utc"),
                        "model_type": predictor.model_type,
                    }
                    for name, value in zip(config.state_cols, x, strict=True):
                        state_record[name] = float(value)
                    if u is not None:
                        for name, value in zip(config.input_cols, u, strict=True):
                            state_record[name] = float(value)
                    state_estimate_records.append(state_record)
                    last_forecasted_row_index = forecast_key
        if config.save_every_batch:
            _save_live_prediction_outputs(outdir, buffer, forecast_frames, state_estimate_records)

    _save_live_prediction_outputs(outdir, buffer, forecast_frames, state_estimate_records)
    forecasts = pd.concat(forecast_frames, ignore_index=True) if forecast_frames else pd.DataFrame()
    result = LivePredictionResult(
        outdir=str(outdir),
        n_batches=n_batches,
        n_samples_seen=n_samples_seen,
        n_clean_samples_buffered=int(buffer.summary()["n_clean_samples_buffered"]),
        n_forecast_origins=len(state_estimate_records),
        n_forecast_rows=len(forecasts),
        n_warnings=int(buffer.summary()["n_warnings"]),
        stream_type=config.stream_type,
        model_type=predictor.model_type,
    )
    summary = {
        "config": asdict(config),
        "result": asdict(result),
        "buffer": buffer.summary(),
        "predictor": predictor.to_summary(),
        "phase": "live_phase_2_online_forecasting_without_kalman_or_alerts",
    }
    (outdir / "live_prediction_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_provenance(outdir, config_path=config_path, extra={"command": "live-prediction", "result": asdict(result)})
    return result


def _save_live_prediction_outputs(
    outdir: Path,
    buffer: RollingLiveBuffer,
    forecast_frames: list[pd.DataFrame],
    state_estimate_records: list[dict[str, Any]],
) -> None:
    """Persist current live prediction state to disk."""

    buffer.save(outdir)
    forecasts = pd.concat(forecast_frames, ignore_index=True) if forecast_frames else pd.DataFrame()
    forecasts.to_csv(outdir / "live_forecasts.csv", index=False)
    forecast_frame_to_wide(forecasts).to_csv(outdir / "live_forecasts_wide.csv", index=False)
    pd.DataFrame(state_estimate_records).to_csv(outdir / "live_state_estimates.csv", index=False)
