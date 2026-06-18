# Root Tool Wrappers

The scripts in this folder are wrapper entrypoints for humans and automation.
They intentionally do not contain the canonical implementation logic.

## Delegation model

- `tools/_agents_bridge.py` resolves the matching path under `.agents/tools/`
- each wrapper in `tools/` should map one-to-one to a real implementation file
- if a new reusable tool is added, add it under `.agents/tools/` first and then
  add the corresponding root wrapper

## Current groups

- `tools/box/` -> `.agents/tools/box/`
- `tools/provenance/` -> `.agents/tools/provenance/`
- `tools/reporting/` -> `.agents/tools/reporting/`
- `tools/studies/` -> `.agents/tools/studies/`
