# TAMU Loop Data Recovery And Box Share-Out

This workflow lets `dmdc-analysis` recreate the sibling `tamu_loop_data/` repo and restore the Box-linked intake and share-out pattern after scratch loss.

## Fixed Box endpoints

Raw-data source folder:

- path: `All Files/TAMU Bubble Flow/Loop Operational Data`
- Box folder ID: `246873664013`
- role: pull-only source for `tamu_loop_data/`

Analysis outputs folder:

- path: `All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data`
- Box folder ID: `385169164073`
- role: outbound destination for `dmdc-analysis/to_box/`

Hard rule:

- never upload anything from `dmdc-analysis` or `tamu_loop_data/` into the raw-data source folder

## Recreate the tamu_loop_data repo

From the root of `dmdc-analysis`:

```bash
python tools/studies/init_tamu_loop_data_repo.py --target-root ../tamu_loop_data
```

That scaffold writes:

- `../tamu_loop_data/README.md`
- `../tamu_loop_data/AGENTS.md`
- `../tamu_loop_data/.gitignore`
- `../tamu_loop_data/tools/box_sync_pull.py`
- `../tamu_loop_data/tools/box_download.py`

The scaffold is self-contained inside `dmdc-analysis/templates/tamu_loop_data_repo/`, so recovery does not depend on an existing scratch copy of `tamu_loop_data/`.

## Box CLI setup

Install Box CLI if needed:

```bash
npm install --global @box/cli
```

Authenticate:

```bash
box login -d
box users:get me
```

## Rebuild the raw-data mirror

After the scaffold exists:

```bash
cd ../tamu_loop_data
python tools/box_sync_pull.py --dry-run
python tools/box_sync_pull.py
```

Optional local bookkeeping:

```bash
env TMPDIR=/tmp python -m dvc add "Loop Operational Data"
```

## Use the rebuilt mirror from dmdc-analysis

Back in `dmdc-analysis`:

```bash
dmdc tamu-inventory \
  --root ../tamu_loop_data/Loop\ Operational\ Data \
  --outdir outputs/tamu_inventory

dmdc tamu-validation-export \
  --inventory-root ../tamu_loop_data/Loop\ Operational\ Data \
  --source-tables \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv \
  --outdir outputs/tamu_validation_export
```

## Stage and upload analysis outputs

Place outbound artifacts under `to_box/`.

Preview:

```bash
python tools/box/upload_to_tamu_flow_loop_box.py --dry-run
```

Upload with version-safe overwrite of changed files:

```bash
python tools/box/upload_to_tamu_flow_loop_box.py --execute
```

Behavior:

- same-name same-size files are skipped
- same-name changed-size files are skipped by default
- same-name changed-size files are uploaded as new Box versions only when `--overwrite-changed` is set
- missing remote subfolders are created under `analyzing_operational_data`
- root `to_box/README.md` is excluded by default

## Minimum recovery checklist

1. Recreate `../tamu_loop_data` with `python tools/studies/init_tamu_loop_data_repo.py`.
2. Re-authenticate Box with `box login -d`.
3. Pull the raw dataset with `../tamu_loop_data/tools/box_sync_pull.py`.
4. Run inventories from `dmdc-analysis` against `../tamu_loop_data/Loop Operational Data`.
5. Stage share-out artifacts in `to_box/`.
6. Upload only to Box folder `385169164073`, never to Box folder `246873664013`.
