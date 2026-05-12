from __future__ import annotations

from pathlib import Path

import pandas as pd

from dmdc.import_workflow import run_import_workflow
from dmdc.importers import FolderTableImporter, TabularFileImporter
from dmdc.live_operator_report import generate_live_operator_report
from dmdc.cli import main


def test_tabular_file_importer_renames_columns(tmp_path: Path):
    src = tmp_path / "raw.csv"
    pd.DataFrame({"time": [0.0, 1.0], "TC01": [300.0, 301.0], "Heater_W": [10.0, 10.0]}).to_csv(src, index=False)
    importer = TabularFileImporter(src, column_mapping={"TC01": "TP1", "Heater_W": "q_heater"})
    result = importer.import_data()
    assert {"time", "TP1", "q_heater"}.issubset(result.frame.columns)
    assert result.metadata["n_rows"] == 2


def test_folder_importer_case_from_filename(tmp_path: Path):
    root = tmp_path / "chunks"
    root.mkdir()
    pd.DataFrame({"time": [0.0], "TP1": [300.0]}).to_csv(root / "run_001.csv", index=False)
    pd.DataFrame({"time": [0.0], "TP1": [301.0]}).to_csv(root / "run_002.csv", index=False)
    result = FolderTableImporter(root, pattern="*.csv", case_from_filename=True).import_data()
    assert len(result.frame) == 2
    assert set(result.frame["case_id"]) == {"run_001", "run_002"}


def test_import_workflow_writes_canonical_csv(tmp_path: Path):
    src = tmp_path / "raw.csv"
    pd.DataFrame({"time": [0.0, 1.0], "TC01": [300.0, 301.0]}).to_csv(src, index=False)
    out = tmp_path / "processed" / "loop.csv"
    summary = run_import_workflow(
        source=src,
        source_type="csv",
        out=out,
        output_format="csv",
        rename_col=["TC01=TP1"],
    )
    assert Path(summary["canonical_output"]).exists()
    imported = pd.read_csv(summary["canonical_output"])
    assert "TP1" in imported.columns
    assert (out.parent / "import_summary.json").exists()


def test_import_data_cli_help_runs(capsys):
    try:
        main(["import-data", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "Import CSV/Excel" in out or "Import" in out


def test_operator_report_from_run_dir(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    pd.DataFrame({"time": [0.0, 1.0], "trust_score": [0.9, 0.8]}).to_csv(run / "live_trust_score.csv", index=False)
    pd.DataFrame({"time": [1.0], "severity": ["warning"], "code": ["TEST"], "message": ["demo"]}).to_csv(run / "live_alerts.csv", index=False)
    pd.DataFrame({"matched_time": [1.0], "state": ["TP1"], "abs_residual": [2.0]}).to_csv(run / "live_forecast_residuals.csv", index=False)
    outdir = tmp_path / "report"
    paths = generate_live_operator_report(run_dir=run, outdir=outdir)
    assert Path(paths["markdown"]).exists()
    assert Path(paths["html"]).exists()
    assert "Operator Report" in Path(paths["markdown"]).read_text()
