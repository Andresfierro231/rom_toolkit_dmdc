"""Online forecast helpers for live ROM workflows.

Live Phase-2 intentionally keeps prediction separate from stream ingestion.
The streaming layer answers "what samples arrived?"; this module answers
"given the newest clean state/input sample, what does a saved ROM predict next?"

The class here is deliberately conservative:

* It loads a model that was trained and validated offline.
* It does **not** update or refit the model online.
* It assumes nonuniform/adaptive physical time when the saved model supports it.
* It falls back to sample-step forecasts for discrete DMD/DMDc/POD models, using
  an explicit ``discrete_dt_seconds`` value when physical horizons are requested.

This gives a safe intermediate step before adding Kalman filtering, residual
alerts, trust scores, or guarded online model adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence
import pickle

import joblib
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm

from .adaptive import AdaptiveDMDcModel
from .continuous import ContinuousDMDcModel
from .model import DMDcModel
from .regularized import RegularizedDMDcModel
from .reduced import PODDMDcPipeline

try:  # POD-ML is optional; importing may fail when sklearn is not installed.
    from .ml import PODDynamicsRegressor
except Exception:  # pragma: no cover - exercised only in minimal installs without sklearn
    PODDynamicsRegressor = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ForecastSettings:
    """Settings controlling live forecast horizons.

    Parameters
    ----------
    horizons_seconds:
        Physical-time horizons to forecast.  For continuous/adaptive models these
        are used directly.  For discrete models they are converted to integer
        sample steps using ``discrete_dt_seconds``.
    discrete_dt_seconds:
        Physical duration represented by one sample-to-sample step for discrete
        models.  If omitted, the predictor tries to read ``metadata_.dt`` from
        the model and otherwise falls back to 1.0.  In live loop work, prefer to
        set this explicitly if using a discrete model.
    """

    horizons_seconds: list[float]
    discrete_dt_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.horizons_seconds:
            raise ValueError("At least one forecast horizon is required.")
        if any(float(h) <= 0 for h in self.horizons_seconds):
            raise ValueError("Forecast horizons must be positive.")
        if self.discrete_dt_seconds is not None and float(self.discrete_dt_seconds) <= 0:
            raise ValueError("discrete_dt_seconds must be positive when supplied.")


@dataclass
class ForecastResult:
    """Forecast table plus metadata for one live-origin sample."""

    forecast_frame: pd.DataFrame
    model_type: str
    origin_time: float | None
    origin_row_index: int | None


class LivePredictor:
    """Wrapper around saved offline ROMs for fast online forecasts.

    Supported saved model objects include:

    * :class:`dmdc.adaptive.AdaptiveDMDcModel`
    * :class:`dmdc.model.DMDcModel`
    * :class:`dmdc.regularized.RegularizedDMDcModel`
    * :class:`dmdc.reduced.PODDMDcPipeline`
    * :class:`dmdc.ml.PODDynamicsRegressor` when optional ML dependencies exist
    * :class:`dmdc.continuous.ContinuousDMDcModel`

    The wrapper exposes a single :meth:`forecast` method that returns a tidy
    long-form table: one row per ``(forecast_origin, horizon, state)``.
    """

    def __init__(self, model: Any, *, model_path: str | Path | None = None, discrete_dt_seconds: float | None = None) -> None:
        self.model = model
        self.model_path = None if model_path is None else str(model_path)
        self.model_type = self._infer_model_type(model)
        self.state_names = self._infer_state_names(model)
        self.input_names = self._infer_input_names(model)
        self.discrete_dt_seconds = discrete_dt_seconds

    @classmethod
    def load(cls, path: str | Path, *, discrete_dt_seconds: float | None = None) -> "LivePredictor":
        """Load a saved model from joblib or pickle and wrap it for live forecasts."""

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Live model file not found: {p}")
        try:
            model = joblib.load(p)
        except Exception:
            with p.open("rb") as f:
                model = pickle.load(f)
        return cls(model, model_path=p, discrete_dt_seconds=discrete_dt_seconds)

    @property
    def n_states(self) -> int:
        return len(self.state_names) if self.state_names is not None else self._infer_n_states()

    @property
    def n_inputs(self) -> int:
        if self.input_names is not None:
            return len(self.input_names)
        return self._infer_n_inputs()

    def forecast(
        self,
        x_current: ArrayLike,
        u_current: ArrayLike | None,
        settings: ForecastSettings,
        *,
        origin_time: float | None = None,
        origin_row_index: int | None = None,
        received_utc: str | None = None,
    ) -> ForecastResult:
        """Forecast from the current measured/estimated state.

        Phase-2 uses the latest measured state directly.  Later phases can call
        this same method with a Kalman-filtered state estimate instead.
        """

        x = np.asarray(x_current, dtype=float).reshape(-1)
        if x.size != self.n_states:
            raise ValueError(f"x_current must have length {self.n_states}; got {x.size}.")
        u = self._prepare_current_input(u_current)
        rows: list[dict[str, Any]] = []
        for h in settings.horizons_seconds:
            pred, effective_h = self._forecast_one_horizon(x, u, float(h), settings)
            for idx, value in enumerate(pred):
                state = self.state_names[idx] if self.state_names is not None else f"x{idx}"
                rows.append(
                    {
                        "origin_time": origin_time,
                        "origin_row_index": origin_row_index,
                        "received_utc": received_utc,
                        "forecast_horizon_s": float(h),
                        "effective_horizon_s": float(effective_h),
                        "target_time": None if origin_time is None else float(origin_time) + float(h),
                        "effective_target_time": None if origin_time is None else float(origin_time) + float(effective_h),
                        "state": state,
                        "predicted_value": float(value),
                        "model_type": self.model_type,
                        "model_path": self.model_path,
                    }
                )
        return ForecastResult(
            forecast_frame=pd.DataFrame(rows),
            model_type=self.model_type,
            origin_time=origin_time,
            origin_row_index=origin_row_index,
        )

    def to_summary(self) -> dict[str, Any]:
        """Return JSON-serializable model metadata for live summaries."""

        return {
            "model_path": self.model_path,
            "model_type": self.model_type,
            "state_names": self.state_names,
            "input_names": self.input_names,
            "n_states": self.n_states,
            "n_inputs": self.n_inputs,
            "discrete_dt_seconds": self.discrete_dt_seconds,
            "notes": [
                "Live forecasts are generated from measured or filtered state vectors, depending on the calling workflow.",
                "This predictor never retrains the model online; monitoring/alerts are handled by Live Phase-4.",
            ],
        }

    # ------------------------------------------------------------------
    # Forecast implementations
    # ------------------------------------------------------------------
    def _forecast_one_horizon(
        self,
        x: NDArray[np.float64],
        u: NDArray[np.float64] | None,
        horizon_s: float,
        settings: ForecastSettings,
    ) -> tuple[NDArray[np.float64], float]:
        model = self.model
        if isinstance(model, AdaptiveDMDcModel):
            U = self._repeat_input(u, 1)
            pred = model.rollout(x, U_future=U, dt_future=np.asarray([horizon_s], dtype=float))[-1]
            return np.asarray(pred, dtype=float), horizon_s
        if isinstance(model, ContinuousDMDcModel):
            pred = self._continuous_step(model.A_c_, model.B_c_, x, u, horizon_s)
            return pred, horizon_s

        # Discrete/sample-to-sample models.  Convert physical seconds to a
        # number of sample steps using explicit or inferred dt.
        dt = self._discrete_dt(settings)
        n_steps = max(1, int(np.ceil(horizon_s / dt)))
        effective = n_steps * dt
        U = self._repeat_input(u, n_steps)
        if isinstance(model, PODDMDcPipeline):
            pred = model.rollout(x, U_future=U, n_steps=n_steps)[-1]
            return np.asarray(pred, dtype=float), effective
        if PODDynamicsRegressor is not None and isinstance(model, PODDynamicsRegressor):  # type: ignore[arg-type]
            pred = model.rollout(x, U_future=U, n_steps=n_steps)[-1]
            return np.asarray(pred, dtype=float), effective
        if isinstance(model, (DMDcModel, RegularizedDMDcModel)):
            pred = model.simulate(x, U_future=U, n_steps=n_steps)[-1]
            return np.asarray(pred, dtype=float), effective
        raise TypeError(
            f"Unsupported live prediction model type: {type(model)!r}. "
            "Use AdaptiveDMDcModel, DMDcModel, RegularizedDMDcModel, PODDMDcPipeline, "
            "PODDynamicsRegressor, or ContinuousDMDcModel."
        )

    def _continuous_step(
        self,
        A_c: NDArray[np.float64] | None,
        B_c: NDArray[np.float64] | None,
        x: NDArray[np.float64],
        u: NDArray[np.float64] | None,
        dt: float,
    ) -> NDArray[np.float64]:
        if A_c is None:
            raise RuntimeError("Continuous model has no A_c_ matrix.")
        A = np.asarray(A_c, dtype=float)
        if B_c is None or np.asarray(B_c).size == 0 or self.n_inputs == 0:
            return expm(A * dt) @ x
        B = np.asarray(B_c, dtype=float)
        u_vec = np.zeros(B.shape[1], dtype=float) if u is None else u
        n = A.shape[0]
        m = B.shape[1]
        aug = np.zeros((n + m, n + m), dtype=float)
        aug[:n, :n] = A
        aug[:n, n:] = B
        step = expm(aug * dt)
        return step[:n, :n] @ x + step[:n, n:] @ u_vec

    def _prepare_current_input(self, u_current: ArrayLike | None) -> NDArray[np.float64] | None:
        n_inputs = self.n_inputs
        if n_inputs == 0:
            return None
        if u_current is None:
            raise ValueError(f"This model expects {n_inputs} input(s), but u_current was None.")
        u = np.asarray(u_current, dtype=float).reshape(-1)
        if u.size != n_inputs:
            raise ValueError(f"u_current must have length {n_inputs}; got {u.size}.")
        return u

    def _repeat_input(self, u: NDArray[np.float64] | None, n_steps: int) -> NDArray[np.float64] | None:
        if self.n_inputs == 0:
            return None
        if u is None:
            raise ValueError("Internal error: missing current input for input-driven model.")
        return np.repeat(u.reshape(1, -1), int(n_steps), axis=0)

    def _discrete_dt(self, settings: ForecastSettings) -> float:
        if settings.discrete_dt_seconds is not None:
            return float(settings.discrete_dt_seconds)
        if self.discrete_dt_seconds is not None:
            return float(self.discrete_dt_seconds)
        metadata = getattr(self.model, "metadata_", None)
        dt = getattr(metadata, "dt", None)
        if dt is not None and float(dt) > 0:
            return float(dt)
        # POD-DMDc/POD-ML often do not store dt.  Use a clear fallback and record
        # effective_horizon_s in the forecast table so this approximation is visible.
        return 1.0

    # ------------------------------------------------------------------
    # Metadata inference helpers
    # ------------------------------------------------------------------
    def _infer_model_type(self, model: Any) -> str:
        if isinstance(model, AdaptiveDMDcModel):
            return "adaptive_dmdc"
        if isinstance(model, ContinuousDMDcModel):
            return "continuous_dmdc"
        if isinstance(model, RegularizedDMDcModel):
            return "ridge_dmdc"
        if isinstance(model, PODDMDcPipeline):
            return "pod_dmdc"
        if PODDynamicsRegressor is not None and isinstance(model, PODDynamicsRegressor):  # type: ignore[arg-type]
            return f"pod_ml_{getattr(model, 'model_type', 'unknown')}"
        if isinstance(model, DMDcModel):
            return "dmdc"
        return type(model).__name__

    def _infer_state_names(self, model: Any) -> list[str] | None:
        for attr in ("metadata_", "summary_"):
            meta = getattr(model, attr, None)
            names = getattr(meta, "state_names", None)
            if names is not None:
                return list(names)
        if isinstance(model, ContinuousDMDcModel):
            meta = getattr(model.discrete_model, "metadata_", None)
            names = getattr(meta, "state_names", None)
            if names is not None:
                return list(names)
        return None

    def _infer_input_names(self, model: Any) -> list[str] | None:
        for attr in ("metadata_", "summary_"):
            meta = getattr(model, attr, None)
            names = getattr(meta, "input_names", None)
            if names is not None:
                return list(names)
        if isinstance(model, ContinuousDMDcModel):
            meta = getattr(model.discrete_model, "metadata_", None)
            names = getattr(meta, "input_names", None)
            if names is not None:
                return list(names)
        return None

    def _infer_n_states(self) -> int:
        model = self.model
        for attr in ("metadata_", "summary_"):
            meta = getattr(model, attr, None)
            n = getattr(meta, "n_states", None)
            if n is not None:
                return int(n)
        if isinstance(model, ContinuousDMDcModel) and model.A_c_ is not None:
            return int(model.A_c_.shape[0])
        raise ValueError("Could not infer number of states from the loaded model. Provide a supported saved model.")

    def _infer_n_inputs(self) -> int:
        model = self.model
        for attr in ("metadata_", "summary_"):
            meta = getattr(model, attr, None)
            n = getattr(meta, "n_inputs", None)
            if n is not None:
                return int(n)
        if isinstance(model, ContinuousDMDcModel):
            if model.B_c_ is not None:
                return int(model.B_c_.shape[1])
            meta = getattr(model.discrete_model, "metadata_", None)
            n = getattr(meta, "n_inputs", None)
            if n is not None:
                return int(n)
        return 0


def forecast_frame_to_wide(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert long-form live forecasts to one row per origin/horizon.

    Long-form is better for logging and plotting.  The wide form is convenient
    for quick inspection, dashboards, and operator-facing tables.
    """

    if frame.empty:
        return pd.DataFrame()
    index_cols = [
        "origin_time",
        "origin_row_index",
        "received_utc",
        "forecast_horizon_s",
        "effective_horizon_s",
        "model_type",
        "model_path",
    ]
    wide = frame.pivot_table(
        index=index_cols,
        columns="state",
        values="predicted_value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    return wide
