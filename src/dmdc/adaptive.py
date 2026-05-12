"""Variable-time-step / adaptive-time DMDc.

Most experimental and system-code time series are *not* sampled on a perfectly
uniform grid.  Standard discrete DMD/DMDc learns one fixed sample-to-sample map,

    x[k+1] = A_d x[k] + B_d u[k],

which is easiest to interpret when every transition represents the same time
interval.  This module provides a complementary model for adaptive/nonuniform
sample times.  It learns a continuous-time generator from finite-difference
slopes,

    dx/dt ≈ A_c x + B_c u,

using the actual transition time step ``dt_k = t[k+1] - t[k]``.  Rollouts then
integrate the learned continuous system over each requested ``dt_k`` using a
zero-order hold for the inputs.  This keeps the default workflow honest for SAM
outputs, adaptive solvers, and experimental logs with irregular sampling.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm

from .model import RankChoice, _as_2d_float


@dataclass
class AdaptiveDMDcMetadata:
    """Metadata for a variable-time-step DMDc fit."""

    n_states: int
    n_inputs: int
    n_samples: int
    n_transitions: int
    n_trajectories: int
    rank_used: int
    singular_values: list[float]
    condition_number: float
    median_dt: float
    min_dt: float
    max_dt: float
    state_names: list[str] | None = None
    input_names: list[str] | None = None
    fit_type: str = "continuous_generator_from_variable_dt"


class AdaptiveDMDcModel:
    """Continuous-generator DMDc fit for nonuniform/adaptive time steps.

    The model estimates ``A_c`` and ``B_c`` in

    ``dx/dt = A_c x + B_c u``

    from trajectories with actual time arrays.  It is intended for data where
    the time step changes across a case.  It can also be used on uniform data,
    but ordinary DMDc is often simpler when the sampling interval is truly fixed.

    Parameters
    ----------
    rank:
        SVD rank used for the least-squares solve.  Same convention as
        :class:`dmdc.model.DMDcModel`: ``"full"``, integer, or energy fraction.
    alpha:
        Ridge/Tikhonov regularization strength.  A small positive value is useful
        for noisy experimental slopes.
    rcond:
        Relative singular-value cutoff used after rank selection.
    """

    def __init__(self, rank: RankChoice = "full", *, alpha: float = 1e-8, rcond: float = 1e-12) -> None:
        if alpha < 0:
            raise ValueError("alpha must be nonnegative.")
        self.rank = rank
        self.alpha = float(alpha)
        self.rcond = float(rcond)
        self.A_c_: NDArray[np.float64] | None = None
        self.B_c_: NDArray[np.float64] | None = None
        self.metadata_: AdaptiveDMDcMetadata | None = None

    def fit(
        self,
        X: ArrayLike,
        U: ArrayLike | None = None,
        *,
        time: ArrayLike,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "AdaptiveDMDcModel":
        """Fit from one trajectory with a physical time vector."""

        return self.fit_trajectories(
            [X],
            None if U is None else [U],
            [time],
            state_names=state_names,
            input_names=input_names,
        )

    def fit_trajectories(
        self,
        trajectories_X: Sequence[ArrayLike],
        trajectories_U: Sequence[ArrayLike | None] | None,
        trajectories_time: Sequence[ArrayLike],
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
    ) -> "AdaptiveDMDcModel":
        """Fit from multiple independent trajectories.

        Each trajectory contributes slopes only within that case.  No transition
        is formed between cases.
        """

        if not trajectories_X:
            raise ValueError("At least one trajectory is required.")
        if trajectories_U is None:
            trajectories_U = [None] * len(trajectories_X)
        if len(trajectories_X) != len(trajectories_U) or len(trajectories_X) != len(trajectories_time):
            raise ValueError("X, U, and time trajectory lists must have the same length.")

        X0_blocks: list[NDArray[np.float64]] = []
        Xdot_blocks: list[NDArray[np.float64]] = []
        U_blocks: list[NDArray[np.float64]] = []
        all_dt: list[NDArray[np.float64]] = []
        n_states_expected: int | None = None
        n_inputs_expected: int | None = None
        total_samples = 0

        for i, (X_i, U_i, t_i) in enumerate(zip(trajectories_X, trajectories_U, trajectories_time, strict=True)):
            X = _as_2d_float(X_i, name=f"X[{i}]")
            t = np.asarray(t_i, dtype=float).reshape(-1)
            if X.shape[0] != t.size:
                raise ValueError(f"time[{i}] length must match X[{i}] rows.")
            if X.shape[0] < 2:
                raise ValueError(f"Trajectory {i} has fewer than two samples.")
            dt = np.diff(t)
            if np.any(dt <= 0):
                raise ValueError(f"time[{i}] must be strictly increasing after sorting/filtering.")
            n_time, n_states = X.shape
            if n_states_expected is None:
                n_states_expected = n_states
            elif n_states != n_states_expected:
                raise ValueError("All trajectories must have the same number of state columns.")

            if U_i is None:
                U = np.zeros((n_time - 1, 0), dtype=float)
            else:
                U = _as_2d_float(U_i, name=f"U[{i}]")
                if U.shape[0] == n_time:
                    U = U[:-1, :]
                elif U.shape[0] != n_time - 1:
                    raise ValueError(f"U[{i}] must have n_time or n_time-1 rows.")
            if n_inputs_expected is None:
                n_inputs_expected = U.shape[1]
            elif U.shape[1] != n_inputs_expected:
                raise ValueError("All trajectories must have the same number of input columns.")

            # Finite-difference slope over the actual adaptive time interval.
            X0_blocks.append(X[:-1, :])
            Xdot_blocks.append((X[1:, :] - X[:-1, :]) / dt[:, None])
            U_blocks.append(U)
            all_dt.append(dt)
            total_samples += n_time

        X0 = np.vstack(X0_blocks)
        Xdot = np.vstack(Xdot_blocks)
        U_all = np.vstack(U_blocks) if U_blocks else np.zeros((X0.shape[0], 0), dtype=float)
        dt_all = np.concatenate(all_dt)
        self._fit_generator(
            X0,
            Xdot,
            U_all,
            state_names=state_names,
            input_names=input_names,
            n_samples=total_samples,
            n_trajectories=len(trajectories_X),
            dt_all=dt_all,
        )
        return self

    def _fit_generator(
        self,
        X0: NDArray[np.float64],
        Xdot: NDArray[np.float64],
        U: NDArray[np.float64],
        *,
        state_names: list[str] | None,
        input_names: list[str] | None,
        n_samples: int,
        n_trajectories: int,
        dt_all: NDArray[np.float64],
    ) -> None:
        n_transitions, n_states = X0.shape
        n_inputs = U.shape[1]
        Omega = np.vstack([X0.T, U.T])
        Y = Xdot.T
        left_modes, s, right_modes_t = np.linalg.svd(Omega, full_matrices=False)
        rank_used = self._choose_rank(s)
        rank_used = max(1, min(rank_used, len(s)))
        if len(s) > 0:
            keep = int(np.sum(s > self.rcond * s[0]))
            rank_used = min(rank_used, max(1, keep))
        Ur = left_modes[:, :rank_used]
        sr = s[:rank_used]
        Vtr = right_modes_t[:rank_used, :]
        if self.alpha > 0:
            factors = sr / (sr**2 + self.alpha)
        else:
            factors = 1.0 / sr
        G = Y @ Vtr.T @ np.diag(factors) @ Ur.T
        self.A_c_ = G[:, :n_states]
        self.B_c_ = G[:, n_states:]
        self.metadata_ = AdaptiveDMDcMetadata(
            n_states=n_states,
            n_inputs=n_inputs,
            n_samples=int(n_samples),
            n_transitions=int(n_transitions),
            n_trajectories=int(n_trajectories),
            rank_used=int(rank_used),
            singular_values=[float(v) for v in s],
            condition_number=float(s[0] / s[-1]) if len(s) and s[-1] > 0 else float("inf"),
            median_dt=float(np.median(dt_all)),
            min_dt=float(np.min(dt_all)),
            max_dt=float(np.max(dt_all)),
            state_names=state_names,
            input_names=input_names,
        )

    def rollout(
        self,
        x0: ArrayLike,
        U_future: ArrayLike | None = None,
        *,
        dt_future: ArrayLike | None = None,
        time_future: ArrayLike | None = None,
        n_steps: int | None = None,
    ) -> NDArray[np.float64]:
        """Roll out over variable future time steps.

        Provide either ``dt_future`` with length ``n_steps`` or ``time_future``
        with length ``n_steps + 1``.  If neither is supplied, the learned median
        ``dt`` is repeated.  That fallback is convenient for quick comparisons,
        but real adaptive-time validation should pass the actual time vector.
        """

        self._check_is_fit()
        x0_vec = np.asarray(x0, dtype=float).reshape(-1)
        n_states = self.metadata_.n_states  # type: ignore[union-attr]
        n_inputs = self.metadata_.n_inputs  # type: ignore[union-attr]
        if x0_vec.size != n_states:
            raise ValueError(f"x0 must have length {n_states}; got {x0_vec.size}.")
        if time_future is not None:
            t = np.asarray(time_future, dtype=float).reshape(-1)
            if t.size < 2:
                raise ValueError("time_future must contain at least two samples.")
            dt_arr = np.diff(t)
        elif dt_future is not None:
            dt_arr = np.asarray(dt_future, dtype=float).reshape(-1)
        else:
            if n_steps is None:
                if U_future is not None:
                    n_steps = np.asarray(U_future).shape[0]
                else:
                    raise ValueError("Provide dt_future, time_future, U_future, or n_steps.")
            dt_arr = np.full(int(n_steps), self.metadata_.median_dt, dtype=float)  # type: ignore[union-attr]
        if np.any(dt_arr <= 0):
            raise ValueError("All future dt values must be positive.")
        if n_steps is not None and int(n_steps) != dt_arr.size:
            raise ValueError("n_steps must match len(dt_future) when both are provided.")
        n_steps = int(dt_arr.size)

        if U_future is None:
            U_arr = np.zeros((n_steps, n_inputs), dtype=float)
        else:
            U_arr = _as_2d_float(U_future, name="U_future")
            if U_arr.shape == (n_steps + 1, n_inputs):
                U_arr = U_arr[:-1, :]
            if U_arr.shape != (n_steps, n_inputs):
                raise ValueError(f"U_future must have shape {(n_steps, n_inputs)}; got {U_arr.shape}.")

        out = np.zeros((n_steps + 1, n_states), dtype=float)
        out[0] = x0_vec
        x = x0_vec
        for k, dt in enumerate(dt_arr):
            x = self._step_zero_order_hold(x, U_arr[k], float(dt))
            out[k + 1] = x
        return out

    def simulate(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        """Compatibility alias using repeated median dt when no dt vector is supplied."""

        return self.rollout(x0, U_future=U_future, n_steps=n_steps)

    def _step_zero_order_hold(self, x: NDArray[np.float64], u: NDArray[np.float64], dt: float) -> NDArray[np.float64]:
        A = self.A_c_  # type: ignore[assignment]
        B = self.B_c_  # type: ignore[assignment]
        if B is None or B.size == 0:
            return expm(A * dt) @ x
        n = A.shape[0]
        m = B.shape[1]
        aug = np.zeros((n + m, n + m), dtype=float)
        aug[:n, :n] = A
        aug[:n, n:] = B
        step = expm(aug * dt)
        Ad = step[:n, :n]
        Bd = step[:n, n:]
        return Ad @ x + Bd @ u

    @property
    def eigenvalues_(self) -> NDArray[np.complex128]:
        self._check_is_fit()
        return np.linalg.eigvals(self.A_c_)  # type: ignore[arg-type]

    def save(self, path: str | Path) -> None:
        self._check_is_fit()
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: str | Path) -> "AdaptiveDMDcModel":
        model = joblib.load(Path(path))
        if not isinstance(model, cls):
            raise TypeError(f"Expected AdaptiveDMDcModel, got {type(model)!r}.")
        return model

    def to_dict(self) -> dict[str, Any]:
        self._check_is_fit()
        return {
            "rank": self.rank,
            "alpha": self.alpha,
            "rcond": self.rcond,
            "metadata": asdict(self.metadata_),  # type: ignore[arg-type]
            "A_c": self.A_c_.tolist(),  # type: ignore[union-attr]
            "B_c": self.B_c_.tolist(),  # type: ignore[union-attr]
            "eigenvalues_real": self.eigenvalues_.real.tolist(),
            "eigenvalues_imag": self.eigenvalues_.imag.tolist(),
            "interpretation": "continuous-time generator fitted from variable-dt finite-difference slopes",
        }

    def _choose_rank(self, singular_values: NDArray[np.float64]) -> int:
        if len(singular_values) == 0:
            raise ValueError("Cannot choose rank from empty singular values.")
        if self.rank is None or self.rank == "full":
            return len(singular_values)
        if self.rank == "auto":
            return int(np.linalg.matrix_rank(np.diag(singular_values)))
        if isinstance(self.rank, int):
            return int(self.rank)
        if isinstance(self.rank, float):
            if not (0.0 < self.rank <= 1.0):
                raise ValueError("Float rank must be an energy fraction in (0, 1].")
            energy = np.cumsum(singular_values**2) / np.sum(singular_values**2)
            return int(np.searchsorted(energy, self.rank) + 1)
        raise ValueError(f"Unsupported rank option: {self.rank!r}")

    def _check_is_fit(self) -> None:
        if self.A_c_ is None or self.B_c_ is None or self.metadata_ is None:
            raise RuntimeError("AdaptiveDMDcModel is not fit yet.")
