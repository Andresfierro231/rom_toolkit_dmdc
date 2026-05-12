"""Example: POD-space Kalman filtering from sparse thermal-loop sensors.

Run after generating the thermal-loop example:

    python -m dmdc.cli make-thermal-loop-example
    PYTHONPATH=src python examples/kalman_state_estimation/example_kalman_pod_state_estimation.py

This example fits POD-DMDc on synthetic loop data, pretends that only TP2, TP4,
and massFlowRate are measured, and reconstructs the full state using a Kalman
filter in POD/modal space.
"""

from pathlib import Path
import pandas as pd
import numpy as np

from dmdc.data import load_trajectories
from dmdc.reduced import PODDMDcPipeline
from dmdc.kalman import estimate_pod_state_with_kalman
from dmdc.metrics import rmse

DATA = Path("examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv")
STATE_COLS = ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TW1", "TW2", "TW3", "massFlowRate"]
INPUT_COLS = ["q_heater", "T_amb", "h_amb"]
SENSOR_COLS = ["TP2", "TP4", "massFlowRate"]


def main() -> None:
    if not DATA.exists():
        raise SystemExit("Generate the example first: python -m dmdc.cli make-thermal-loop-example")
    cases = load_trajectories(DATA, state_cols=STATE_COLS, input_cols=INPUT_COLS, time_col="time", case_col="case_id")
    train = [c for c in cases if c.case_id != "salt_test_5_unseen_hot"]
    test = [c for c in cases if c.case_id == "salt_test_5_unseen_hot"][0]
    model = PODDMDcPipeline(pod_rank=0.999, dmdc_rank="full", center=True).fit_trajectories(
        [c.X for c in train], [c.U for c in train], state_names=STATE_COLS, input_names=INPUT_COLS
    )
    selected_indices = [STATE_COLS.index(name) for name in SENSOR_COLS]
    measurements = test.X[:, selected_indices]
    U_future = test.U[:-1]
    # The filter accepts one input per measurement time.  Pad the final input by repeating the last row.
    U_for_filter = np.vstack([U_future, U_future[-1:]])
    a_est, x_recon, result = estimate_pod_state_with_kalman(
        model.pod_,
        model.model_.A_,
        measurements,
        selected_indices,
        reduced_B=model.model_.B_,
        U=U_for_filter,
        R=np.eye(len(SENSOR_COLS)) * 0.05**2,
        Q=np.eye(model.model_.A_.shape[0]) * 1e-5,
    )
    out = Path("outputs/kalman_example")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(x_recon, columns=[f"estimated_{c}" for c in STATE_COLS]).to_csv(out / "kalman_full_state_estimate.csv", index=False)
    pd.DataFrame(a_est, columns=[f"a{i+1}" for i in range(a_est.shape[1])]).to_csv(out / "kalman_modal_estimate.csv", index=False)
    print(f"Full-state reconstruction RMSE from sparse sensors: {rmse(test.X, x_recon):.6g}")
    print(f"Saved outputs to {out}")


if __name__ == "__main__":
    main()
