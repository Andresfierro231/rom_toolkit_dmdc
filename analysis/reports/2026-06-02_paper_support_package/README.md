# Paper Support Package

Generated: `2026-06-02T16:07:00-05:00`

This package collects paper-support claims, reusable figure inputs, and figure assets built from saved repo outputs.

## Reproduce

```bash
python tools/reporting/build_paper_support_package.py --outdir analysis/reports/2026-06-02_paper_support_package --jsalt2-with-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602 --jsalt2-no-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602 --jsalt2-with-h-sweep-dir outputs/overnight_sweeps/jsalt2_with_h_pair_20260601 --jsalt2-no-h-sweep-dir outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601 --tamu-validation-export-dir outputs/tamu_validation_export_20260602_filtered --tamu-validation-catalog-dir outputs/tamu_validation_catalog_20260602_loop_sources_v1 --prior-tamu-validation-export-dir outputs/tamu_validation_export_overnight_20260525
```

## Main artifacts

- Claim matrix: `analysis/reports/2026-06-02_paper_support_package/claim_matrix.csv`
- Figure manifest: `analysis/reports/2026-06-02_paper_support_package/figure_manifest.csv`
- Figure captions: `analysis/reports/2026-06-02_paper_support_package/captions.md`
- Figure directory: `analysis/reports/2026-06-02_paper_support_package/figures`
- Source data directory: `analysis/reports/2026-06-02_paper_support_package/data`

## Notes

- `ready_now` rows are claims that can already be supported from the current saved outputs, with stated caveats.
- `needs_more_analysis` rows are intentionally preserved so the package doubles as the next paper-work plan.
