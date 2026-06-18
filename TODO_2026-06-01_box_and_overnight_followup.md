# TODO 2026-06-01: Box Cleanup And Overnight Follow-Up

## Status

Active

## Completed today

- Uploaded the flat inventory summary files from `to_box/flat_inventory_upload_2026-05-26/` to Box folder `385169164073`.
- Uploaded the nested staging folder `to_box/operational_data_inventory_2026-05-26/` to the same Box destination.
- Uploaded the local `flat_inventory_upload_2026-05-26/` folder view as a remote subfolder as well.
- Verified the Box root now contains:
  - root-level flat summary files
  - `flat_inventory_upload_2026-05-26/`
  - `operational_data_inventory_2026-05-26/`
- Deleted the remote smoke-test file `box_upload_smoke_test_2026-05-28.txt` from Box.
- Deleted the local smoke-test staging file `to_box/box_upload_smoke_test_2026-05-28.txt`.
- Retired `TODO_2026-05-29_tamu_box_followup.md` because its upload tasks are no longer current.

## Active analysis tasks

1. Review `outputs/tamu_inventory_20260526_detailed_v2/folder_summaries.md` manually for domain-specific notes, especially dated folders and `Jadyn_runs`.
2. Review `outputs/tamu_validation_export_overnight_20260525/nearest_fit_suggestions.csv` and `inventory_validation_candidates.csv` to choose real validation cases.
3. Decide the JSALT2 `h` strategy:
   - keep `h`
   - drop `h`
   - keep both as named variants
4. Inspect `stability_warnings.txt` and `uncertainty_summary.csv` for the JSALT2 compare outputs if a tighter interpretation is needed.

## Overnight run candidates worth considering

1. Re-run the no-`h` JSALT2 sweep using the repaired autonomous campaign lineage from `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/` so the sweep provenance points at the fully repaired no-input workflow rather than the earlier failed-at-inspect run.
2. Run a matching with-`h` versus no-`h` sweep pair again only if today’s code changes affect compare, sweep, or validation behavior. Without new code changes, the repo already has a useful overnight pair from `2026-05-25`.
3. Rebuild TAMU inventory and validation export overnight only if the sibling raw-data mirror changed since `2026-05-26`; otherwise it is unnecessary churn.
4. Run the full pytest regression overnight if more code lands today in `src/dmdc/`, `src/dmdc/campaign.py`, `src/dmdc/cli.py`, or the campaign wrapper scripts.

## Deferred for now

- No Box uploader hardening task is scheduled today. Keep it as future work only if the helper shows a real post-upload hang again in normal use.

## Provenance for today's Box cleanup

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Commands run:
  - `python tools/box/upload_to_tamu_flow_loop_box.py --dry-run --source-root to_box/flat_inventory_upload_2026-05-26`
  - `python tools/box/upload_to_tamu_flow_loop_box.py --execute --source-root to_box/flat_inventory_upload_2026-05-26`
  - `python tools/box/upload_to_tamu_flow_loop_box.py --dry-run`
  - `python tools/box/upload_to_tamu_flow_loop_box.py --execute`
  - `box files:delete 2251382041589 --yes --force`
  - `box folders:items 385169164073 --max-items 1000 --fields type,id,name,size`

## Rules

- Box outputs destination: `385169164073`
- Raw-data source folder: `246873664013`
- Never upload anything from `dmdc-analysis` to the raw-data folder
