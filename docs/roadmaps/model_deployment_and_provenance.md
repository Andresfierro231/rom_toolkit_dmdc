# Model deployment, registry, provenance, and versioning plan

The live system should eventually load models by registry name/stage instead of raw paths.  This avoids accidental use of stale or unvalidated models.

## Proposed registry commands

```bash
dmdc model-register --model outputs/sweep/best_model/model.pkl --name simple_loop_pod_dmdc_v1 --registry models/
dmdc model-promote --name simple_loop_pod_dmdc_v1 --stage production --registry models/
dmdc model-list --registry models/
```

## Registry metadata

Each model registration should include:

```text
model name
model stage
model path
model type
training data path/hash
config hash
validation metrics
stability summary
operating-condition envelope
created timestamp
package version
git commit hash if available
```

## Live config integration

Future live configs should support:

```toml
[model]
registry_name = "simple_loop_pod_dmdc_v1"
stage = "production"
```

The current repo already writes provenance in many output folders.  The next hardening step is formal schema/version validation for every live table and archive manifest.
