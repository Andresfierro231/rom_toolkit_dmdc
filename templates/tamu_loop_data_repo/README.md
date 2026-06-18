# TAMU Loop Data

This repository is a pull-only local mirror of the raw TAMU loop data from Box.

Its job is narrow:

1. Pull raw data from the Box source folder into `Loop Operational Data/`.
2. Keep lightweight sync scripts, inventories, and operating docs.
3. Hand the raw data off to `dmdc-analysis` for actual analysis work.

It is not the place for plots, notes, repaired data, derived tables, or report outputs.

## Hard Rules

### Rule 1: This repo only pulls from Box

Allowed direction:

```text
Box raw-data folder  ->  this local mirror
```

Not allowed:

```text
this local mirror  ->  any Box folder
```

### Rule 2: Never publish outputs from here

NEVER upload anything from this repo back to Box.

That includes:

- plots
- notes
- manuscripts
- repaired files
- derived CSV or Parquet tables
- inventory summaries
- DVC metadata
- anything produced by analysis

### Rule 3: Analysis belongs in `dmdc-analysis`

Use this repo to maintain the raw local data mirror.

Use `dmdc-analysis` to:

- run `dmdc` workflows
- generate inventories
- make plots
- write notes
- prepare artifacts for sharing

The intended split is:

```text
tamu_loop_data/      -> raw data intake only
dmdc-analysis/       -> analysis, figures, notes, reports, staging for share-out
```

## Daily Workflow

Preview the Box pull:

```bash
python tools/box_sync_pull.py --dry-run
```

Run the Box pull:

```bash
python tools/box_sync_pull.py
```

Optionally refresh the local DVC pointer:

```bash
env TMPDIR=/tmp python -m dvc add "Loop Operational Data"
```

Then move to `dmdc-analysis` for inventories and analysis:

```bash
dmdc tamu-inventory --root ../tamu_loop_data/Loop\ Operational\ Data
```

## Box Source Folder

- folder name: `Loop Operational Data`
- Box folder ID: `246873664013`

## Critical Warning

- Never upload analysis outputs into the raw-data Box folder.
- Never use this repo as the staging area for outbound Box uploads.
- Never assume the Box source folder is safe for collaborative output publishing.
