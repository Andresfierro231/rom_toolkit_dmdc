"""Example: fit delay-DMDc by embedding state history before DMDc fitting.

Run from repo root:

    python examples/example_delay_fit.py
"""

from dmdc import DMDcModel, load_timeseries, make_delay_embedding
from dmdc.diagnostics import evaluate_model


ds = load_timeseries(
    "data/example_timeseries.csv",
    state_cols=["x1", "x2"],
    input_cols=["u1"],
    time_col="time",
)

Z, U_aligned, z_names = make_delay_embedding(ds.X, ds.U, n_delays=3, state_names=ds.state_cols)
model = DMDcModel(rank="full")
model.fit(Z, U_aligned, state_names=z_names, input_names=ds.input_cols, dt=ds.dt)

print(evaluate_model(model, Z, U_aligned))
print("Embedded states:", z_names)
