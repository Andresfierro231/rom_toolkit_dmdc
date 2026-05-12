"""Plotting utilities for DMDc workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray

from .model import DMDcModel


def plot_singular_values(model: DMDcModel, path: str | Path | None = None) -> None:
    s = np.asarray(model.metadata_.singular_values)
    fig, ax = plt.subplots()
    ax.semilogy(np.arange(1, len(s) + 1), s, marker="o")
    ax.set_xlabel("Index")
    ax.set_ylabel("Singular value")
    ax.set_title("Singular value spectrum of Omega = [X; U]")
    ax.grid(True, which="both")
    _save_or_show(fig, path)


def plot_eigenvalues(model: DMDcModel, path: str | Path | None = None) -> None:
    eigvals = model.eigenvalues_
    theta = np.linspace(0, 2 * np.pi, 400)
    fig, ax = plt.subplots()
    ax.plot(np.cos(theta), np.sin(theta), linestyle="--", label="unit circle")
    ax.scatter(eigvals.real, eigvals.imag, marker="x", label="eig(A)")
    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)
    ax.set_xlabel("Real")
    ax.set_ylabel("Imaginary")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("DMDc eigenvalues")
    ax.legend()
    ax.grid(True)
    _save_or_show(fig, path)


def plot_true_vs_predicted(
    X_true: NDArray[np.float64],
    X_pred: NDArray[np.float64],
    *,
    time: NDArray[np.float64] | None = None,
    state_names: Sequence[str] | None = None,
    path: str | Path | None = None,
    max_states: int = 8,
) -> None:
    n_states = X_true.shape[1]
    n_plot = min(n_states, max_states)
    t = time if time is not None else np.arange(X_true.shape[0])
    fig, ax = plt.subplots()
    for i in range(n_plot):
        name = state_names[i] if state_names and i < len(state_names) else f"x{i}"
        ax.plot(t, X_true[:, i], label=f"true {name}")
        ax.plot(t, X_pred[:, i], linestyle="--", label=f"pred {name}")
    ax.set_xlabel("time" if time is not None else "sample index")
    ax.set_ylabel("state value")
    ax.set_title("True vs. DMDc rollout prediction")
    ax.legend(ncol=2, fontsize="small")
    ax.grid(True)
    _save_or_show(fig, path)


def plot_reconstruction_error_vs_sensors(error_frame, path: str | Path | None = None) -> None:
    """Plot relative reconstruction error as QR-selected sensors are added."""
    fig, ax = plt.subplots()
    ax.plot(error_frame["n_sensors"], error_frame["relative_reconstruction_error"], marker="o")
    ax.set_xlabel("number of selected sensors/states")
    ax.set_ylabel("relative reconstruction error")
    ax.set_title("Q-DEIM reconstruction error vs selected sensors")
    ax.grid(True)
    _save_or_show(fig, path)


def _save_or_show(fig: plt.Figure, path: str | Path | None) -> None:
    fig.tight_layout()
    if path is None:
        plt.show()
    else:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out)
    plt.close(fig)


def plot_pod_singular_values(singular_values, path: str | Path | None = None) -> None:
    """Plot POD singular values."""
    s = np.asarray(singular_values, dtype=float)
    fig, ax = plt.subplots()
    ax.semilogy(np.arange(1, len(s) + 1), s, marker="o")
    ax.set_xlabel("mode index")
    ax.set_ylabel("singular value")
    ax.set_title("POD singular value spectrum")
    ax.grid(True, which="both")
    _save_or_show(fig, path)


def plot_pod_cumulative_energy(cumulative_energy, path: str | Path | None = None) -> None:
    """Plot cumulative POD energy."""
    e = np.asarray(cumulative_energy, dtype=float)
    fig, ax = plt.subplots()
    ax.plot(np.arange(1, len(e) + 1), e, marker="o")
    ax.set_xlabel("number of modes")
    ax.set_ylabel("cumulative energy")
    ax.set_ylim(0, 1.02)
    ax.set_title("POD cumulative energy")
    ax.grid(True)
    _save_or_show(fig, path)


def plot_pod_reconstruction_error_vs_rank(error_frame, path: str | Path | None = None) -> None:
    """Plot POD reconstruction error versus rank."""
    fig, ax = plt.subplots()
    ax.plot(error_frame["rank"], error_frame["relative_frobenius_error"], marker="o")
    ax.set_xlabel("POD rank")
    ax.set_ylabel("relative reconstruction error")
    ax.set_title("POD reconstruction error vs rank")
    ax.grid(True)
    _save_or_show(fig, path)


def plot_pod_coefficients(coefficients, path: str | Path | None = None, *, time=None, max_modes: int = 8) -> None:
    """Plot the first few POD modal coefficient time series."""
    a = np.asarray(coefficients, dtype=float)
    t = np.asarray(time) if time is not None else np.arange(a.shape[0])
    n_plot = min(a.shape[1], max_modes)
    fig, ax = plt.subplots()
    for j in range(n_plot):
        ax.plot(t, a[:, j], label=f"a{j+1}")
    ax.set_xlabel("time" if time is not None else "sample index")
    ax.set_ylabel("modal coefficient")
    ax.set_title("POD modal coefficients")
    ax.legend(ncol=2, fontsize="small")
    ax.grid(True)
    _save_or_show(fig, path)
