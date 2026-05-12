from pathlib import Path

import pandas as pd

from dmdc.resampling import inspect_table, resample_all_cases
from dmdc.cli import main


def test_inspect_table_detects_irregular_time():
    df = pd.DataFrame({"case_id": ["a", "a", "a"], "time": [0.0, 1.0, 3.5], "x": [1.0, 2.0, 3.0], "u": [0.0, 0.1, 0.2]})
    result = inspect_table(df, time_col="time", case_col="case_id", state_cols=["x"], input_cols=["u"])
    codes = {w.code for w in result.warnings}
    assert "IRREGULAR_TIME_STEP" in codes
    assert not result.dt_summary_by_case.empty


def test_resample_all_cases():
    df = pd.DataFrame({"case_id": ["a", "a", "a"], "time": [0.0, 1.0, 2.0], "x": [0.0, 2.0, 4.0]})
    out = resample_all_cases(df, time_col="time", case_col="case_id", dt=0.5, columns=["x"])
    assert len(out) == 5
    assert out.loc[1, "x"] == 1.0


def test_cli_inspect_and_resample(tmp_path: Path):
    data = tmp_path / "data.csv"
    inspect_out = tmp_path / "inspection"
    resampled = tmp_path / "resampled.csv"
    pd.DataFrame({"case_id": ["a", "a", "a"], "time": [0.0, 1.0, 2.0], "x": [0.0, 2.0, 4.0], "u": [1.0, 1.0, 1.0]}).to_csv(data, index=False)
    main(["inspect-data", "--data", str(data), "--state-cols", "x", "--input-cols", "u", "--time-col", "time", "--case-col", "case_id", "--outdir", str(inspect_out)])
    main(["resample", "--data", str(data), "--time-col", "time", "--case-col", "case_id", "--columns", "x", "u", "--dt", "0.5", "--out", str(resampled)])
    assert (inspect_out / "inspection_summary.json").exists()
    assert (inspect_out / "warnings.txt").exists()
    assert resampled.exists()


def test_cli_inspect_config_applies_state_and_input_columns(tmp_path: Path):
    """Regression test: config-provided state/input columns must override argparse [] defaults."""
    data = tmp_path / "data.csv"
    outdir = tmp_path / "inspection_from_config"
    config = tmp_path / "inspect.toml"
    pd.DataFrame(
        {
            "case_id": ["a", "a", "a"],
            "time": [0.0, 1.0, 2.0],
            "x": [0.0, 2.0, 4.0],
            "u": [1.0, 1.0, 1.0],
        }
    ).to_csv(data, index=False)
    config.write_text(
        f'''
[data]
path = "{data}"
time_col = "time"
case_col = "case_id"
state_cols = ["x"]
input_cols = ["u"]

[output]
outdir = "{outdir}"
'''.strip(),
        encoding="utf-8",
    )
    main(["inspect-data", "--config", str(config)])
    state_variance = pd.read_csv(outdir / "state_variance.csv")
    input_variance = pd.read_csv(outdir / "input_variance.csv")
    assert state_variance["column"].tolist() == ["x"]
    assert input_variance["column"].tolist() == ["u"]
