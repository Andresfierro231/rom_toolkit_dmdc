import numpy as np

from dmdc.graph import GraphConstrainedDMDcModel, LoopGraph


def test_loop_graph_ring_mask_orientation():
    graph = LoopGraph.ring(["TP1", "TP2", "TP3"], directed=True)
    mask = graph.allowed_mask()
    # TP2 may depend on TP1, plus itself.
    assert mask[1, 0]
    assert mask[1, 1]
    assert not mask[0, 1]


def test_graph_constrained_model_respects_mask():
    X = np.zeros((60, 3))
    X[0] = [1.0, 0.0, -0.5]
    A_true = np.array([
        [0.9, 0.0, 0.05],
        [0.1, 0.8, 0.0],
        [0.0, 0.2, 0.7],
    ])
    for k in range(59):
        X[k + 1] = A_true @ X[k]
    graph = LoopGraph(nodes=["x0", "x1", "x2"], edges=[("x2", "x0"), ("x0", "x1"), ("x1", "x2")])
    model = GraphConstrainedDMDcModel(graph=graph)
    model.fit(X, None, state_names=["x0", "x1", "x2"])
    assert model.A_[0, 1] == 0.0
    assert model.A_[1, 2] == 0.0
    assert model.A_[2, 0] == 0.0
