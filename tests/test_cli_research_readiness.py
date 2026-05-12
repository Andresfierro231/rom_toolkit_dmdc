from pathlib import Path

from dmdc.cli import main


def test_make_thermal_loop_example_cli(tmp_path):
    out = tmp_path / "thermal"
    main(["make-thermal-loop-example", "--outdir", str(out), "--n-time", "10"])
    assert (out / "thermal_loop_synthetic.csv").exists()
    assert (out / "loop_geometry.toml").exists()
    assert (out / "provenance.json").exists()


def test_recommend_cli(tmp_path):
    table = tmp_path / "model_comparison.csv"
    table.write_text("model_name,test_rollout_rmse,stability_status,status\na,2,stable_by_spectral_radius,ok\nb,1,potentially_unstable,ok\n")
    out = tmp_path / "rec"
    main(["recommend", "--table", str(table), "--outdir", str(out)])
    assert (out / "best_model_recommendation.txt").exists()
    assert "a" in (out / "best_model_recommendation.txt").read_text()


def test_continuous_cli_on_single_case(tmp_path):
    data_dir = tmp_path / "thermal"
    main(["make-thermal-loop-example", "--outdir", str(data_dir), "--n-time", "12"])
    out = tmp_path / "continuous"
    main([
        "continuous",
        "--data", str(data_dir / "thermal_loop_synthetic.csv"),
        "--time-col", "time",
        "--case-col", "case_id",
        "--case-id", "salt_test_1",
        "--state-cols", "TP1", "TP2", "massFlowRate",
        "--input-cols", "q_heater", "T_amb", "h_amb",
        "--outdir", str(out),
    ])
    assert (out / "A_continuous.csv").exists()
    assert (out / "provenance.json").exists()
