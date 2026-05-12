from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import PODBasis, select_pod_sensors, reconstruct_from_sensors
from dmdc.cli import main


def _make_multicase_csv(path: Path) -> None:
    rows = []
    # Three short stable trajectories with a known input.  The test intentionally
    # keeps the data small so the sweep command remains fast in CI and examples.
    for case_idx, gain in enumerate([0.82, 0.90, 0.97], start=1):
        x = np.array([1.0 + 0.1 * case_idx, -0.25 * case_idx])
        for k in range(12):
            u = 0.03 * case_idx
            rows.append({"case_id": f"run_{case_idx:03d}", "time": float(k), "x1": x[0], "x2": x[1], "u1": u})
            x = np.array([gain * x[0] + 0.08 * x[1] + u, -0.04 * x[0] + 0.72 * x[1]])
    pd.DataFrame(rows).to_csv(path, index=False)


def test_pod_sparse_sensing_reconstructs_with_all_sensors():
    t = np.linspace(0.0, 1.0, 20)
    X = np.column_stack([np.sin(t), np.cos(t)])
    pod = PODBasis(rank="full", center=True).fit(X, state_names=["s", "c"])
    selected = select_pod_sensors(pod, n_sensors=2)
    X_hat = reconstruct_from_sensors(X[:, selected.selected_indices], pod, selected.selected_indices)
    assert X_hat.shape == X.shape
    assert np.linalg.norm(X - X_hat) / np.linalg.norm(X) < 1e-10
    assert len(selected.selected_state_names) == 2


def test_cli_pod_sensors_config(tmp_path: Path):
    data = tmp_path / "multi.csv"
    _make_multicase_csv(data)
    out = tmp_path / "pod_sensors"
    cfg = tmp_path / "pod_sensors.toml"
    cfg.write_text(
        f'''
[data]
path = "{data}"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]

[pod]
rank = "full"
center = true

[sensor_selection]
n_sensors = 2
outdir = "{out}"

[output]
plots = false
''',
        encoding="utf-8",
    )
    main(["pod-sensors", "--config", str(cfg)])
    assert (out / "selected_sensors.csv").exists()
    assert (out / "sparse_sensor_reconstruction.csv").exists()
    assert (out / "pod_sensor_summary.json").exists()


def test_cli_sweep_config(tmp_path: Path):
    data = tmp_path / "multi.csv"
    _make_multicase_csv(data)
    out = tmp_path / "sweep"
    cfg = tmp_path / "sweep.toml"
    cfg.write_text(
        f'''
[data]
path = "{data}"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[split]
train_cases = ["run_001", "run_002"]
test_cases = ["run_003"]

[sweep]
models = ["persistence", "pod_dmdc"]
pod_ranks = ["full"]
dmdc_ranks = ["full"]
n_delays = [1, 2]
outdir = "{out}"

[pod]
center = true

[output]
plots = false
''',
        encoding="utf-8",
    )
    main(["sweep", "--config", str(cfg)])
    results = pd.read_csv(out / "sweep_results.csv")
    assert not results.empty
    assert {"persistence", "pod_dmdc"}.issubset(set(results["model_name"]))
    assert (out / "best_models.csv").exists()
    assert (out / "runs").exists()
