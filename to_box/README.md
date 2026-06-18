# to_box

This directory is the staging area for team-facing outputs that may be uploaded to Box from `dmdc-analysis`.

The configured Box destination is:

- path: `All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data`
- Box folder ID: `385169164073`

Use it for:

- plots
- slide-ready figures
- brief notes
- CSV summaries meant for collaborators
- inventory overviews staged for collaborators
- other lightweight outbound artifacts

Do not use it for:

- raw TAMU loop data
- copies of `Loop Operational Data/`
- large Box mirror folders
- anything intended for the raw-data Box source folder

## Critical rule

Uploads from `dmdc-analysis/to_box/` must go to a separate Box outputs folder, never to the raw-data Box folder used by `tamu_loop_data/`.

Keep the direction split clear:

```text
raw-data Box folder         -> tamu_loop_data/
dmdc-analysis/to_box/       -> separate Box outputs folder
```

If a future agent is unsure which Box folder is the destination, stop and confirm the outputs folder before uploading anything.

## Recommended command

Preview first:

```bash
python tools/box/upload_to_tamu_flow_loop_box.py --dry-run
```

Then upload:

```bash
python tools/box/upload_to_tamu_flow_loop_box.py --execute
```

Only request a new Box version for changed same-name files if you explicitly want to replace the remote copy:

```bash
python tools/box/upload_to_tamu_flow_loop_box.py --execute --overwrite-changed
```

Default safety behavior:

- same-name same-size remote files are kept
- same-name changed-size remote files are skipped unless `--overwrite-changed` is provided
- remote files that are not represented locally are left alone
- local `to_box/` contents are never deleted by the uploader
