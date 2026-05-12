from types import SimpleNamespace
from pathlib import Path

from dmdc.config import expand_case_runs, load_config
from dmdc.cli import cmd_fit, cmd_workflow


def test_load_and_expand_workflow_config():
    cfg = load_config("configs/example_workflow.toml")
    runs = expand_case_runs(cfg)
    assert len(runs) == 3
    assert runs[0]["case_id"] is None
    assert runs[1]["case_id"] == "run_001"
    assert runs[1]["outdir"].endswith("only_run_001")
    assert runs[2]["outdir"] == "outputs/my_custom_folder/run_002"


def test_fit_from_config(tmp_path):
    cfg_path = tmp_path / "fit.toml"
    outdir = tmp_path / "fit_output"
    cfg_path.write_text(
        f'''
[data]
path = "data/example_timeseries.csv"
time_col = "time"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[model]
rank = "full"
n_delays = 1

[output]
outdir = "{outdir}"
plots = false
'''
    )
    args = SimpleNamespace(
        command="fit",
        config=str(cfg_path),
        data=None,
        state_cols=None,
        input_cols=[],
        time_col=None,
        case_col=None,
        case_id=None,
        rank="full",
        center=False,
        scale=False,
        outdir=None,
        plots=False,
        n_delays=1,
    )
    cmd_fit(args)
    assert (outdir / "model.pkl").exists()
    assert (outdir / "diagnostics.json").exists()


def test_workflow_creates_separate_case_folders(tmp_path):
    cfg_path = tmp_path / "workflow.toml"
    root = tmp_path / "cases"
    cfg_path.write_text(
        f'''
[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[model]
rank = "full"
n_delays = 1

[output]
root = "{root}"
plots = false

[[cases]]
name = "run_001_fit"
case_id = "run_001"

[[cases]]
name = "run_002_fit"
case_id = "run_002"
'''
    )
    cmd_workflow(SimpleNamespace(config=str(cfg_path)))
    assert (root / "run_001_fit" / "model.pkl").exists()
    assert (root / "run_002_fit" / "model.pkl").exists()
