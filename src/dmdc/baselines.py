"""Simple baseline models for honest ROM comparisons.

These models are deliberately simple. Their purpose is to prevent a ROM from
looking impressive only because it was never compared against a persistence or
basic regression baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .model import DMDcModel, RankChoice
from .regularized import RegularizedDMDcModel
from .adaptive import AdaptiveDMDcModel


class PersistenceModel:
    """Baseline that predicts the current state remains unchanged."""

    name = "persistence"

    def fit_trajectories(self, trajectories_X: Sequence[ArrayLike], trajectories_U=None, **kwargs) -> "PersistenceModel":
        X0 = np.asarray(trajectories_X[0], dtype=float)
        self.n_states_ = int(X0.shape[1])
        self.n_inputs_ = 0
        return self

    def rollout(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        x = np.asarray(x0, dtype=float).reshape(1, -1)
        if n_steps is None:
            n_steps = 0 if U_future is None else np.asarray(U_future).shape[0]
        return np.repeat(x, n_steps + 1, axis=0)


class MeanModel:
    """Baseline that predicts the training-set mean state at every future step."""

    name = "mean"

    def fit_trajectories(self, trajectories_X: Sequence[ArrayLike], trajectories_U=None, **kwargs) -> "MeanModel":
        X = np.vstack([np.asarray(x, dtype=float) for x in trajectories_X])
        self.mean_ = np.mean(X, axis=0)
        self.n_states_ = int(X.shape[1])
        self.n_inputs_ = 0
        return self

    def rollout(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        if n_steps is None:
            n_steps = 0 if U_future is None else np.asarray(U_future).shape[0]
        out = np.repeat(self.mean_[None, :], n_steps + 1, axis=0)
        out[0] = np.asarray(x0, dtype=float).reshape(-1)
        return out


@dataclass
class FittedComparisonModel:
    """Thin adapter giving different model types a common rollout interface."""

    name: str
    model: object
    spectral_radius: float | None = None
    n_unstable_eigenvalues: int | None = None

    def rollout(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        if hasattr(self.model, "rollout"):
            return self.model.rollout(x0, U_future=U_future, n_steps=n_steps)  # type: ignore[attr-defined]
        if hasattr(self.model, "simulate"):
            return self.model.simulate(x0, U_future=U_future, n_steps=n_steps)  # type: ignore[attr-defined]
        raise TypeError(f"Model {self.name!r} has no rollout/simulate method.")


def fit_baseline_or_rom(
    model_name: str,
    train_X: Sequence[ArrayLike],
    train_U: Sequence[ArrayLike | None] | None,
    *,
    train_time: Sequence[ArrayLike] | None = None,
    state_names: list[str] | None = None,
    input_names: list[str] | None = None,
    dmdc_rank: RankChoice = "full",
    pod_rank: RankChoice = 0.999,
    center: bool = True,
    scale: bool = False,
) -> object:
    """Fit a supported comparison model by name."""

    key = model_name.lower()
    if key == "persistence":
        return PersistenceModel().fit_trajectories(train_X, train_U)
    if key == "mean":
        return MeanModel().fit_trajectories(train_X, train_U)
    if key in {"dmd", "dmdc"}:
        # DMDcModel automatically becomes no-input DMD when U is None or zero-column.
        return DMDcModel(rank=dmdc_rank, center=False, scale=False).fit_trajectories(
            list(train_X), list(train_U) if train_U is not None else None, state_names=state_names, input_names=input_names
        )
    if key in {"ridge_dmdc", "regularized_dmdc", "ridge_dmd"}:
        # Ridge/Tikhonov DMDc is useful for noisy experimental data or collinear inputs.
        return RegularizedDMDcModel(rank=dmdc_rank, alpha=1e-4, center=False, scale=False).fit_trajectories(
            list(train_X), list(train_U) if train_U is not None else None, state_names=state_names, input_names=input_names
        )
    if key in {"adaptive_dmdc", "variable_dt_dmdc", "adaptive"}:
        if train_time is None:
            raise ValueError("adaptive_dmdc requires time arrays; load data with --time-col.")
        return AdaptiveDMDcModel(rank=dmdc_rank, alpha=1e-8).fit_trajectories(
            list(train_X),
            list(train_U) if train_U is not None else None,
            list(train_time),
            state_names=state_names,
            input_names=input_names,
        )
    if key == "pod_dmdc":
        from .reduced import PODDMDcPipeline

        return PODDMDcPipeline(pod_rank=pod_rank, dmdc_rank=dmdc_rank, center=center, scale=scale).fit_trajectories(
            train_X, train_U, state_names=state_names, input_names=input_names
        )
    if key == "pod_ml" or key.startswith("pod_ml_"):
        from .ml import PODDynamicsRegressor

        model_type = "ridge" if key == "pod_ml" else key.removeprefix("pod_ml_")
        return PODDynamicsRegressor(pod_rank=pod_rank, model_type=model_type, center=center, scale=scale).fit_trajectories(
            train_X, train_U, state_names=state_names, input_names=input_names
        )
    raise ValueError(f"Unsupported comparison model {model_name!r}.")
