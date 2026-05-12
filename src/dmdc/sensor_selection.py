"""SVD + pivoted-QR tools for identifying important state variables/sensors.

The main use case is Q-DEIM-style state/sensor selection. Given a snapshot matrix
X with rows as time samples and columns as state variables, we compute

    X^T = U Sigma V^T

so that the left singular vectors U live in state space. Pivoted QR on U_r^T
then selects rows of U_r, equivalently original state variables, that best span
the retained rank-r subspace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import qr


@dataclass(frozen=True)
class SensorSelectionResult:
    """Result of SVD + pivoted-QR state/sensor ranking."""

    ranking: pd.DataFrame
    selected_state_names: list[str]
    selected_indices: list[int]
    singular_values: list[float]
    rank_used: int

    def save(self, outdir: str | Path) -> None:
        """Write ranking, selected sensors, and singular values to disk."""
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        self.ranking.to_csv(out / "sensor_ranking.csv", index=False)
        (out / "selected_sensors.txt").write_text("\n".join(self.selected_state_names) + "\n", encoding="utf-8")
        pd.DataFrame({"index": np.arange(1, len(self.singular_values) + 1), "singular_value": self.singular_values}).to_csv(
            out / "singular_values.csv", index=False
        )


def qr_sensor_ranking(
    X: ArrayLike,
    state_names: Sequence[str] | None = None,
    *,
    rank: int | float | str | None = "full",
    n_sensors: int | None = None,
    center: bool = False,
    scale: bool = False,
) -> SensorSelectionResult:
    """Rank state variables using pivoted QR on retained left singular vectors.

    Parameters
    ----------
    X:
        Snapshot matrix with shape ``(n_timesteps, n_states)``.
    state_names:
        Names corresponding to columns of ``X``.
    rank:
        SVD truncation. Supports ``"full"``, ``"auto"``, integer rank, or an
        energy fraction in ``(0, 1]`` such as ``0.999``.
    n_sensors:
        Number of states to mark as selected. Defaults to ``rank_used``.
    center, scale:
        Optional preprocessing applied column-wise before SVD. Scaling is often
        useful when mixing temperatures, pressures, and flow rates.

    Returns
    -------
    SensorSelectionResult
        Ranking table and selected state names/indices.

    Notes
    -----
    This is useful for answering: which measured states are most informative for
    spanning the dominant low-rank state subspace? It is not the same as causal
    importance. Always compare rollout/reconstruction errors before removing
    sensors from a predictive model.
    """

    X_arr = _as_2d_float(X, "X")
    n_timesteps, n_states = X_arr.shape
    if n_timesteps < 2:
        raise ValueError("At least two time samples are required.")
    names = list(state_names) if state_names is not None else [f"x{i}" for i in range(n_states)]
    if len(names) != n_states:
        raise ValueError(f"Expected {n_states} state names; got {len(names)}.")

    X_proc = X_arr.copy()
    means = X_proc.mean(axis=0) if center else np.zeros(n_states)
    scales = X_proc.std(axis=0, ddof=0) if scale else np.ones(n_states)
    scales[scales == 0.0] = 1.0
    X_proc = (X_proc - means) / scales

    # Column variables become rows in state-space snapshot convention.
    left_modes, singular_values, _ = np.linalg.svd(X_proc.T, full_matrices=False)
    rank_used = _choose_rank(singular_values, rank)
    rank_used = max(1, min(rank_used, left_modes.shape[1]))
    n_select = rank_used if n_sensors is None else int(n_sensors)
    n_select = max(1, min(n_select, n_states))

    Ur = left_modes[:, :rank_used]
    # Pivot columns of Ur.T, which correspond to original state coordinates.
    _, rmat, pivots = qr(Ur.T, pivoting=True, mode="economic")

    row_norms = np.linalg.norm(Ur, axis=1)
    selected_set = set(int(i) for i in pivots[:n_select])
    rows = []
    for order, idx in enumerate(pivots, start=1):
        idx_int = int(idx)
        rows.append(
            {
                "pivot_order": order,
                "state_index": idx_int,
                "state_name": names[idx_int],
                "selected": idx_int in selected_set,
                "row_norm_in_retained_modes": float(row_norms[idx_int]),
                "abs_r_diagonal": float(abs(rmat[order - 1, order - 1])) if order - 1 < min(rmat.shape) else np.nan,
            }
        )
    ranking = pd.DataFrame(rows)
    selected_indices = [int(i) for i in pivots[:n_select]]
    selected_state_names = [names[i] for i in selected_indices]
    return SensorSelectionResult(
        ranking=ranking,
        selected_state_names=selected_state_names,
        selected_indices=selected_indices,
        singular_values=[float(v) for v in singular_values],
        rank_used=rank_used,
    )


def reconstruction_error_vs_sensors(
    X: ArrayLike,
    selected_indices: Sequence[int],
    *,
    rank: int | float | str | None = "full",
    center: bool = False,
    scale: bool = False,
) -> pd.DataFrame:
    """Estimate full-state reconstruction error as selected sensors are added.

    For each k, this uses the first k selected coordinates to reconstruct the
    full state from the retained SVD basis via

        x ≈ U_r (C U_r)^† C x.

    The returned errors are relative Frobenius errors over the full trajectory.
    """

    X_arr = _as_2d_float(X, "X")
    n_states = X_arr.shape[1]
    if any(i < 0 or i >= n_states for i in selected_indices):
        raise ValueError("selected_indices contains an out-of-range state index.")

    means = X_arr.mean(axis=0) if center else np.zeros(n_states)
    scales = X_arr.std(axis=0, ddof=0) if scale else np.ones(n_states)
    scales[scales == 0.0] = 1.0
    X_proc = (X_arr - means) / scales
    left_modes, singular_values, _ = np.linalg.svd(X_proc.T, full_matrices=False)
    rank_used = _choose_rank(singular_values, rank)
    rank_used = max(1, min(rank_used, left_modes.shape[1]))
    Ur = left_modes[:, :rank_used]

    rows = []
    denom = np.linalg.norm(X_proc)
    for k in range(1, len(selected_indices) + 1):
        idx = list(selected_indices[:k])
        CUr = Ur[idx, :]
        Y = X_proc[:, idx]
        coeff = np.linalg.pinv(CUr) @ Y.T
        X_rec_proc = (Ur @ coeff).T
        err = np.linalg.norm(X_proc - X_rec_proc) / denom if denom else np.linalg.norm(X_proc - X_rec_proc)
        rows.append({"n_sensors": k, "relative_reconstruction_error": float(err)})
    return pd.DataFrame(rows)


def _choose_rank(singular_values: NDArray[np.float64], rank: int | float | str | None) -> int:
    if len(singular_values) == 0:
        raise ValueError("Cannot choose rank from an empty singular-value array.")
    if rank is None or rank == "full":
        return len(singular_values)
    if rank == "auto":
        return int(np.linalg.matrix_rank(np.diag(singular_values)))
    if isinstance(rank, int):
        if rank < 1:
            raise ValueError("rank must be positive.")
        return rank
    if isinstance(rank, float):
        if not (0.0 < rank <= 1.0):
            raise ValueError("Float rank must be an energy fraction in (0, 1].")
        energy = np.cumsum(singular_values**2) / np.sum(singular_values**2)
        return int(np.searchsorted(energy, rank) + 1)
    raise ValueError(f"Unsupported rank option: {rank!r}")


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
