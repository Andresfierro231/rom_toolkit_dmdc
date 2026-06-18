# AGENTS.md

## Repository role

This repository is a raw-data intake mirror for the TAMU loop dataset.

Its scope is intentionally narrow:

- pull raw files from the Box source folder
- preserve local sync tooling and operating docs
- keep lightweight inventories for orientation
- hand the raw data off to `dmdc-analysis`

This is not the analysis workspace.
This is not the report workspace.
This is not the outbound Box publishing workspace.

## Non-negotiable Box policy

- NEVER upload anything from this repository back to Box.
- NEVER push plots, notes, summaries, inventories, repaired data, or derived outputs from here.
- NEVER use the raw-data Box folder as a publication target.
- Allowed direction is Box raw-data folder -> local mirror only.

If a user asks for Box upload behavior from this repository, stop and redirect that work to `dmdc-analysis/to_box/` and the separate Box outputs folder.

## Primary local paths

- Raw local mirror: `Loop Operational Data/`
- Preferred sync script: `tools/box_sync_pull.py`
- Single-file helper: `tools/box_download.py`
- Detailed inventory mirror: `tamu_inventory_detailed/`
- Short inventory mirror: `tamu_inventory/`

## Repository-specific rules

- Treat this repo as pull-only from Box.
- Prefer `tools/box_sync_pull.py` over ad hoc Box folder downloads.
- Do not create analysis outputs here unless the user explicitly wants temporary scratch work.
- Do not delete local files casually; this mirror may contain local-only context that should not be removed by default.
- Keep credentials and Box tokens out of tracked files.
- Future GitHub persistence for this workflow should include scripts, docs, and instructions only.
