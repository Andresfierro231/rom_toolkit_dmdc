# Presentation Slide Outline

Generated: `2026-06-08T12:35:00-05:00`

Audience assumption: technical research update with interest in what is claim-ready now, what changed this week, and what the next analysis block should do.

## Slide 1

**Title**

Ethan Ground-Truth Scope Reset and Current Predictive Results

**Purpose**

Set the frame for the presentation: what changed, what is ready now, and what remains open.

**Figures**

- None required.

**Speaker Notes**

We reset the near-term program around Ethan CFD as the working ground truth. That means the immediate objective is no longer broad validation readiness across every source. The immediate objective is to predict future Ethan CFD behavior in 2D and 1D, understand where those predictors fail, and use TAMU later as an external check rather than as the day-to-day gating dataset.

## Slide 2

**Title**

Current Headline Results

**Purpose**

Give the audience the three main conclusions up front.

**Figures**

- Optional small text-only summary box.

**Speaker Notes**

Three points matter today. First, JSALT2 remains the most presentation-ready positive result: broader tuned delay-4 DMDc beats the narrow compare surface on the current split. Second, the new Ethan predictive workflows are now fully wired into the repo and have first real compare and validate outputs. Third, the current Ethan explicit-case split is baseline-dominated by persistence, with failures concentrated in the native Salt 2 holdout rather than spread uniformly across all held-out cases.

## Slide 3

**Title**

What Is Safe To Claim Today

**Purpose**

Separate ready-now claims from work-in-progress.

**Figures**

- Use as a screenshot or cropped table from [claim_matrix.md](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/claim_matrix.md)

**Speaker Notes**

The safe claims are split into three buckets. JSALT2 has ready-now model-selection and stability claims on the current split. TAMU has ready-now curation and source-catalog claims, but not unseen-case predictive validation. Ethan now has ready-now workflow and baseline findings, but not a “ROM already wins” claim. That distinction matters because it keeps the presentation honest while still showing concrete progress.

## Slide 4

**Title**

JSALT2: Broader Search Changed the Winner

**Purpose**

Present the strongest current positive modeling result.

**Figures**

- [jsalt2_surface_winner_comparison.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_surface_winner_comparison.pdf)

**Speaker Notes**

On the current split, moving from the narrow compare surface to the broader tuned sweep changes the selected winner from delay-1 POD-DMDc to delay-4 DMDc. With `h`, held-out RMSE drops from `0.33082` to `0.17407`. Without `h`, it drops from `0.37290` to `0.17075`. The right framing is that this is a current-split result, not yet a repeated-split robustness claim.

## Slide 5

**Title**

JSALT2: Improvement Is Consistent Across Held-Out Cases

**Purpose**

Show that the JSALT2 gain is not just one aggregate scalar.

**Figures**

- [jsalt2_case_rmse_comparison.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_case_rmse_comparison.pdf)

**Speaker Notes**

This slide shows why the broader search result is useful rather than cosmetic. The tuned-surface winner improves per-case held-out RMSE across the current held-out cases, for both the with-`h` and no-`h` variants. That makes JSALT2 the clearest current example of a search-surface decision materially changing predictive performance.

## Slide 6

**Title**

JSALT2: Stability Filtering Changes the Selection Story

**Purpose**

Explain why lowest raw error is not the final decision rule.

**Figures**

- [jsalt2_stability_tradeoff.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/figures/jsalt2_stability_tradeoff.pdf)

**Speaker Notes**

This is the key methodological point. The best raw-error adaptive DMDc candidate is excluded because it is flagged as potentially unstable. The selected delay-4 DMDc winner is not simply the lowest error point; it is the best candidate that also survives the stability screen. That is a presentation-worthy lesson because it is general, not just JSALT2-specific.

## Slide 7

**Title**

Ethan Program Reset: What Is Now in the Repo

**Purpose**

Show the infrastructure progress before showing the current predictive disappointment.

**Figures**

- Optional callout image or text block listing:
  - [study_config_2d.toml](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/studies/ethan_ground_truth_predictive/study_config_2d.toml)
  - [study_config_1d_axial_heat.toml](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml)
  - [ethan_ground_truth_predictive_manifest.json](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/data/processed/ethan_ground_truth_predictive_manifest.json)

**Speaker Notes**

This week’s Ethan result is not only numeric. We now have a repo-native table builder, canonical Ethan 2D and 1D study tables, explicit-case split configs, refreshed inspections, and executable compare and validate workflows. The 2D table has `22,140` rows across `9` salt cases. The 1D axial heat table has `20,520` rows across the same `9` cases. Both are usable for ROM workflows today.

## Slide 8

**Title**

Ethan 2D: Current Held-Out Winner Is the Persistence Baseline

**Purpose**

Present the first real Ethan predictive result clearly.

**Figures**

