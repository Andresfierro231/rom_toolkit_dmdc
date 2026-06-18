# Journal 2026-06-09 Current State

Date: `2026-06-09`

Role:

- `Coordinator`

Repository state:

- Branch: `main`
- Commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Working tree: dirty, with substantial pre-existing tracked and untracked changes

Files inspected for this log:

- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv`
- `analysis/reports/2026-06-09_coordination_task_assignments/NEXT_DMDc_ANALYSIS_PLAN.md`
- `analysis/campaigns/2026-06-08_ethan_ground_truth_predictive_scope_reset.yaml`
- `studies/ethan_ground_truth_predictive/study_config_2d.toml`
- `studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml`
- `studies/ethan_ground_truth_predictive/README.md`
- `outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.csv`
- `outputs/ethan_ground_truth_predictive/2d_validation/validation_summary.csv`
- `outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/validation_summary.csv`
- `src/dmdc/cli.py`

Commands used for this clarification pass:

```bash
sed -n '1,240p' analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv
rg -n "ethan_ground_truth_predictive|1D axial heat|2D" studies analysis/campaigns configs/templates src/dmdc -g '*.toml' -g '*.yaml' -g '*.md'
sed -n '1,240p' studies/ethan_ground_truth_predictive/study_config_2d.toml
sed -n '1,240p' studies/ethan_ground_truth_predictive/study_config_1d_axial_heat.toml
sed -n '1,220p' outputs/ethan_ground_truth_predictive/2d_compare/model_comparison.csv
sed -n '1,220p' outputs/ethan_ground_truth_predictive/1d_axial_heat_compare/model_comparison.csv
sed -n '1,220p' outputs/ethan_ground_truth_predictive/2d_validation/validation_summary.csv
sed -n '1,220p' outputs/ethan_ground_truth_predictive/1d_axial_heat_validation/validation_summary.csv
rg -n "Salt 2|val_salt_test_2|native" outputs/ethan_ground_truth_predictive/2d_validation outputs/ethan_ground_truth_predictive/1d_axial_heat_validation -g '*.csv' -g '*.md'
sed -n '1540,1625p' src/dmdc/cli.py
sed -n '300,340p' src/dmdc/cli.py
```

Current state summary:

- `IMPL-TAMU-001` is complete. The TAMU workbook audit-path bug is fixed and the real-data rerun confirmed that the single-phase office workbook now participates in the repeated-source audit.
- `STAB-CLI-001` is complete. The scoped campaign/CLI/config stabilization slice passed without additional code edits.
- The manuscript repo has been synchronized to the new TAMU post-fix state and rebuilt successfully.
- The next highest-value analysis task in this repo is Ethan predictive follow-up, specifically the broader `2D` and `1D axial heat` compare-config work.

Ethan-specific findings confirmed today:

- The current Ethan `2D` lane is narrow: one explicit split, `pod_rank = 0.999`, `center = true`, `scale = false`, and a fixed `n_delays = 4` model contract in `study_config_2d.toml`.
- The current Ethan `1D axial heat` lane is likewise narrow: one explicit split, `pod_rank = 0.999`, `center = true`, `scale = false`, and a fixed `n_delays = 4` model contract in `study_config_1d_axial_heat.toml`.
- On the current held-out split, `persistence` remains the best compare winner in both lanes:
  - `2D`: test RMSE `5.557706183000499`
  - `1D axial heat`: test RMSE `4.087636896404323`
- The current validated `pod_dmdc` runs are still useful only as failure baselines:
  - `2D` validate test RMSE `156.8483948279097`
  - `1D axial heat` validate test RMSE `17.073730133234395`
- The worst failure is concentrated in `val_salt_test_2_coarse_mesh_laminar`, which is also flagged in the saved operating-condition summaries as an extrapolation case through `is_native_validation`.

Important workflow constraint verified today:

- `dmdc compare --config ...` currently flattens one fixed `pod/model` setting from the study config.
- It does not expose a config-level `n_delays` search surface for a multi-candidate run.
- Therefore, truly broader Ethan search work should be expressed as either:
  - a small family of explicit broadened configs, or
  - `dmdc sweep --config ...` runs for delay/rank/model exploration

Concrete next steps:

1. Create a broader `2D` Ethan config family or sweep config that preserves the current explicit train/test case lists but expands:
   - models: at least `dmdc`, `ridge_dmdc`, `adaptive_dmdc`, `pod_dmdc`
   - `n_delays = [1, 2, 4, 8]`
   - `pod_rank` around `2, 3, 4, 0.999`
   - `center = [true, false]`
   - `scale = [true, false]`
2. Create a matching broader `1D axial heat` config family or sweep config with the same held-out cases and the same main search dimensions.
3. Run broadened Ethan `compare` or `sweep` only. Do not rerun `validate` yet.
4. Inspect per-case outputs first, with explicit attention to whether any candidate improves native Salt 2 generalization enough to beat `persistence` on the existing split.
5. Only if a candidate beats `persistence`, prepare the follow-on `validate` config and then run held-out validation.

Immediate recommended implementation target:

- Draft:
  - `studies/ethan_ground_truth_predictive/study_config_2d_broad.toml`
  - `studies/ethan_ground_truth_predictive/study_config_1d_axial_heat_broad.toml`
- If a single-run search surface is preferred, add sweep-oriented Ethan configs instead of assuming `compare` alone will search `n_delays`.

Status note:

- Updated `analysis/reports/2026-06-09_coordination_task_assignments/NEXT_DMDc_ANALYSIS_PLAN.md` today to make the Ethan “broader compare-config work” definition explicit and to record the `compare` versus `sweep` constraint.
