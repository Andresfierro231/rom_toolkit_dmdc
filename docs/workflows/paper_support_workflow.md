# Paper Support Workflow

Use this workflow to turn saved study outputs into a reusable paper-support
package with:

- a claim matrix
- source CSV tables for each figure
- PDF and SVG figures
- LaTeX figure wrappers
- caption drafts
- a manifest with provenance

The current manuscript workspace that consumes these assets is:

- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis`

After generating or refreshing a paper-support package in this repository,
mirror the imported figures/tables plus manuscript-facing provenance notes into
that paper repository.

## Command

```bash
python tools/reporting/build_paper_support_package.py \
  --outdir analysis/reports/2026-06-02_paper_support_package \
  --jsalt2-with-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602 \
  --jsalt2-no-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602 \
  --jsalt2-with-h-sweep-dir outputs/overnight_sweeps/jsalt2_with_h_pair_20260601 \
  --jsalt2-no-h-sweep-dir outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601 \
  --tamu-validation-export-dir outputs/tamu_validation_export_20260602_filtered \
  --tamu-validation-catalog-dir outputs/tamu_validation_catalog_20260602_loop_sources_v1 \
  --prior-tamu-validation-export-dir outputs/tamu_validation_export_overnight_20260525
```

## What it writes

- `claim_matrix.csv` and `claim_matrix.md`
- `figure_manifest.csv`
- `captions.md`
- `figures/*.pdf`
- `figures/*.svg`
- `figures/*.tex`
- `data/*.csv` and `data/*.md`
- `MANIFEST.yaml`
- `provenance.json`
- `README.md`

## Current figure set

- `jsalt2_surface_winner_comparison`
- `jsalt2_case_rmse_comparison`
- `jsalt2_stability_tradeoff`
- `tamu_candidate_cleanup`
- `tamu_catalog_buckets`

## When to rerun

Rerun the package whenever one of these changes:

- a new JSALT2 sweep or compare-equivalent run becomes authoritative
- the TAMU filtered validation export changes
- the TAMU raw-source catalog changes
- the paper needs refreshed captions, manifests, or figure bundles

## Notes

- The package is built from saved outputs under `outputs/`; it does not retrain
  or rerun expensive studies.
- `ready_now` claims in the matrix are current evidence-backed claims with
  explicit caveats.
- `needs_more_analysis` claims are intentionally retained so the package also
  functions as a paper work plan.
