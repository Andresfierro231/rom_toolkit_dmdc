"""Stability diagnostics for learned discrete-time ROMs.

The diagnostics here are intentionally conservative: they warn the user when a
learned state-transition matrix may produce divergent rollouts, but they do not
modify a model unless an explicit opt-in stabilization routine is called.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .utils import write_json


@dataclass
class StabilitySummary:
    """Serializable stability summary for a discrete-time transition matrix."""

    spectral_radius: float
    n_eigenvalues: int
    n_unstable_eigenvalues: int
    max_real_part: float
    max_imag_abs: float
    condition_number: float | None
    status: str
    warning: str | None


def analyze_transition_matrix(
    A: ArrayLike,
    *,
    warn_if_spectral_radius_above: float = 1.0,
    marginal_tol: float = 1e-6,
) -> dict[str, Any]:
    """Analyze a discrete-time transition matrix.

    Parameters
    ----------
    A:
        Square transition matrix for ``x[k+1] = A x[k]`` or reduced coordinates.
    warn_if_spectral_radius_above:
        Threshold for declaring potential discrete-time instability.
    marginal_tol:
        Numerical tolerance around the unit circle.
    """

    arr = np.asarray(A, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"A must be square; got shape {arr.shape}.")
    eig = np.linalg.eigvals(arr)
    radii = np.abs(eig)
    spectral_radius = float(np.max(radii)) if eig.size else 0.0
    n_unstable = int(np.sum(radii > warn_if_spectral_radius_above + marginal_tol))
    cond = float(np.linalg.cond(arr)) if arr.size else None
    if spectral_radius > warn_if_spectral_radius_above + marginal_tol:
        status = "potentially_unstable"
        warning = (
            f"The learned A matrix has spectral radius {spectral_radius:.6g}, "
            f"above the discrete-time threshold {warn_if_spectral_radius_above:.6g}. "
            "Rollouts may diverge even when one-step error is small. Suggested actions: "
            "reduce rank, add regularization, scale variables, use POD-DMDc, or compare forecast-horizon error."
        )
    elif abs(spectral_radius - warn_if_spectral_radius_above) <= marginal_tol:
        status = "marginal"
        warning = (
            f"The learned A matrix has spectral radius {spectral_radius:.6g}, very close to the unit circle. "
            "Long rollouts may be sensitive to noise and numerical errors."
        )
    else:
        status = "stable_by_spectral_radius"
        warning = None
    summary = StabilitySummary(
        spectral_radius=spectral_radius,
        n_eigenvalues=int(eig.size),
        n_unstable_eigenvalues=n_unstable,
        max_real_part=float(np.max(eig.real)) if eig.size else 0.0,
        max_imag_abs=float(np.max(np.abs(eig.imag))) if eig.size else 0.0,
        condition_number=cond,
        status=status,
        warning=warning,
    )
    return {
        "summary": asdict(summary),
        "eigenvalues": eig,
        "eigenvalue_table": eigenvalue_table(eig),
        "warnings": [] if warning is None else [warning],
    }


def eigenvalue_table(eigenvalues: ArrayLike) -> pd.DataFrame:
    """Return eigenvalues as a CSV-friendly table."""

    eig = np.asarray(eigenvalues)
    return pd.DataFrame(
        {
            "index": np.arange(eig.size, dtype=int),
            "real": eig.real,
            "imag": eig.imag,
            "abs": np.abs(eig),
            "angle_rad": np.angle(eig),
        }
    )


def save_stability_outputs(result: dict[str, Any], outdir: str | Path) -> None:
    """Save stability diagnostics to JSON, CSV, and warnings text."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(result["summary"], out / "stability_summary.json")
    result["eigenvalue_table"].to_csv(out / "eigenvalues.csv", index=False)
    warnings = result.get("warnings", [])
    (out / "stability_warnings.txt").write_text("\n\n".join(warnings) if warnings else "No stability warnings emitted.\n", encoding="utf-8")


def plot_eigenvalues_table(eigen_df: pd.DataFrame, path: str | Path) -> None:
    """Plot eigenvalues in the complex plane with the unit circle."""

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), linestyle="--", label="unit circle")
    if not eigen_df.empty:
        ax.scatter(eigen_df["real"], eigen_df["imag"], label="eigenvalues")
    ax.axhline(0.0, linewidth=0.8)
    ax.axvline(0.0, linewidth=0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Real")
    ax.set_ylabel("Imaginary")
    ax.set_title("Discrete-time eigenvalues")
    ax.legend()
    ax.grid(True)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
