from pathlib import Path

import numpy as np
import pandas as pd

from dmdc.adaptive import AdaptiveDMDcModel
from dmdc.cli import main


def test_adaptive_dmdc_fits_nonuniform_decay() -> None:
    t = np.array([0.0, 0.05, 0.12, 0.25, 0.43, 0.9, 1.4, 2.0])
    x = np.exp(-0.4 * t)[:, None]
    model = AdaptiveDMDcModel(alpha=0.0).fit(x, time=t)
    pred = model.rollout(x[0], time_future=t)
    assert pred.shape == x.shape
    assert np.sqrt(np.mean((pred - x) ** 2)) < 1.0e-2
    assert model.metadata_.min_dt < model.metadata_.max_dt


def test_adaptive_fit_cli_multicase_nonuniform(tmp_path: Path) -> None:
    rows = []
    for case_id, rate in [("a", -0.2), ("b", -0.35)]:
        t = np.array([0.0, 0.1, 0.27, 0.55, 1.0])
        x = np.exp(rate * t)
        for ti, xi in zip(t, x):
            rows.append({"case_id": case_id, "time": ti, "x1": xi})
    data = tmp_path / "nonuniform.csv"
    pd.DataFrame(rows).to_csv(data, index=False)
    out = tmp_path / "out"
    main([
        "adaptive-fit",
        "--data", str(data),
        "--time-col", "time",
        "--case-col", "case_id",
        "--state-cols", "x1",
        "--outdir", str(out),
    ])
    assert (out / "adaptive_dmdc_summary.json").exists()
    assert (out / "adaptive_rollout_predictions.csv").exists()
    assert (out / "provenance.json").exists()


def test_compare_supports_adaptive_dmdc(tmp_path: Path) -> None:
    rows = []
    for case_id, rate in [("train", -0.2), ("test", -0.22)]:
        t = np.array([0.0, 0.05, 0.16, 0.4, 0.9, 1.5])
        x = np.exp(rate * t)
        for ti, xi in zip(t, x):
            rows.append({"case_id": case_id, "time": ti, "x1": xi})
    data = tmp_path / "cases.csv"
    pd.DataFrame(rows).to_csv(data, index=False)
    out = tmp_path / "compare"
    main([
        "compare",
        "--data", str(data),
        "--time-col", "time",
        "--case-col", "case_id",
        "--state-cols", "x1",
        "--train-cases", "train",
        "--test-cases", "test",
        "--models", "persistence", "adaptive_dmdc",
        "--outdir", str(out),
    ])
    table = pd.read_csv(out / "model_comparison.csv")
    assert "adaptive_dmdc" in set(table["model_name"])
