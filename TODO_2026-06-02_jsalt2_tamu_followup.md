# TODO 2026-06-02: JSALT2 And TAMU Follow-Up

## Status

Active

## Completed today

- Added maintained parsing for the Jadyn office workbooks inside `dmdc-analysis`:
  - `SinglePhaseDataBase.xlsx` now parses into normalized steady-state rows
  - `TwoPhaseDataBase.xlsx` now parses into a separate noncanonical case family
  - export/catalog commands now emit:
    - `office_workbook_case_rows.csv`
    - `office_workbook_promotion_decisions.csv`
- Extended the TAMU validation tests to cover:
  - workbook parsing
  - canonical-vs-workbook blocking behavior
  - noncanonical two-phase workbook handling
  - result: `7 passed`
- Filtered TAMU validation candidate generation so collaborator-facing tables no longer surface example/demo rows, the empty pseudo-row `2025_06_19`, or metadata-only `Jadyn_runs` rows.
- Added a regression test covering the example-folder and pseudo-row failure mode.
- Regenerated filtered TAMU inventory and validation-export artifacts under `outputs/tamu_inventory_20260602_filtered/` and `outputs/tamu_validation_export_20260602_filtered/`.
- Staged the filtered inventory/validation artifacts under:
  - `to_box/flat_inventory_upload_2026-06-02_filtered/`
  - `to_box/operational_data_inventory_2026-06-02_filtered/`
- Uploaded both filtered staging folders to the Box outputs destination `385169164073`.
- Submitted the full pytest guardrail from `login3` as Slurm job `3202576`; `sacct` reports `COMPLETED` with exit code `0:0`.
- Ran apples-to-apples JSALT2 compare-equivalent sweeps that match the default compare surface:
  - `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/`
  - `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/`
- Resolved the earlier compare-vs-sweep confusion: the default compare path and the compare-equivalent sweeps agree on `pod_dmdc`; the broader June 1 sweep winners differ only because they searched `n_delays=4` and wider hyperparameters.
- Confirmed the current TAMU raw-data mirror path in this workspace is now `../tamu_box_loop_data/Loop Operational Data` rather than `../tamu_loop_data_25_mayo/Loop Operational Data`.
- Implemented the maintained TAMU validation catalog path:
  - CLI: `dmdc tamu-validation-catalog`
  - repeated-source exact-match audit for normalized Salt/Water validation rows
  - raw-source bucket exports for steady sensor, transient sensor, steady velocity-profile, and unknown/not-yet-interpretable candidates
  - reproducible velocity-profile plot bundles with per-case provenance notes and flattened plotting CSVs
- Ran the live audited validation export against:
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv`
  - `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
  - `../physor2026_andrew/Validation_Data/validation_data.csv`
  Output root:
  - `outputs/tamu_validation_export_20260602_contract_audit/`
- Ran the corrected live workbook-reconciliation export against the same three maintained source tables.
  Output root:
  - `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/`
- Ran the live raw-source validation catalog against `../tamu_box_loop_data/Loop Operational Data`.
  Output root:
  - `outputs/tamu_validation_catalog_20260602_loop_sources_v1/`
- Verified the new raw-mirror intake wrapper in `tamu_box_loop_data` with a real preview-only Box crawl:
  - `downloaded=0`
  - `pruned=0`
  - upstream-manifest files seen: `342`
  - run manifest root: `../tamu_box_loop_data/.box_sync_runs/20260602_133547/`

## Current read

- The raw-data mirror path changed, but the visible contents of `Loop Operational Data/` do not show an obvious new raw-data drop relative to the May 25 inventory basis.
- The new preview-only Box crawl agrees with that read: the upstream manifest matched the current local mirror and produced no raw-file downloads.
- The filtered TAMU candidate table dropped from `54` rows to `43` rows.
- The live repeated-source normalization audit currently shows no drift across the maintained Salt/Water sources:
  - audited rows: `16`
  - repeated-source rows with mismatches: `0`
- The first live raw-source catalog pass produced:
  - `steady_sensor_candidates = 2`
  - `transient_sensor_candidates = 69`
  - `steady_velocity_profile_candidates = 47`
  - `unknown_or_not_yet_interpretable = 30`
  - `velocity_profile_plot_index.csv` rows: `46` successful plotted PIV-style bundles
- The office-workbook parser is now live and the corrected export writes:
  - `office_workbook_case_rows.csv`
  - `office_workbook_promotion_decisions.csv`
