import numpy as np

from dmdc.delayed import make_delay_embedding
from dmdc.model import DMDcModel


def test_make_delay_embedding_shapes_and_names():
    X = np.arange(20, dtype=float).reshape(10, 2)
    U = np.ones((10, 1))
    Z, U_aligned, names = make_delay_embedding(X, U, n_delays=3, state_names=["TP1", "TP2"])

    assert Z.shape == (8, 6)
    assert U_aligned.shape == (8, 1)
    assert names == ["TP1__lag0", "TP2__lag0", "TP1__lag1", "TP2__lag1", "TP1__lag2", "TP2__lag2"]
    np.testing.assert_allclose(Z[0], np.array([4, 5, 2, 3, 0, 1], dtype=float))


def test_no_input_dmd_fit_works():
    A = np.array([[0.9, 0.1], [-0.2, 0.95]])
    X = np.zeros((40, 2))
    X[0] = [1.0, -0.5]
    for k in range(39):
        X[k + 1] = A @ X[k]

    model = DMDcModel(rank="full")
    model.fit(X, None, state_names=["x1", "x2"])
    assert model.metadata_.n_inputs == 0
    pred = model.simulate(X[0], None, n_steps=5)
    assert pred.shape == (6, 2)
