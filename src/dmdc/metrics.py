"""Small metric helpers shared by diagnostics, POD, and validation workflows."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def relative_frobenius_error(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    denom = np.linalg.norm(y)
    if denom == 0:
        return float(np.linalg.norm(y - p))
    return float(np.linalg.norm(y - p) / denom)


def error_by_column(y_true: ArrayLike, y_pred: ArrayLike, names: list[str] | None = None) -> list[dict[str, float | str | int]]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    if y.shape != p.shape:
        raise ValueError(f"Shapes must match; got {y.shape} and {p.shape}.")
    names = names or [f"x{i}" for i in range(y.shape[1])]
    rows = []
    for i, name in enumerate(names):
        residual = y[:, i] - p[:, i]
        rows.append(
            {
                "index": i,
                "state": name,
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "mae": float(np.mean(np.abs(residual))),
                "max_abs": float(np.max(np.abs(residual))),
                "bias": float(np.mean(residual)),
            }
        )
    return rows


def cumulative_energy(singular_values: ArrayLike) -> NDArray[np.float64]:
    s = np.asarray(singular_values, dtype=float)
    if s.size == 0:
        return np.array([], dtype=float)
    total = np.sum(s**2)
    if total <= 0:
        return np.ones_like(s)
    return np.cumsum(s**2) / total