- Important unfinished bug:
  - the real-data export is parsing the office workbook rows, but the repeated-source audit still reports:
    - `n_consistency_mismatches = 0`
    - `repeated-source rows = 0`
  - at the same time, `office_workbook_promotion_decisions.csv` shows the single-phase rows as:
    - `promotion_status = blocked_by_mismatch`
    - `consistency_status = not_audited`
  - interpretation:
    - the workbook rows are being written out
    - but the real-data repeated-source wiring is not yet consuming those single-phase rows in the live audit path
    - this must be debugged before trusting the workbook blocking report
- The biggest remaining catalog ambiguity is no longer whether the office workbooks can be parsed.
  It is whether the parsed single-phase workbook rows should be compared on exact raw precision, rounded-to-canonical precision, or some explicitly documented intermediate policy.
- SAM Stage A clarification:
  - the maintained collection `2026-06-02_nonhx_cooler_heat_removal_stage_a_salt2_followup_prep_v1/` is not just "prepared"
  - it already has `6` runtime rows
  - all `6` are fast failures with `last_time` only about `7.9 s` to `84.5 s`
  - this is a failed dev sweep, not a pending clean submission
- 2D follow-up clarification:
  - the executable next-leg path is currently `downcomer`, not just documentation
  - Salt 4 already has multiple complete passive downcomer cases in the existing campaign
  - Salt 3 recovery root `...__salt3_two_case_slurm_2026-06-02_v3_fixids/` reached:
    - `rad_off`: `complete`
    - `rad_on`: `stopped_without_converging` at `20000` max iterations
- Ethan status at wrap-up:
  - continuation `3202708` still running
  - render jobs `3203083` and `3203084` still pending
- No new SAM, 2D, or Ethan submissions were launched in this pass because the safe next actions depend on the workbook-audit bug fix plus the clarified SAM/2D state above.
- The current JSALT2 external collection still appears to be the same `11` named case directories, so `max_files = 11` is already effectively the full collection for this study at the moment.
- The key JSALT2 policy decision is now explicit:
  - default compare surface still says `pod_dmdc` is best at delay `1`
  - broader tuned sweep surface is the authoritative selection surface
  - both with-`h` and no-`h` variants remain active while the input-treatment policy stays open

## Active decisions

1. JSALT2 selection policy is now: use the broader tuned sweep surface as the authoritative final model-selection surface.
2. Keep both with-`h` and no-`h` study variants active until a separate official policy decision resolves the input-treatment question.
3. Decide whether the current `Jadyn_runs` subtree should ever become a validation candidate source once it has real metadata, or whether it should remain excluded from these collaborator-facing candidate tables.

## Next analysis to do

1. Monitor the submitted broader sweep jobs `3202984` and `3202985` and capture their final outputs when they finish.
2. Design the next JSALT2 robustness batch around split and search-surface sensitivity, not just one more repetition of the same pair:
   - repeated by-case splits or leave-one-case-out style checks
   - `n_delays = [1, 2, 4, 8]` for delay-capable linear models
   - `pod_rank` sensitivity around `2, 3, 4, 0.999`
   - `center` / `scale` toggles
3. Review the freshly uploaded filtered TAMU candidate tables with collaborators and decide whether any additional filter heuristics are needed.
4. Use `outputs/tamu_validation_catalog_20260602_loop_sources_v1/` as the live TAMU triage root for the next pass:
   - inspect the `steady_sensor_candidates.csv` office workbook rows manually
   - review `unknown_or_not_yet_interpretable.csv` and promote any files that actually contain reusable steady or transient measurements
   - spot-check the generated `velocity_profile_plots/` bundles before wider share-out
5. Decide whether the maintained exact-match audit set should remain anchored to:
   - Fluid salt + Fluid water + PHYSOR wide table
   - or whether additional repeated tables should be added to the audit
6. Keep monitoring `../ethan_runs/` separately; the runtime-recovery lane is now beyond the old bootstrap blocker and active continuation `3202708` is the remaining 3D gate.
7. First task tomorrow:
   - debug why `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/office_workbook_case_rows.csv` is populated while the same run's repeated-source audit still shows zero repeated rows and `not_audited` workbook promotion statuses
8. After that bug is fixed:
   - rerun `tamu-validation-export`
   - rerun `tamu-validation-catalog`
   - then re-read the single-phase workbook discrepancy policy using the new real report
9. Only after the workbook audit is trustworthy:
   - decide whether the next 2D action is another Salt 3 downcomer recovery for the remaining `rad_on` case
   - or a documented promotion/exclusion decision using the current Salt 3/Salt 4 passive evidence
10. For SAM tomorrow:
   - treat the current Stage A collection as failed-dev evidence
   - decide whether to redesign the sweep or pause until the Salt2 boundary-condition contract is tightened

## Rules

- Box outputs destination: `385169164073`
- Raw-data source folder: `246873664013`
- Never upload anything from `dmdc-analysis` into the raw-data Box folder
