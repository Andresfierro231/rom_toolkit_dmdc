# TAMU Real-Data Rerun After IMPL Fix

Generated: `2026-06-09`

## Purpose

Verify on the maintained real-data contract that the `IMPL-TAMU-001` workbook-audit fix moves single-phase office workbook rows from `not_audited` into the repeated-source consistency audit with real statuses.

## Repository state

- Branch: `main`
- Commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Working tree: dirty before and after this rerun

## Commands run

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-export \
  --inventory-root "../tamu_box_loop_data/Loop Operational Data" \
  --source-tables \
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv" \
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv" \
    "../physor2026_andrew/Validation_Data/validation_data.csv" \
  --outdir outputs/tamu_validation_export_20260609_post_impl_fix
```

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-catalog \
  --inventory-root "../tamu_box_loop_data/Loop Operational Data" \
  --source-tables \
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv" \
    "../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv" \
    "../physor2026_andrew/Validation_Data/validation_data.csv" \
  --outdir outputs/tamu_validation_catalog_20260609_post_impl_fix
```

## Output roots

- `outputs/tamu_validation_export_20260609_post_impl_fix/`
- `outputs/tamu_validation_catalog_20260609_post_impl_fix/`

## Files inspected

- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_export_summary.json`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_index.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_report.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_summary.md`
- `outputs/tamu_validation_export_20260609_post_impl_fix/office_workbook_promotion_decisions.csv`
- `outputs/tamu_validation_catalog_20260609_post_impl_fix/validation_catalog_summary.json`

## Key results

- Export summary:
  - `n_inventory_candidates = 43`
  - `n_normalized_cases = 8`
  - `n_nearest_fit_rows = 24`
  - `n_consistency_rows = 24`
  - `n_consistency_mismatches = 16`
  - `n_office_workbook_rows = 14`
  - `n_office_workbook_blocked = 8`

- Catalog summary:
  - `n_catalog_rows = 148`
  - `n_velocity_plot_rows = 46`
  - `n_consistency_rows = 24`
  - `n_consistency_mismatches = 16`
  - `n_office_workbook_rows = 14`
  - `n_office_workbook_blocked = 8`

## Audit-path verification

The `IMPL-TAMU-001` fix worked on real data.

Evidence:

- `validation_source_index.csv` now shows the single-phase workbook as:
  - `parsed_case_rows = 8`
  - `repeated_source_rows = 8`
- `validation_source_consistency_report.csv` now includes single-phase workbook rows for:
  - `Salt 1` through `Salt 4`
  - `Water 1` through `Water 4`
- `office_workbook_promotion_decisions.csv` now shows:
  - `consistency_status = mismatch`
  - not `not_audited`

This means the remaining problem is no longer audit wiring. The remaining problem is actual disagreement across maintained sources.

## Interpretation

The old state was ambiguous: workbook rows were parsed, but the repeated-source audit did not consume them, so the blocking report was not trustworthy.

The new state is trustworthy enough to support review:

- the single-phase office workbook participates in the repeated-source audit
- the canonical wide Fluid salt/water tables remain the chosen canonical rows
- both the PHYSOR table and the single-phase office workbook disagree with those canonical rows on many fields

The open question is now policy, not plumbing:

- whether the Fluid salt/water tables are the sole authoritative canonical source
- whether PHYSOR should remain in the exact-match audit set
- whether workbook-vs-canonical disagreement should be compared at raw precision, rounded precision, or a documented tolerance policy

## Immediate next decisions

1. Review whether `../physor2026_andrew/Validation_Data/validation_data.csv` should remain in the maintained exact-match audit set, given that it currently mismatches the canonical Fluid tables on every repeated case.
2. Decide whether workbook mismatch policy should stay exact-match or move to a documented tolerance/rounding contract.
3. If the canonical source contract changes, rerun:
   - `tamu-validation-export`
   - `tamu-validation-catalog`
4. Only after that policy decision, decide whether any workbook-derived rows should be promoted or continue to remain blocked.

## Exact files to inspect next

- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_report.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_summary.md`
- `outputs/tamu_validation_export_20260609_post_impl_fix/office_workbook_promotion_decisions.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_index.csv`
- `outputs/tamu_validation_catalog_20260609_post_impl_fix/validation_catalog_summary.json`
