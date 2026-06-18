# Checkpoint — 2026-06-10_source_authority_and_manuscript_followup

## Date and campaign/task name

- Date: `2026-06-10`
- Task: clarify source authority, record suggested resolution policies, and
  stage manuscript-methods follow-up work.

## Research question

What does ``source authority'' mean for the current paper, which evidence
streams are allowed to govern which claim classes, and what practical policy
choices should the project make to reduce ambiguity in TAMU and DMDc claims?

## Repository state

- Analysis repo branch: `main`
- Analysis repo commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Analysis repo dirty working tree: `True`
- Manuscript repo branch: `main`
- Manuscript repo commit: `11903c7152f03f42266435c0357a0a332805e065`
- Manuscript repo dirty working tree: `True`

## Source files inspected

- `analysis/reports/2026-06-09_coordination_task_assignments/NEXT_DMDc_ANALYSIS_PLAN.md`
- `analysis/reports/2026-06-09_coordination_task_assignments/JOURNAL_2026-06-09_CURRENT_STATE.md`
- `analysis/reports/2026-06-09_coordination_task_assignments/TAMU_REALDATA_RERUN_POST_IMPL_FIX.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/EXECUTIVE_SUMMARY.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/CHECKPOINT.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/source_of_truth_audit.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/TODO.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/paper_journal.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/04_methods_workflow.tex`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/06_trust_limits.tex`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/appendices/app_a_source_of_truth_audit.tex`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_report.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_summary.md`
- `outputs/tamu_validation_export_20260609_post_impl_fix/office_workbook_promotion_decisions.csv`
- `outputs/tamu_validation_export_20260609_post_impl_fix/office_workbook_case_rows.csv`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv`
- `../physor2026_andrew/Validation_Data/validation_data.csv`

## Commands run

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
ls -lt analysis/reports
sed -n '1,260p' analysis/reports/2026-06-09_coordination_task_assignments/NEXT_DMDc_ANALYSIS_PLAN.md
sed -n '1,260p' analysis/reports/2026-06-09_coordination_task_assignments/JOURNAL_2026-06-09_CURRENT_STATE.md
sed -n '1,260p' analysis/reports/2026-06-09_coordination_task_assignments/TAMU_REALDATA_RERUN_POST_IMPL_FIX.md
sed -n '1,260p' analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/EXECUTIVE_SUMMARY.md
sed -n '1,320p' analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/CHECKPOINT.md
sed -n '1,260p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/source_of_truth_audit.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/TODO.md
sed -n '1,260p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/paper_journal.md
sed -n '1,240p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/04_methods_workflow.tex
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/06_trust_limits.tex
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/appendices/app_a_source_of_truth_audit.tex
sed -n '1,220p' outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_summary.md
head -40 outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_consistency_report.csv
head -40 outputs/tamu_validation_export_20260609_post_impl_fix/office_workbook_promotion_decisions.csv
head -40 outputs/tamu_validation_export_20260609_post_impl_fix/validation_source_index.csv
head -8 ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv
head -8 ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv
sed -n '1,40p' ../physor2026_andrew/Validation_Data/validation_data.csv
python3.11 - <<'PY'
... workbook-versus-Fluid and PHYSOR-versus-Fluid comparison scripts ...
PY
```

## Inputs used

- The current manuscript-side source-of-truth audit note
- The June 9 TAMU post-fix rerun checkpoint
- The June 8 Ethan predictive scope-reset checkpoint
- The current manuscript TODO and methods/trust-limit sections
- The June 9 TAMU consistency outputs and the three underlying maintained
  source tables currently in dispute

## Outputs generated

- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/CHECKPOINT.md`
- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/METHODS_EXPANSION_AGENT_BRIEF.md`
- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/source_disagreement_claim_matrix.csv`

## Key numerical results

