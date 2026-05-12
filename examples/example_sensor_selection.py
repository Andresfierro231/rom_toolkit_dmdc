"""Example: rank important state variables using SVD + pivoted QR.

Run from repo root:

    python examples/example_sensor_selection.py
"""

from dmdc import load_timeseries, qr_sensor_ranking, reconstruction_error_vs_sensors


ds = load_timeseries(
    "data/example_timeseries.csv",
    state_cols=["x1", "x2"],
    input_cols=["u1"],
    time_col="time",
)

result = qr_sensor_ranking(ds.X, ds.state_cols, rank="full", n_sensors=2, scale=True)
result.save("outputs/example_sensor_selection")

errors = reconstruction_error_vs_sensors(ds.X, result.selected_indices, rank="full", scale=True)
errors.to_csv("outputs/example_sensor_selection/reconstruction_error_vs_sensors.csv", index=False)

print(result.ranking)
print("Selected states:", result.selected_state_names)
