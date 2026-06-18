# Checkpoint — 2026-06-02_paper_support_package

Generated: 2026-06-02T16:15:00-05:00

## Date and campaign/task name

- Date: `2026-06-02`
- Task: build a reusable paper-support package with claim matrix, source CSV bundles, paper-ready figures, captions, and provenance for current JSALT2 and TAMU analysis artifacts.

## Research question

Can the current saved JSALT2 and TAMU outputs be turned into a reusable, provenance-preserving paper-support bundle that clearly separates claims already supported by current evidence from claims that still need more analysis?

## Repository state

- Branch: `main`
- Commit: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree: `True`

## Source files inspected

- `.agents/tools/reporting/build_paper_support_package.py`
- `tools/reporting/build_paper_support_package.py`
- `docs/workflows/paper_support_workflow.md`
- `docs/analysis_menu.md`
- `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/best_model_recommendation.json`
- `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/best_model_recommendation.json`
- `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/best_model_recommendation.json`
- `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/best_model_recommendation.json`
- `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/sweep_results.csv`
- `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/sweep_results.csv`
- `outputs/tamu_validation_export_20260602_filtered/validation_export_summary.json`
- `outputs/tamu_validation_export_20260602_filtered/inventory_validation_candidates.csv`
- `outputs/tamu_validation_export_overnight_20260525/validation_export_summary.json`
- `outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv`
- `outputs/tamu_validation_catalog_20260602_loop_sources_v1/validation_catalog_summary.json`
- `outputs/tamu_validation_catalog_20260602_loop_sources_v1/validation_catalog_summary.md`
- `outputs/tamu_validation_catalog_20260602_loop_sources_v1/validation_source_consistency_report.csv`

## Commands run

- `python tools/reporting/build_paper_support_package.py --help`
- `python tools/reporting/build_paper_support_package.py --outdir analysis/reports/2026-06-02_paper_support_package --jsalt2-with-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602 --jsalt2-no-h-compare-dir outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602 --jsalt2-with-h-sweep-dir outputs/overnight_sweeps/jsalt2_with_h_pair_20260601 --jsalt2-no-h-sweep-dir outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601 --tamu-validation-export-dir outputs/tamu_validation_export_20260602_filtered --tamu-validation-catalog-dir outputs/tamu_validation_catalog_20260602_loop_sources_v1 --prior-tamu-validation-export-dir outputs/tamu_validation_export_overnight_20260525`

## Inputs used

- JSALT2 delay-1 compare-equivalent outputs:
  - `outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602`
  - `outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602`
- JSALT2 authoritative broader tuned sweeps:
  - `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601`
  - `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601`
- TAMU filtered export:
  - `outputs/tamu_validation_export_20260602_filtered`
- TAMU prior export for cleanup comparison:
  - `outputs/tamu_validation_export_overnight_20260525`
- TAMU raw-source catalog:
  - `outputs/tamu_validation_catalog_20260602_loop_sources_v1`

## Outputs generated

### Tooling and docs

- `.agents/tools/reporting/build_paper_support_package.py`
- `tools/reporting/build_paper_support_package.py`
- `docs/workflows/paper_support_workflow.md`
- updated `docs/analysis_menu.md`

### Paper-support package

- `analysis/reports/2026-06-02_paper_support_package/README.md`
- `analysis/reports/2026-06-02_paper_support_package/MANIFEST.yaml`
- `analysis/reports/2026-06-02_paper_support_package/provenance.json`
- `analysis/reports/2026-06-02_paper_support_package/claim_matrix.csv`
- `analysis/reports/2026-06-02_paper_support_package/claim_matrix.md`
- `analysis/reports/2026-06-02_paper_support_package/figure_manifest.csv`
- `analysis/reports/2026-06-02_paper_support_package/captions.md`
- `analysis/reports/2026-06-02_paper_support_package/data/`
- `analysis/reports/2026-06-02_paper_support_package/figures/`
- `analysis/reports/2026-06-02_paper_support_package/CHECKPOINT.md`

## Key numerical results