- TAMU repeated-source rows audited after the June 9 rerun: `24`
- TAMU repeated-source mismatches after the June 9 rerun: `16`
- Office single-phase workbook repeated rows now participating in the audit: `8`
- Ethan current held-out `2D` baseline winner: `persistence`, test RMSE `5.557706183000499`
- Ethan current held-out `1D axial heat` baseline winner: `persistence`,
  test RMSE `4.087636896404323`

## Plots/tables generated

- None in this checkpoint. This pass is policy and manuscript-structure work.

## Interpretation

``Source authority'' is the rule that says which saved artifact is allowed to
govern a particular manuscript claim when multiple repos, scripts, tables, or
human-curated summaries exist.

In the current paper, source authority is split by claim class:

- Ethan CFD representative-case claims are governed by the imported June 4 and
  June 5 Ethan report packages and their cited saved outputs.
- Secondary DMDc and TAMU claims are governed by the imported paper-support
  package from `dmdc-analysis` and the saved outputs named in its provenance.
- Solver-semantics and deeper ROM-method claims do not yet have a completed
  authority chain; those claims should remain explicitly limited until a direct
  code audit or derivation appendix is completed.

The current ambiguity is strongest on the TAMU side. The June 9 rerun resolved
the audit-plumbing question: the office workbook now participates in the
repeated-source audit. The remaining ambiguity is no longer ``was the audit
wired up?'' but ``which source is canonical when maintained sources disagree,
and what tolerance policy should define a meaningful mismatch?''

## Actual disputed claims and sources

The detailed claim matrix for this pass is stored in:

- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/source_disagreement_claim_matrix.csv`

The useful split is not just by case, but by disagreement type:

| Claim class | Cases | Canonical source | Competing source | What actually disagrees | Current reading |
|---|---|---|---|---|---|
| Workbook wall-temperature exact mismatches | `Salt 1`, `Salt 2` | Fluid wide tables | Single-phase office workbook | `TW1_C` through `TW11_C` plus `unlabeled_TW11_K_excluded` | The observed deltas are tiny hidden-precision differences, with maximum absolute difference about `0.00488 C`. |
| Workbook TP plus TW exact mismatches | `Salt 3`, `Salt 4`, `Water 1`-`Water 4` | Fluid wide tables | Single-phase office workbook | `TP1_C`-`TP6_C` and `TW1_C`-`TW11_C` | Again this looks like precision or rounding noise; the largest observed workbook-versus-Fluid delta in this pass is about `0.00497 C`. |
| PHYSOR temperature mismatches | all eight maintained cases | Fluid wide tables | PHYSOR validation table | `TP1_C`-`TP6_C` and `TW1_C`-`TW11_C` | After converting PHYSOR temperatures from Kelvin to Celsius, these values match the Fluid tables to floating-point roundoff. This looks like a unit-normalization issue, not a real scientific disagreement. |
| PHYSOR air-side mismatch | all eight maintained cases | Fluid wide tables | PHYSOR validation table | `air_flow_Lpm` | The PHYSOR table carries `Average Velocity Air (m/s)` values such as `0.4057` for Salt 1, while the Fluid table carries `Air flow = 37.0 L/min`. These are semantically different quantities and should not be compared as if they were the same field. |
| PHYSOR missing or noncomparable context fields | all eight maintained cases | Fluid wide tables | PHYSOR validation table | `air_T_inlet_C`, `air_T_outlet_C`, `power_uncertainty_pct`, and sometimes `unlabeled_TW11_K_excluded` | These do not appear to be cleanly comparable maintained fields in the PHYSOR source, so treating them as direct value mismatches likely overstates the disagreement. |
| Source-authority labeling inconsistency | all eight maintained cases | consistency report | source index note | source authority metadata | `validation_source_consistency_report.csv` clearly uses the Fluid tables as canonical rows, but `validation_source_index.csv` still labels PHYSOR as a canonical wide validation source table. That documentation inconsistency should be corrected. |

### Numerical evidence from this pass

- Single-phase office workbook versus Fluid wide tables:
  - maximum observed absolute difference across the compared maintained fields:
    `0.004966311899011089 C`
  - the current workbook mismatches therefore look like exact-match or
    rounding artifacts rather than large source disagreement
- PHYSOR versus Fluid wide tables:
  - `Heater Power (W)` and `Heat Removed (W)` match exactly on all eight cases
  - after Kelvin-to-Celsius conversion, the PHYSOR TP and TW temperatures match
    the Fluid tables to floating-point roundoff
  - the largest obvious remaining semantic mismatch is the air-side quantity,
    where PHYSOR `Average Velocity Air (m/s)` is being treated like Fluid
    `Air flow (L/min)`

## Suggested solutions

1. Adopt a claim-class authority matrix and keep it in both repos.
   - Ethan CFD results: Ethan report packages.
   - DMDc current-split ROM results: `dmdc-analysis` support packages.
   - TAMU readiness and consistency results: TAMU export/catalog packages.
   - Solver or ROM semantics: only audited code paths or a derivation appendix.

2. Adopt a single canonical-source rule for TAMU repeated-source auditing.
   - Recommended current default: the Fluid salt/water tables remain canonical
     until a formal replacement is approved.
   - PHYSOR and the office workbook should remain comparison sources, not silent
     co-equal authorities.

3. Adopt an explicit mismatch policy with tiers.
   - Exact match for identifiers and categorical fields.
   - Tolerance-based comparison for floating-point physical quantities.
   - Separate reporting of ``exact mismatch'', ``within tolerance'', and
     ``material mismatch'' so the paper does not flatten all disagreement into
     one bucket.

4. Fix the likely PHYSOR normalization and field-mapping issues before making
   strong policy claims from the current mismatch totals.
   - Convert PHYSOR temperatures from Kelvin to Celsius before repeated-source
     comparison.
   - Stop mapping `Average Velocity Air (m/s)` onto `air_flow_Lpm`.
   - Distinguish `missing_or_noncomparable` from `mismatch`.

5. Add claim language that names the governing artifact class.
   - For example: ``The current TAMU claim is governed by the June 9
     post-fix validation export and catalog rerun'' rather than by a generic
     folder or a manuscript-side table alone.

6. For DMDc methods claims, create a visible two-layer policy.
   - Main text: workflow-level math and operational interpretation.
   - Appendix: derivation outline and explicit list of code-audit items still
     required before stronger algorithmic claims are made.

## Limitations

- This checkpoint does not rerun TAMU exports or Ethan ROM comparisons.
- No new numerical results were generated here.
- The solver-code authority path is still only scoped, not completed.

## Bugs or anomalies

- None encountered during this policy-only checkpoint.

## Follow-up tasks

1. Mirror the authority matrix into the manuscript prose and appendix so the
   reader can see which evidence stream governs which claim class.
2. Expand the DMDc methods section to describe the compare surface, tuned sweep
   surface, stability filter, split limitation, keep-`h` versus no-`h` policy,
   and the boundary between main-text workflow claims and appendix-level math.
3. Repair the PHYSOR normalization and field-mapping audit path, then rerun the
   TAMU repeated-source export to see which disagreements remain after unit and
   semantic mismatches are removed.
4. Define and document the canonical repeated-source baseline and a tolerance
   policy before any new manuscript wording is promoted.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/CHECKPOINT.md`
- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/METHODS_EXPANSION_AGENT_BRIEF.md`
- `analysis/reports/2026-06-10_source_authority_and_manuscript_followup/source_disagreement_claim_matrix.csv`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/source_of_truth_audit.md`
- `analysis/reports/2026-06-09_coordination_task_assignments/TAMU_REALDATA_RERUN_POST_IMPL_FIX.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/EXECUTIVE_SUMMARY.md`

## Missing information

- No solver-code audit note has yet been linked as the governing authority for
  deeper DMDc math or implementation-semantics claims.
