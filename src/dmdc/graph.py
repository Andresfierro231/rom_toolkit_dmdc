"""Graph/topology helpers for loop-aware DMDc.

A standard dense DMDc model lets every state influence every other state. For a
thermal-fluid loop, it can be useful to encode which measurement points are
neighbors or upstream/downstream of each other. This module provides a small
LoopGraph object and a graph-constrained DMDc model that zeros forbidden entries
of A by solving row-wise least-squares problems using only allowed predecessors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .model import DMDcMetadata, DMDcModel, _as_2d_float


@dataclass(frozen=True)
class LoopGraph:
    """Directed or undirected connectivity graph for state variables.

    Edges are written as ``(source, target)`` and mean source may influence
    target in one sample. With ``include_self=True``, each state also depends on
    itself.
    """

    nodes: list[str]
    edges: list[tuple[str, str]]
    directed: bool = True
    include_self: bool = True

    def adjacency_matrix(self) -> NDArray[np.float64]:
        idx = {name: i for i, name in enumerate(self.nodes)}
        A = np.zeros((len(self.nodes), len(self.nodes)), dtype=float)
        if self.include_self:
            np.fill_diagonal(A, 1.0)
        for source, target in self.edges:
            if source not in idx or target not in idx:
                raise ValueError(f"Edge ({source!r}, {target!r}) references a node not in nodes.")
            # A[target, source] is allowed because x_target(k+1) can depend on x_source(k).
            A[idx[target], idx[source]] = 1.0
            if not self.directed:
                A[idx[source], idx[target]] = 1.0
        return A

    def allowed_mask(self, state_names: Sequence[str] | None = None) -> NDArray[np.bool_]:
        """Return Boolean mask where mask[i, j] allows A[i, j] to be nonzero."""
        if state_names is not None and list(state_names) != self.nodes:
            missing = [name for name in state_names if name not in self.nodes]
            if missing:
                raise ValueError(f"state_names contain nodes missing from graph: {missing}")
            # Reorder graph adjacency to match state_names.
            base = self.adjacency_matrix().astype(bool)
            graph_idx = {name: i for i, name in enumerate(self.nodes)}
            order = [graph_idx[name] for name in state_names]
            return base[np.ix_(order, order)]
        return self.adjacency_matrix().astype(bool)

    @classmethod
    def ring(cls, nodes: Sequence[str], *, directed: bool = True, include_self: bool = True) -> "LoopGraph":
        """Create a simple loop/ring graph node0 -> node1 -> ... -> node0."""
        names = list(nodes)
        if len(names) < 2:
            raise ValueError("A ring graph needs at least two nodes.")
        edges = [(names[i], names[(i + 1) % len(names)]) for i in range(len(names))]
        return cls(nodes=names, edges=edges, directed=directed, include_self=include_self)


class GraphConstrainedDMDcModel(DMDcModel):
    """DMDc with a graph sparsity mask on the state-transition matrix A.

    This model solves each row of

        x_{k+1} = A x_k + B u_k

    using only graph-allowed state predictors for that row plus all input
    predictors. It is intended for physically interpretable loop models. Because
    the row-wise constrained least-squares solve is not the same as the SVD
    pseudoinverse used by ``DMDcModel``, use it as a second-stage model after a
    dense baseline has been established.
    """

    def __init__(self, graph: LoopGraph | NDArray[np.bool_], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.graph = graph
        self.graph_mask_: NDArray[np.bool_] | None = None

    def fit_transitions(
        self,
        X0: ArrayLike,
        X1: ArrayLike,
        U: ArrayLike | None = None,
        *,
        state_names: list[str] | None = None,
        input_names: list[str] | None = None,
        dt: float | None = None,
        n_samples: int | None = None,
        n_trajectories: int = 1,
    ) -> "GraphConstrainedDMDcModel":
        X0_arr = _as_2d_float(X0, name="X0")
        X1_arr = _as_2d_float(X1, name="X1")
        if X0_arr.shape != X1_arr.shape:
            raise ValueError("X0 and X1 must have identical shapes.")
        if U is None:
            U_arr = np.zeros((X0_arr.shape[0], 0), dtype=float)
        else:
            U_arr = _as_2d_float(U, name="U")
            if U_arr.shape[0] != X0_arr.shape[0]:
                raise ValueError("U must have one row per transition.")

        n_transitions, n_states = X0_arr.shape
        n_inputs = U_arr.shape[1]
        mask = self._make_mask(n_states, state_names)
        self.graph_mask_ = mask

        X0_proc, U_proc = self._fit_transform_training_data(X0_arr, U_arr)
        X1_proc = self._transform_states(X1_arr)

        A = np.zeros((n_states, n_states), dtype=float)
        B = np.zeros((n_states, n_inputs), dtype=float)
        residual_norms = []
        for row in range(n_states):
            allowed = np.where(mask[row])[0]
            design = X0_proc[:, allowed]
            if n_inputs:
                design = np.hstack([design, U_proc])
            coeff, residuals, _, _ = np.linalg.lstsq(design, X1_proc[:, row], rcond=self.rcond)
            A[row, allowed] = coeff[: len(allowed)]
            if n_inputs:
                B[row, :] = coeff[len(allowed) :]
            pred = design @ coeff
            residual_norms.append(float(np.linalg.norm(X1_proc[:, row] - pred)))

        # Diagnostics comparable to dense model: SVD of the unconstrained design matrix.
        Omega = np.vstack([X0_proc.T, U_proc.T])
        _, s, _ = np.linalg.svd(Omega, full_matrices=False)
        rank_used = self._choose_rank(s)
        rank_used = max(1, min(rank_used, len(s)))
        condition_number = float(s[0] / s[-1]) if len(s) > 0 and s[-1] > 0 else float("inf")

        self.A_ = A
        self.B_ = B
        self.metadata_ = DMDcMetadata(
            n_states=n_states,
            n_inputs=n_inputs,
            n_samples=int(n_samples if n_samples is not None else n_transitions + 1),
            n_transitions=int(n_transitions),
            n_trajectories=int(n_trajectories),
            rank_used=rank_used,
            singular_values=[float(v) for v in s],
            condition_number=condition_number,
            state_names=state_names,
            input_names=input_names,
            dt=dt,
        )
        self.row_residual_norms_ = residual_norms
        return self

    def _make_mask(self, n_states: int, state_names: Sequence[str] | None) -> NDArray[np.bool_]:
        if isinstance(self.graph, LoopGraph):
            mask = self.graph.allowed_mask(state_names)
        else:
            mask = np.asarray(self.graph, dtype=bool)
        if mask.shape != (n_states, n_states):
            raise ValueError(f"Graph mask must have shape {(n_states, n_states)}; got {mask.shape}.")
        if np.any(mask.sum(axis=1) == 0):
            raise ValueError("Every state row must have at least one allowed predecessor.")
        return mask
