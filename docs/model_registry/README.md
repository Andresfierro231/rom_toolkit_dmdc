# Model registry and deployment

The model registry prevents confusion about which validated model is powering a
live dashboard. Instead of a live config pointing to an arbitrary path, register
and promote a model:

```bash
dmdc model-register \
  --model outputs/compare/best_model.pkl \
  --name simple_loop_pod_dmdc_v1 \
  --stage candidate \
  --metrics outputs/compare/model_comparison.csv
```

Promote a specific immutable version:

```bash
dmdc model-promote --name simple_loop_pod_dmdc_v1 --version <VERSION> --stage production
```

Then live configs can use:

```toml
[model]
registry_name = "simple_loop_pod_dmdc_v1"
stage = "production"
registry_root = "models/registry"
```

The live run writes `model_identity.json`, and the Streamlit operator dashboard
shows the registry name, stage, and version at the top.

## Theory / workflow idea

The registry separates three concepts:

1. **Training output**: a model file produced by `compare`, `sweep`, or `pod-dmdc`.
2. **Immutable registered version**: a copied artifact with SHA256 and metadata.
3. **Deployment stage**: a pointer like `candidate`, `staging`, or `production`.

This mirrors good experimental practice: validation results stay tied to a model
version, while live deployment references a named stage.
