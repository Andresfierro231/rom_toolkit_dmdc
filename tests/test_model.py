import numpy as np

from dmdc import DMDcModel


def test_dmdc_recovers_linear_system():
    A_true = np.array([[0.9, 0.1], [-0.2, 0.8]])
    B_true = np.array([[0.5], [0.1]])
    rng = np.random.default_rng(1)
    n = 200
    U = rng.normal(size=(n, 1))
    X = np.zeros((n, 2))
    X[0] = [1.0, -0.5]
    for k in range(n - 1):
        X[k + 1] = A_true @ X[k] + B_true @ U[k]

    model = DMDcModel(rank="full")
    model.fit(X, U)

    assert np.allclose(model.A_, A_true, atol=1e-10)
    assert np.allclose(model.B_, B_true, atol=1e-10)


def test_simulate_shape():
    X = np.array([[1.0], [0.9], [0.81], [0.729]])
    model = DMDcModel().fit(X)
    out = model.simulate([1.0], n_steps=3)
    assert out.shape == (4, 1)
