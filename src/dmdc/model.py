"""
DMDc model implementation.

Mathematical problem
--------------------
Given a measured or simulated trajectory with state snapshots x_k and controls u_k,
DMDc approximates the discrete-time controlled linear dynamics

    x_{k+1} = A x_k + B u_k.

For a trajectory of length m+1, define

    X  = [x_0, x_1, ..., x_{m-1}]      shape: (n_states, m)
    Xp = [x_1, x_2, ..., x_m]          shape: (n_states, m)
    U  = [u_0, u_1, ..., u_{m-1}]      shape: (n_inputs, m)

and the augmented snapshot matrix

    Omega = [X; U].

Then

    Xp ≈ [A B] Omega.

This module estimates [A B] using an SVD-truncated least-squares pseudoinverse.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
from numpy.typing import ArrayLike, NDArray

RankChoice = int | float | Literal["auto", "full"] | None


@dataclass
class DMDcMetadata:
    """Metadata describing a fitted DMDc model."""

    n_states: int
    n_inputs: int
    n_samples: int
    n_transitions: int
    n_trajectories: int
    rank_used: int
    singular_values: list[float]
    condition_number: float
    state_names: list[str] | None = None
    input_names: list[str] | None = None
    dt: float | None = None


class DMDcModel:
    """Dynamic Mode Decomposition with control.

    Parameters
    ----------
    rank:
        Truncation rank for the SVD of Omega = [X; U].
        - int: use exactly that rank, clipped to available dimensions.
        - float in (0, 1): use the smallest rank whose cumulative singular-value energy
          exceeds the requested fraction.
        - "auto": use the numerical matrix rank from NumPy.
        - "full" or None: use all singular values.
    rcond:
        Relative singular-value cutoff. Singular values below rcond * s_max are discarded.
    center:
        Whether to subtract the mean from state and input data before fitting. This is useful
        for perturbation dynamics. For absolute-state prediction, leave False unless you
        understand the affine shift implied by centering.
    scale:
        Whether to divide state and input columns by standard deviation before fitting.
        This helps with poorly scaled variables such as pressure, temperature, and flow rate.
    """

    def __init__(
        self,
        rank: RankChoice = "full",
        rcond: float = 1e-12,
        center: bool = False,
        scale: bool = False,
    ) -> None:
        self.rank = rank
        self.rcond = rcond
        self.center = center
        self.scale = scale

        self.A_: NDArray[np.float64] | None = None
        self.B_: NDArray[np.float64] | None = None
        self.metadata_: DMDcMetadata | None = None
        self.x_mean_: NDArray[np.float64] | None = None
        self.u_mean_: NDArray[np.float64] | None = None
        self.x_scale_: NDArray[np.float64] | None = None
        self.u_scale_: NDArray[np.float64] | None = None

    def fit(
        self,
        X: ArrayLike,
        U: ArrayLike | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
        dt: float | None = None,
    ) -> "DMDcModel":
        """Fit A and B from a single time-series trajectory.

        Parameters
        ----------
        X:
            State trajectory with shape ``(n_timesteps, n_states)``.
        U:
            Input/control trajectory with shape ``(n_timesteps, n_inputs)``, or ``None`` for no inputs.
            When ``U`` has the same number of rows as ``X``, this method uses ``U[:-1]`` to match
            transitions ``X[:-1] -> X[1:]``. When ``U`` has one fewer row than ``X``, it is assumed to
            already align with transitions.

        Notes
        -----
        This is a convenience wrapper around :meth:`fit_trajectories` with one trajectory. For
        experiments or simulation sweeps with several independent cases, prefer ``fit_trajectories``
        so the final state of one case is not incorrectly connected to the first state of the next.
        """

        return self.fit_trajectories(
            [X],
            None if U is None else [U],
            state_names=state_names,
            input_names=input_names,
            dt=dt,
        )

    def fit_trajectories(
        self,
        trajectories_X: list[ArrayLike] | tuple[ArrayLike, ...],
        trajectories_U: list[ArrayLike | None] | tuple[ArrayLike | None, ...] | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
        dt: float | None = None,
    ) -> "DMDcModel":
        """Fit DMDc from multiple independent trajectories.

        Each trajectory contributes only internal transitions

        ``x_k -> x_{k+1}``

        within that trajectory. The method deliberately **does not** create an artificial transition
        from the last row of case ``i`` to the first row of case ``i+1``.

        Parameters
        ----------
        trajectories_X:
            Sequence of state arrays. Each item has shape ``(n_timesteps_i, n_states)``.
        trajectories_U:
            Sequence of input arrays. Each item may have either ``n_timesteps_i`` rows or
            ``n_timesteps_i - 1`` rows. Use ``None`` for no-input DMD.
        """

        if not trajectories_X:
            raise ValueError("At least one state trajectory is required.")
        if trajectories_U is None:
            trajectories_U = [None] * len(trajectories_X)
        if len(trajectories_U) != len(trajectories_X):
            raise ValueError("trajectories_X and trajectories_U must have the same length.")

        X0_blocks: list[NDArray[np.float64]] = []
        X1_blocks: list[NDArray[np.float64]] = []
        U_blocks: list[NDArray[np.float64]] = []
        n_states_expected: int | None = None
        n_inputs_expected: int | None = None
        total_samples = 0

        for i, (X_i, U_i) in enumerate(zip(trajectories_X, trajectories_U, strict=True)):
            X_arr = _as_2d_float(X_i, name=f"X[{i}]")
            n_time, n_states = X_arr.shape
            if n_time < 2:
                raise ValueError(f"Trajectory {i} has {n_time} rows; at least two time steps are required.")
            if n_states_expected is None:
                n_states_expected = n_states
            elif n_states != n_states_expected:
                raise ValueError(
                    f"All trajectories must have the same number of states. Expected {n_states_expected}, got {n_states} in trajectory {i}."
                )

            if U_i is None:
                U_arr = np.zeros((n_time - 1, 0), dtype=float)
            else:
                U_arr = _as_2d_float(U_i, name=f"U[{i}]")
                if U_arr.shape[0] == n_time:
                    U_arr = U_arr[:-1, :]
                elif U_arr.shape[0] != n_time - 1:
                    raise ValueError(
                        f"U[{i}] must have either {n_time} rows or {n_time - 1} rows; got {U_arr.shape[0]}."
                    )
            if n_inputs_expected is None:
                n_inputs_expected = U_arr.shape[1]
            elif U_arr.shape[1] != n_inputs_expected:
                raise ValueError(
                    f"All trajectories must have the same number of inputs. Expected {n_inputs_expected}, got {U_arr.shape[1]} in trajectory {i}."
                )

            X0_blocks.append(X_arr[:-1, :])
            X1_blocks.append(X_arr[1:, :])
            U_blocks.append(U_arr)
            total_samples += n_time

        X0 = np.vstack(X0_blocks)
        X1 = np.vstack(X1_blocks)
        U = np.vstack(U_blocks) if U_blocks else np.zeros((X0.shape[0], 0), dtype=float)
        return self.fit_transitions(
            X0,
            X1,
            U,
            state_names=state_names,
            input_names=input_names,
            dt=dt,
            n_samples=total_samples,
            n_trajectories=len(trajectories_X),
        )

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
    ) -> "DMDcModel":
        """Fit A and B from already-aligned transition matrices.

        ``X0[j]`` and ``U[j]`` are used to predict ``X1[j]``. This low-level method is useful when
        transitions have already been assembled manually.
        """

        X0_arr = _as_2d_float(X0, name="X0")
        X1_arr = _as_2d_float(X1, name="X1")
        if X0_arr.shape != X1_arr.shape:
            raise ValueError(f"X0 and X1 must have identical shapes; got {X0_arr.shape} and {X1_arr.shape}.")
        if X0_arr.shape[0] < 1:
            raise ValueError("At least one transition is required.")

        if U is None:
            U_arr = np.zeros((X0_arr.shape[0], 0), dtype=float)
        else:
            U_arr = _as_2d_float(U, name="U")
            if U_arr.shape[0] != X0_arr.shape[0]:
                raise ValueError(f"U must have one row per transition; expected {X0_arr.shape[0]}, got {U_arr.shape[0]}.")

        n_transitions, n_states = X0_arr.shape
        n_inputs = U_arr.shape[1]

        X0_proc, U_proc = self._fit_transform_training_data(X0_arr, U_arr)
        X1_proc = self._transform_states(X1_arr)

        # Work in column-snapshot convention.
        X_mat = X0_proc.T
        Xp_mat = X1_proc.T
        U_mat = U_proc.T
        Omega = np.vstack([X_mat, U_mat])

        U_svd, s, Vt = np.linalg.svd(Omega, full_matrices=False)
        rank_used = self._choose_rank(s)
        rank_used = max(1, min(rank_used, len(s)))

        # Additional numerical cutoff to avoid division by tiny singular values.
        if len(s) > 0:
            keep_by_rcond = int(np.sum(s > self.rcond * s[0]))
            rank_used = min(rank_used, max(1, keep_by_rcond))

        Ur = U_svd[:, :rank_used]
        sr = s[:rank_used]
        Vtr = Vt[:rank_used, :]

        # [A B] = Xp V Sigma^{-1} U^T
        G = Xp_mat @ Vtr.T @ np.diag(1.0 / sr) @ Ur.T
        A_scaled = G[:, :n_states]
        B_scaled = G[:, n_states:]

        # If center/scale is used, A and B operate in transformed coordinates.
        self.A_ = A_scaled
        self.B_ = B_scaled
        condition_number = float(s[0] / s[-1]) if len(s) > 0 and s[-1] > 0 else float("inf")
        self.metadata_ = DMDcMetadata(
            n_states=n_states,
            n_inputs=n_inputs,
            n_samples=int(n_samples if n_samples is not None else n_transitions + 1),
            n_transitions=int(n_transitions),
            n_trajectories=int(n_trajectories),
            rank_used=rank_used,
            singular_values=[float(v) for v in s],
            condition_number=condition_number,
            state_names=state_names,
            input_names=input_names,
            dt=dt,
        )
        return self

    def predict_one_step(self, X: ArrayLike, U: ArrayLike | None = None) -> NDArray[np.float64]:
        """Predict x_{k+1} for each provided x_k and u_k.

        X shape: (n_samples, n_states)
        U shape: (n_samples, n_inputs). If no-input model, U may be None.
        """

        self._check_is_fit()
        X_arr = _as_2d_float(X, name="X")
        U_arr = self._prepare_input_for_prediction(U, X_arr.shape[0])

        X_proc = self._transform_states(X_arr)
        U_proc = self._transform_inputs(U_arr)
        Xp_proc = X_proc @ self.A_.T + U_proc @ self.B_.T  # type: ignore[union-attr]
        return self._inverse_transform_states(Xp_proc)

    def simulate(self, x0: ArrayLike, U_future: ArrayLike | None = None, n_steps: int | None = None) -> NDArray[np.float64]:
        """Roll out the learned model from an initial condition.

        Returns an array of shape (n_steps + 1, n_states), including x0.
        """

        self._check_is_fit()
        x0_arr = np.asarray(x0, dtype=float).reshape(-1)
        n_states = self.metadata_.n_states  # type: ignore[union-attr]
        n_inputs = self.metadata_.n_inputs  # type: ignore[union-attr]
        if x0_arr.size != n_states:
            raise ValueError(f"x0 must have length {n_states}; got {x0_arr.size}.")

        if U_future is None:
            if n_steps is None:
                raise ValueError("Provide n_steps when U_future is None.")
            U_arr = np.zeros((n_steps, n_inputs), dtype=float)
        else:
            U_arr = _as_2d_float(U_future, name="U_future")
            if n_inputs == 0 and U_arr.shape[1] != 0:
                raise ValueError("This model was fit without inputs; U_future should be None or zero-column.")
            if U_arr.shape[1] != n_inputs:
                raise ValueError(f"U_future must have {n_inputs} columns; got {U_arr.shape[1]}.")
            if n_steps is not None and U_arr.shape[0] != n_steps:
                raise ValueError("n_steps must match U_future rows when both are provided.")
            n_steps = U_arr.shape[0]

        trajectory = np.zeros((n_steps + 1, n_states), dtype=float)
        trajectory[0] = x0_arr
        x = x0_arr[None, :]
        for k in range(n_steps):
            u = U_arr[k : k + 1, :]
            x = self.predict_one_step(x, u)
            trajectory[k + 1] = x.reshape(-1)
        return trajectory

    @property
    def eigenvalues_(self) -> NDArray[np.complex128]:
        """Eigenvalues of the learned A matrix."""

        self._check_is_fit()
        return np.linalg.eigvals(self.A_)  # type: ignore[arg-type]

    def save(self, path: str | Path) -> None:
        """Save model to disk using joblib."""

        self._check_is_fit()
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: str | Path) -> "DMDcModel":
        """Load model from disk."""

        model = joblib.load(Path(path))
        if not isinstance(model, cls):
            raise TypeError(f"Expected a DMDcModel object, got {type(model)!r}.")
        return model

    def to_dict(self) -> dict[str, Any]:
        """Serializable summary of the model."""

        self._check_is_fit()
        return {
            "rank": self.rank,
            "rcond": self.rcond,
            "center": self.center,
            "scale": self.scale,
            "metadata": asdict(self.metadata_),  # type: ignore[arg-type]
            "A": self.A_.tolist(),  # type: ignore[union-attr]
            "B": self.B_.tolist(),  # type: ignore[union-attr]
            "eigenvalues_real": self.eigenvalues_.real.tolist(),
            "eigenvalues_imag": self.eigenvalues_.imag.tolist(),
        }

    def _choose_rank(self, singular_values: NDArray[np.float64]) -> int:
        if len(singular_values) == 0:
            raise ValueError("Cannot choose rank from an empty singular-value array.")
        if self.rank is None or self.rank == "full":
            return len(singular_values)
        if self.rank == "auto":
            return int(np.linalg.matrix_rank(np.diag(singular_values)))
        if isinstance(self.rank, int):
            if self.rank < 1:
                raise ValueError("rank must be positive.")
            return self.rank
        if isinstance(self.rank, float):
            if not (0.0 < self.rank <= 1.0):
                raise ValueError("Float rank must be an energy fraction in (0, 1].")
            energy = np.cumsum(singular_values**2) / np.sum(singular_values**2)
            return int(np.searchsorted(energy, self.rank) + 1)
        raise ValueError(f"Unsupported rank option: {self.rank!r}")

    def _fit_transform_training_data(
        self, X0: NDArray[np.float64], U: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        self.x_mean_ = X0.mean(axis=0) if self.center else np.zeros(X0.shape[1])
        self.u_mean_ = U.mean(axis=0) if self.center and U.shape[1] else np.zeros(U.shape[1])
        self.x_scale_ = X0.std(axis=0, ddof=0) if self.scale else np.ones(X0.shape[1])
        self.u_scale_ = U.std(axis=0, ddof=0) if self.scale and U.shape[1] else np.ones(U.shape[1])
        self.x_scale_[self.x_scale_ == 0] = 1.0
        if self.u_scale_.size:
            self.u_scale_[self.u_scale_ == 0] = 1.0
        return self._transform_states(X0), self._transform_inputs(U)

    def _transform_states(self, X: NDArray[np.float64]) -> NDArray[np.float64]:
        return (X - self.x_mean_) / self.x_scale_  # type: ignore[operator]

    def _transform_inputs(self, U: NDArray[np.float64]) -> NDArray[np.float64]:
        if U.shape[1] == 0:
            return U
        return (U - self.u_mean_) / self.u_scale_  # type: ignore[operator]

    def _inverse_transform_states(self, X_proc: NDArray[np.float64]) -> NDArray[np.float64]:
        return X_proc * self.x_scale_ + self.x_mean_  # type: ignore[operator]

    def _prepare_input_for_prediction(
        self, U: ArrayLike | None, n_rows: int
    ) -> NDArray[np.float64]:
        n_inputs = self.metadata_.n_inputs  # type: ignore[union-attr]
        if U is None:
            if n_inputs == 0:
                return np.zeros((n_rows, 0), dtype=float)
            raise ValueError(f"This model expects {n_inputs} input columns; U cannot be None.")
        U_arr = _as_2d_float(U, name="U")
        if U_arr.shape != (n_rows, n_inputs):
            raise ValueError(f"U must have shape {(n_rows, n_inputs)}; got {U_arr.shape}.")
        return U_arr

    def _check_is_fit(self) -> None:
        if self.A_ is None or self.B_ is None or self.metadata_ is None:
            raise RuntimeError("DMDcModel is not fit yet.")


def _as_2d_float(value: ArrayLike, *, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 1D or 2D array; got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
