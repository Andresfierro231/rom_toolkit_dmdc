# Phase 3–4 Workflow: POD-DMDc and Unseen-Case Validation

This phase adds two major capabilities:

1. **POD-DMDc**, which fits DMD/DMDc in POD modal-coordinate space.
2. **Unseen-case validation**, which trains on selected cases and evaluates rollout error on held-out cases.

## Recommended workflow

```text
1. Inspect data.
2. Resample only if needed.
3. Fit POD to understand rank/energy.
4. Fit POD-DMDc.
5. Validate on unseen cases.
6. Inspect error_by_case.csv, error_by_state.csv, and forecast_horizon_errors.csv.
```

## Minimal command sequence

```bash
dmdc inspect-data --config configs/example_inspect_data.toml

dmdc pod --config configs/example_pod.toml

dmdc pod-dmdc --config configs/example_pod_dmdc.toml

dmdc validate --config configs/example_validate_unseen_cases.toml
```

## Thermal-loop interpretation

For thermal-hydraulic loop data, use state columns such as:

```text
TP1, TP2, TP3, TP4, TP5, TP6, massFlowRate, wall temperatures
```

Use input columns for known boundary or forcing variables:

```text
q_heater, T_amb, h_amb, pump speed, inlet temperature
```

If no forcing is known, omit input columns. The workflow becomes POD-DMD instead of POD-DMDc.
