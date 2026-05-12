from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

from dmdc.archive_schema import validate_archive_schema, build_archive_context_index
from dmdc.campaign import run_campaign
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
    assert result.steps_requested == ["inspect", "compare"]


def test_new_cli_help_commands(capsys):
    for command in ["model-register", "model-list", "model-promote", "model-resolve", "validate-archive-schema", "archive-context", "resources", "campaign"]:
        try:
            main([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0
    out = capsys.readouterr().out
    assert "model" in out.lower() or "campaign" in out.lower()
