from pathlib import Path

import pandas as pd

from dmdc.data import load_timeseries


def test_load_csv(tmp_path: Path):
    path = tmp_path / "data.csv"
    pd.DataFrame({"time": [0, 1, 2], "x": [1, 2, 3], "u": [0, 1, 0]}).to_csv(path, index=False)
    ds = load_timeseries(path, state_cols=["x"], input_cols=["u"], time_col="time")
    assert ds.X.shape == (3, 1)
    assert ds.U.shape == (3, 1)
    assert ds.dt == 1.0
