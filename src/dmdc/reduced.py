"""POD-based reduced-order modeling pipelines.

This module keeps the repo's main philosophy explicit:
POD is an SVD-based projection layer, while DMD/DMDc supplies the transparent
linear dynamics in the reduced coordinates.  Optional ML models can be added
later, but they should operate on modal coefficients rather than replacing POD.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .model import DMDcModel, RankChoice
from .pod import PODBasis
from .metrics import rmse, relative_frobenius_error, error_by_column
from .utils import write_json


@dataclass
class PODDMDcSummary:
    """Serializable summary of a POD-DMDc fit."""

    pod_rank_used: int
    dmdc_rank_used: int
    n_states: int
    n_inputs: int
    n_modal_states: int
    n_trajectories: int
    state_names: list[str] | None
    input_names: list[str] | None
    no_input_dmd: bool


class PODDMDcPipeline:
    """POD projection followed by DMD/DMDc in modal-coordinate space.

    Parameters
    ----------
    pod_rank:
        POD rank choice. Integer means exact number of retained modes; float in ``(0, 1]`` means
        cumulative POD energy threshold; ``"full"`` keeps all available modes.
    dmdc_rank:
        SVD truncation rank used by the reduced DMD/DMDc model.
    center, scale:
        Preprocessing for the POD basis. Centering is normally recommended for POD.

    Notes
    -----
    This class fits

    ``a_{k+1} ≈ A_r a_k + B_r u_k``

    where ``a_k`` are POD modal coefficients. If no inputs are supplied, it reduces to POD-DMD:

    ``a_{k+1} ≈ A_r a_k``.
    """

    def __init__(
        self,
        pod_rank: RankChoice = 0.999,
        dmdc_rank: RankChoice = "full",
        *,
        center: bool = True,
        scale: bool = False,
        n_delays: int = 1,
    ) -> None:
        if n_delays != 1:
            raise NotImplementedError(
                "PODDMDcPipeline currently supports n_delays=1. Use the existing fit --n-delays path for delay-DMDc, or add delay embedding before POD explicitly."
            )
        self.pod_rank = pod_rank
        self.dmdc_rank = dmdc_rank
        self.center = center
        self.scale = scale
        self.n_delays = n_delays
        self.pod_: PODBasis | None = None
        self.model_: DMDcModel | None = None
        self.summary_: PODDMDcSummary | None = None

    def fit(
        self,
        X: ArrayLike,
        U: ArrayLike | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "PODDMDcPipeline":
        """Fit POD-DMDc from a single trajectory shaped ``(n_time, n_states)``."""

        return self.fit_trajectories([X], None if U is None else [U], state_names=state_names, input_names=input_names)

    def fit_trajectories(
        self,
        trajectories_X: Sequence[ArrayLike],
        trajectories_U: Sequence[ArrayLike | None] | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "PODDMDcPipeline":
        """Fit POD-DMDc from multiple independent trajectories/cases."""

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
        modal_names = [f"a{i+1}" for i in range(self.pod_.rank_ or A_list[0].shape[1])]
        self.model_ = DMDcModel(rank=self.dmdc_rank, center=False, scale=False).fit_trajectories(
            A_list,
            U_list,
            state_names=modal_names,
            input_names=input_names,
        )
        self.summary_ = PODDMDcSummary(
            pod_rank_used=int(self.pod_.rank_ or 0),
            dmdc_rank_used=int(self.model_.metadata_.rank_used),
            n_states=n_states,
            n_inputs=int(self.model_.metadata_.n_inputs),
            n_modal_states=int(self.pod_.rank_ or 0),
            n_trajectories=len(X_list),
            state_names=state_names,
            input_names=input_names,
            no_input_dmd=int(self.model_.metadata_.n_inputs) == 0,
        )
        return self

    def transform(self, X: ArrayLike) -> NDArray[np.float64]:
        """Project full states into POD modal coordinates."""
        self._check_is_fit()
        return self.pod_.transform(X)  # type: ignore[union-attr]

    def reconstruct(self, modal_coefficients: ArrayLike) -> NDArray[np.float64]:
        """Reconstruct full states from modal coefficients."""
        self._check_is_fit()
        return self.pod_.inverse_transform(modal_coefficients)  # type: ignore[union-attr]

    def predict_one_step(self, X: ArrayLike, U: ArrayLike | None = None) -> NDArray[np.float64]:
        """Predict one full-state step ahead for each row of ``X``."""
        self._check_is_fit()
        A = self.transform(X)
        A_next = self.model_.predict_one_step(A, U)  # type: ignore[union-attr]
        return self.reconstruct(A_next)

    def rollout(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        """Roll out the reduced model and reconstruct the full state trajectory."""
        self._check_is_fit()
        x0_arr = np.asarray(x0, dtype=float).reshape(1, -1)
        a0 = self.transform(x0_arr).reshape(-1)
        A_roll = self.model_.simulate(a0, U_future=U_future, n_steps=n_steps)  # type: ignore[union-attr]
        return self.reconstruct(A_roll)

    def evaluate_trajectory(self, X: ArrayLike, U: ArrayLike | None = None, *, state_names: list[str] | None = None) -> dict[str, Any]:
        """Evaluate rollout error on one trajectory."""
        X_arr = _as_2d_float(X, "X")
        U_arr = None if U is None else _as_2d_float(U, "U")
        U_future = None
        if U_arr is not None and U_arr.shape[1] > 0:
            U_future = U_arr[:-1] if U_arr.shape[0] == X_arr.shape[0] else U_arr
        rollout = self.rollout(X_arr[0], U_future=U_future, n_steps=X_arr.shape[0] - 1)
        names = state_names or self.summary_.state_names if self.summary_ else None
        return {
            "rmse": rmse(X_arr, rollout),
            "relative_frobenius_error": relative_frobenius_error(X_arr, rollout),
            "by_state": error_by_column(X_arr, rollout, names),
        }

    @property
    def eigenvalues_(self) -> NDArray[np.complex128]:
        self._check_is_fit()
        return self.model_.eigenvalues_  # type: ignore[union-attr]

    def to_dict(self) -> dict[str, Any]:
        self._check_is_fit()
        return {
            "summary": asdict(self.summary_),  # type: ignore[arg-type]
            "pod": self.pod_.to_summary(),  # type: ignore[union-attr]
            "reduced_dmdc": self.model_.to_dict(),  # type: ignore[union-attr]
        }

    def save(self, path: str | Path) -> None:
        self._check_is_fit()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: str | Path) -> "PODDMDcPipeline":
        obj = joblib.load(Path(path))
        if not isinstance(obj, cls):
            raise TypeError(f"Expected PODDMDcPipeline, got {type(obj)!r}.")
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
        coeffs = self.transform(X_arr)
        U_future = None
        if U_arr is not None and U_arr.shape[1] > 0:
            U_future = U_arr[:-1] if U_arr.shape[0] == X_arr.shape[0] else U_arr
        rollout = self.rollout(X_arr[0], U_future=U_future, n_steps=X_arr.shape[0] - 1)
        modal_rollout = self.transform(rollout)
        names = state_names or (self.summary_.state_names if self.summary_ else None) or [f"x{i}" for i in range(X_arr.shape[1])]

        self.save(out / "pod_dmdc_model.pkl")
        write_json(self.to_dict(), out / "pod_dmdc_summary.json")
        diagnostics = {
            "rollout_rmse": rmse(X_arr, rollout),
            "rollout_relative_frobenius_error": relative_frobenius_error(X_arr, rollout),
            "error_by_state": error_by_column(X_arr, rollout, names),
        }
        write_json(diagnostics, out / "diagnostics.json")

        coeff_df = pd.DataFrame(coeffs, columns=[f"a{i+1}" for i in range(coeffs.shape[1])])
        modal_roll_df = pd.DataFrame(modal_rollout, columns=[f"pred_a{i+1}" for i in range(modal_rollout.shape[1])])
        pred_df = pd.DataFrame(rollout, columns=[f"pred_{c}" for c in names])
        if time is not None:
            t = np.asarray(time)
            coeff_df.insert(0, "time", t)
            modal_roll_df.insert(0, "time", t)
            pred_df.insert(0, "time", t)
        coeff_df.to_csv(out / "modal_coefficients.csv", index=False)
        modal_roll_df.to_csv(out / "modal_rollout_predictions.csv", index=False)
        pred_df.to_csv(out / "reconstructed_rollout_predictions.csv", index=False)
        return diagnostics

    def _check_is_fit(self) -> None:
        if self.pod_ is None or self.model_ is None or self.summary_ is None:
            raise RuntimeError("PODDMDcPipeline is not fit yet.")


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D; got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
