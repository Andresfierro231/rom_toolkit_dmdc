"""Diagnostics for fitted DMDc models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .model import DMDcModel


def rmse(y_true: NDArray[np.float64], y_pred: NDArray[np.float64]) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def relative_frobenius_error(y_true: NDArray[np.float64], y_pred: NDArray[np.float64]) -> float:
    denom = np.linalg.norm(y_true)
    if denom == 0:
        return float(np.linalg.norm(y_true - y_pred))
    return float(np.linalg.norm(y_true - y_pred) / denom)


def evaluate_model(model: DMDcModel, X: NDArray[np.float64], U: NDArray[np.float64]) -> dict[str, Any]:
    """Compute standard one-step and rollout diagnostics."""

    X0 = X[:-1]
    X1 = X[1:]
    U0 = U[:-1] if U.shape[0] == X.shape[0] else U
    one_step = model.predict_one_step(X0, U0 if U0.shape[1] else None)
    rollout = model.simulate(X[0], U0 if U0.shape[1] else None, n_steps=X.shape[0] - 1)
    eigvals = model.eigenvalues_
    spectral_radius = float(np.max(np.abs(eigvals))) if eigvals.size else 0.0
    return {
        "one_step_rmse": rmse(X1, one_step),
        "one_step_relative_frobenius_error": relative_frobenius_error(X1, one_step),
        "rollout_rmse": rmse(X, rollout),
        "rollout_relative_frobenius_error": relative_frobenius_error(X, rollout),
        "spectral_radius_A": spectral_radius,
        "is_discrete_time_stable_by_spectral_radius": bool(spectral_radius < 1.0),
        "rank_used": model.metadata_.rank_used,
        "condition_number_omega": model.metadata_.condition_number,
    }


def save_diagnostics(diagnostics: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")


def evaluate_trajectories(
    model: DMDcModel,
    trajectories_X: list[NDArray[np.float64]],
    trajectories_U: list[NDArray[np.float64]],
    case_ids: list[str | int] | None = None,
) -> dict[str, Any]:
    """Compute diagnostics for multiple independent trajectories.

    The aggregate metrics are transition-weighted, so longer trajectories contribute more to the
    global error. Per-case metrics are also returned for troubleshooting.
    """

    if len(trajectories_X) != len(trajectories_U):
        raise ValueError("trajectories_X and trajectories_U must have the same length.")
    if case_ids is None:
        case_ids = list(range(len(trajectories_X)))

    per_case: list[dict[str, Any]] = []
    true_one: list[NDArray[np.float64]] = []
    pred_one: list[NDArray[np.float64]] = []
    true_roll: list[NDArray[np.float64]] = []
    pred_roll: list[NDArray[np.float64]] = []

    for cid, X, U in zip(case_ids, trajectories_X, trajectories_U, strict=True):
        d = evaluate_model(model, X, U)
        d["case_id"] = cid
        d["n_timesteps"] = int(X.shape[0])
        d["n_transitions"] = int(X.shape[0] - 1)
        per_case.append(d)

        U0 = U[:-1] if U.shape[0] == X.shape[0] else U
        one = model.predict_one_step(X[:-1], U0 if U0.shape[1] else None)
        roll = model.simulate(X[0], U0 if U0.shape[1] else None, n_steps=X.shape[0] - 1)
        true_one.append(X[1:])
        pred_one.append(one)
        true_roll.append(X)
        pred_roll.append(roll)

    X1_all = np.vstack(true_one)
    one_all = np.vstack(pred_one)
    X_all = np.vstack(true_roll)
    roll_all = np.vstack(pred_roll)
    eigvals = model.eigenvalues_
    spectral_radius = float(np.max(np.abs(eigvals))) if eigvals.size else 0.0
    return {
        "one_step_rmse": rmse(X1_all, one_all),
        "one_step_relative_frobenius_error": relative_frobenius_error(X1_all, one_all),
        "rollout_rmse": rmse(X_all, roll_all),
        "rollout_relative_frobenius_error": relative_frobenius_error(X_all, roll_all),
        "spectral_radius_A": spectral_radius,
        "is_discrete_time_stable_by_spectral_radius": bool(spectral_radius < 1.0),
        "rank_used": model.metadata_.rank_used,
        "condition_number_omega": model.metadata_.condition_number,
        "n_trajectories": model.metadata_.n_trajectories,
        "n_transitions": model.metadata_.n_transitions,
        "per_case": per_case,
    }
