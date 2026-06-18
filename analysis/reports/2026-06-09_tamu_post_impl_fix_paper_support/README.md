# TAMU Post-Implementation Paper Support Update

This package updates the manuscript-facing TAMU evidence after the real-data
rerun completed on `2026-06-09`.

## Inputs

- Validation export root: `outputs/tamu_validation_export_20260609_post_impl_fix`
- Validation catalog root: `outputs/tamu_validation_catalog_20260609_post_impl_fix`

## Main interpretation

- The single-phase office workbook now participates in the repeated-source audit.
- The previous `not_audited` state is resolved.
- The remaining issue is substantive disagreement across maintained sources, not missing audit coverage.

## Artifacts

- `data/*.csv`: figure source data
- `figures/*.pdf`: manuscript-ready vector figures
- `figures/*.svg`: editable vector figures
- `figures/*.tex`: LaTeX wrappers
- `captions.md`: proposed captions

## Figure-level analysis

### tamu_repeated_source_coverage

The important update is not the absolute row count; it is that the office
single-phase workbook now contributes eight repeated-source rows. That means
the audit path is now working on real data.

### tamu_single_phase_workbook_mismatch_counts

These mismatch counts show that the remaining blocker is not missing audit
coverage. It is a real source-disagreement problem concentrated in thermal
state fields and some ancillary uncertainty/unlabeled fields.

### tamu_catalog_bucket_counts_post_impl_fix

The catalog remains a readiness artifact. It shows triage progress and source
availability, but it still does not constitute unseen-case predictive validation.
