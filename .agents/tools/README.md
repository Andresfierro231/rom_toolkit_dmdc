# Agent Tools

This folder is the canonical home for reusable agent-side Python tools.

## Namespaces

- `provenance/`: git state, hashing, manifest validation
- `reporting/`: manifests, checkpoints, journals, figure/table helpers
- `studies/`: campaign initialization, runtime-row maintenance, campaign summaries

## Rule

Keep business logic here. Root `tools/` scripts should remain thin wrappers that
delegate into these files through `tools/_agents_bridge.py`.
