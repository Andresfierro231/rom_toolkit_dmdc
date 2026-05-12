from __future__ import annotations

from pathlib import Path

import pandas as pd

from dmdc.live_adaptation import LiveAdaptationConfig, compute_bias_update_events
from dmdc.model_registry import register_model, promote_model, resolve_model, read_registry_index, write_model_identity
from dmdc.hpc_workflows import write_hpc_workflow_plan
from dmdc.resources import get_resource_summary


def test_bias_updates_skip_low_trust_and_clip_updates() -> None:
    residuals = pd.DataFrame(
        {
            "matched_time": [1.0, 2.0, 3.0],
            "forecast_horizon_s": [5.0, 5.0, 5.0],
            "state": ["TP4", "TP4", "TP4"],
            "residual": [50.0, 50.0, 50.0],
            "abs_residual": [50.0, 50.0, 50.0],
        }
    )
    trust = pd.DataFrame({"time": [1.0, 2.0, 3.0], "trust_score": [0.2, 0.9, 0.9]})
    cfg = LiveAdaptationConfig(
        stream_type="csv_replay",
        path="unused.csv",
        model_path="unused.pkl",
        measurement_cols=["TP4"],
        adaptation_method="horizon_state_bias",
        bias_learning_rate=1.0,
        max_update_step=0.25,
        max_abs_bias=0.4,
        update_only_when_trust_above=0.7,
        clip_residual_abs=1.0,
    )
    events = compute_bias_update_events(residuals=residuals, alerts=pd.DataFrame(), trust=trust, config=cfg)
    assert list(events["accepted"]) == [False, True, True]
    assert "trust" in str(events.loc[0, "rejection_reason"]).lower()
    assert events.loc[1:, "delta_bias"].abs().max() <= 0.25 + 1e-12
    assert events["new_bias"].abs().max() <= 0.4 + 1e-12


def test_bias_updates_can_skip_on_critical_alert() -> None:
    residuals = pd.DataFrame(
        {"matched_time": [1.0], "forecast_horizon_s": [5.0], "state": ["TP1"], "residual": [2.0], "abs_residual": [2.0]}
    )
    alerts = pd.DataFrame({"time": [1.0], "severity": ["critical"], "code": ["DROP"]})
    trust = pd.DataFrame({"time": [1.0], "trust_score": [1.0]})
    cfg = LiveAdaptationConfig(
        stream_type="csv_replay",
        path="unused.csv",
        model_path="unused.pkl",
        measurement_cols=["TP1"],
        update_only_when_trust_above=0.0,
        skip_on_alert_severity=["critical"],
    )
    events = compute_bias_update_events(residuals=residuals, alerts=alerts, trust=trust, config=cfg)
    assert len(events) == 1
    assert not bool(events.loc[0, "accepted"])
    assert "alert" in str(events.loc[0, "rejection_reason"]).lower()


def test_model_registry_deployment_and_identity_file(tmp_path: Path) -> None:
    model = tmp_path / "model.pkl"
    model.write_bytes(b"model bytes")
    metrics = tmp_path / "metrics.csv"
    pd.DataFrame({"model_name": ["demo"], "test_rollout_rmse": [1.2]}).to_csv(metrics, index=False)
    registry = tmp_path / "registry"

    registered = register_model(
        model,
        name="Simple Loop POD-DMDc",
        version="v1",
        stage="candidate",
        registry_root=registry,
        metrics_path=metrics,
        model_type="pod_dmdc",
        notes="unit test",
    )
    assert Path(registered.registered_model_path).exists()
    assert registered.metrics_path and Path(registered.metrics_path).exists()
    assert len(read_registry_index(registry)) == 1

    promote_model("Simple_Loop_POD-DMDc", version="v1", stage="production", registry_root=registry)
    resolved = resolve_model(name="Simple_Loop_POD-DMDc", stage="production", registry_root=registry)
    identity = write_model_identity(tmp_path / "live_run", resolved)
    assert identity.exists()
    text = identity.read_text(encoding="utf-8")
    assert "Simple_Loop_POD-DMDc" in text
    assert "production" in text


def test_hpc_plan_local_default_and_fixme_templates(tmp_path: Path) -> None:
    cfg = tmp_path / "campaign.toml"
    cfg.write_text(
        f'''
[campaign]
name = "demo"
root = "{tmp_path / 'campaigns'}"

[execution]
mode = "local"
steps = ["inspect", "compare", "archive"]

[data]
path = "data/example_multicase_timeseries.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["x1", "x2"]
input_cols = ["u1"]
''',
        encoding="utf-8",
    )
    result = write_hpc_workflow_plan(cfg, outdir=tmp_path / "hpc")
    assert result.execution_mode == "local"
    plan_text = Path(result.command_plan).read_text(encoding="utf-8")
    assert "run locally first" in plan_text.lower()
    slurm_text = Path(result.slurm_campaign_template).read_text(encoding="utf-8")
    assert "FIXME_ACCOUNT" in slurm_text
    assert "FIXME_PARTITION" in slurm_text
    local_text = Path(result.local_runner).read_text(encoding="utf-8")
    assert "dmdc inspect-data" in local_text


def test_resource_summary_contains_core_fields() -> None:
    resources = get_resource_summary()
    assert resources["cpu_count"] >= 1
    assert "python" in resources
    assert "platform" in resources
