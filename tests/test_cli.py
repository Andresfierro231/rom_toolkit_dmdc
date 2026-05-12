from pathlib import Path

import pandas as pd

from dmdc.cli import main


def test_cli_fit(tmp_path: Path):
    data = tmp_path / "data.csv"
    out = tmp_path / "out"
    pd.DataFrame({"time": [0, 1, 2, 3], "x": [1.0, 0.8, 0.64, 0.512], "u": [0, 0, 0, 0]}).to_csv(data, index=False)
    main(["fit", "--data", str(data), "--state-cols", "x", "--input-cols", "u", "--time-col", "time", "--outdir", str(out)])
    assert (out / "model.pkl").exists()
    assert (out / "diagnostics.json").exists()
