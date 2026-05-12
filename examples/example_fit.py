"""Example DMDc fit using the included synthetic dataset."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dmdc import DMDcModel, load_timeseries
from dmdc.diagnostics import evaluate_model

DATA = ROOT / "data" / "example_timeseries.csv"


def main() -> None:
    ds = load_timeseries(DATA, state_cols=["x1", "x2"], input_cols=["u1"], time_col="time")
    model = DMDcModel(rank="full")
    model.fit(ds.X, ds.U, state_names=ds.state_cols, input_names=ds.input_cols, dt=ds.dt)
    diagnostics = evaluate_model(model, ds.X, ds.U)
    print("A =")
    print(model.A_)
    print("B =")
    print(model.B_)
    print("diagnostics =")
    print(diagnostics)


if __name__ == "__main__":
    main()
