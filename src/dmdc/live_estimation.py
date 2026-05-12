"""Live Phase-3: POD-Kalman state estimation for streaming ROM workflows.

This module adds the first online *state estimation* layer on top of the Phase-1
stream adapters and Phase-2 live forecast tools.  The intended workflow is:

1. Train and validate a POD-DMDc model offline.
2. Save the fitted ``PODDMDcPipeline`` object.
3. Stream a subset of measured state columns from the loop.
4. Use a POD-space Kalman filter to estimate the full state.
5. Optionally forecast from the filtered full-state estimate.

The estimator is deliberately conservative: it does **not** retrain the ROM, it
does **not** issue model-trust alerts yet, and it does **not** perform control.
It only combines a validated reduced model with live measurements to produce a
cleaner current-state estimate and uncertainty metadata.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import shutil

import joblib
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .live_buffer import RollingLiveBuffer
from .live_predictor import ForecastSettings, LivePredictor, forecast_frame_to_wide
from .provenance import write_provenance
from .reduced import PODDMDcPipeline
from .streaming import make_stream_adapter, run_stream_until_done


@dataclass
class PODKalmanEstimatorSettings:
    """Noise/covariance settings for the live POD-Kalman estimator.

    Parameters
    ----------
    process_noise:
        Scalar process-noise level used as ``Q = process_noise * I`` in modal
        coordinates.  Larger values let the estimate move away from the ROM
        prediction more easily.
    measurement_noise:
        Scalar measurement-noise level used as ``R = measurement_noise * I`` in
        physical measurement units.  Larger values make the filter trust sensors
        less and the ROM prediction more.
    initial_covariance:
        Initial modal covariance scalar.  Larger values mean the first few
        measurements are trusted more strongly.
    """

    process_noise: float = 1.0e-6
    measurement_noise: float = 1.0e-3
    initial_covariance: float = 1.0

    def __post_init__(self) -> None:
        if self.process_noise < 0:
            raise ValueError("process_noise must be nonnegative.")
        if self.measurement_noise <= 0:
            raise ValueError("measurement_noise must be positive.")
        if self.initial_covariance <= 0:
            raise ValueError("initial_covariance must be positive.")


@dataclass
class PODKalmanUpdate:
    """One online POD-Kalman update result."""

    modal_state: NDArray[np.float64]
    full_state: NDArray[np.float64]
    covariance: NDArray[np.float64]
    predicted_measurement: NDArray[np.float64]
    innovation: NDArray[np.float64]
    kalman_gain: NDArray[np.float64]
    covariance_trace: float
    innovation_norm: float
    initialized_from_measurement: bool


class LivePODKalmanEstimator:
    """Online POD-space Kalman estimator for a saved ``PODDMDcPipeline``.

    The offline POD-DMDc model evolves modal coefficients,

    ``a[k+1] = A_r a[k] + B_r u[k]``.

    Live sensors observe a subset of full-state variables,

    ``y[k] = C x[k] + v[k]``.

    The POD reconstruction is

    ``x[k] = mean + diag(scale) Phi a[k]``.

    Therefore the measurement equation in modal coordinates is

    ``y[k] = mean_selected + H a[k] + v[k]``

    with ``H = diag(scale_selected) Phi_selected``.
    """

    def __init__(
        self,
        model: PODDMDcPipeline,
        *,
        measurement_cols: list[str],
        state_cols: list[str] | None = None,
        input_cols: list[str] | None = None,
        settings: PODKalmanEstimatorSettings | None = None,
    ) -> None:
        if not isinstance(model, PODDMDcPipeline):
            raise TypeError("LivePODKalmanEstimator currently requires a saved PODDMDcPipeline model.")
        model._check_is_fit()  # type: ignore[attr-defined]
        self.model = model
        self.pod = model.pod_
        self.reduced_model = model.model_
        if self.pod is None or self.reduced_model is None:
            raise RuntimeError("POD-DMDc model is not fitted.")
        inferred_state_cols = model.summary_.state_names if model.summary_ else None
        if inferred_state_cols is None:
            inferred_state_cols = self.pod.state_names_
        if inferred_state_cols is None:
            inferred_state_cols = [f"x{i}" for i in range(self.pod.modes_.shape[0])]  # type: ignore[union-attr]
        self.state_cols = list(state_cols or inferred_state_cols)
        self.input_cols = list(input_cols or (model.summary_.input_names if model.summary_ and model.summary_.input_names else []))
        self.measurement_cols = list(measurement_cols)
        if not self.measurement_cols:
            raise ValueError("At least one measurement column is required for live Kalman estimation.")
        self.settings = settings or PODKalmanEstimatorSettings()

        state_to_index = {name: i for i, name in enumerate(self.state_cols)}
        missing = [name for name in self.measurement_cols if name not in state_to_index]
        if missing:
            raise ValueError(f"measurement_cols must be a subset of model state columns; missing {missing!r}.")
        self.selected_indices = [state_to_index[name] for name in self.measurement_cols]

        self.A = np.asarray(self.reduced_model.A_, dtype=float)
        B = self.reduced_model.B_
        self.B = np.zeros((self.A.shape[0], 0), dtype=float) if B is None else np.asarray(B, dtype=float)
        self.n_modal = self.A.shape[0]
        self.n_inputs = self.B.shape[1]
        self.H = self._make_observation_matrix()
        self.measurement_mean = np.asarray(self.pod.mean_, dtype=float)[self.selected_indices]

        self.Q = np.eye(self.n_modal) * float(self.settings.process_noise)
        self.R = np.eye(len(self.measurement_cols)) * float(self.settings.measurement_noise)
        self.P = np.eye(self.n_modal) * float(self.settings.initial_covariance)
        self.a: NDArray[np.float64] | None = None
        self.n_updates = 0

    @classmethod
    def load(
        cls,
        model_path: str | Path,
        *,
        measurement_cols: list[str],
        state_cols: list[str] | None = None,
        input_cols: list[str] | None = None,
        settings: PODKalmanEstimatorSettings | None = None,
    ) -> "LivePODKalmanEstimator":
        """Load a saved POD-DMDc model and create an online estimator."""

        model = joblib.load(Path(model_path))
        return cls(model, measurement_cols=measurement_cols, state_cols=state_cols, input_cols=input_cols, settings=settings)

    def update(self, measurements: NDArray[np.float64], inputs: NDArray[np.float64] | None = None) -> PODKalmanUpdate:
        """Assimilate one measurement vector and return the filtered full state."""

        y = np.asarray(measurements, dtype=float).reshape(-1)
        if y.size != len(self.measurement_cols):
            raise ValueError(f"Expected {len(self.measurement_cols)} measurements, got {y.size}.")
        u = self._prepare_input(inputs)
        initialized = False

        if self.a is None:
            # Initialize modal coefficients from the first sparse measurement by
            # least-squares projection.  This is an estimate, not a guarantee of
            # exact full-state reconstruction when only a few sensors are present.
            self.a = np.linalg.pinv(self.H) @ (y - self.measurement_mean)
            initialized = True
        else:
            self.a = self.A @ self.a + (self.B @ u if self.n_inputs else 0.0)
            self.P = self.A @ self.P @ self.A.T + self.Q

        y_pred = self.measurement_mean + self.H @ self.a
        innovation = y - y_pred
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.pinv(S)
        self.a = self.a + K @ innovation
        I = np.eye(self.n_modal)
        # Joseph form is more numerically robust, but this simplified update is
        # adequate for the small reduced systems used in this repo.
        self.P = (I - K @ self.H) @ self.P

        full = self.pod.inverse_transform(self.a.reshape(1, -1)).reshape(-1)
        self.n_updates += 1
        return PODKalmanUpdate(
            modal_state=self.a.copy(),
            full_state=np.asarray(full, dtype=float),
            covariance=self.P.copy(),
            predicted_measurement=y_pred.copy(),
            innovation=innovation.copy(),
            kalman_gain=K.copy(),
            covariance_trace=float(np.trace(self.P)),
            innovation_norm=float(np.linalg.norm(innovation)),
            initialized_from_measurement=initialized,
        )

    def to_summary(self) -> dict[str, Any]:
        """Return JSON-serializable estimator metadata."""

        return {
            "estimator_type": "pod_kalman",
            "state_cols": self.state_cols,
            "measurement_cols": self.measurement_cols,
            "input_cols": self.input_cols,
            "selected_indices": self.selected_indices,
            "n_modal_states": self.n_modal,
            "n_inputs": self.n_inputs,
            "settings": asdict(self.settings),
            "n_updates": self.n_updates,
            "notes": [
                "Phase-3 estimates the current state with POD-space Kalman filtering.",
                "It does not retrain the ROM online and does not issue residual alerts yet.",
            ],
        }

    def _make_observation_matrix(self) -> NDArray[np.float64]:
        modes = np.asarray(self.pod.modes_, dtype=float)
        scale = np.asarray(self.pod.scale_, dtype=float)
        # PODBasis reconstructs x = mean + (a Phi^T) * scale.  For selected rows,
        # y = mean_selected + diag(scale_selected) Phi_selected a.
        return scale[self.selected_indices, None] * modes[self.selected_indices, :]

    def _prepare_input(self, inputs: NDArray[np.float64] | None) -> NDArray[np.float64]:
        if self.n_inputs == 0:
            return np.zeros(0, dtype=float)
        if inputs is None:
            raise ValueError("This estimator's reduced model expects inputs, but no input vector was provided.")
        u = np.asarray(inputs, dtype=float).reshape(-1)
        if u.size != self.n_inputs:
            raise ValueError(f"Expected {self.n_inputs} inputs, got {u.size}.")
        return u


@dataclass
class LiveEstimationConfig:
    """Configuration for live replay/tail POD-Kalman state estimation."""

    stream_type: str
    path: str
    model_path: str
    measurement_cols: list[str]
    state_cols: list[str] | None = None
    input_cols: list[str] | None = None
    time_col: str | None = None
    case_col: str | None = None
    case_id: str | int | float | None = None
    outdir: str = "outputs/live_estimation"
    chunk_size: int = 1
    poll_seconds: float = 0.0
    max_samples: int | None = None
    max_polls: int | None = None
    buffer_seconds: float | None = None
    buffer_max_samples: int | None = None
    start_at_end: bool = False
    save_every_batch: bool = False
    process_noise: float = 1.0e-6
    measurement_noise: float = 1.0e-3
    initial_covariance: float = 1.0
    forecast_horizons_seconds: list[float] | None = None
    discrete_dt_seconds: float | None = None


@dataclass
class LiveEstimationResult:
    """Summary returned by :func:`run_live_estimation`."""

    outdir: str
    n_batches: int
    n_samples_seen: int
    n_clean_samples_buffered: int
    n_estimate_updates: int
    n_forecast_rows: int
    n_warnings: int
    stream_type: str
    estimator_type: str
    model_type: str


def run_live_estimation(config: LiveEstimationConfig, *, config_path: str | Path | None = None) -> LiveEstimationResult:
    """Run live/replay ingestion plus POD-Kalman state estimation.

    The stream only needs to contain ``measurement_cols`` and ``input_cols``.
    The saved model can contain a larger full state; the estimator reconstructs
    that full state from the sparse measurements.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if config_path is not None:
        try:
            shutil.copyfile(config_path, outdir / "config_used.toml")
        except OSError:
            pass

    input_cols = list(config.input_cols or [])
    adapter = make_stream_adapter(
        stream_type=config.stream_type,
        path=config.path,
        chunk_size=config.chunk_size,
        start_at_end=config.start_at_end,
        case_col=config.case_col,
        case_id=config.case_id,
        time_col=config.time_col,
    )
    # For sparse-state estimation the live buffer validates the actually
    # measured state columns, not the full hidden/model state.
    buffer = RollingLiveBuffer(
        state_cols=list(config.measurement_cols),
        input_cols=input_cols,
        time_col=config.time_col,
        case_col=config.case_col,
        buffer_seconds=config.buffer_seconds,
        max_samples=config.buffer_max_samples,
    )
    settings = PODKalmanEstimatorSettings(
        process_noise=float(config.process_noise),
        measurement_noise=float(config.measurement_noise),
        initial_covariance=float(config.initial_covariance),
    )
    estimator = LivePODKalmanEstimator.load(
        config.model_path,
        measurement_cols=list(config.measurement_cols),
        state_cols=list(config.state_cols) if config.state_cols else None,
        input_cols=input_cols,
        settings=settings,
    )
    predictor = LivePredictor.load(config.model_path, discrete_dt_seconds=config.discrete_dt_seconds)
    forecast_settings = ForecastSettings(
        horizons_seconds=list(config.forecast_horizons_seconds or []),
        discrete_dt_seconds=config.discrete_dt_seconds,
    ) if config.forecast_horizons_seconds else None

    state_records: list[dict[str, Any]] = []
    modal_records: list[dict[str, Any]] = []
    covariance_records: list[dict[str, Any]] = []
    innovation_records: list[dict[str, Any]] = []
    forecast_frames: list[pd.DataFrame] = []
    n_batches = 0
    n_samples_seen = 0
    last_estimated_row_index: int | None = None

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
            estimate_key = int(row_index) if row_index is not None else len(clean)
            if estimate_key != last_estimated_row_index:
                y = np.asarray([latest[c] for c in config.measurement_cols], dtype=float)
                u = np.asarray([latest[c] for c in input_cols], dtype=float) if input_cols else None
                update = estimator.update(y, u)
                origin_time = float(latest[config.time_col]) if config.time_col and latest.get(config.time_col) is not None else None
                origin_row = None if row_index is None else int(row_index)
                received = latest.get("_received_utc")
                _append_estimation_records(
                    state_records,
                    modal_records,
                    covariance_records,
                    innovation_records,
                    estimator,
                    update,
                    origin_time=origin_time,
                    origin_row_index=origin_row,
                    received_utc=received,
                    measurements=y,
                    inputs=u,
                )
                if forecast_settings is not None:
                    forecast = predictor.forecast(
                        update.full_state,
                        u,
                        forecast_settings,
                        origin_time=origin_time,
                        origin_row_index=origin_row,
                        received_utc=received,
                    )
                    # Mark that this forecast was produced from the filtered
                    # state estimate rather than the raw measurement vector.
                    frame = forecast.forecast_frame.copy()
                    if not frame.empty:
                        frame["forecast_origin_type"] = "pod_kalman_filtered_state"
                    forecast_frames.append(frame)
                last_estimated_row_index = estimate_key
        if config.save_every_batch:
            _save_live_estimation_outputs(outdir, buffer, state_records, modal_records, covariance_records, innovation_records, forecast_frames)

    _save_live_estimation_outputs(outdir, buffer, state_records, modal_records, covariance_records, innovation_records, forecast_frames)
    forecasts = pd.concat(forecast_frames, ignore_index=True) if forecast_frames else pd.DataFrame()
    result = LiveEstimationResult(
        outdir=str(outdir),
        n_batches=n_batches,
        n_samples_seen=n_samples_seen,
        n_clean_samples_buffered=int(buffer.summary()["n_clean_samples_buffered"]),
        n_estimate_updates=len(state_records),
        n_forecast_rows=len(forecasts),
        n_warnings=int(buffer.summary()["n_warnings"]),
        stream_type=config.stream_type,
        estimator_type="pod_kalman",
        model_type="PODDMDcPipeline",
    )
    summary = {
        "config": asdict(config),
        "result": asdict(result),
        "buffer": buffer.summary(),
        "estimator": estimator.to_summary(),
        "phase": "live_phase_3_pod_kalman_state_estimation_without_alerts_or_online_retraining",
    }
    (outdir / "live_estimation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_provenance(outdir, config_path=config_path, extra={"command": "live-estimation", "result": asdict(result)})
    return result


def _append_estimation_records(
    state_records: list[dict[str, Any]],
    modal_records: list[dict[str, Any]],
    covariance_records: list[dict[str, Any]],
    innovation_records: list[dict[str, Any]],
    estimator: LivePODKalmanEstimator,
    update: PODKalmanUpdate,
    *,
    origin_time: float | None,
    origin_row_index: int | None,
    received_utc: str | None,
    measurements: NDArray[np.float64],
    inputs: NDArray[np.float64] | None,
) -> None:
    base: dict[str, Any] = {
        "origin_time": origin_time,
        "origin_row_index": origin_row_index,
        "received_utc": received_utc,
        "estimator_type": "pod_kalman",
        "covariance_trace": update.covariance_trace,
        "innovation_norm": update.innovation_norm,
        "initialized_from_measurement": bool(update.initialized_from_measurement),
    }
    state_record = dict(base)
    for name, value in zip(estimator.state_cols, update.full_state, strict=True):
        state_record[name] = float(value)
    if inputs is not None:
        for name, value in zip(estimator.input_cols, inputs, strict=True):
            state_record[name] = float(value)
    state_records.append(state_record)

    modal_record = dict(base)
    for i, value in enumerate(update.modal_state, start=1):
        modal_record[f"a{i}"] = float(value)
    modal_records.append(modal_record)

    cov_record = dict(base)
    for i, value in enumerate(np.diag(update.covariance), start=1):
        cov_record[f"var_a{i}"] = float(value)
    covariance_records.append(cov_record)

    for name, measured, predicted, innov in zip(
        estimator.measurement_cols,
        measurements,
        update.predicted_measurement,
        update.innovation,
        strict=True,
    ):
        row = dict(base)
        row.update(
            {
                "measurement": name,
                "measured_value": float(measured),
                "predicted_measurement": float(predicted),
                "innovation": float(innov),
            }
        )
        innovation_records.append(row)


def _save_live_estimation_outputs(
    outdir: Path,
    buffer: RollingLiveBuffer,
    state_records: list[dict[str, Any]],
    modal_records: list[dict[str, Any]],
    covariance_records: list[dict[str, Any]],
    innovation_records: list[dict[str, Any]],
    forecast_frames: list[pd.DataFrame],
) -> None:
    """Persist current live-estimation state to disk."""

    buffer.save(outdir)
    pd.DataFrame(state_records).to_csv(outdir / "live_state_estimates.csv", index=False)
    pd.DataFrame(modal_records).to_csv(outdir / "live_modal_estimates.csv", index=False)
    pd.DataFrame(covariance_records).to_csv(outdir / "live_estimate_covariance.csv", index=False)
    pd.DataFrame(innovation_records).to_csv(outdir / "live_kalman_innovations.csv", index=False)
    forecasts = pd.concat(forecast_frames, ignore_index=True) if forecast_frames else pd.DataFrame()
    forecasts.to_csv(outdir / "live_forecasts.csv", index=False)
    forecast_frame_to_wide(forecasts).to_csv(outdir / "live_forecasts_wide.csv", index=False)
