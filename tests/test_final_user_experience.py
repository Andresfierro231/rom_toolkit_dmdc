from pathlib import Path
import subprocess
import sys


def test_final_navigation_docs_exist_and_link_core_workflows():
    required = [
        Path("WORKFLOWS.md"),
        Path("COMMANDS.md"),
        Path("docs/navigation/workflow_map.md"),
        Path("docs/navigation/command_index.md"),
        Path("configs/templates/one_command_local_workflow.toml"),
        Path("scripts/workflows/run_campaign_local.sh"),
        Path("USER_EXPERIENCE_REVIEW.md"),
    ]
    for path in required:
        assert path.exists(), f"Missing final UX artifact: {path}"
        assert path.read_text(encoding="utf-8").strip(), f"Empty final UX artifact: {path}"

    workflow_text = Path("WORKFLOWS.md").read_text(encoding="utf-8")
    assert "dmdc campaign" in workflow_text
    assert "--steps import inspect compare" in workflow_text
    assert "live_replay_adapt" in workflow_text


def test_guide_command_smoke(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "dmdc.cli", "guide"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "Minimal workflows" in result.stdout
    assert "dmdc campaign" in result.stdout
    assert "Live digital twin workflow" in result.stdout

    out = tmp_path / "guide.md"
    subprocess.run(
        [sys.executable, "-m", "dmdc.cli", "guide", "--markdown", "--out", str(out)],
        check=True,
        text=True,
        capture_output=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "# DMDc/ROM Command Guide" in text
    assert "One-command campaign workflow" in text


def test_one_command_template_dry_run_smoke(tmp_path):
    cfg = Path("configs/templates/one_command_local_workflow.toml")
    result = subprocess.run(
        [sys.executable, "-m", "dmdc.cli", "campaign", "--config", str(cfg), "--dry-run", "--steps", "inspect", "compare"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "Campaign directory" in result.stdout
    assert "Plan:" in result.stdout
    assert "Next steps:" in result.stdout
