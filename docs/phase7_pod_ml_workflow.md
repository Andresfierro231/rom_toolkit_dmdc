# Phase 7 workflow: optional POD-ML, integrated with the ROM toolkit

Phase 7 adds optional ML dynamics in POD coefficient space and integrates it with existing commands.

## New command

```bash
dmdc pod-ml --config configs/example_pod_ml.toml
```

## Compare POD-ML against existing models

```bash
dmdc compare --config configs/example_compare_with_pod_ml.toml
```

This is the recommended way to use POD-ML. Do not judge an ML model only from training reconstruction. Compare held-out rollout error against:

- persistence
- mean predictor
- DMDc
- POD-DMDc
- POD-ML

## Model names for comparison

```text
pod_ml_ridge
pod_ml_random_forest
pod_ml_gradient_boosting
pod_ml_mlp
```

`pod_ml` by itself defaults to ridge.

## Integration points

Phase 7 integrates with:

- `PODBasis` from Phase 2
- multi-case trajectory loading
- train/test comparison dashboards
- LaTeX report generation through `dmdc report`
- existing plotting utilities
- existing metrics and residual/error-by-state machinery

## Philosophy reminder

POD-ML is optional. The repo should remain defensible as a scientific ROM toolkit because the core methods are still transparent SVD/POD and DMD/DMDc.
