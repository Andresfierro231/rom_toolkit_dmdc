"""Example: fit one DMDc model from several independent trajectories."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dmdc import DMDcModel, load_trajectories
from dmdc.diagnostics import evaluate_trajectories, save_diagnostics
from dmdc.utils import ensure_dir, write_json

OUT = ensure_dir(ROOT / "outputs" / "example_multicase_fit")

datasets = load_trajectories(
    ROOT / "data" / "example_multicase_timeseries.csv",
    state_cols=["x1", "x2"],
    input_cols=["u1"],
    time_col="time",
    case_col="case_id",
)

model = DMDcModel(rank="full")
model.fit_trajectories(
    [ds.X for ds in datasets],
    [ds.U for ds in datasets],
    state_names=datasets[0].state_cols,
    input_names=datasets[0].input_cols,
    dt=datasets[0].dt,
)

model.save(OUT / "model.pkl")
write_json(model.to_dict(), OUT / "model_summary.json")

diagnostics = evaluate_trajectories(
    model,
    [ds.X for ds in datasets],
    [ds.U for ds in datasets],
    [ds.case_id for ds in datasets],
)
save_diagnostics(diagnostics, OUT / "diagnostics.json")
print(f"Saved multi-case outputs to {OUT}")
