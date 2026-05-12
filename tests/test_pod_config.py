from types import SimpleNamespace
from pathlib import Path

from dmdc.config import flatten_pod_config, load_config
from dmdc.cli import cmd_pod


def test_flatten_pod_config():
    cfg = load_config("configs/example_pod.toml")
    flat = flatten_pod_config(cfg)
    assert flat["data"] == "data/example_timeseries.csv"
    assert flat["state_cols"] == ["x1", "x2"]
    assert flat["center"] is True


def test_cmd_pod_from_config(tmp_path: Path):
    cfg = tmp_path / "pod.toml"
    out = tmp_path / "pod_out"
    cfg.write_text(
        f'''
[data]
path = "data/example_timeseries.csv"
time_col = "time"
state_cols = ["x1", "x2"]

[pod]
rank = 0.999
center = true
scale = false

[output]
outdir = "{out}"
plots = false
'''
    )
    args = SimpleNamespace(command="pod", config=str(cfg), data=None, state_cols=None, time_col=None, case_col=None, case_id=None, rank="full", energy_threshold=None, center=False, scale=False, outdir=None, plots=False)
    cmd_pod(args)
    assert (out / "pod_basis.pkl").exists()
