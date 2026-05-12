"""Delay-coordinate helpers for DMD/DMDc.

Delay embeddings are useful for loop systems because transport/advection often
means a disturbance appears downstream several samples later. Instead of fitting
x_{k+1} from x_k only, a delay model fits from

    z_k = [x_k, x_{k-1}, ..., x_{k-d+1}]

where d is the number of delays.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray


def make_delay_embedding(
    X: ArrayLike,
    U: ArrayLike | None = None,
    *,
    n_delays: int,
    state_names: Sequence[str] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64] | None, list[str]]:
    """Create a delay-embedded trajectory.

    Parameters
    ----------
    X:
        State trajectory with shape ``(n_timesteps, n_states)``.
    U:
        Optional input trajectory with shape ``(n_timesteps, n_inputs)``. The
        returned input trajectory is aligned with the embedded rows and has
        ``n_timesteps - n_delays + 1`` rows.
    n_delays:
        Number of state history blocks. ``n_delays=1`` returns the original X.
    state_names:
        Optional names for state columns. Returned names are suffixed with
        ``__lag0``, ``__lag1``, etc.

    Returns
    -------
    Z, U_aligned, z_names
        ``Z[k] = [X[k+n_delays-1], X[k+n_delays-2], ..., X[k]]``.
    """

    X_arr = _as_2d_float(X, "X")
    if n_delays < 1:
        raise ValueError("n_delays must be at least 1.")
    n_time, n_states = X_arr.shape
    if n_time < n_delays + 1:
        raise ValueError("Need at least n_delays + 1 samples to fit transitions after embedding.")

    names = list(state_names) if state_names is not None else [f"x{i}" for i in range(n_states)]
    if len(names) != n_states:
        raise ValueError(f"Expected {n_states} state names; got {len(names)}.")

    rows = []
    for end in range(n_delays - 1, n_time):
        blocks = [X_arr[end - lag] for lag in range(n_delays)]
        rows.append(np.concatenate(blocks))
    Z = np.vstack(rows)

    z_names = []
    for lag in range(n_delays):
        z_names.extend([f"{name}__lag{lag}" for name in names])

    U_aligned = None
    if U is not None:
        U_arr = _as_2d_float(U, "U")
        if U_arr.shape[0] != n_time:
            raise ValueError(f"U must have the same number of rows as X before embedding; got {U_arr.shape[0]} and {n_time}.")
        U_aligned = U_arr[n_delays - 1 :, :]
    return Z, U_aligned, z_names


def make_delay_embeddings_for_trajectories(
    trajectories_X: Sequence[ArrayLike],
    trajectories_U: Sequence[ArrayLike | None] | None = None,
    *,
    n_delays: int,
    state_names: Sequence[str] | None = None,
) -> tuple[list[NDArray[np.float64]], list[NDArray[np.float64] | None], list[str]]:
    """Apply delay embedding to several independent trajectories."""

    if trajectories_U is None:
        trajectories_U = [None] * len(trajectories_X)
    if len(trajectories_X) != len(trajectories_U):
        raise ValueError("trajectories_X and trajectories_U must have the same length.")
    Zs: list[NDArray[np.float64]] = []
    Us: list[NDArray[np.float64] | None] = []
    z_names: list[str] | None = None
    for X, U in zip(trajectories_X, trajectories_U, strict=True):
        Z, U_aligned, names = make_delay_embedding(X, U, n_delays=n_delays, state_names=state_names)
        Zs.append(Z)
        Us.append(U_aligned)
        z_names = names
    return Zs, Us, z_names or []


def _as_2d_float(value: ArrayLike, name: str) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr
