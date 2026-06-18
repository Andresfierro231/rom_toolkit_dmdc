# Next DMDc Analysis Plan

Generated: `2026-06-09`

## Purpose

This plan sequences the most useful next `dmdc-analysis` work after `IMPL-TAMU-001`.
The goal is to reduce uncertainty in current modeling claims before adding more
downstream artifacts.

## Current read

- `IMPL-TAMU-001` is complete.
- `STAB-CLI-001` remains open and should be handled before broader new analysis.
- Ethan predictive work is active but currently baseline-dominated by `persistence`.
- TAMU export/catalog logic now needs a real-data rerun to confirm the fix.
- JSALT2 already has a useful positive result, but the strongest remaining need is robustness rather than another one-off sweep.

## Priority order

1. `STAB-CLI-001`
2. TAMU real-data rerun after `IMPL-TAMU-001`
3. Ethan broader `2D` and `1D` compare-config work
4. JSALT2 robustness batch
5. Ethan `1D` transport-contract repair
6. Cross-study synthesis report

## Task queue

### 1. STAB-CLI-001

Role:

- `Implementer + Tester`

Why first:

- The working tree already contains a large CLI/campaign/config hardening bundle.
- It should be stabilized before adding more analysis churn on top of it.

Primary scope:

- Validate and finish the current campaign-run indexing, derived-config, CLI help, wrapper-script, and related documentation/test updates.

Validation command:

```bash
env PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_registry_campaign_archive_schema.py \
  tests/test_hardening_cli_packaging.py \
  tests/test_adaptive_variable_dt.py \
  tests/test_inspection_resampling.py
```

Secondary smoke checks:

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --help
env PYTHONPATH=src .venv/bin/python -m dmdc.cli guide
```

Gate to next task:

- The scoped `STAB` pytest slice passes.
- The `STAB-CLI-001` status note is updated with outcomes and unresolved issues.

### 2. TAMU Real-Data Rerun

Role:

- `Tester + Reviewer`

Why next:

- `IMPL-TAMU-001` fixed the audit logic, but the fix has only been proven with scoped tests.
- The maintained real-data export/catalog path needs a rerun to convert the code fix into trusted repo outputs.

Primary scope:

- Rerun the maintained TAMU validation export and validation catalog paths against the live raw-mirror/source-table contract.
- Verify that previously `not_audited` single-phase workbook rows now participate in the consistency report.

Recommended commands:

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

What to inspect:

- `validation_source_consistency_report.csv`
- `validation_source_consistency_summary.md`
- `office_workbook_case_rows.csv`
- `office_workbook_promotion_decisions.csv`
- `validation_source_index.csv`

Decision gate:

- If workbook rows now appear as repeated-source rows with meaningful `match` or `mismatch` statuses, the audit path is trustworthy.
- If they still show `not_audited`, open a new TAMU follow-up task instead of moving on as if the issue is solved.

### 3. Ethan Broader Compare Configs

Role:

- `Implementer`

Why next:

- The highest-value unresolved modeling question is whether Ethan ROMs can beat `persistence` once the search surface is broadened.

Primary scope:

- Create broader `2D` and `1D axial heat` compare configs aimed at the native Salt 2 failure mode.
- Run `compare` only.
- Do not rerun `validate` until a candidate beats `persistence`.

Expected edit area:

- `studies/ethan_ground_truth_predictive/`
- possibly a new dated config variant under that study

Recommended command shape:

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli compare --config <broader_2d_config>
env PYTHONPATH=src .venv/bin/python -m dmdc.cli compare --config <broader_1d_config>
```

Suggested search dimensions:

- preserve the current explicit-case split as the first gating benchmark so results remain comparable to the current `persistence` baseline
- broaden the model family beyond the current fixed `pod_dmdc` defaults, including at minimum `dmdc`, `ridge_dmdc`, `adaptive_dmdc`, `pod_dmdc`, and optionally `pod_ml_ridge`
- test delay counts `n_delays = [1, 2, 4, 8]` for delay-capable linear models
- test `pod_rank` around `2, 3, 4, 0.999`
- test `center = [true, false]`
- test `scale = [true, false]`, especially for the `2D` lane where temperature states and `mdot_mean_abs_kg_s` currently share one unscaled state vector
- review split variants after a candidate emerges, with emphasis on the native Salt 2 holdout that is currently marked as an extrapolation case

