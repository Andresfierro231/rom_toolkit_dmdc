from __future__ import annotations

from pathlib import Path

import pandas as pd

from dmdc.live_archive import LiveArchiveConfig, archive_live_run, read_archive_manifest, load_archive_kind
from dmdc.live_summaries import LiveSummaryConfig, summarize_live_archive
from dmdc.live_quicklooks import QuicklookConfig, make_archive_quicklooks


def _make_run_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "time": [0.0, 1.0, 2.0, 61.0],
            "TP1": [600.0, 601.0, 602.0, 604.0],
            "TP2": [590.0, 590.5, 591.0, 593.0],
            "q_heater": [30.0, 30.0, 35.0, 35.0],
        }
    ).to_csv(path / "cleaned_stream_log.csv", index=False)
    pd.DataFrame(
        {
            "origin_time": [0.0, 1.0, 2.0],
            "target_time": [1.0, 2.0, 61.0],
            "matched_time": [1.0, 2.0, 61.0],
            "forecast_horizon_s": [1.0, 1.0, 59.0],
            "state": ["TP1", "TP1", "TP2"],
            "measured_value": [601.0, 602.0, 593.0],
            "predicted_value": [600.5, 601.5, 591.0],
            "residual": [0.5, 0.5, 2.0],
            "abs_residual": [0.5, 0.5, 2.0],
        }
    ).to_csv(path / "live_forecast_residuals.csv", index=False)
    pd.DataFrame({"time": [0.0, 1.0, 2.0, 61.0], "trust_score": [1.0, 0.9, 0.8, 0.7]}).to_csv(
        path / "live_trust_score.csv", index=False
    )
    pd.DataFrame(
        {
            "time": [1.0, 2.0, 61.0],
            "state": ["TP1", "TP1", "TP2"],
            "bias_value": [0.01, 0.02, 0.03],
            "forecast_horizon_s": [1.0, 1.0, 59.0],
            "residual_used": [0.5, 0.5, 2.0],
            "update_allowed": [True, True, True],
        }
    ).to_csv(path / "live_bias_state_timeseries.csv", index=False)
    pd.DataFrame({"time": [61.0], "severity": ["warning"], "code": ["FORECAST_RESIDUAL_HIGH"]}).to_csv(
        path / "live_alerts.csv", index=False
    )
    return path


def test_archive_live_run_writes_manifest_and_loads_kind(tmp_path):
    run_dir = _make_run_dir(tmp_path / "run")
    archive = tmp_path / "archive"
    result = archive_live_run(run_dir, LiveArchiveConfig(root=str(archive), format="csv"))

    assert result.n_rows_archived > 0
    manifest = read_archive_manifest(archive)
    assert not manifest.empty
    assert {"cleaned_stream", "residuals", "trust_score", "bias_state_timeseries", "alerts"}.issubset(
        set(manifest["data_kind"])
    )
    cleaned = load_archive_kind(archive, "cleaned_stream")
    assert list(cleaned["TP1"]) == [600.0, 601.0, 602.0, 604.0]


def test_archive_summaries_and_quicklooks(tmp_path):
    run_dir = _make_run_dir(tmp_path / "run")
    archive = tmp_path / "archive"
    archive_live_run(run_dir, LiveArchiveConfig(root=str(archive), format="csv"))

    summary = summarize_live_archive(
        LiveSummaryConfig(archive_root=str(archive), windows_seconds=[60.0], state_cols=["TP1", "TP2"])
    )
    assert summary.n_summary_files >= 3
    assert (archive / "summaries" / "state_summary_60s.csv").exists()
    assert (archive / "summaries" / "residual_summary_60s.csv").exists()

    quick = make_archive_quicklooks(QuicklookConfig(archive_root=str(archive), window_label="60s"))
    assert quick.n_plots >= 2
    assert any(Path(p).suffix == ".png" for p in quick.plots)


def test_archive_search_finds_alerts_and_residuals(tmp_path):
    from dmdc.archive_search import ArchiveSearchConfig, search_archive

    run_dir = _make_run_dir(tmp_path / "run")
    archive = tmp_path / "archive"
    archive_live_run(run_dir, LiveArchiveConfig(root=str(archive), format="csv"))

    residual_result = search_archive(
        ArchiveSearchConfig(archive_root=str(archive), outdir=str(tmp_path / "search_resid"), residual_above=1.0)
    )
    assert residual_result.n_matching_rows == 1
    rows = pd.read_csv(residual_result.results_csv)
    assert rows.iloc[0]["state"] == "TP2"

    alert_result = search_archive(
        ArchiveSearchConfig(archive_root=str(archive), outdir=str(tmp_path / "search_alert"), alert_code="FORECAST_RESIDUAL_HIGH")
    )
    assert alert_result.n_matching_rows == 1
