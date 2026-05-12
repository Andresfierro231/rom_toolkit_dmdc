from pathlib import Path

import pandas as pd

from dmdc.operator_schematic import build_sensor_status_table, write_schematic_status_outputs
from dmdc.archive_benchmark import ArchiveBenchmarkConfig, run_archive_benchmark
from dmdc.hpc_workflows import write_hpc_workflow_plan


def test_operator_schematic_colors_by_residual(tmp_path: Path):
    geom = tmp_path / "geometry.toml"
    geom.write_text('description = "demo"\n[positions_m]\nTP1 = 0.0\nTP2 = 1.0\nTP3 = 2.0\n', encoding="utf-8")
    residuals = pd.DataFrame(
        {
            "matched_time": [1.0, 1.0, 1.0],
            "state": ["TP1", "TP2", "TP3"],
            "residual": [0.2, 2.5, -7.0],
            "abs_residual": [0.2, 2.5, 7.0],
        }
    )
    cleaned = pd.DataFrame({"time": [1.0], "TP1": [10.0], "TP2": [11.0], "TP3": [12.0]})
    table = build_sensor_status_table(
        state_names=["TP1", "TP2", "TP3"],
        residuals=residuals,
        cleaned_stream=cleaned,
        geometry_path=geom,
        warning_threshold=2.0,
        critical_threshold=5.0,
    )
    assert table["status"].tolist() == ["nominal", "warning", "critical"]
    paths = write_schematic_status_outputs(table, tmp_path / "schematic", warning_threshold=2.0, critical_threshold=5.0)
    assert Path(paths["table"]).exists()
    assert Path(paths["summary"]).exists()


def test_archive_benchmark_small_run(tmp_path: Path):
    result = run_archive_benchmark(
        ArchiveBenchmarkConfig(
            n_rows=200,
            n_states=4,
            n_inputs=1,
            outdir=str(tmp_path / "benchmark"),
            archive_root=str(tmp_path / "benchmark" / "archive"),
            archive_format="csv",
            windows_seconds=[60.0],
            make_quicklooks=False,
        )
    )
    assert result.n_rows == 200
    assert result.archive_write_mb_per_sec >= 0
    assert Path(result.metrics_csv).exists()
    assert Path(result.summary_json).exists()


def test_hpc_plan_writes_local_and_slurm_skeletons(tmp_path: Path):
    cfg = tmp_path / "study.toml"
    cfg.write_text('[execution]\nmode = "local"\nsteps = ["inspect", "compare", "archive"]\n', encoding="utf-8")
    result = write_hpc_workflow_plan(cfg, outdir=tmp_path / "hpc_plan")
    assert Path(result.command_plan).exists()
    assert Path(result.local_runner).exists()
    assert Path(result.slurm_campaign_template).exists()
    text = Path(result.slurm_campaign_template).read_text(encoding="utf-8")
    assert "FIXME_ACCOUNT" in text
    assert "dmdc compare" in text