What "broader" should mean in practice:

- For `2D`, do not keep only the current 18-state, unscaled, `pod_rank = 0.999`, `n_delays = 4` contract. Add at least one broader search surface that checks whether mixed-unit scaling, lower POD rank, and shorter delay stacks reduce the catastrophic native Salt 2 error while retaining performance on the Jin-held-out cases.
- For `1D axial heat`, do not keep only the current heat-only, unscaled, `pod_rank = 0.999`, `n_delays = 4` contract. Add a broader search surface that checks whether simpler delay settings and lower-order linear models can generalize better than the current overfit `pod_dmdc` baseline on the same held-out cases.
- Keep the first pass on the same train/test case lists. Once a model beats `persistence`, then add one or more split-robustness follow-up configs such as leave-one-case-family-out or native-Salt-2-focused variants.
- Record the native Salt 2 per-case error explicitly in the Ethan status note because the current failure is concentrated there, not uniformly spread across all test cases.

Workflow note:

- `dmdc compare --config ...` currently uses one fixed `pod/model` setting from the config and does not expose a config-level `n_delays` search surface. If delay count, POD rank, or centering/scaling need to vary within one run, prefer `dmdc sweep --config ...` or a small family of explicit broadened configs rather than assuming `compare` alone will search those dimensions.

Decision gate:

- Only advance to `validate` if the held-out compare winner beats `persistence` on the explicit-case split.

### 4. JSALT2 Robustness Batch

Role:

- `Implementer + Reviewer`

Why after Ethan compare:

- JSALT2 already has a positive result, but the next valuable step is robustness, not another narrow win.
- Ethan currently has the more urgent baseline problem.

Primary scope:

- Test whether the current JSALT2 winner remains preferred under split and search-surface sensitivity.

Suggested batch design:

- repeated by-case splits or leave-one-case-out style checks
- `n_delays = [1, 2, 4, 8]`
- `pod_rank` sensitivity
- `center` / `scale` toggles
- keep both with-`h` and no-`h` variants active

Desired outcome:

- move from “current split winner” to “robustly preferred under reasonable split/search variation,” or document where that claim breaks down

### 5. Ethan 1D Transport-Contract Repair

Role:

- `Implementer`

Why later:

- It is important, but it does not unblock the current immediate decision of whether the existing Ethan lanes can beat `persistence`.

Primary scope:

- Repair zero-advance transport extraction so the `1D` lane can move beyond axial heat aggregates toward a fuller axial state contract.

Expected outcome:

- refreshed sibling Ethan report package
- rebuilt canonical `1D` table
- updated study contract for the `1D` lane

### 6. Cross-Study Synthesis

Role:

- `Writer + Reviewer`

Why last:

- This is most useful after the stabilization, TAMU rerun, and Ethan/JSALT2 follow-ups generate fresh evidence.

Primary scope:

- produce one compact report covering:
  - what is claim-ready now
  - what is promising but not yet robust
  - what remains data-readiness only

Suggested structure:

- JSALT2 current best-supported claim
- Ethan current baseline and broader-search status
- TAMU current readiness and remaining policy questions

## Rules

- Do not mix `STAB-CLI-001` edits with Ethan config work in the same implementation pass.
- Do not rerun Ethan `validate` until a broader `compare` winner beats `persistence`.
- Do not present TAMU as an unseen-case predictive validation story until the rerun audit outputs are reviewed and trusted.
- Preserve the existing `dmdc` CLI workflow; prefer study configs, compare/validate runs, and durable outputs under `outputs/` and `analysis/`.

## Status target

Use this directory as the coordination record:

- `analysis/reports/2026-06-09_coordination_task_assignments/`

Update:

- `STAB-CLI-001-STATUS.md` during stabilization work
- a new dated TAMU rerun note after the real-data rerun
- a new Ethan status note once broader compare configs start
