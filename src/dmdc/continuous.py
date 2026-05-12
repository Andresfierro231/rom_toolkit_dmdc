"""Continuous-time interpretation of discrete DMD/DMDc models.

Even when data are sampled discretely, a fitted discrete map can be converted to
an approximate continuous-time generator when the sample interval ``dt`` is known:

``A_c = logm(A_d) / dt``.

This does not make irregularly sampled data magically continuous; it simply gives
physical units for growth/decay rates and frequencies when the discrete map is a
reasonable approximation of a fixed time-step operator.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
from numpy.typing import ArrayLike
from scipy.linalg import logm

from .model import DMDcModel, RankChoice


@dataclass
class ContinuousTimeSummary:
    dt: float
    max_growth_rate: float
    max_frequency_rad_per_time: float
    n_modes: int
    note: str


def discrete_to_continuous(A_d: ArrayLike, B_d: ArrayLike | None = None, *, dt: float) -> tuple[np.ndarray, np.ndarray | None]:
    """Convert a discrete-time linear map to approximate continuous matrices.

    ``A_c`` is computed with the matrix logarithm.  If ``B_d`` is supplied, an
    approximate ``B_c`` is obtained from ``B_d = M B_c`` where
    ``M = integral_0^dt exp(A_c tau) dtau`` and ``M ≈ A_c^{-1}(A_d-I)``.
    """

    if dt <= 0:
        raise ValueError("dt must be positive for continuous-time conversion.")
    A_d = np.asarray(A_d, dtype=float)
    if A_d.ndim != 2 or A_d.shape[0] != A_d.shape[1]:
        raise ValueError("A_d must be square.")
    A_c = np.real_if_close(logm(A_d) / dt).astype(float)
    if B_d is None:
        return A_c, None
    B_d = np.asarray(B_d, dtype=float)
    if B_d.size == 0:
        return A_c, B_d.copy()
    try:
        M = np.linalg.solve(A_c, A_d - np.eye(A_d.shape[0]))
    except np.linalg.LinAlgError:
        # Small-A_c fallback: integral exp(A tau) d tau ≈ dt I.
        M = dt * np.eye(A_d.shape[0])
    B_c, *_ = np.linalg.lstsq(M, B_d, rcond=None)
    return A_c, B_c


class ContinuousDMDcModel:
    """Fit a discrete DMDc model and expose continuous-time matrices."""

    def __init__(self, *, dt: float, rank: RankChoice = "full", center: bool = False, scale: bool = False) -> None:
        self.dt = float(dt)
        self.discrete_model = DMDcModel(rank=rank, center=center, scale=scale)
        self.A_c_: np.ndarray | None = None
        self.B_c_: np.ndarray | None = None
        self.summary_: ContinuousTimeSummary | None = None

    def fit(self, X: ArrayLike, U: ArrayLike | None = None, *, state_names: list[str] | None = None, input_names: list[str] | None = None) -> "ContinuousDMDcModel":
        self.discrete_model.fit(X, U, state_names=state_names, input_names=input_names, dt=self.dt)
        self.A_c_, self.B_c_ = discrete_to_continuous(self.discrete_model.A_, self.discrete_model.B_, dt=self.dt)
        eig = np.linalg.eigvals(self.A_c_)
        self.summary_ = ContinuousTimeSummary(
            dt=self.dt,
            max_growth_rate=float(np.max(eig.real)) if eig.size else 0.0,
            max_frequency_rad_per_time=float(np.max(np.abs(eig.imag))) if eig.size else 0.0,
            n_modes=int(eig.size),
            note="Continuous matrices are derived from the fitted discrete map using scipy.linalg.logm.",
        )
        return self

    def simulate_discrete(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> np.ndarray:
        """Use the underlying discrete model for sampled rollouts."""

        return self.discrete_model.simulate(x0, U_future=U_future, n_steps=n_steps)

    def to_dict(self) -> dict[str, Any]:
        if self.A_c_ is None or self.summary_ is None:
            raise RuntimeError("ContinuousDMDcModel is not fit yet.")
        return {
            "summary": asdict(self.summary_),
            "A_c": self.A_c_.tolist(),
            "B_c": None if self.B_c_ is None else self.B_c_.tolist(),
            "discrete_model": self.discrete_model.to_dict(),
        }
