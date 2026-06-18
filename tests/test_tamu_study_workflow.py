from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "tamu_loop_data_onboarding"


def test_tamu_study_files_exist_and_parse():
    required = [
        STUDY / "README.md",
        STUDY / "study_config.toml",
        STUDY / "scripts" / "run_01_inventory.sh",
        STUDY / "scripts" / "run_02_export_validation_cases.sh",
        ROOT / "docs" / "workflows" / "tamu_data_intake_and_validation.md",
    ]
    for path in required:
        assert path.exists(), path
    cfg = tomllib.loads((STUDY / "study_config.toml").read_text(encoding="utf-8"))
    assert cfg["study"]["name"] == "tamu_loop_data_onboarding"
    assert "raw_root" in cfg["paths"]


def test_tamu_study_shell_scripts_are_valid_bash():
    for script in sorted((STUDY / "scripts").glob("*.sh")):
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, f"{script}: {result.stderr}"
