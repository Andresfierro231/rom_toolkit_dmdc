"""Kalman filtering and POD-space state estimation.

A Kalman filter combines a dynamical model with noisy measurements.  In ROM work
this is often used in reduced coordinates:

    a[k+1] = A_r a[k] + B_r u[k] + w[k]
    y[k]   = C Phi_r a[k] + v[k]

where ``a`` are POD coefficients and ``y`` are sparse sensor measurements.  The
filter estimates the latent coefficients from partial observations, then POD
reconstructs the full state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np
from numpy.typing import ArrayLike


@dataclass
class KalmanFilterResult:
    """Output of a linear Kalman filter."""

    state_estimates: np.ndarray
    covariance_estimates: np.ndarray
    innovations: np.ndarray


class LinearKalmanFilter:
    """Minimal discrete-time linear Kalman filter.

    Parameters use the standard notation:
    ``x[k+1]=A x[k]+B u[k]+w[k]`` and ``y[k]=C x[k]+D u[k]+v[k]``.
    """

    def __init__(self, A: ArrayLike, C: ArrayLike, *, B: ArrayLike | None = None, D: ArrayLike | None = None, Q: ArrayLike | None = None, R: ArrayLike | None = None) -> None:
        self.A = np.asarray(A, dtype=float)
        self.C = np.asarray(C, dtype=float)
        self.B = None if B is None else np.asarray(B, dtype=float)
        self.D = None if D is None else np.asarray(D, dtype=float)
        n = self.A.shape[0]
        m = self.C.shape[0]
        self.Q = np.eye(n) * 1e-8 if Q is None else np.asarray(Q, dtype=float)
        self.R = np.eye(m) * 1e-4 if R is None else np.asarray(R, dtype=float)
        if self.A.shape != (n, n):
            raise ValueError("A must be square.")
        if self.C.shape[1] != n:
            raise ValueError("C must have one column per state variable.")

    def filter(self, measurements: ArrayLike, *, x0: ArrayLike, P0: ArrayLike | None = None, U: ArrayLike | None = None) -> KalmanFilterResult:
        y = np.asarray(measurements, dtype=float)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        n_steps = y.shape[0]
        n = self.A.shape[0]
        x = np.asarray(x0, dtype=float).reshape(n)
        P = np.eye(n) if P0 is None else np.asarray(P0, dtype=float)
        U_arr = None if U is None else np.asarray(U, dtype=float)
        xs = np.zeros((n_steps, n))
        Ps = np.zeros((n_steps, n, n))
        innov = np.zeros_like(y)
        I = np.eye(n)
        for k in range(n_steps):
            u = None if U_arr is None else U_arr[k].reshape(-1)
            if k > 0:
                x = self.A @ x + (self.B @ u if self.B is not None and u is not None else 0.0)
                P = self.A @ P @ self.A.T + self.Q
            y_pred = self.C @ x + (self.D @ u if self.D is not None and u is not None else 0.0)
            innovation = y[k] - y_pred
            S = self.C @ P @ self.C.T + self.R
            K = P @ self.C.T @ np.linalg.pinv(S)
            x = x + K @ innovation
            P = (I - K @ self.C) @ P
            xs[k] = x
            Ps[k] = P
            innov[k] = innovation
        return KalmanFilterResult(xs, Ps, innov)


def pod_measurement_matrix(pod_modes: ArrayLike, selected_indices: Sequence[int], scale: ArrayLike | None = None) -> np.ndarray:
    """Return the POD measurement matrix for selected full-state rows.

    If the POD basis was fit with scaling, the physical reconstruction is
    ``x = mean + diag(scale) Phi a`` rather than simply ``mean + Phi a``.
    Pass ``pod_basis.scale_`` so sparse sensor estimation is performed in
    physical units.  When ``scale`` is omitted, this reduces to the traditional
    ``C Phi`` expression.
    """

    Phi = np.asarray(pod_modes, dtype=float)
    H = Phi[list(selected_indices), :]
    if scale is not None:
        s = np.asarray(scale, dtype=float).reshape(-1)
        H = s[list(selected_indices), None] * H
    return H


def estimate_pod_state_with_kalman(
    pod_basis,
    reduced_A: ArrayLike,
    measurements: ArrayLike,
    selected_indices: Sequence[int],
    *,
    reduced_B: ArrayLike | None = None,
    U: ArrayLike | None = None,
    Q: ArrayLike | None = None,
    R: ArrayLike | None = None,
) -> tuple[np.ndarray, np.ndarray, KalmanFilterResult]:
    """Estimate POD coefficients and reconstruct full states from sparse sensors."""

    C_red = pod_measurement_matrix(pod_basis.modes_, selected_indices, getattr(pod_basis, "scale_", None))
    y = np.asarray(measurements, dtype=float)
    mean_selected = pod_basis.mean_[list(selected_indices)] if getattr(pod_basis, "mean_", None) is not None else 0.0
    y_centered = y - mean_selected
    x0 = np.linalg.pinv(C_red) @ y_centered[0]
    kf = LinearKalmanFilter(reduced_A, C_red, B=reduced_B, Q=Q, R=R)
    result = kf.filter(y_centered, x0=x0, U=U)
    X_recon = pod_basis.inverse_transform(result.state_estimates)
    return result.state_estimates, X_recon, result
