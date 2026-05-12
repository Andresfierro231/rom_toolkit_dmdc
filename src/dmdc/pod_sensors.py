"""POD sparse sensing and QR/Q-DEIM reconstruction utilities.

This module is Phase 9 of the ROM workflow.  The older ``sensor_selection`` module
answers a generic question: "which state columns span the dominant SVD subspace?"
This module answers the POD-specific sparse-sensing question:

    If I can measure only a few physical states, can I estimate POD modal
    coefficients and reconstruct the full state?

Mathematical idea
-----------------
POD gives the approximation

    x ≈ mean + scale * (Phi_r a)

where ``Phi_r`` is the retained POD basis and ``a`` is the modal coefficient
vector.  If only selected coordinates are measured,

    y = C x,

then after applying the same centering/scaling used by POD,

    y_proc ≈ C Phi_r a.

The least-squares coefficient estimate is therefore

    a ≈ (C Phi_r)^† y_proc.

The helper functions below implement this calculation carefully and expose it
through a beginner-friendly CLI workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import qr

from .metrics import relative_frobenius_error, rmse, error_by_column
from .pod import PODBasis
from .utils import write_json


@dataclass(frozen=True)
class PODSensorSelectionResult:
    """Result of POD-based QR/Q-DEIM sensor selection.

    Attributes
    ----------
    ranking:
        Table containing the QR pivot order and selected-state metadata.
    selected_indices:
        Integer indices into the original state vector.
    selected_state_names:
        Human-readable state names corresponding to ``selected_indices``.
    rank_used:
        Number of POD modes retained in the supplied basis.
    n_sensors:
        Number of selected sensors/states.
    """

    ranking: pd.DataFrame
    selected_indices: list[int]
    selected_state_names: list[str]
    rank_used: int
    n_sensors: int

    def save(self, outdir: str | Path) -> None:
        """Save selected sensor tables to disk."""
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        self.ranking.to_csv(out / "selected_sensors.csv", index=False)
        (out / "selected_sensors.txt").write_text("\n".join(self.selected_state_names) + "\n", encoding="utf-8")


def select_pod_sensors(pod_basis: PODBasis, n_sensors: int | None = None) -> PODSensorSelectionResult:
    """Select informative physical states from a fitted POD basis using pivoted QR.

    Parameters
    ----------
    pod_basis:
        Fitted :class:`~dmdc.pod.PODBasis` object.
    n_sensors:
        Number of sensors/states to select.  If omitted, selects one sensor per
        retained POD mode.  The function will never select more states than exist.

    Notes
    -----
    We perform pivoted QR on ``Phi_r.T``.  Its columns correspond to rows of
    ``Phi_r``, which correspond to the original physical state coordinates.
    This is the standard Q-DEIM-style greedy selection strategy.
    """

    _check_pod_is_fit(pod_basis)
    modes = np.asarray(pod_basis.modes_, dtype=float)
    n_states, rank_used = modes.shape
    names = pod_basis.state_names_ or [f"x{i}" for i in range(n_states)]
    n_select = rank_used if n_sensors is None else int(n_sensors)
    n_select = max(1, min(n_select, n_states))

    # QR with column pivoting greedily chooses state coordinates that best span
    # the retained POD modal subspace.  The pivot vector is already a ranking of
    # original state indices.
    _, rmat, pivots = qr(modes.T, pivoting=True, mode="economic")
    row_norms = np.linalg.norm(modes, axis=1)
    selected_set = set(int(i) for i in pivots[:n_select])
    rows: list[dict[str, Any]] = []
    for order, idx in enumerate(pivots, start=1):
        i = int(idx)
        rows.append(
            {
                "pivot_order": order,
                "state_index": i,
                "state_name": names[i],
                "selected": i in selected_set,
                "row_norm_in_pod_modes": float(row_norms[i]),
                "abs_r_diagonal": float(abs(rmat[order - 1, order - 1])) if order - 1 < min(rmat.shape) else np.nan,
            }
        )
    selected_indices = [int(i) for i in pivots[:n_select]]
    selected_names = [names[i] for i in selected_indices]
    return PODSensorSelectionResult(
        ranking=pd.DataFrame(rows),
        selected_indices=selected_indices,
        selected_state_names=selected_names,
        rank_used=rank_used,
        n_sensors=n_select,
    )


def estimate_coefficients_from_sensors(
    y: ArrayLike,
    pod_basis: PODBasis,
    selected_indices: Sequence[int],
) -> NDArray[np.float64]:
    """Estimate POD modal coefficients from sparse sensor measurements.

    Parameters
    ----------
    y:
        Sparse measurements with shape ``(n_snapshots, n_selected_sensors)``.
        Columns must appear in the same order as ``selected_indices``.
    pod_basis:
        Fitted POD basis used to define ``Phi_r``, means, and scales.
    selected_indices:
        Integer positions of the measured states in the original full-state vector.

    Returns
    -------
    ndarray
        Estimated modal coefficients with shape ``(n_snapshots, pod_rank)``.
    """

    _check_pod_is_fit(pod_basis)
    idx = _validate_indices(selected_indices, pod_basis.modes_.shape[0])  # type: ignore[union-attr]
    y_arr = _as_2d_float(y, "y")
    if y_arr.shape[1] != len(idx):
        raise ValueError(f"y has {y_arr.shape[1]} columns, but {len(idx)} selected indices were supplied.")

    # Apply the same preprocessing POD used before solving for modal coefficients.
    mean_sel = np.asarray(pod_basis.mean_, dtype=float)[idx]
    scale_sel = np.asarray(pod_basis.scale_, dtype=float)[idx]
    y_proc = (y_arr - mean_sel) / scale_sel

    C_phi = np.asarray(pod_basis.modes_, dtype=float)[idx, :]
    # For each snapshot row y_proc[k], solve min_a ||C Phi a - y_proc[k]||_2.
    # pinv(C_phi) has shape (rank, n_selected), so this yields (n_snapshots, rank).
    return y_proc @ np.linalg.pinv(C_phi).T


def reconstruct_from_sensors(
    y: ArrayLike,
    pod_basis: PODBasis,
    selected_indices: Sequence[int],
) -> NDArray[np.float64]:
    """Reconstruct full states from sparse sensor measurements and a POD basis."""

    coeffs = estimate_coefficients_from_sensors(y, pod_basis, selected_indices)
    return pod_basis.inverse_transform(coeffs)


def reconstruction_error_vs_pod_sensors(
    X: ArrayLike,
    pod_basis: PODBasis,
    selected_indices: Sequence[int],
) -> pd.DataFrame:
    """Compute full-state reconstruction error as POD-selected sensors are added.

    The first row uses only the first selected sensor, the second row uses the
    first two selected sensors, and so on.  This is the most useful plot for
    deciding how many thermocouples/sensors are enough for sparse reconstruction.
    """

    X_arr = _as_2d_float(X, "X")
    idx_all = _validate_indices(selected_indices, X_arr.shape[1])
    rows: list[dict[str, float | int]] = []
    for k in range(1, len(idx_all) + 1):
        idx = idx_all[:k]
        y = X_arr[:, idx]
        X_hat = reconstruct_from_sensors(y, pod_basis, idx)
        rows.append(
            {
                "n_sensors": k,
                "rmse": rmse(X_arr, X_hat),
                "relative_reconstruction_error": relative_frobenius_error(X_arr, X_hat),
            }
        )
    return pd.DataFrame(rows)


def run_pod_sensor_workflow(
    X: ArrayLike,
    *,
    state_names: Sequence[str] | None,
    rank: int | float | str | None,
    n_sensors: int | None,
    center: bool,
    scale: bool,
    outdir: str | Path,
    time: ArrayLike | None = None,
) -> dict[str, Any]:
    """Fit POD, select sensors, reconstruct from sparse sensors, and save outputs.

    This function powers the ``dmdc pod-sensors`` command and is intentionally
    reusable from notebooks/scripts.  It does not plot directly; plotting stays in
    ``plotting.py`` and the CLI calls it when requested.
    """

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    X_arr = _as_2d_float(X, "X")
    names = list(state_names) if state_names is not None else [f"x{i}" for i in range(X_arr.shape[1])]

    pod = PODBasis(rank=rank, center=center, scale=scale).fit(X_arr, state_names=names)
    pod.save(out / "pod_basis.pkl")
    write_json(pod.to_summary() | {"n_snapshots": int(X_arr.shape[0])}, out / "pod_summary.json")

    selection = select_pod_sensors(pod, n_sensors=n_sensors)
    selection.save(out)

    selected = selection.selected_indices
    y = X_arr[:, selected]
    coeffs = estimate_coefficients_from_sensors(y, pod, selected)
    X_hat = pod.inverse_transform(coeffs)
    err_curve = reconstruction_error_vs_pod_sensors(X_arr, pod, selected)

    selected_measurements = pd.DataFrame(y, columns=[f"measured_{names[i]}" for i in selected])
    coeff_df = pd.DataFrame(coeffs, columns=[f"a{i+1}" for i in range(coeffs.shape[1])])
    recon_df = pd.DataFrame(X_hat, columns=[f"recon_{name}" for name in names])
    if time is not None:
        t = np.asarray(time)
        selected_measurements.insert(0, "time", t)
        coeff_df.insert(0, "time", t)
        recon_df.insert(0, "time", t)
    selected_measurements.to_csv(out / "sparse_sensor_measurements.csv", index=False)
    coeff_df.to_csv(out / "sparse_sensor_coefficients.csv", index=False)
    recon_df.to_csv(out / "sparse_sensor_reconstruction.csv", index=False)
    err_curve.to_csv(out / "reconstruction_error_vs_sensors.csv", index=False)
    pd.DataFrame(error_by_column(X_arr, X_hat, names)).to_csv(out / "sparse_sensor_reconstruction_error.csv", index=False)

    summary: dict[str, Any] = {
        "rank_requested": rank,
        "pod_rank_used": int(pod.rank_ or 0),
        "n_sensors": int(len(selected)),
        "selected_indices": selected,
        "selected_state_names": selection.selected_state_names,
        "rmse": rmse(X_arr, X_hat),
        "relative_frobenius_error": relative_frobenius_error(X_arr, X_hat),
        "note": "Sparse reconstruction used only the selected sensor columns and the fitted POD basis.",
    }
    write_json(summary, out / "pod_sensor_summary.json")
    return summary


def _check_pod_is_fit(pod_basis: PODBasis) -> None:
    if not getattr(pod_basis, "fitted_", False) or pod_basis.modes_ is None:
        raise RuntimeError("PODBasis must be fit before sparse-sensor operations.")


def _validate_indices(indices: Sequence[int], n_states: int) -> list[int]:
    idx = [int(i) for i in indices]
    if not idx:
        raise ValueError("At least one selected index is required.")
    bad = [i for i in idx if i < 0 or i >= n_states]
    if bad:
        raise ValueError(f"Selected indices out of range for {n_states} states: {bad}")
    return idx


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D; got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
