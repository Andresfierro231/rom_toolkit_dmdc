import numpy as np

from dmdc.sensor_selection import qr_sensor_ranking, reconstruction_error_vs_sensors


def test_qr_sensor_ranking_returns_named_selected_states():
    t = np.linspace(0.0, 2.0 * np.pi, 80)
    X = np.column_stack([
        np.sin(t),
        np.cos(t),
        np.sin(t) + np.cos(t),
        0.01 * np.sin(7 * t),
    ])
    result = qr_sensor_ranking(X, ["TP1", "TP2", "TP3", "noise"], rank=2, n_sensors=2)

    assert result.rank_used == 2
    assert len(result.selected_state_names) == 2
    assert set(result.ranking.columns) >= {"pivot_order", "state_name", "selected"}


def test_reconstruction_error_vs_sensors_is_well_formed():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(50, 5))
    result = qr_sensor_ranking(X, rank=3, n_sensors=3)
    errors = reconstruction_error_vs_sensors(X, result.selected_indices, rank=3)

    assert list(errors["n_sensors"]) == [1, 2, 3]
    assert np.all(np.isfinite(errors["relative_reconstruction_error"]))
