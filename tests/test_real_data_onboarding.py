from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONBOARDING = ROOT / "examples" / "real_data_onboarding"


def test_real_data_onboarding_files_exist_and_are_linked():
    required = [
        ONBOARDING / "README.md",
        ONBOARDING / "column_map.toml",
        ONBOARDING / "study_config.toml",
        ONBOARDING / "notes.md",
        ROOT / "docs" / "tutorials" / "real_data_onboarding.md",
    ]
    for path in required:
        assert path.exists(), path

    readme = (ONBOARDING / "README.md").read_text(encoding="utf-8")
    assert "adaptive" in readme.lower()
    assert "dmdc import-data" in readme
    assert "dmdc live-dashboard" in readme
    assert "Do not assume uniform" not in readme  # phrasing is positive: default assumption is adaptive/nonuniform

    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "examples/real_data_onboarding/README.md" in root_readme


def test_real_data_onboarding_configs_parse_and_have_expected_sections():
    study = tomllib.loads((ONBOARDING / "study_config.toml").read_text(encoding="utf-8"))
    for section in [
        "importer",
        "data",
        "time",
        "split",
        "adaptive",
        "compare",
        "validation",
        "stream",
        "monitor",
        "live_adaptation",
        "live_archive",
        "dashboard",
        "output",
    ]:
        assert section in study
    assert study["time"]["assume_uniform"] is False
    assert "adaptive_dmdc" in study["compare"]["models"]
    assert study["live_adaptation"]["method"] == "horizon_state_bias"

    column_map = tomllib.loads((ONBOARDING / "column_map.toml").read_text(encoding="utf-8"))
    assert "columns" in column_map
    assert column_map["columns"]["TC01"] == "TP1"


def test_real_data_onboarding_shell_scripts_are_valid_bash():
    scripts = sorted((ONBOARDING / "scripts").glob("*.sh"))
    assert scripts
    for script in scripts:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, f"{script}: {result.stderr}"


def test_real_data_onboarding_includes_incremental_workflow_steps():
    scripts_dir = ONBOARDING / "scripts"
    expected = [
        "run_01_import.sh",
        "run_02_inspect.sh",
        "run_03_adaptive_fit.sh",
        "run_04_pod_dmdc.sh",
        "run_05_compare_models.sh",
        "run_06_validate_unseen_cases.sh",
        "run_07_live_replay_monitor.sh",
        "run_08_live_replay_adapt.sh",
        "run_09_live_dashboard.sh",
        "run_10_operator_report.sh",
    ]
    for name in expected:
        assert (scripts_dir / name).exists()
