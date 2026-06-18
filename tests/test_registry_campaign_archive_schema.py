from __future__ import annotations
from types import SimpleNamespace
from pathlib import Path
import json
import pandas as pd
import pytest

from dmdc.archive_schema import validate_archive_schema, build_archive_context_index
from dmdc.campaign import run_campaign
from dmdc import cli as cli_module
from dmdc.cli import main
from dmdc.live_archive import LiveArchiveConfig, archive_live_run
from dmdc.model_registry import register_model, promote_model, resolve_model, read_registry_index


def test_model_registry_register_promote_resolve(tmp_path: Path):
    model = tmp_path / "model.pkl"
    model.write_bytes(b"demo model bytes")
    registry = tmp_path / "registry"
    meta = register_model(model, name="simple loop", registry_root=registry, stage="candidate", version="v1", model_type="demo")
    assert Path(meta.registered_model_path).exists()
    idx = read_registry_index(registry)
    assert len(idx) == 1
    promote_model("simple_loop", version="v1", stage="production", registry_root=registry)
    resolved = resolve_model(name="simple_loop", stage="production", registry_root=registry)
    assert resolved["model_path"].endswith("model.pkl")
    assert resolved["version"] == "v1"


def test_archive_schema_validation_and_context(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    pd.DataFrame({"time": [0.0, 1.0], "TP1": [300.0, 301.0]}).to_csv(run / "cleaned_stream_log.csv", index=False)
    pd.DataFrame({"time": [0.0, 1.0], "trust_score": [1.0, 0.9]}).to_csv(run / "live_trust_score.csv", index=False)
    archive = tmp_path / "archive"
    archive_live_run(run, LiveArchiveConfig(root=str(archive), format="csv"))
    result = validate_archive_schema(archive)
    assert result.manifest_rows >= 1
    assert Path(result.validation_report).exists()
    assert Path(result.context_index_csv).exists()
    context = pd.read_csv(result.context_index_csv)
    assert "data_kind" in context.columns
    paths = build_archive_context_index(archive)
    assert Path(paths["data_kind_summary_csv"]).exists()


def test_campaign_dry_run_writes_plan(tmp_path: Path):
    cfg = tmp_path / "campaign.toml"
    cfg.write_text(
        f'''
[campaign]
name = "demo"
root = "{tmp_path / 'campaigns'}"
steps = ["inspect", "compare"]
[execution]
mode = "local"
[data]
path = "data/example_multicase_timeseries.csv"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]
time_col = "time"
[output]
inspection_outdir = "{tmp_path / 'inspection'}"
comparison_outdir = "{tmp_path / 'compare'}"
''',
        encoding="utf-8",
    )
    result = run_campaign(cfg, dry_run=True)
    assert Path(result.plan_md).exists()
    assert Path(result.step_index_csv).exists()
    assert Path(result.derived_config_path).exists()
    assert Path(result.run_index_csv).exists()
    assert Path(result.campaign_group_dir).exists()
    assert Path(result.campaign_dir).parent == Path(result.campaign_group_dir)
    assert result.steps_requested == ["inspect", "compare"]


def test_campaign_runs_are_unique_and_indexed(tmp_path: Path):
    cfg = tmp_path / "campaign.toml"
    cfg.write_text(
        f'''
[campaign]
name = "demo"
root = "{tmp_path / 'campaigns'}"
steps = ["inspect"]
[execution]
mode = "local"
[data]
path = "data/example_multicase_timeseries.csv"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]
time_col = "time"
[output]
inspection_outdir = "{tmp_path / 'inspection'}"
''',
        encoding="utf-8",
    )
    first = run_campaign(cfg, dry_run=True)
    second = run_campaign(cfg, dry_run=True)
    assert first.run_id != second.run_id
    assert Path(first.campaign_dir) != Path(second.campaign_dir)
    run_index = pd.read_csv(second.run_index_csv)
    assert len(run_index) == 2
    latest = (Path(second.campaign_group_dir) / "latest_run.txt").read_text(encoding="utf-8").strip()
    assert latest == second.campaign_dir


def test_new_cli_help_commands(capsys):
    for command in ["model-register", "model-list", "model-promote", "model-resolve", "validate-archive-schema", "archive-context", "resources", "campaign", "tamu-inventory", "tamu-validation-export"]:
        try:
            main([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0
    out = capsys.readouterr().out
    assert "model" in out.lower() or "campaign" in out.lower()


def test_campaign_cli_raises_nonzero_exit_on_failed_run(monkeypatch, tmp_path: Path, capsys):
    result = SimpleNamespace(
        campaign_dir=str(tmp_path / "campaign"),
        campaign_group_dir=str(tmp_path / "campaigns"),
        run_id="run_demo",
        steps_requested=["inspect"],
        steps_run=[],
        n_succeeded=0,
        n_failed=1,
        dry_run=False,
        step_index_csv=str(tmp_path / "campaign" / "campaign_step_index.csv"),
        plan_md=str(tmp_path / "campaign" / "campaign_plan.md"),
        next_steps_md=str(tmp_path / "campaign" / "next_steps.md"),
        derived_config_path=str(tmp_path / "campaign" / "config.toml"),
        run_index_csv=str(tmp_path / "campaigns" / "campaign_runs.csv"),
    )
    monkeypatch.setattr(cli_module, "run_campaign", lambda config, steps=None, dry_run=False: result)
    with pytest.raises(SystemExit) as exc:
        main(["campaign", "--config", str(tmp_path / "study.toml")])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "failed: 1" in out


def test_campaign_cli_dry_run_does_not_raise_on_zero_failures(monkeypatch, tmp_path: Path, capsys):
    result = SimpleNamespace(
        campaign_dir=str(tmp_path / "campaign"),
        campaign_group_dir=str(tmp_path / "campaigns"),
        run_id="run_demo",
        steps_requested=["inspect"],
        steps_run=["inspect"],
        n_succeeded=0,
        n_failed=0,
        dry_run=True,
        step_index_csv=str(tmp_path / "campaign" / "campaign_step_index.csv"),
        plan_md=str(tmp_path / "campaign" / "campaign_plan.md"),
        next_steps_md=str(tmp_path / "campaign" / "next_steps.md"),
        derived_config_path=str(tmp_path / "campaign" / "config.toml"),
        run_index_csv=str(tmp_path / "campaigns" / "campaign_runs.csv"),
    )
    monkeypatch.setattr(cli_module, "run_campaign", lambda config, steps=None, dry_run=False: result)
    main(["campaign", "--config", str(tmp_path / "study.toml"), "--dry-run"])
    out = capsys.readouterr().out
    assert "dry-run: True" in out
    assert "Plan: " in out
