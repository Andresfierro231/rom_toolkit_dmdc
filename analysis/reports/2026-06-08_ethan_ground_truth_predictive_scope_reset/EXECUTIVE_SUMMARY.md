# Executive Summary

Generated: `2026-06-08T12:24:00-05:00`

## Scope Reset

For the next analysis phase, `Ethan CFD` is treated as the working ground-truth source for model development. The near-term objective is no longer to use TAMU as a gating dataset for day-to-day modeling decisions. The objective is to predict future Ethan CFD behavior in two aligned lanes:

- a `2D` predictive lane using dense thermal and flow states
- a `1D` axial lane using aggregated axial heat-transport states

Both lanes are now scaffolded as repo-native studies under [studies/ethan_ground_truth_predictive](</scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/studies/ethan_ground_truth_predictive>) and are backed by canonical tables built from sibling `ethan_runs` artifacts.

## What Is Ready Today

The Ethan predictive study contract is now implemented:

- Canonical 2D table: [ethan_ground_truth_predictive_2d.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/data/processed/ethan_ground_truth_predictive_2d.csv)
- Canonical 1D axial heat table: [ethan_ground_truth_predictive_1d_axial_heat.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/data/processed/ethan_ground_truth_predictive_1d_axial_heat.csv)
- Manifest/provenance: [ethan_ground_truth_predictive_manifest.json](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/data/processed/ethan_ground_truth_predictive_manifest.json)

Measured status from today’s rebuilt tables and inspections:

- `2D`: `22,140` rows across `9` salt cases, all `9/9` usable for ROM workflows, no inspection warnings.
- `1D axial heat`: `20,520` rows across `9` salt cases, all `9/9` usable for ROM workflows, with only two irregular-time-step warnings on Kirst cases.

Actual predictive outputs now also exist for both lanes:

- 2D compare: [outputs/ethan_ground_truth_predictive/2d_compare](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_compare)
- 2D validation: [outputs/ethan_ground_truth_predictive/2d_validation](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_validation)
- 1D compare: [outputs/ethan_ground_truth_predictive/1d_axial_heat_compare](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/1d_axial_heat_compare)
- 1D validation: [outputs/ethan_ground_truth_predictive/1d_axial_heat_validation](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/1d_axial_heat_validation)

Current measured predictive result on the explicit held-out split:

- `2D compare`: best held-out model is `persistence` with test RMSE `5.56`; all ROM candidates overfit the training set and miss badly on the native Salt 2 holdout.
- `1D compare`: best held-out model is `persistence` with test RMSE `4.09`; the same overfit pattern appears in the ROM candidates.
- `2D validate` on the current `pod_dmdc` default: train RMSE `0.899`, test RMSE `156.85`.
- `1D validate` on the current `pod_dmdc` default: train RMSE `0.359`, test RMSE `17.07`.

The failure mode is concentrated rather than universal. On both lanes, the Jin held-out cases stay low-error, while `val_salt_test_2_coarse_mesh_laminar` dominates the test failure:

- `2D pod_dmdc` test RMSE by case: Salt 2 native `300.34`, Salt 3 Jin `1.03`, Salt 4 Jin `1.25`.
- `1D pod_dmdc` test RMSE by case: Salt 2 native `111.18`, Salt 3 Jin `0.332`, Salt 4 Jin `0.388`.

Dry-run campaign plans were also refreshed for both lanes:

- [2D campaign plan](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/campaigns/ethan_ground_truth_predictive_2d/run_20260608T170452Z_da378d7c/campaign_plan.md)
- [1D campaign plan](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/campaigns/ethan_ground_truth_predictive_1d_axial_heat/run_20260608T170452Z_8eb5b180/campaign_plan.md)

## What TAMU Would Need

TAMU does not become a predictive unseen-case validation story until it moves beyond inventory and metadata tables into a held-out predictive package. Concretely, that would require:

1. Imported canonical TAMU timeseries tables with trusted state and input columns, not just folder metadata.
2. Explicit case-aware train/test splits where TAMU cases are unseen during fitting.
3. Executed `compare` and `validate` outputs on those held-out TAMU cases.
4. Durable per-case error tables, operating-envelope summaries, and claim-level evidence showing when the Ethan-trained models generalize and when they do not.

Until those artifacts exist, TAMU remains a future external-check path rather than a current predictive-validation claim.

## Next Needed Runs

The next execution block is now narrower:

1. Treat `persistence` as the current acceptance bar in both lanes and preserve that result as the baseline claim.
2. Run broader Ethan-only ROM sweeps that specifically target the Salt 2 native gap instead of repeating the current narrow compare surface.
3. Revisit split design and static-input policy if the native Salt 2 case is acting as a domain shift rather than a normal held-out case.
4. Repair the zero-advance transport extraction so the 1D lane can move beyond axial heat aggregates.
5. Stage replay only after a ROM lane can beat the persistence baseline on the explicit-case split.
