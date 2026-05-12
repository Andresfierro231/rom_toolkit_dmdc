# Spatial dependence, delay embeddings, and QR sensor selection

This note explains the three loop-oriented upgrades in this repository.

## 1. Spatial dependence through the state vector

If your state vector is

```math
x_k = [TP1_k, TP2_k, TP3_k, TP4_k, \dot m_k]^T,
```

then the learned matrix `A` in

```math
x_{k+1} \approx A x_k + B u_k
```

already captures cross-dependence between points. Entry `A[i, j]` says how much state `j` at the current sample contributes linearly to state `i` at the next sample.

The limitation is that dense DMDc does not know the loop geometry. It does not automatically know that `TP2` is upstream of `TP3`, or that `TP6` returns to `TP1` through a loop branch.

## 2. Graph-constrained DMDc

Use `LoopGraph` when you want to encode physical adjacency.

```python
from dmdc import GraphConstrainedDMDcModel, LoopGraph

graph = LoopGraph(
    nodes=["TP1", "TP2", "TP3", "TP4"],
    edges=[("TP1", "TP2"), ("TP2", "TP3"), ("TP3", "TP4"), ("TP4", "TP1")],
    directed=True,
    include_self=True,
)

model = GraphConstrainedDMDcModel(graph=graph)
model.fit(X, U, state_names=graph.nodes, input_names=["heater_power"])
```

The edge `(source, target)` means `target(k+1)` may depend on `source(k)`. The model forces forbidden entries of `A` to zero and solves row-wise least-squares problems using graph-allowed predictors.

Recommended use: first fit dense DMDc as a baseline, then compare graph-constrained DMDc against the dense model. The graph-constrained model is more interpretable but can be less accurate if the graph is too restrictive.

## 3. Delay-DMDc for transport delay

Thermal-fluid loops often have advective delay. A heater perturbation may not appear at a downstream thermocouple until several samples later. Delay embedding replaces `x_k` with

```math
z_k = [x_k, x_{k-1}, \ldots, x_{k-d+1}]^T.
```

CLI example:

```bash
dmdc fit \
  --data data/example_timeseries.csv \
  --state-cols x1 x2 \
  --input-cols u1 \
  --time-col time \
  --n-delays 3 \
  --rank 0.999 \
  --outdir outputs/delay_fit \
  --plots
```

Python example:

```python
from dmdc import DMDcModel, make_delay_embedding

Z, U_aligned, z_names = make_delay_embedding(X, U, n_delays=4, state_names=state_names)
model = DMDcModel(rank=0.999)
model.fit(Z, U_aligned, state_names=z_names, input_names=input_names)
```

## 4. QR/Q-DEIM-style sensor selection

Given snapshot data `X`, compute the dominant state-space left singular vectors `U_r`. Then perform pivoted QR on `U_r.T`. The pivot order ranks original state variables by how useful they are for spanning the retained low-rank subspace.

CLI example:

```bash
dmdc select-sensors \
  --data my_loop_data.csv \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 massFlowRate \
  --time-col time \
  --rank 0.999 \
  --n-sensors 4 \
  --scale \
  --outdir outputs/sensor_selection \
  --plots
```

Outputs:

```text
sensor_ranking.csv
selected_sensors.txt
singular_values.csv
reconstruction_error_vs_sensors.csv
reconstruction_error_vs_sensors.pdf
```

Interpretation warning: QR-selected sensors are important for reconstructing the dominant low-rank subspace. This is not identical to causal importance. Always compare predictive performance before removing states from the model.