- [model_comparison.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.pdf)
- Optional supporting table from [model_comparison.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv)

**Speaker Notes**

On the current explicit held-out split, the best 2D held-out model is `persistence` with test RMSE `5.56`. The ROM candidates fit the training cases extremely well, but they do not generalize cleanly to the full test set. The right interpretation is not “ROM failed everywhere.” The right interpretation is “our current search surface and split policy do not yet beat a strong baseline.”

## Slide 9

**Title**

Ethan 2D: Failure Is Concentrated in Native Salt 2

**Purpose**

Show that the 2D miss is structured and diagnosable.

**Figures**

- [true_vs_pred_first_test_case.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_validation/true_vs_pred_first_test_case.pdf)
- [forecast_error_vs_horizon.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/2d_validation/forecast_error_vs_horizon.pdf)

**Speaker Notes**

The current `pod_dmdc` validation result is train RMSE `0.899` and test RMSE `156.85`. That sounds catastrophic unless we show the structure. The problem is concentrated in `val_salt_test_2_coarse_mesh_laminar`, where test RMSE is about `300.34`, while the held-out Jin Salt 3 and Salt 4 cases remain near `1.03` and `1.25`. So this looks more like a domain-shift or case-policy gap than a general inability to model unseen dynamics.

## Slide 10

**Title**

Ethan 1D Axial Heat: Same Story, Smaller State Space

**Purpose**

Show that the 1D lane is useful but currently exhibits the same generalization gap.

**Figures**

- [model_comparison.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.pdf)
- [true_vs_pred_first_test_case.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/true_vs_pred_first_test_case.pdf)

**Speaker Notes**

The 1D lane is already useful as an axial heat ROM, but it is not yet a predictive winner. The best held-out baseline is again `persistence`, now with test RMSE `4.09`. The current `pod_dmdc` validation result is train RMSE `0.359` and test RMSE `17.07`. Again, the failure is dominated by the native Salt 2 holdout, while the held-out Jin cases stay low-error. So 1D is not exempt from the same split challenge, but it is a lighter-weight lane for testing ideas.

## Slide 11

**Title**

TAMU: Data-Readiness Story, Not Yet a Predictive Validation Story

**Purpose**

Prevent overclaiming while still showing progress on TAMU.

**Figures**

- [tamu_candidate_cleanup.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/figures/tamu_candidate_cleanup.pdf)
- [tamu_catalog_buckets.pdf](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-02_paper_support_package/figures/tamu_catalog_buckets.pdf)

**Speaker Notes**

TAMU is still an onboarding and curation story. The current mirror has `53` case-like subfolders under `23` top-level items, `0` metadata parse failures, and `43` normalized candidate rows, but still `0` auto-ready predictive validation rows. The useful presentation claim is that the TAMU pipeline is now much cleaner and more structured. The unsafe claim would be that we already have unseen-case predictive validation on TAMU.

## Slide 12

**Title**

What TAMU Would Need To Become a True Unseen-Case Test

**Purpose**

Answer the obvious forward-looking question directly.

**Figures**

- Text flow or simple process diagram built from these steps:
  - canonical TAMU timeseries import
  - explicit held-out TAMU case splits
  - executed `compare`
  - executed `validate`
  - per-case error and envelope summary

**Speaker Notes**

There are four missing pieces. We need canonical TAMU timeseries tables, not just metadata. We need explicit held-out TAMU train/test splits. We need executed predictive `compare` and `validate` outputs on those unseen TAMU cases. And we need durable per-case evidence showing when Ethan-trained models do and do not generalize. Until those exist, TAMU remains a future external-check path.

## Slide 13

**Title**

Immediate Next Runs

**Purpose**

End with a crisp, technically defensible action list.

**Figures**

- [NEXT_NEEDED_RUNS.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv) as a simplified table

**Speaker Notes**

The next block is now narrower than it was at the start of the day. First, preserve `persistence` as the current acceptance bar in both Ethan lanes. Second, broaden the 2D and 1D Ethan-only ROM searches specifically around the native Salt 2 failure mode. Third, rerun validation only after a revised candidate beats persistence. Fourth, repair the zero-advance transport extraction so the 1D lane can graduate from axial heat aggregates to a fuller axial state contract. Replay is not the immediate bottleneck anymore; Salt 2 generalization is.

## Slide 14

**Title**

Bottom Line

**Purpose**

Close the talk with a precise summary.

**Figures**

- None required.

**Speaker Notes**

The bottom line is that the repo now supports the Ethan-ground-truth predictive program end to end. JSALT2 still provides the clearest current positive modeling result. Ethan now provides the clearest current modeling challenge: the present ROM surfaces do not yet beat persistence on the explicit held-out split, and the failure is concentrated in native Salt 2. TAMU remains important, but as a later external-check story rather than as today’s predictive headline.