- Paper-support figure count: `5`
- Source data bundle count: `6`
- Claim matrix rows: `9`
- `ready_now` claim rows: `6`
- `needs_more_analysis` rows: `3`
- JSALT2 delay-1 compare-equivalent winner with `h`: `pod_dmdc`, `test_rollout_rmse = 0.3308193645862872`
- JSALT2 delay-1 compare-equivalent winner without `h`: `pod_dmdc`, `test_rollout_rmse = 0.37289603980526714`
- JSALT2 broader tuned-surface stable winner with `h`: `dmdc`, `n_delays = 4`, `test_rollout_rmse = 0.17407191740679362`
- JSALT2 broader tuned-surface stable winner without `h`: `dmdc`, `n_delays = 4`, `test_rollout_rmse = 0.17075270970574585`
- Best raw-error excluded unstable candidate in the current package: `adaptive_dmdc`, `test_rollout_rmse = 0.160784`, `spectral_radius = 6.563`, `n_unstable_eigenvalues = 7`
- TAMU prior candidate count: `54`
- TAMU filtered candidate count: `43`
- Nuisance rows removed from collaborator-facing candidate table: `11`
- TAMU raw-source catalog counts:
  - steady sensor candidates: `2`
  - transient sensor candidates: `69`
  - steady velocity-profile candidates: `47`
  - unknown / not yet interpretable: `30`
- TAMU repeated-source consistency audit rows: `16`
- TAMU repeated-source mismatches: `0`

## Plots/tables generated

### Figures

- `analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_surface_winner_comparison.pdf`
- `analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_case_rmse_comparison.pdf`
- `analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_stability_tradeoff.pdf`
- `analysis/reports/2026-06-02_paper_support_package/figures/tamu_candidate_cleanup.pdf`
- `analysis/reports/2026-06-02_paper_support_package/figures/tamu_catalog_buckets.pdf`

### Figure source data

- `analysis/reports/2026-06-02_paper_support_package/data/jsalt2_surface_winner_comparison.csv`
- `analysis/reports/2026-06-02_paper_support_package/data/jsalt2_case_rmse_comparison.csv`
- `analysis/reports/2026-06-02_paper_support_package/data/jsalt2_stability_tradeoff.csv`
- `analysis/reports/2026-06-02_paper_support_package/data/tamu_candidate_cleanup.csv`
- `analysis/reports/2026-06-02_paper_support_package/data/tamu_catalog_buckets.csv`
- `analysis/reports/2026-06-02_paper_support_package/data/tamu_removed_candidate_rows.csv`

### Claims and captions

- `analysis/reports/2026-06-02_paper_support_package/claim_matrix.csv`
- `analysis/reports/2026-06-02_paper_support_package/figure_manifest.csv`
- `analysis/reports/2026-06-02_paper_support_package/captions.md`

## Interpretation

The repository now has a reusable paper-support workflow rather than a one-off note. The new tool reads already-saved outputs, creates consistent figure bundles in PDF/SVG/LaTeX-wrapper form, records the source CSV behind each plot, and writes a claim matrix that explicitly separates what is publishable now from what still needs more analysis.

For JSALT2, the package makes the central current claim legible: the selected winner depends on the authoritative search surface. The narrow delay-1 compare-equivalent surface selects `pod_dmdc`, while the broader tuned sweep surface selects delay-4 `dmdc`. The package also captures the stability-vs-error tradeoff that explains why the lower raw-error `adaptive_dmdc` candidates are not the present recommendation.

For TAMU, the package frames the current work correctly as data readiness and curation evidence. It supports claims about candidate cleanup, validation-catalog organization, and repeated-source consistency, while preserving a visible reminder that predictive validation on unseen TAMU cases still remains to be done.

## Limitations

- The package does not create new modeling results; it only reorganizes existing saved outputs into paper-ready assets.
- JSALT2 claims in the package are still current-split claims, not repeated-split robustness claims.
- The package does not yet assemble rollout overlay figures from saved state trajectories; it currently focuses on summary and per-case error figures.
- TAMU package claims are still about data readiness and cataloging, not ROM predictive performance on selected unseen cases.

## Bugs or anomalies

- `apply_patch` and some sandboxed commands remained blocked on this node due namespace exhaustion (`bwrap ... ENOSPC`), so the new tool and docs were written through the escalated shell path.
- No package-generation failures were observed once the tool was on disk.

## Follow-up tasks

1. Add representative JSALT2 rollout overlay figures for the selected stable winner and the best excluded unstable candidate.
2. Extend the paper-support tool with repeated-split summary ingestion once the next robustness batch exists.
3. Feed selected TAMU catalog cases into `validate` and `compare` workflows so the package can grow from data-readiness claims into predictive-validation claims.
4. If this workflow becomes central to manuscript production, add it to `docs/navigation/workflow_map.md` or a dedicated paper-writing section in the main README.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-02_paper_support_package/README.md`
- `analysis/reports/2026-06-02_paper_support_package/claim_matrix.md`
- `analysis/reports/2026-06-02_paper_support_package/figure_manifest.csv`
- `analysis/reports/2026-06-02_paper_support_package/captions.md`
- `analysis/reports/2026-06-02_paper_support_package/figures/`
- `.agents/tools/reporting/build_paper_support_package.py`
- `docs/workflows/paper_support_workflow.md`
