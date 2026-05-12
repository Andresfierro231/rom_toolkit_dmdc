"""Optional machine-learning models for POD modal-coefficient dynamics.

This module deliberately keeps the repository's core philosophy intact:
POD is still an SVD-based basis, and DMD/DMDc remains the primary transparent
linear dynamics model.  The classes here are optional reduced-coordinate
surrogates that learn dynamics in POD coefficient space, for example

    [a_k, u_k] -> a_{k+1}

where ``a_k`` are POD modal coefficients and ``u_k`` are optional controls.
The learned ML model never replaces POD itself; it only acts after projection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import pickle
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .metrics import error_by_column, relative_frobenius_error, rmse
from .model import RankChoice
from .pod import PODBasis
from .utils import write_json


@dataclass
class PODMLSummary:
    """Serializable summary of a fitted POD-ML dynamics model."""

    model_type: str
    pod_rank_used: int
    n_states: int
    n_inputs: int
    n_modal_states: int
    n_trajectories: int
    recursive_rollout: bool
    state_names: list[str] | None
    input_names: list[str] | None
    no_input_model: bool


class PODDynamicsRegressor:
    """Optional scikit-learn dynamics model in POD modal-coordinate space.

    Parameters
    ----------
    pod_rank:
        POD rank choice. Integer means exact number of retained modes; float in ``(0, 1]`` means
        cumulative energy threshold; ``"full"`` keeps all available modes.
    model_type:
        One of ``"ridge"``, ``"random_forest"``, ``"gradient_boosting"``, or ``"mlp"``.
    center, scale:
        Preprocessing choices for the POD basis.
    recursive_rollout:
        If true, rollouts feed each predicted modal state back into the regressor. This is the
        usual dynamical-system interpretation and exposes rollout stability/generalization issues.
    model_kwargs:
        Optional keyword arguments passed to the underlying scikit-learn estimator.

    Notes
    -----
    The supervised learning problem is

        features = [a_k, u_k]
        target   = a_{k+1}

    where ``a_k`` are POD coefficients. When no inputs are supplied, the feature vector is simply
    ``a_k``.  This class is optional and intended for nonlinear reduced dynamics experiments; it is
    not a replacement for SVD/POD or DMD/DMDc.
    """

    def __init__(
        self,
        pod_rank: RankChoice = 0.999,
        *,
        model_type: str = "ridge",
        center: bool = True,
        scale: bool = False,
        recursive_rollout: bool = True,
        model_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.pod_rank = pod_rank
        self.model_type = model_type
        self.center = center
        self.scale = scale
        self.recursive_rollout = recursive_rollout
        self.model_kwargs = dict(model_kwargs or {})
        self.pod_: PODBasis | None = None
        self.regressor_: Any | None = None
        self.summary_: PODMLSummary | None = None

    def fit(
        self,
        X: ArrayLike,
        U: ArrayLike | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "PODDynamicsRegressor":
        """Fit from one full-state trajectory shaped ``(n_time, n_states)``."""

        return self.fit_trajectories([X], None if U is None else [U], state_names=state_names, input_names=input_names)

    def fit_trajectories(
        self,
        trajectories_X: Sequence[ArrayLike],
        trajectories_U: Sequence[ArrayLike | None] | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "PODDynamicsRegressor":
        """Fit from multiple independent trajectories/cases."""

        if not trajectories_X:
            raise ValueError("At least one trajectory is required.")
        X_list = [_as_2d_float(X, f"X[{i}]") for i, X in enumerate(trajectories_X)]
        n_states = X_list[0].shape[1]
        for i, X in enumerate(X_list):
            if X.shape[0] < 2:
                raise ValueError(f"Trajectory {i} has fewer than two snapshots.")
            if X.shape[1] != n_states:
                raise ValueError("All trajectories must have the same number of state columns.")

        if trajectories_U is None:
            U_list: list[NDArray[np.float64] | None] = [None] * len(X_list)
        else:
            if len(trajectories_U) != len(X_list):
                raise ValueError("trajectories_U must match trajectories_X length.")
            U_list = [None if U is None else _as_2d_float(U, f"U[{i}]") for i, U in enumerate(trajectories_U)]

        X_stack = np.vstack(X_list)
        self.pod_ = PODBasis(rank=self.pod_rank, center=self.center, scale=self.scale).fit(X_stack, state_names=state_names)
        A_list = [self.pod_.transform(X) for X in X_list]
        feature_blocks: list[NDArray[np.float64]] = []
        target_blocks: list[NDArray[np.float64]] = []
        n_inputs_expected: int | None = None
        for i, (A, U) in enumerate(zip(A_list, U_list, strict=True)):
            A0 = A[:-1]
            A1 = A[1:]
            U0 = _align_inputs(U, n_time=A.shape[0], name=f"U[{i}]")
            if n_inputs_expected is None:
                n_inputs_expected = U0.shape[1]
            elif U0.shape[1] != n_inputs_expected:
                raise ValueError("All input trajectories must have the same number of columns.")
            feature_blocks.append(np.hstack([A0, U0]) if U0.shape[1] else A0)
            target_blocks.append(A1)

        features = np.vstack(feature_blocks)
        targets = np.vstack(target_blocks)
        self.regressor_ = _make_regressor(self.model_type, self.model_kwargs)
        self.regressor_.fit(features, targets)
        self.summary_ = PODMLSummary(
            model_type=self.model_type,
            pod_rank_used=int(self.pod_.rank_ or 0),
            n_states=n_states,
            n_inputs=int(n_inputs_expected or 0),
            n_modal_states=int(self.pod_.rank_ or 0),
            n_trajectories=len(X_list),
            recursive_rollout=bool(self.recursive_rollout),
            state_names=state_names,
            input_names=input_names,
            no_input_model=int(n_inputs_expected or 0) == 0,
        )
        return self

    def transform(self, X: ArrayLike) -> NDArray[np.float64]:
        """Project full states into POD modal coefficients."""
        self._check_is_fit()
        return self.pod_.transform(X)  # type: ignore[union-attr]

    def reconstruct(self, modal_coefficients: ArrayLike) -> NDArray[np.float64]:
        """Reconstruct full states from modal coefficients."""
        self._check_is_fit()
        return self.pod_.inverse_transform(modal_coefficients)  # type: ignore[union-attr]

    def predict_next(self, a: ArrayLike, u: ArrayLike | None = None) -> NDArray[np.float64]:
        """Predict the next modal coefficient vector(s)."""
        self._check_is_fit()
        A = _as_2d_float(a, "a")
        U = self._prepare_input(u, A.shape[0])
        features = np.hstack([A, U]) if U.shape[1] else A
        pred = np.asarray(self.regressor_.predict(features), dtype=float)  # type: ignore[union-attr]
        if pred.ndim == 1:
            pred = pred.reshape(-1, 1)
        return pred

    def rollout(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        """Recursively roll out the reduced ML dynamics and reconstruct full states."""
        self._check_is_fit()
        x0_arr = np.asarray(x0, dtype=float).reshape(1, -1)
        if x0_arr.shape[1] != self.summary_.n_states:  # type: ignore[union-attr]
            raise ValueError(f"x0 must have length {self.summary_.n_states}; got {x0_arr.shape[1]}.")  # type: ignore[union-attr]
        n_inputs = self.summary_.n_inputs  # type: ignore[union-attr]
        if U_future is None:
            if n_steps is None:
                raise ValueError("Provide n_steps when U_future is None.")
            U_arr = np.zeros((n_steps, n_inputs), dtype=float)
        else:
            U_arr = _as_2d_float(U_future, "U_future")
            if U_arr.shape[1] != n_inputs:
                raise ValueError(f"U_future must have {n_inputs} columns; got {U_arr.shape[1]}.")
            if n_steps is not None and U_arr.shape[0] != n_steps:
                raise ValueError("n_steps must match U_future rows when both are provided.")
            n_steps = U_arr.shape[0]

        a = self.transform(x0_arr)
        modal = np.zeros((int(n_steps) + 1, a.shape[1]), dtype=float)
        modal[0] = a.reshape(-1)
        for k in range(int(n_steps)):
            u = U_arr[k : k + 1, :] if n_inputs else None
            a = self.predict_next(a, u)
            modal[k + 1] = a.reshape(-1)
        return self.reconstruct(modal)

    def evaluate_trajectory(self, X: ArrayLike, U: ArrayLike | None = None, *, state_names: list[str] | None = None) -> dict[str, Any]:
        """Evaluate recursive rollout error on one trajectory."""
        X_arr = _as_2d_float(X, "X")
        U_arr = None if U is None else _as_2d_float(U, "U")
        U_future = None
        if U_arr is not None and U_arr.shape[1] > 0:
            U_future = U_arr[:-1] if U_arr.shape[0] == X_arr.shape[0] else U_arr
        rollout = self.rollout(X_arr[0], U_future=U_future, n_steps=X_arr.shape[0] - 1)
        names = state_names or (self.summary_.state_names if self.summary_ else None)
        return {
            "rmse": rmse(X_arr, rollout),
            "relative_frobenius_error": relative_frobenius_error(X_arr, rollout),
            "by_state": error_by_column(X_arr, rollout, names),
        }

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable metadata."""
        self._check_is_fit()
        return {
            "summary": asdict(self.summary_),  # type: ignore[arg-type]
            "pod": self.pod_.to_summary(),  # type: ignore[union-attr]
            "model_kwargs": self.model_kwargs,
            "philosophy": "Optional ML in POD coefficient space; SVD/POD remains the basis construction method.",
        }

    def save(self, path: str | Path) -> None:
        """Save the fitted POD-ML model with the standard-library pickle module.

        The ML estimators themselves are optional scikit-learn objects, but saving/loading does
        not require joblib. This keeps the package importable even when users install only the
        non-ML core dependencies.
        """
        self._check_is_fit()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "PODDynamicsRegressor":
        """Load a saved PODDynamicsRegressor."""
        with Path(path).open("rb") as f:
            obj = pickle.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Expected PODDynamicsRegressor, got {type(obj)!r}.")
        return obj

    def save_outputs(
        self,
        X: ArrayLike,
        U: ArrayLike | None,
        outdir: str | Path,
        *,
        time: ArrayLike | None = None,
        state_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save model, summaries, modal coefficients, rollout, and reconstructed predictions."""
        self._check_is_fit()
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        X_arr = _as_2d_float(X, "X")
        U_arr = None if U is None else _as_2d_float(U, "U")
        U_future = None
        if U_arr is not None and U_arr.shape[1] > 0:
            U_future = U_arr[:-1] if U_arr.shape[0] == X_arr.shape[0] else U_arr
        rollout = self.rollout(X_arr[0], U_future=U_future, n_steps=X_arr.shape[0] - 1)
        coeffs = self.transform(X_arr)
        pred_coeffs = self.transform(rollout)
        names = state_names or (self.summary_.state_names if self.summary_ else None) or [f"x{i}" for i in range(X_arr.shape[1])]

        self.save(out / "pod_ml_model.pkl")
        write_json(self.to_dict(), out / "pod_ml_summary.json")
        diagnostics = {
            "rollout_rmse": rmse(X_arr, rollout),
            "rollout_relative_frobenius_error": relative_frobenius_error(X_arr, rollout),
            "error_by_state": error_by_column(X_arr, rollout, names),
        }
        write_json(diagnostics, out / "diagnostics.json")
        coeff_df = pd.DataFrame(coeffs, columns=[f"a{i+1}" for i in range(coeffs.shape[1])])
        pred_coeff_df = pd.DataFrame(pred_coeffs, columns=[f"pred_a{i+1}" for i in range(pred_coeffs.shape[1])])
        pred_df = pd.DataFrame(rollout, columns=[f"pred_{c}" for c in names])
        if time is not None:
            t = np.asarray(time)
            coeff_df.insert(0, "time", t)
            pred_coeff_df.insert(0, "time", t)
            pred_df.insert(0, "time", t)
        coeff_df.to_csv(out / "modal_coefficients.csv", index=False)
        pred_coeff_df.to_csv(out / "modal_predictions.csv", index=False)
        pred_df.to_csv(out / "reconstructed_predictions.csv", index=False)
        return diagnostics

    def _prepare_input(self, u: ArrayLike | None, n_rows: int) -> NDArray[np.float64]:
        n_inputs = self.summary_.n_inputs  # type: ignore[union-attr]
        if u is None:
            if n_inputs == 0:
                return np.zeros((n_rows, 0), dtype=float)
            raise ValueError(f"This POD-ML model expects {n_inputs} input columns; u cannot be None.")
        U = _as_2d_float(u, "u")
        if U.shape != (n_rows, n_inputs):
            raise ValueError(f"u must have shape {(n_rows, n_inputs)}; got {U.shape}.")
        return U

    def _check_is_fit(self) -> None:
        if self.pod_ is None or self.regressor_ is None or self.summary_ is None:
            raise RuntimeError("PODDynamicsRegressor is not fit yet.")


def _make_regressor(model_type: str, kwargs: dict[str, Any]):
    """Create a scikit-learn regressor with a helpful optional-dependency error."""

    try:
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.linear_model import Ridge
        from sklearn.multioutput import MultiOutputRegressor
        from sklearn.neural_network import MLPRegressor
    except Exception as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "POD-ML requires scikit-learn. Install with `pip install dmdc-analysis[ml]` or `pip install scikit-learn`, or use POD-DMDc instead."
        ) from exc

    key = model_type.lower().replace("-", "_")
    if key == "ridge":
        return Ridge(**{"alpha": 1.0, **kwargs})
    if key in {"random_forest", "rf"}:
        return RandomForestRegressor(**{"n_estimators": 100, "random_state": 0, **kwargs})
    if key in {"gradient_boosting", "gb"}:
        return MultiOutputRegressor(GradientBoostingRegressor(**{"random_state": 0, **kwargs}))
    if key == "mlp":
        return MLPRegressor(**{"hidden_layer_sizes": (64, 64), "max_iter": 1000, "random_state": 0, **kwargs})
    raise ValueError(f"Unsupported POD-ML model_type={model_type!r}. Use ridge, random_forest, gradient_boosting, or mlp.")


def _align_inputs(U: NDArray[np.float64] | None, *, n_time: int, name: str) -> NDArray[np.float64]:
    if U is None:
        return np.zeros((n_time - 1, 0), dtype=float)
    if U.shape[0] == n_time:
        return U[:-1]
    if U.shape[0] == n_time - 1:
        return U
    raise ValueError(f"{name} must have either {n_time} rows or {n_time - 1} rows; got {U.shape[0]}.")


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 1D or 2D; got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
