"""Regularized DMD/DMDc models.

The original :class:`dmdc.model.DMDcModel` uses SVD-truncated least squares.  For
noisy experimental data or collinear inputs, a ridge/Tikhonov penalty can make
the estimated operator less sensitive to small singular directions.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
import numpy as np
from numpy.typing import ArrayLike, NDArray

from .model import DMDcModel, DMDcMetadata, RankChoice, _as_2d_float


class RegularizedDMDcModel(DMDcModel):
    """DMD/DMDc with ridge/Tikhonov regularization.

    The fitted matrix solves

    ``min_G ||Xp - G Omega||_F^2 + alpha ||G||_F^2``

    where ``G = [A B]`` and ``Omega = [X; U]``.  Setting ``alpha=0`` recovers the
    ordinary least-squares solution without explicit SVD truncation.
    """

    def __init__(
        self,
        rank: RankChoice = "full",
        *,
        alpha: float = 1e-6,
        rcond: float = 1e-12,
        center: bool = False,
        scale: bool = False,
    ) -> None:
        super().__init__(rank=rank, rcond=rcond, center=center, scale=scale)
        if alpha < 0:
            raise ValueError("alpha must be nonnegative.")
        self.alpha = float(alpha)

    def fit_transitions(
        self,
        X0: ArrayLike,
        X1: ArrayLike,
        U: ArrayLike | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
        dt: float | None = None,
        n_samples: int | None = None,
        n_trajectories: int = 1,
    ) -> "RegularizedDMDcModel":
        X0_arr = _as_2d_float(X0, name="X0")
        X1_arr = _as_2d_float(X1, name="X1")
        if X0_arr.shape != X1_arr.shape:
            raise ValueError(f"X0 and X1 must have identical shapes; got {X0_arr.shape} and {X1_arr.shape}.")
        if U is None:
            U_arr = np.zeros((X0_arr.shape[0], 0), dtype=float)
        else:
            U_arr = _as_2d_float(U, name="U")
            if U_arr.shape[0] != X0_arr.shape[0]:
                raise ValueError("U must have one row per transition.")

        n_transitions, n_states = X0_arr.shape
        n_inputs = U_arr.shape[1]
        X0_proc, U_proc = self._fit_transform_training_data(X0_arr, U_arr)
        X1_proc = self._transform_states(X1_arr)
        X_mat = X0_proc.T
        Xp_mat = X1_proc.T
        U_mat = U_proc.T
        Omega = np.vstack([X_mat, U_mat])
        U_svd, s, Vt = np.linalg.svd(Omega, full_matrices=False)
        rank_used = max(1, min(self._choose_rank(s), len(s)))
        Ur = U_svd[:, :rank_used]
        sr = s[:rank_used]
        Vtr = Vt[:rank_used, :]

        # Ridge pseudoinverse in the retained SVD subspace:
        # Omega^T (Omega Omega^T + alpha I)^-1 = V diag(s/(s^2+alpha)) U^T
        factors = sr / (sr**2 + self.alpha)
        G = Xp_mat @ Vtr.T @ np.diag(factors) @ Ur.T
        self.A_ = G[:, :n_states]
        self.B_ = G[:, n_states:]
        self.metadata_ = DMDcMetadata(
            n_states=n_states,
            n_inputs=n_inputs,
            n_samples=int(n_samples if n_samples is not None else n_transitions + 1),
            n_transitions=int(n_transitions),
            n_trajectories=int(n_trajectories),
            rank_used=rank_used,
            singular_values=[float(v) for v in s],
            condition_number=float(s[0] / s[-1]) if len(s) and s[-1] > 0 else float("inf"),
            state_names=state_names,
            input_names=input_names,
            dt=dt,
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        out = super().to_dict()
        out["regularization"] = {"type": "ridge", "alpha": self.alpha}
        return out
