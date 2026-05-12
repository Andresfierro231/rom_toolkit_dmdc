import numpy as np
import pandas as pd

from dmdc import DMDcModel, load_trajectories


def test_fit_trajectories_does_not_connect_cases():
    A = np.array([[0.9, 0.1], [-0.05, 0.95]])
    B = np.array([[0.2], [0.1]])
    Xs = []
    Us = []
    for x0 in [np.array([1.0, 0.0]), np.array([-2.0, 1.0]), np.array([0.5, -1.0])]:
        U = np.ones((8, 1)) * 0.3
        X = np.zeros((9, 2))
        X[0] = x0
        for k in range(8):
            X[k + 1] = A @ X[k] + B @ U[k]
        Xs.append(X)
        Us.append(U)

    model = DMDcModel(rank="full").fit_trajectories(Xs, Us)
    assert model.metadata_.n_trajectories == 3
    assert model.metadata_.n_transitions == 24
    assert np.allclose(model.A_, A, atol=1e-10)
    assert np.allclose(model.B_, B, atol=1e-10)


def test_load_trajectories_from_case_column(tmp_path):
    rows = []
    for case_id, offset in [("a", 0.0), ("b", 10.0)]:
        for k in range(4):
            rows.append({"case_id": case_id, "time": float(k), "x1": offset + k, "x2": 2*k, "u1": 1.0})
    path = tmp_path / "multi.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    datasets = load_trajectories(path, state_cols=["x1", "x2"], input_cols=["u1"], time_col="time", case_col="case_id")
    assert len(datasets) == 2
    assert datasets[0].case_id == "a"
    assert datasets[1].case_id == "b"
    assert datasets[0].X.shape == (4, 2)
