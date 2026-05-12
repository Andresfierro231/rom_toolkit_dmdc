from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest

from dmdc.adaptive import AdaptiveDMDcModel
from dmdc.archive_benchmark import ArchiveBenchmarkConfig, run_archive_benchmark
from dmdc.kalman import LinearKalmanFilter
from dmdc.model import DMDcModel
from dmdc.pod import PODBasis
from dmdc.regularized import RegularizedDMDcModel


def test_dmdc_recovers_known_linear_system() -> None:
    rng = np.random.default_rng(4)
    A = np.array([[0.9, 0.1], [-0.05, 0.85]])
    B = np.array([[0.2], [-0.1]])
    n = 200
    X = np.zeros((n, 2))
    X[0] = [1.0, -0.5]
    U = rng.normal(size=(n, 1))
    for k in range(n - 1):
        X[k + 1] = A @ X[k] + B[:, 0] * U[k, 0]

    model = DMDcModel(rank="full").fit(X, U)
    assert np.allclose(model.A_, A, atol=1e-10)
    assert np.allclose(model.B_, B, atol=1e-10)


def test_pod_reconstruction_error_decreases_with_rank() -> None:
    rng = np.random.default_rng(5)
    X = rng.normal(size=(120, 6))
    errors = []
    for rank in [1, 2, 4, 6]:
        pod = PODBasis(rank=rank, center=True).fit(X)
        errors.append(pod.reconstruction_error(X)["relative_frobenius_error"])
    assert errors == sorted(errors, reverse=True)
    assert errors[-1] < 1e-12


def test_adaptive_dmdc_recovers_continuous_decay_on_nonuniform_time() -> None:
    t = np.cumsum(np.linspace(0.05, 0.15, 80))
    # Use Euler-generated data so the finite-difference adaptive model has an exact target.
    a = -0.7
    b = 0.4
    u = np.sin(0.3 * t)
    x = np.zeros_like(t)
    x[0] = 1.5
    for k, dt in enumerate(np.diff(t)):
        x[k + 1] = x[k] + dt * (a * x[k] + b * u[k])
    model = AdaptiveDMDcModel(rank="full", alpha=0.0).fit(x[:, None], u[:, None], time=t)
    assert np.isclose(model.A_c_[0, 0], a, atol=1e-10)
    assert np.isclose(model.B_c_[0, 0], b, atol=1e-10)


def test_kalman_filter_reduces_noisy_measurement_error() -> None:
    rng = np.random.default_rng(6)
    n = 80
    true = np.zeros(n)
    true[0] = 2.0
    for k in range(n - 1):
        true[k + 1] = 0.95 * true[k]
    y = true + rng.normal(scale=0.2, size=n)
    kf = LinearKalmanFilter(A=[[0.95]], C=[[1.0]], Q=[[1e-4]], R=[[0.04]])
    result = kf.filter(y[:, None], x0=[y[0]], P0=[[1.0]])
    filtered = result.state_estimates[:, 0]
    assert np.sqrt(np.mean((filtered - true) ** 2)) < np.sqrt(np.mean((y - true) ** 2))


def test_regularized_dmdc_shrinks_ill_conditioned_coefficients() -> None:
    rng = np.random.default_rng(7)
    base = rng.normal(size=80)
    X0 = np.column_stack([base, base + 1e-6 * rng.normal(size=80)])
    X1 = X0 @ np.array([[0.9, 0.0], [0.0, 0.8]]).T + 1e-3 * rng.normal(size=(80, 2))
    unreg = DMDcModel(rank="full").fit_transitions(X0, X1)
    reg = RegularizedDMDcModel(rank="full", alpha=1e-2).fit_transitions(X0, X1)
    assert np.linalg.norm(reg.A_) < np.linalg.norm(unreg.A_)


def test_archive_benchmark_writes_core_metrics(tmp_path: Path) -> None:
    result = run_archive_benchmark(
        ArchiveBenchmarkConfig(
            n_rows=200,
            n_states=4,
            outdir=str(tmp_path / "bench"),
            archive_root=str(tmp_path / "bench" / "archive"),
            archive_format="csv",
            make_quicklooks=False,
            windows_seconds=[60.0],
        )
    )
    metrics = pd.read_csv(result.metrics_csv)
    for col in ["archive_write_mb_per_sec", "summary_rows_per_sec", "peak_memory_mb", "summarize_seconds"]:
        assert col in metrics.columns
        assert np.isfinite(float(metrics.loc[0, col]))
    summary = json.loads(Path(result.summary_json).read_text(encoding="utf-8"))
    assert summary["n_rows"] == 200


@pytest.mark.large
def test_large_archive_benchmark_marker_is_available(tmp_path: Path) -> None:
    """Opt-in smoke test for larger benchmark plumbing.

    This intentionally remains modest so it can run on a workstation when the
    user asks for ``pytest -m large``.  It is skipped by default in normal CI.
    """

    result = run_archive_benchmark(
        ArchiveBenchmarkConfig(
            n_rows=5_000,
            n_states=8,
            outdir=str(tmp_path / "large_bench"),
            archive_root=str(tmp_path / "large_bench" / "archive"),
            archive_format="csv",
            make_quicklooks=False,
            windows_seconds=[60.0],
        )
    )
    assert Path(result.metrics_csv).exists()
