from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import PODDynamicsRegressor
from dmdc.cli import main


def _make_multicase_csv(path: Path) -> None:
    rows = []
    for case_idx, gain in enumerate([0.8, 0.9, 1.0], start=1):
        x = np.array([1.0 + 0.1 * case_idx, -0.2 * case_idx])
        for k in range(10):
            u = 0.05 * case_idx
            rows.append({"case_id": f"run_{case_idx:03d}", "time": float(k), "x1": x[0], "x2": x[1], "u1": u})
            x = np.array([gain * x[0] + 0.1 * x[1] + u, -0.05 * x[0] + 0.7 * x[1]])
    pd.DataFrame(rows).to_csv(path, index=False)


def test_pod_dynamics_regressor_ridge_rollout():
    t = np.linspace(0, 1, 20)
    X = np.column_stack([np.sin(t), np.cos(t)])
    rom = PODDynamicsRegressor(pod_rank="full", model_type="ridge", center=True).fit(X, state_names=["s", "c"])
    pred = rom.rollout(X[0], n_steps=X.shape[0] - 1)
    assert pred.shape == X.shape
    assert rom.summary_.model_type == "ridge"
    assert rom.summary_.n_inputs == 0


def test_cli_pod_ml_single_case(tmp_path: Path):
    data = tmp_path / "data.csv"
    pd.DataFrame(
        {
            "time": [0, 1, 2, 3, 4, 5],
            "x1": [1.0, 0.8, 0.64, 0.512, 0.4096, 0.32768],
            "x2": [0.0, 0.1, 0.18, 0.244, 0.2952, 0.33616],
        }
    ).to_csv(data, index=False)
    out = tmp_path / "pod_ml"
    main([
        "pod-ml",
        "--data", str(data),
        "--state-cols", "x1", "x2",
        "--time-col", "time",
        "--pod-rank", "full",
        "--model-type", "ridge",
        "--center",
        "--outdir", str(out),
    ])
    assert (out / "pod_ml_model.pkl").exists()
    assert (out / "pod_ml_summary.json").exists()
    assert (out / "reconstructed_predictions.csv").exists()


def test_cli_pod_ml_config_and_compare(tmp_path: Path):
    data = tmp_path / "multi.csv"
    _make_multicase_csv(data)
    podml_out = tmp_path / "podml_config"
    cfg = tmp_path / "pod_ml.toml"
    cfg.write_text(
        f'''
[data]
path = "{data}"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[pod]
rank = "full"
center = true
scale = false

[ml]
model_type = "ridge"
outdir = "{podml_out}"

[output]
plots = false
''',
        encoding="utf-8",
    )
    main(["pod-ml", "--config", str(cfg)])
    assert (podml_out / "error_by_case.csv").exists()

    compare_out = tmp_path / "compare"
    main([
        "compare",
        "--data", str(data),
        "--case-col", "case_id",
        "--time-col", "time",
        "--state-cols", "x1", "x2",
        "--input-cols", "u1",
        "--train-cases", "run_001", "run_002",
        "--test-cases", "run_003",
        "--models", "persistence", "pod_dmdc", "pod_ml_ridge",
        "--pod-rank", "full",
        "--outdir", str(compare_out),
    ])
    comp = pd.read_csv(compare_out / "model_comparison.csv")
    assert "pod_ml_ridge" in set(comp["model_name"])
