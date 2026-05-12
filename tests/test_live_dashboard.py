from pathlib import Path
import json

import pandas as pd

from dmdc import read_live_dashboard_tables, summarize_live_dashboard, write_dashboard_summary
from dmdc.cli import main


def _write_dashboard_fixture(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "time": [0.0, 0.5, 1.0],
            "_stream_row_index": [0, 1, 2],
            "TP1": [600.0, 601.0, 602.0],
            "TP2": [599.0, 599.5, 600.1],
            "q_heater": [40.0, 40.0, 41.0],
        }
    ).to_csv(out / "cleaned_stream_log.csv", index=False)
    pd.DataFrame(
        {
            "origin_time": [0.0, 0.5, 1.0],
            "TP1": [600.1, 600.9, 602.2],
            "TP2": [598.9, 599.6, 600.2],
        }
    ).to_csv(out / "live_state_estimates.csv", index=False)
    pd.DataFrame(
        {
            "origin_time": [0.0, 0.0, 0.5, 0.5],
            "forecast_horizon_s": [0.5, 0.5, 0.5, 0.5],
            "target_time": [0.5, 0.5, 1.0, 1.0],
            "state": ["TP1", "TP2", "TP1", "TP2"],
            "predicted_value": [600.8, 599.4, 602.1, 600.0],
        }
    ).to_csv(out / "live_forecasts.csv", index=False)
    pd.DataFrame(
        {
            "matched_time": [0.5, 1.0],
            "state": ["TP1", "TP2"],
            "residual": [0.2, 0.1],
            "abs_residual": [0.2, 0.1],
        }
    ).to_csv(out / "live_forecast_residuals.csv", index=False)
    pd.DataFrame(
        {
            "time": [0.5],
            "severity": ["warning"],
            "code": ["FORECAST_RESIDUAL_HIGH"],
            "state": ["TP1"],
            "message": ["TP1 residual high"],
        }
    ).to_csv(out / "live_alerts.csv", index=False)
    pd.DataFrame({"time": [0.0, 0.5, 1.0], "trust_score": [1.0, 0.9, 0.9]}).to_csv(
        out / "live_trust_score.csv", index=False
    )
    pd.DataFrame(
        {
            "time": [0.5, 1.0],
            "measurement": ["TP1", "TP2"],
            "innovation": [0.1, -0.2],
        }
    ).to_csv(out / "live_kalman_innovations.csv", index=False)
    pd.DataFrame({"time": [0.5, 1.0], "covariance_trace": [0.3, 0.25]}).to_csv(
        out / "live_estimate_covariance.csv", index=False
    )


def test_dashboard_summary_reads_live_phase4_folder(tmp_path: Path) -> None:
    out = tmp_path / "live_monitoring"
    _write_dashboard_fixture(out)
    tables = read_live_dashboard_tables(out)
    assert not tables["cleaned"].empty
    summary = summarize_live_dashboard(out)
    assert summary.status == "warning"
    assert summary.n_clean_samples == 3
    assert summary.n_alerts == 1
    assert summary.latest_trust_score == 0.9
    assert "TP1" in summary.available_states
    assert summary.forecast_horizons_seconds == [0.5]


def test_live_dashboard_write_summary_only_cli(tmp_path: Path) -> None:
    out = tmp_path / "live_monitoring"
    _write_dashboard_fixture(out)
    main(["live-dashboard", "--run-dir", str(out), "--write-summary-only"])
    path = out / "live_dashboard_summary.json"
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["n_alerts"] == 1
    assert payload["status"] == "warning"


def test_live_dashboard_config_summary_only(tmp_path: Path) -> None:
    out = tmp_path / "live_monitoring"
    _write_dashboard_fixture(out)
    cfg = tmp_path / "dashboard.toml"
    cfg.write_text(
        f'''
[dashboard]
run_dir = "{out}"
write_summary_only = true
refresh_seconds = 1.0
''',
        encoding="utf-8",
    )
    main(["live-dashboard", "--config", str(cfg)])
    assert (out / "live_dashboard_summary.json").exists()


