# Coordinator Assignments

Generated: `2026-06-09`

## Purpose

This repo does not contain the requested `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`,
`.agent/ROLES.md`, or `.agent/status/` tree. This note is the durable repo-native
assignment record for the current work split.

## Repository state

- Branch: `main`
- Commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Working tree: dirty before this note was written

## Source files inspected

- `AGENTS.md`
- `.agents/AGENTS.md`
- `TODO_2026-06-01_box_and_overnight_followup.md`
- `TODO_2026-06-02_jsalt2_tamu_followup.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/CHECKPOINT.md`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv`
- `tests/test_tamu_inventory_and_validation.py`
- `tests/test_tamu_study_workflow.py`
- `tests/test_registry_campaign_archive_schema.py`
- `tests/test_hardening_cli_packaging.py`
- `configs/templates/central_campaign_config.toml`

## Commands run

- `pwd`
- `git rev-parse --show-toplevel`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short`
- `git diff --stat`
- `find . -name AGENTS.md -o -name AGENTS.override.md`
- `rg --files -g 'BOARD.md' -g 'FILE_OWNERSHIP.md' -g 'ROLES.md' -g 'AGENTS.override.md' -g 'AGENTS.md'`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' .agents/AGENTS.md`
- `sed -n '1,320p' TODO_2026-06-02_jsalt2_tamu_followup.md`
- `sed -n '1,220p' analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/NEXT_NEEDED_RUNS.csv`
- `sed -n '1,220p' tests/test_tamu_inventory_and_validation.py`
- `sed -n '1,220p' tests/test_tamu_study_workflow.py`
- `sed -n '1,220p' tests/test_registry_campaign_archive_schema.py`
- `sed -n '1,220p' tests/test_hardening_cli_packaging.py`

## Task assignments

### IMPL-TAMU-001

- Assigned role: `Implementer`
- Scope: fix the TAMU workbook-audit wiring bug in the maintained validation export path, then rerun the TAMU export/catalog validation path only as needed to verify the fix.
- Primary goal: resolve the mismatch between populated `office_workbook_case_rows.csv` outputs and repeated-source audit results that currently show zero repeated rows and `not_audited` workbook promotion states.

Allowed files to edit:

- `src/dmdc/tamu_data.py`
- `src/dmdc/cli.py`
- `tests/test_tamu_inventory_and_validation.py`
- `tests/test_tamu_study_workflow.py`
- `docs/workflows/tamu_data_intake_and_validation.md`
- `studies/tamu_loop_data_onboarding/README.md`
- `studies/tamu_loop_data_onboarding/study_config.toml`
- `studies/tamu_loop_data_onboarding/scripts/run_01_inventory.sh`
- `studies/tamu_loop_data_onboarding/scripts/run_02_export_validation_cases.sh`
- a new dated status or handoff file under `analysis/reports/2026-06-09_coordination_task_assignments/`

Files not to edit for this task:

- `src/dmdc/campaign.py`
- `src/dmdc/config.py`
- `src/dmdc/command_catalog.py`
- `scripts/workflows/run_campaign_local.sh`
- `configs/templates/central_campaign_config.toml`
- `studies/ethan_ground_truth_predictive/*`
- historical report artifacts outside the dated status target for this task

Validation command:

```bash
env PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_tamu_inventory_and_validation.py \
  tests/test_tamu_study_workflow.py
```

Optional secondary smoke check:

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-export --help
env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-catalog --help
```

Status target:

- `analysis/reports/2026-06-09_coordination_task_assignments/IMPL-TAMU-001-STATUS.md`

### STAB-CLI-001

- Assigned role: `Implementer + Tester`
- Scope: stabilize and validate the current dirty-tree campaign/CLI/config hardening bundle without expanding into new TAMU bug-fix logic or broader Ethan model-search work.
- Primary goal: make the current campaign-run indexing, derived-config behavior, CLI packaging/help, and related docs/tests internally consistent and regression-tested.

Allowed files to edit:

- `src/dmdc/campaign.py`
- `src/dmdc/cli.py`
- `src/dmdc/config.py`
- `src/dmdc/command_catalog.py`
- `src/dmdc/resampling.py`
- `src/dmdc/__init__.py`
- `scripts/workflows/run_campaign_local.sh`
- `configs/templates/central_campaign_config.toml`
- `examples/real_data_onboarding/scripts/_common.sh`
- `examples/real_data_onboarding/scripts/run_01_import.sh`
- `examples/real_data_onboarding/scripts/run_02_inspect.sh`
- `examples/real_data_onboarding/scripts/run_03_adaptive_fit.sh`
- `examples/real_data_onboarding/scripts/run_04_pod_dmdc.sh`
- `examples/real_data_onboarding/scripts/run_05_compare_models.sh`
- `examples/real_data_onboarding/scripts/run_06_validate_unseen_cases.sh`
- `examples/real_data_onboarding/scripts/run_07_live_replay_monitor.sh`
- `examples/real_data_onboarding/scripts/run_08_live_replay_adapt.sh`
- `examples/real_data_onboarding/scripts/run_09_live_dashboard.sh`
- `examples/real_data_onboarding/scripts/run_10_operator_report.sh`
- `README.md`
- `WORKFLOWS.md`
- `COMMANDS.md`
- `docs/analysis_menu.md`
- `docs/navigation/choose_your_path.md`
- `docs/navigation/workflow_map.md`
- `docs/workflows/README.md`
- `docs/workflows/research_provenance_workflow.md`
- `tests/test_registry_campaign_archive_schema.py`
- `tests/test_hardening_cli_packaging.py`
- `tests/test_adaptive_variable_dt.py`
- `tests/test_inspection_resampling.py`
- a new dated status or handoff file under `analysis/reports/2026-06-09_coordination_task_assignments/`

Files not to edit for this task:

- `src/dmdc/tamu_data.py`
- `tests/test_tamu_inventory_and_validation.py`
- `tests/test_tamu_study_workflow.py`
- `studies/ethan_ground_truth_predictive/*`
- `analysis/reports/2026-06-08_ethan_ground_truth_predictive_scope_reset/*`
- broader Ethan compare/validate configs or outputs
- Box staging/upload material under `to_box/`

Validation command:

```bash
env PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_registry_campaign_archive_schema.py \
  tests/test_hardening_cli_packaging.py \
  tests/test_adaptive_variable_dt.py \
  tests/test_inspection_resampling.py
```

Optional secondary smoke check:

```bash
env PYTHONPATH=src .venv/bin/python -m dmdc.cli campaign --help
env PYTHONPATH=src .venv/bin/python -m dmdc.cli guide
```

Status target:

- `analysis/reports/2026-06-09_coordination_task_assignments/STAB-CLI-001-STATUS.md`

## Deferred task outside current scope

- `COORD-ETHAN-001`: broader Ethan `2D` and `1D` ROM-search configs remain deferred until `IMPL-TAMU-001` and `STAB-CLI-001` are cleanly handled or explicitly deprioritized.

## Coordination rules

- Do not mix `IMPL-TAMU-001` and `STAB-CLI-001` in the same commit unless the dependency is unavoidable and documented.
- If one task needs to touch a file owned by the other task, stop and document the dependency first in the relevant status file.
- Use `analysis/reports/2026-06-09_coordination_task_assignments/` as the replacement for the missing `.agent/status/` and `.agent/handoffs/` paths in this repository.
