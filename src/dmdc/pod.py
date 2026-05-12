"""Proper Orthogonal Decomposition (POD) basis tools.

POD is the SVD-based reduced basis layer for this ROM repository.  It does not replace DMD/DMDc;
it provides a lower-dimensional coordinate system in which DMD/DMDc or optional ML models can act.

Conventions
-----------
Most public methods accept time-major data with shape ``(n_snapshots, n_states)`` because that is
natural for CSV files and pandas.  Internally and in the mathematical docs, the snapshot matrix is
viewed as ``X^T`` with columns as snapshots.  The POD modes ``Phi`` are stored with shape
``(n_states, rank)`` and modal coefficients are returned with shape ``(n_snapshots, rank)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .metrics import cumulative_energy, error_by_column, relative_frobenius_error, rmse
from .utils import write_json

RankChoice = int | float | Literal["full", "auto"] | None


@dataclass
class PODSummary:
    """Serializable metadata for a fitted POD basis."""

    n_states: int
    n_snapshots: int
    rank_used: int
    rank_requested: str | int | float | None
    centered: bool
    scaled: bool
    singular_values: list[float]
    explained_energy: list[float]
    cumulative_energy: list[float]
    state_names: list[str] | None


class PODBasis:
    """SVD/POD basis for reducing high-dimensional state snapshots.

    Parameters
    ----------
    rank:
        ``"full"`` for all modes, an integer number of modes, or a float in ``(0, 1]`` interpreted
        as cumulative energy threshold.
    energy_threshold:
        Optional explicit cumulative energy threshold. If provided, it overrides a float ``rank``.
    center:
        Subtract the per-state mean before SVD. This is normally recommended for POD.
    scale:
        Divide states by their standard deviation before SVD. Useful when variables have very
        different units, but reconstructed values are always returned in original units.
    """

    def __init__(
        self,
        rank: RankChoice = "full",
        *,
        energy_threshold: float | None = None,
        center: bool = True,
        scale: bool = False,
    ) -> None:
        self.rank = rank
        self.energy_threshold = energy_threshold
        self.center = center
        self.scale = scale
        self.modes_: NDArray[np.float64] | None = None
        self.singular_values_: NDArray[np.float64] | None = None
        self.explained_energy_: NDArray[np.float64] | None = None
        self.cumulative_energy_: NDArray[np.float64] | None = None
        self.mean_: NDArray[np.float64] | None = None
        self.scale_: NDArray[np.float64] | None = None
        self.rank_: int | None = None
        self.state_names_: list[str] | None = None
        self.fitted_: bool = False

    def fit(self, X: ArrayLike, state_names: list[str] | None = None) -> "PODBasis":
        """Fit POD modes from state snapshots shaped ``(n_snapshots, n_states)``."""

        X_arr = _as_2d_float(X, "X")
        n_snapshots, n_states = X_arr.shape
        if n_snapshots < 1:
            raise ValueError("At least one snapshot is required.")
        self.state_names_ = list(state_names) if state_names is not None else [f"x{i}" for i in range(n_states)]
        self.mean_ = X_arr.mean(axis=0) if self.center else np.zeros(n_states)
        self.scale_ = X_arr.std(axis=0, ddof=0) if self.scale else np.ones(n_states)
        self.scale_[self.scale_ == 0] = 1.0
        X_proc = (X_arr - self.mean_) / self.scale_

        left_modes, singular_values, _right_modes_t = np.linalg.svd(X_proc.T, full_matrices=False)
        self.singular_values_ = singular_values
        self.explained_energy_ = _explained_energy(singular_values)
        self.cumulative_energy_ = cumulative_energy(singular_values)
        rank_used = self._choose_rank(singular_values)
        rank_used = max(1, min(rank_used, left_modes.shape[1]))
        self.rank_ = rank_used
        self.modes_ = left_modes[:, :rank_used]
        self.fitted_ = True
        return self

    def transform(self, X: ArrayLike) -> NDArray[np.float64]:
        """Project full states onto the retained POD basis.

        Returns
        -------
        ndarray
            Modal coefficients with shape ``(n_snapshots, rank)``.
        """

        self._check_is_fit()
        X_arr = _as_2d_float(X, "X")
        X_proc = (X_arr - self.mean_) / self.scale_  # type: ignore[operator]
        return X_proc @ self.modes_  # type: ignore[operator]

    def inverse_transform(self, coefficients: ArrayLike) -> NDArray[np.float64]:
        """Reconstruct full states from modal coefficients."""

        self._check_is_fit()
        A = _as_2d_float(coefficients, "coefficients")
        X_proc = A @ self.modes_.T  # type: ignore[union-attr]
        return X_proc * self.scale_ + self.mean_  # type: ignore[operator]

    def fit_transform(self, X: ArrayLike, state_names: list[str] | None = None) -> NDArray[np.float64]:
        """Fit the basis and return modal coefficients."""

        return self.fit(X, state_names=state_names).transform(X)

    def reconstruction_error(self, X: ArrayLike) -> dict[str, object]:
        """Compute reconstruction error for the retained basis."""

        X_arr = _as_2d_float(X, "X")
        X_hat = self.inverse_transform(self.transform(X_arr))
        return {
            "rmse": rmse(X_arr, X_hat),
            "relative_frobenius_error": relative_frobenius_error(X_arr, X_hat),
            "by_state": error_by_column(X_arr, X_hat, self.state_names_),
        }

    def save(self, path: str | Path) -> None:
        """Save the POD object using joblib."""

        self._check_is_fit()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: str | Path) -> "PODBasis":
        """Load a saved PODBasis object."""

        obj = joblib.load(Path(path))
        if not isinstance(obj, cls):
            raise TypeError(f"Expected PODBasis, got {type(obj)!r}.")
        return obj

    def to_summary(self) -> dict[str, Any]:
        """Return JSON-serializable POD metadata."""

        self._check_is_fit()
        summary = PODSummary(
            n_states=int(self.modes_.shape[0]),  # type: ignore[union-attr]
            n_snapshots=-1,
            rank_used=int(self.rank_),  # type: ignore[arg-type]
            rank_requested=self.rank,
            centered=bool(self.center),
            scaled=bool(self.scale),
            singular_values=self.singular_values_.astype(float).tolist(),  # type: ignore[union-attr]
            explained_energy=self.explained_energy_.astype(float).tolist(),  # type: ignore[union-attr]
            cumulative_energy=self.cumulative_energy_.astype(float).tolist(),  # type: ignore[union-attr]
            state_names=self.state_names_,
        )
        return summary.__dict__

    def save_outputs(
        self,
        X: ArrayLike,
        outdir: str | Path,
        *,
        time: ArrayLike | None = None,
        case_id: object | None = None,
    ) -> dict[str, object]:
        """Save common POD artifacts for a fitted basis and dataset."""

        self._check_is_fit()
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        X_arr = _as_2d_float(X, "X")
        coeffs = self.transform(X_arr)
        recon = self.inverse_transform(coeffs)
        self.save(out / "pod_basis.pkl")
        summary = self.to_summary()
        summary["n_snapshots"] = int(X_arr.shape[0])
        summary["reconstruction_error"] = self.reconstruction_error(X_arr)
        write_json(summary, out / "pod_summary.json")

        coeff_cols = [f"a{i+1}" for i in range(coeffs.shape[1])]
        coeff_df = pd.DataFrame(coeffs, columns=coeff_cols)
        recon_df = pd.DataFrame(recon, columns=[f"recon_{c}" for c in self.state_names_])
        err_df = pd.DataFrame(summary["reconstruction_error"]["by_state"])  # type: ignore[index]
        if time is not None:
            coeff_df.insert(0, "time", np.asarray(time))
            recon_df.insert(0, "time", np.asarray(time))
        if case_id is not None:
            coeff_df.insert(0, "case_id", case_id)
            recon_df.insert(0, "case_id", case_id)
        coeff_df.to_csv(out / "pod_coefficients.csv", index=False)
        recon_df.to_csv(out / "pod_reconstruction.csv", index=False)
        err_df.to_csv(out / "pod_reconstruction_error.csv", index=False)
        return summary

    def _choose_rank(self, singular_values: NDArray[np.float64]) -> int:
        if singular_values.size == 0:
            raise ValueError("Cannot choose POD rank from no singular values.")
        threshold = self.energy_threshold
        if threshold is None and isinstance(self.rank, float):
            threshold = self.rank
        if threshold is not None:
            if not (0.0 < threshold <= 1.0):
                raise ValueError("energy_threshold must be in (0, 1].")
            energy = cumulative_energy(singular_values)
            return int(np.searchsorted(energy, threshold) + 1)
        if self.rank is None or self.rank == "full":
            return len(singular_values)
        if self.rank == "auto":
            return int(np.linalg.matrix_rank(np.diag(singular_values)))
        if isinstance(self.rank, int):
            if self.rank < 1:
                raise ValueError("rank must be positive.")
            return self.rank
        raise ValueError(f"Unsupported POD rank option: {self.rank!r}")

    def _check_is_fit(self) -> None:
        if not self.fitted_ or self.modes_ is None or self.mean_ is None or self.scale_ is None:
            raise RuntimeError("PODBasis is not fit yet.")


def save_reconstruction_error_vs_rank(
    X: ArrayLike,
    out_csv: str | Path,
    *,
    max_rank: int | None = None,
    center: bool = True,
    scale: bool = False,
    state_names: list[str] | None = None,
) -> pd.DataFrame:
    """Fit POD at increasing ranks and save reconstruction error curve."""

    X_arr = _as_2d_float(X, "X")
    max_available = min(X_arr.shape)
    max_rank = max_available if max_rank is None else min(max_rank, max_available)
    rows = []
    for r in range(1, max_rank + 1):
        pod = PODBasis(rank=r, center=center, scale=scale).fit(X_arr, state_names=state_names)
        err = pod.reconstruction_error(X_arr)
        rows.append({"rank": r, "rmse": err["rmse"], "relative_frobenius_error": err["relative_frobenius_error"], "cumulative_energy": float(pod.cumulative_energy_[r - 1])})
    df = pd.DataFrame(rows)
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    return df


def _explained_energy(singular_values: NDArray[np.float64]) -> NDArray[np.float64]:
    total = np.sum(singular_values**2)
    if total <= 0:
        return np.zeros_like(singular_values)
    return singular_values**2 / total


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D; got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
