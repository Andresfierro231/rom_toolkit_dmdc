from pathlib import Path
import numpy as np
import pandas as pd

from dmdc.case_quality import summarize_case_quality
from dmdc.continuous import discrete_to_continuous
from dmdc.kalman import LinearKalmanFilter
from dmdc.operating_conditions import summarize_operating_conditions
from dmdc.recommendations import recommend_best_model
from dmdc.regularized import RegularizedDMDcModel
from dmdc.thermal_loop_example import generate_thermal_loop_dataframe, write_thermal_loop_example
from dmdc.uncertainty import bootstrap_mean_ci


def test_regularized_dmdc_fits_no_input_linear_system():
    A = np.array([[0.9, 0.1], [0.0, 0.8]])
    x = np.zeros((40, 2))
    x[0] = [1.0, 0.5]
    for k in range(39):
        x[k + 1] = A @ x[k]
    model = RegularizedDMDcModel(alpha=1e-8).fit(x)
    pred = model.simulate(x[0], n_steps=39)
    assert pred.shape == x.shape
    assert np.mean((pred - x) ** 2) < 1e-6


def test_discrete_to_continuous_round_trip_scalar_decay():
    A_d = np.array([[np.exp(-0.2)]])
    A_c, B_c = discrete_to_continuous(A_d, None, dt=1.0)
    assert B_c is None
    assert np.allclose(A_c, [[-0.2]], atol=1e-8)


def test_kalman_filter_runs_for_simple_system():
    kf = LinearKalmanFilter(A=[[1.0]], C=[[1.0]], Q=[[1e-6]], R=[[1e-3]])
    y = np.ones((5, 1))
    result = kf.filter(y, x0=[0.0])
    assert result.state_estimates.shape == (5, 1)
    assert result.state_estimates[-1, 0] > 0.9


def test_operating_condition_summary_flags_extrapolation():
    train = pd.DataFrame({"q": [10.0, 20.0, 15.0]})
    test = pd.DataFrame({"q": [25.0]})
    summary = summarize_operating_conditions(train, test, condition_cols=["q"])
    assert bool(summary.loc[0, "test_outside_train_range"])


def test_case_quality_marks_short_case_bad():
    df = pd.DataFrame({"case_id": ["a", "b", "b"], "time": [0.0, 0.0, 1.0], "x": [1.0, 2.0, 3.0]})
    quality = summarize_case_quality(df, case_col="case_id", time_col="time", required_cols=["x"], min_samples=2)
    row_a = quality[quality["case_id"] == "a"].iloc[0]
    assert row_a["usable_for_rom"] is False or row_a["usable_for_rom"] == False


def test_recommend_best_model_prefers_stable_low_error():
    df = pd.DataFrame(
        {
            "model_name": ["unstable_good", "stable_ok"],
            "test_rollout_rmse": [0.1, 0.2],
            "stability_status": ["potentially_unstable", "stable_by_spectral_radius"],
            "status": ["ok", "ok"],
        }
    )
    rec = recommend_best_model(df)
    assert rec["recommendation"]["model_name"] == "stable_ok"


def test_bootstrap_mean_ci_has_bounds():
    ci = bootstrap_mean_ci([1.0, 2.0, 3.0], n_bootstrap=50)
    assert ci.ci_low <= ci.estimate <= ci.ci_high


def test_thermal_loop_example_writer(tmp_path):
    paths = write_thermal_loop_example(tmp_path, n_time=12, seed=1)
    assert Path(paths["data"]).exists()
    df = pd.read_csv(paths["data"])
    assert {"TP1", "TP6", "massFlowRate", "q_heater", "case_id"}.issubset(df.columns)
    assert df["case_id"].nunique() >= 5
