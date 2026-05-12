from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from dmdc.archive_schema import validate_archive_schema
from dmdc.import_workflow import run_import_workflow
from dmdc.importers import FolderTableImporter
from dmdc.importers.tabular import is_probably_stable_file
from dmdc.live_archive import LiveArchiveConfig, archive_live_run
from dmdc.operator_schematic import build_sensor_status_table, residual_to_status, summarize_sensor_status


def test_folder_importer_skips_corrupt_file_but_imports_readable_files(tmp_path: Path) -> None:
    root = tmp_path / "chunks"
    root.mkdir()
    pd.DataFrame({"time": [0.0], "TC01": [300.0]}).to_csv(root / "run_001.csv", index=False)
    (root / "broken.csv").write_text('not,a,valid\n"unterminated', encoding="utf-8")

    result = FolderTableImporter(
        root,
        pattern="*.csv",
        case_from_filename=True,
        column_mapping={"TC01": "TP1"},
    ).import_data()

    assert "TP1" in result.frame.columns
    assert set(result.frame["case_id"]) == {"run_001"}
    assert any("Skipped" in warning for warning in result.warnings)


def test_import_workflow_folder_case_mapping_and_sidecars(tmp_path: Path) -> None:
    root = tmp_path / "daq"
    root.mkdir()
    for name, offset in [("case_a", 0.0), ("case_b", 1.0)]:
        pd.DataFrame({"Time_s": [0.0, 0.1], "TC01": [300.0 + offset, 301.0 + offset]}).to_csv(
            root / f"{name}.csv", index=False
        )
    out = tmp_path / "processed" / "loop.csv"
    summary = run_import_workflow(
        source=root,
        source_type="labview_daq",
        out=out,
        output_format="csv",
        rename_col=["Time_s=time", "TC01=TP1"],
        case_from_filename=True,
    )
    data = pd.read_csv(summary["canonical_output"])
    assert {"time", "TP1", "case_id", "source_file"}.issubset(data.columns)
    assert set(data["case_id"]) == {"case_a", "case_b"}
    assert (out.parent / "import_metadata.json").exists()


def test_partial_file_helper_flags_empty_files(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    full = tmp_path / "full.csv"
    full.write_text("time,TP1\n0,300\n", encoding="utf-8")
    assert not is_probably_stable_file(empty)
    assert is_probably_stable_file(full)


def test_archive_schema_accepts_relative_manifest_paths_and_detects_missing_files(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    pd.DataFrame({"time": [0.0, 1.0], "TP1": [300.0, 301.0]}).to_csv(run / "cleaned_stream_log.csv", index=False)
    archive = tmp_path / "archive"
    archive_live_run(run, LiveArchiveConfig(root=str(archive), format="csv"))

    valid = validate_archive_schema(archive)
    assert valid.n_errors == 0
    assert valid.status in {"passed", "warning"}

    manifest = pd.read_csv(archive / "manifest.csv")
    victim = archive / str(manifest.iloc[0]["path"])
    victim.unlink()
    invalid = validate_archive_schema(archive)
    assert invalid.status == "failed"
    summary = json.loads(Path(invalid.json_summary).read_text(encoding="utf-8"))
    assert any("missing file" in err.lower() for err in summary["errors"])


def test_operator_schematic_thresholds_and_missing_residuals(tmp_path: Path) -> None:
    assert residual_to_status(None, 2.0, 5.0)[0] == "unknown"
    assert residual_to_status(1.9, 2.0, 5.0)[0] == "nominal"
    assert residual_to_status(2.0, 2.0, 5.0)[0] == "warning"
    assert residual_to_status(5.0, 2.0, 5.0)[0] == "critical"

    geometry = tmp_path / "geometry.toml"
    geometry.write_text(
        '[positions_m]\nTP1 = 0.0\nTP2 = 0.5\nTP3 = 1.0\n[geometry]\ndescription = "demo"\n',
        encoding="utf-8",
    )
    residuals = pd.DataFrame(
        {
            "matched_time": [10.0, 10.0],
            "state": ["TP1", "TP2"],
            "residual": [0.5, -6.0],
            "abs_residual": [0.5, 6.0],
        }
    )
    cleaned = pd.DataFrame({"time": [10.0], "TP1": [300.0], "TP2": [301.0]})
    table = build_sensor_status_table(
        state_names=["TP1", "TP2", "TP3"],
        residuals=residuals,
        cleaned_stream=cleaned,
        geometry_path=geometry,
        warning_threshold=2.0,
        critical_threshold=5.0,
    )
    status = dict(zip(table["state"], table["status"], strict=False))
    measured = dict(zip(table["state"], table["measurement_available"], strict=False))
    assert status == {"TP1": "nominal", "TP2": "critical", "TP3": "unknown"}
    assert measured["TP3"] is False
    summary = summarize_sensor_status(table, warning_threshold=2.0, critical_threshold=5.0)
    assert summary.n_critical == 1
    assert summary.n_unknown == 1
