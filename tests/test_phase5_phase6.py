from pathlib import Path

import numpy as np
import pandas as pd

from dmdc.stability import analyze_transition_matrix
from dmdc.reports import generate_latex_report
from dmdc.cli import main


def test_stability_detects_unstable_matrix():
    result = analyze_transition_matrix(np.diag([0.9, 1.2]))
    assert result["summary"]["spectral_radius"] == 1.2
    assert result["summary"]["n_unstable_eigenvalues"] == 1
    assert result["warnings"]


def test_compare_cli_and_report(tmp_path: Path):
    out = tmp_path / "compare"
    main([
        "compare",
        "--data", "data/example_multicase_timeseries.csv",
        "--case-col", "case_id",
        "--time-col", "time",
        "--state-cols", "x1", "x2",
        "--input-cols", "u1",
        "--train-cases", "run_001", "run_002",
        "--test-cases", "run_003",
        "--models", "persistence", "mean", "dmdc", "pod_dmdc",
        "--outdir", str(out),
        "--plots",
        "--report",
    ])
    comp = pd.read_csv(out / "model_comparison.csv")
    assert {"model_name", "test_rollout_rmse", "generalization_gap", "spectral_radius"}.issubset(comp.columns)
    assert (out / "model_comparison.tex").exists()
    assert (out / "stability_dashboard.csv").exists()
    assert (out / "report" / "report.tex").exists()

    tex = generate_latex_report(out)
    assert tex.exists()
    assert "Reduced-Order Model Analysis Report" in tex.read_text()