def test_write_dashboard_summary_function(tmp_path: Path) -> None:
    out = tmp_path / "live_monitoring"
    _write_dashboard_fixture(out)
    path = write_dashboard_summary(out)
    assert path.exists()

from dmdc import read_archive_dashboard_tables, summarize_archive_dashboard, write_archive_dashboard_summary


def _write_archive_dashboard_fixture(root: Path) -> None:
    (root / "summaries").mkdir(parents=True, exist_ok=True)
    (root / "quicklooks").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "schema_version": ["live_archive_v1", "live_archive_v1"],
            "run_id": ["run_001", "run_001"],
            "data_kind": ["cleaned_stream", "trust_score"],
            "path": ["cleaned_stream/date=relative/hour=0000/part.csv", "trust_score/date=relative/hour=0000/part.csv"],
            "format": ["csv", "csv"],
            "n_rows": [100, 10],
            "file_size_bytes": [5000, 1000],
        }
    ).to_csv(root / "manifest.csv", index=False)
    pd.DataFrame({"window_start": [0.0, 60.0], "mean": [0.95, 0.80], "min": [0.9, 0.6], "p05": [0.91, 0.62]}).to_csv(
        root / "summaries" / "trust_summary_60s.csv", index=False
    )
    pd.DataFrame({"window_start": [0.0, 60.0], "state": ["TP1", "TP1"], "mae": [0.5, 0.7], "rmse": [0.6, 0.9]}).to_csv(
        root / "summaries" / "residual_summary_60s.csv", index=False
    )
    pd.DataFrame({"window_start": [0.0, 60.0], "state": ["TP1", "TP1"], "last_bias": [0.1, 0.2], "mean_bias": [0.08, 0.15]}).to_csv(
        root / "summaries" / "bias_summary_60s.csv", index=False
    )
    pd.DataFrame({"severity": ["warning"], "code": ["FORECAST_RESIDUAL_HIGH"], "alert_count": [3]}).to_csv(
        root / "summaries" / "alert_summary.csv", index=False
    )
    # Use an empty manifest that points to no actual plot; summary mode should still work.
    (root / "quicklooks" / "quicklook_manifest.json").write_text('{"plots": []}', encoding="utf-8")


def test_archive_dashboard_summary_reads_summaries(tmp_path: Path) -> None:
    archive = tmp_path / "live_archive"
    _write_archive_dashboard_fixture(archive)
    tables = read_archive_dashboard_tables(archive, window_label="60s")
    assert not tables["manifest"].empty
    assert not tables["trust_summary"].empty
    summary = summarize_archive_dashboard(archive, window_label="60s")
    assert summary.status == "warning"
    assert summary.total_archived_rows == 110
    assert summary.n_alerts_reported == 3
    assert "cleaned_stream" in summary.data_kinds


def test_archive_dashboard_write_summary_only_cli(tmp_path: Path) -> None:
    archive = tmp_path / "live_archive"
    _write_archive_dashboard_fixture(archive)
    main(["live-dashboard", "--archive-root", str(archive), "--mode", "archive", "--write-summary-only"])
    path = archive / "archive_dashboard_summary.json"
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["manifest_rows"] == 2
    assert payload["n_alerts_reported"] == 3


def test_archive_dashboard_config_summary_only(tmp_path: Path) -> None:
    archive = tmp_path / "live_archive"
    _write_archive_dashboard_fixture(archive)
    cfg = tmp_path / "archive_dashboard.toml"
    cfg.write_text(
        f'''
[dashboard]
mode = "archive"
archive_root = "{archive}"
window_label = "60s"
write_summary_only = true
''',
        encoding="utf-8",
    )
    main(["live-dashboard", "--config", str(cfg)])
    assert (archive / "archive_dashboard_summary.json").exists()


def test_write_archive_dashboard_summary_function(tmp_path: Path) -> None:
    archive = tmp_path / "live_archive"
    _write_archive_dashboard_fixture(archive)
    path = write_archive_dashboard_summary(archive)
    assert path.exists()
