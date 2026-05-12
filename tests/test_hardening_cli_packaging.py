from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run_module(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "dmdc.cli", *args],
        cwd=cwd or Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )


def test_python_module_cli_entrypoints_work_from_source_tree(tmp_path: Path) -> None:
    """The CLI should be testable before users run an editable install."""

    guide = _run_module("guide")
    assert "Minimal workflows" in guide.stdout
    assert "dmdc campaign" in guide.stdout

    help_result = _run_module("--help")
    assert "Start with: dmdc guide" in help_result.stdout

    out = tmp_path / "guide.md"
    _run_module("guide", "--markdown", "--out", str(out))
    assert out.exists()
    assert "# DMDc/ROM Command Guide" in out.read_text(encoding="utf-8")


def test_console_script_help_if_installed() -> None:
    """When installed, the console script should expose the same command guide."""

    exe = shutil.which("dmdc")
    if exe is None:
        # Source-tree tests should not require an installed console script.
        return
    result = subprocess.run([exe, "guide"], text=True, capture_output=True, check=True, timeout=45)
    assert "Minimal workflows" in result.stdout


def test_central_campaign_dry_run_selected_steps(tmp_path: Path) -> None:
    cfg = tmp_path / "study.toml"
    cfg.write_text(
        f'''
[campaign]
name = "hardening_demo"
root = "{tmp_path / 'campaigns'}"
steps = ["import", "inspect", "compare", "dashboard"]

[execution]
mode = "local"

[importer]
source = "data/example_multicase_timeseries.csv"
source_type = "csv"
out = "{tmp_path / 'processed.csv'}"
output_format = "csv"

[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]

[output]
inspection_outdir = "{tmp_path / 'inspection'}"
comparison_outdir = "{tmp_path / 'comparison'}"
live_outdir = "{tmp_path / 'live'}"
''',
        encoding="utf-8",
    )
    result = _run_module("campaign", "--config", str(cfg), "--dry-run", "--steps", "inspect", "compare")
    assert "Campaign directory" in result.stdout
    assert "Next steps:" in result.stdout
    step_index = tmp_path / "campaigns" / "hardening_demo" / "campaign_step_index.csv"
    assert step_index.exists()
