import json
from pathlib import Path

import numpy as np
import pandas as pd

from dmdc import PODDMDcPipeline, load_trajectories
from dmdc.splits import split_by_case_ids, split_by_fraction
from dmdc.validation import run_pod_dmdc_validation
from dmdc.cli import main


def test_pod_dmdc_pipeline_no_input_rollout():
    t = np.arange(30)
    x1 = 0.9 ** t
    x2 = 0.8 ** t
    X = np.column_stack([x1, x2])
    pipe = PODDMDcPipeline(pod_rank="full", dmdc_rank="full").fit(X, state_names=["x1", "x2"])
    pred = pipe.rollout(X[0], n_steps=X.shape[0] - 1)
    assert pred.shape == X.shape
    assert pipe.summary_.no_input_dmd is True
    assert np.isfinite(pred).all()


def test_pod_dmdc_pipeline_with_inputs_multicase():
    datasets = load_trajectories(
        "data/example_multicase_timeseries.csv",
        state_cols=["x1", "x2"],
        input_cols=["u1"],
        time_col="time",
        case_col="case_id",
    )
    pipe = PODDMDcPipeline(pod_rank=0.999, dmdc_rank="full").fit_trajectories(
        [ds.X for ds in datasets[:2]], [ds.U for ds in datasets[:2]], state_names=["x1", "x2"], input_names=["u1"]
    )
    U = datasets[0].U[:-1]
    pred = pipe.rollout(datasets[0].X[0], U_future=U, n_steps=datasets[0].X.shape[0] - 1)
    assert pred.shape == datasets[0].X.shape
    assert pipe.summary_.n_inputs == 1


def test_case_splits():
    datasets = load_trajectories(
        "data/example_multicase_timeseries.csv",
        state_cols=["x1", "x2"],
        input_cols=["u1"],
        time_col="time",
        case_col="case_id",
    )
    explicit = split_by_case_ids(datasets, train_cases=["run_001", "run_002"], test_cases=["run_003"])
    assert len(explicit.train) == 2
    assert len(explicit.test) == 1
    frac = split_by_fraction(datasets, train_fraction=0.67)
    assert len(frac.train) >= 1 and len(frac.test) >= 1


def test_validation_outputs(tmp_path):
    datasets = load_trajectories(
        "data/example_multicase_timeseries.csv",
        state_cols=["x1", "x2"],
        input_cols=["u1"],
        time_col="time",
        case_col="case_id",
    )
    summary = run_pod_dmdc_validation(
        datasets[:2], datasets[2:], pod_rank=0.999, dmdc_rank="full", outdir=tmp_path, plots=False, forecast_horizons=[1, 2]
    )
    assert (tmp_path / "validation_summary.json").exists()
    assert (tmp_path / "error_by_case.csv").exists()
    assert (tmp_path / "forecast_horizon_errors.csv").exists()
    assert "test_rollout_rmse" in summary


def test_pod_dmdc_cli_smoke(tmp_path):
    out = tmp_path / "pod_dmdc_cli"
    main([
        "pod-dmdc",
        "--data", "data/example_multicase_timeseries.csv",
        "--case-col", "case_id",
        "--time-col", "time",
        "--state-cols", "x1", "x2",
        "--input-cols", "u1",
        "--pod-rank", "0.999",
        "--outdir", str(out),
    ])
    assert (out / "pod_dmdc_model.pkl").exists()
    assert (out / "reconstructed_rollout_predictions.csv").exists()


def test_validate_cli_smoke(tmp_path):
    out = tmp_path / "validate_cli"
    main([
        "validate",
        "--data", "data/example_multicase_timeseries.csv",
        "--case-col", "case_id",
        "--time-col", "time",
        "--state-cols", "x1", "x2",
        "--input-cols", "u1",
        "--train-cases", "run_001", "run_002",
        "--test-cases", "run_003",
        "--forecast-horizons", "1", "2",
        "--outdir", str(out),
    ])
    assert (out / "validation_summary.csv").exists()
    assert (out / "residuals.csv").exists()
