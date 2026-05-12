from pathlib import Path

import numpy as np
import pandas as pd

from dmdc.pod import PODBasis, save_reconstruction_error_vs_rank
from dmdc.cli import main


def test_pod_fit_transform_inverse_full_rank():
    t = np.linspace(0, 1, 20)
    X = np.column_stack([np.sin(t), np.cos(t)])
    pod = PODBasis(rank="full", center=True).fit(X, state_names=["s", "c"])
    coeffs = pod.transform(X)
    recon = pod.inverse_transform(coeffs)
    assert coeffs.shape[0] == X.shape[0]
    assert coeffs.shape[1] == pod.rank_
    assert np.linalg.norm(X - recon) < 1e-10


def test_pod_rank_integer_and_energy_threshold():
    rng = np.random.default_rng(123)
    a = rng.normal(size=(40, 2))
    basis = rng.normal(size=(2, 5))
    X = a @ basis
    pod_int = PODBasis(rank=1, center=True).fit(X)
    assert pod_int.rank_ == 1
    pod_energy = PODBasis(rank=0.99, center=True).fit(X)
    assert pod_energy.rank_ <= 2


def test_save_reconstruction_error_vs_rank(tmp_path: Path):
    X = np.column_stack([np.arange(6.0), np.arange(6.0) ** 2])
    out = tmp_path / "errors.csv"
    df = save_reconstruction_error_vs_rank(X, out, center=True)
    assert out.exists()
    assert {"rank", "relative_frobenius_error", "cumulative_energy"}.issubset(df.columns)


def test_cli_pod(tmp_path: Path):
    data = tmp_path / "data.csv"
    out = tmp_path / "pod"
    pd.DataFrame({"time": [0, 1, 2, 3], "x1": [1.0, 0.5, 0.25, 0.125], "x2": [0.0, 1.0, 0.0, -1.0]}).to_csv(data, index=False)
    main(["pod", "--data", str(data), "--state-cols", "x1", "x2", "--time-col", "time", "--rank", "full", "--center", "--outdir", str(out)])
    assert (out / "pod_basis.pkl").exists()
    assert (out / "pod_coefficients.csv").exists()
    assert (out / "pod_summary.json").exists()
