# IMPL-TAMU-001 Status

Status: completed

Role:

- `Implementer`

Scope:

- Fix the TAMU workbook-audit wiring bug in the maintained validation export path.

Files inspected:

- `src/dmdc/tamu_data.py`
- `tests/test_tamu_inventory_and_validation.py`
- `tests/test_tamu_study_workflow.py`
- `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/validation_source_index.csv`
- `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/office_workbook_case_rows.csv`
- `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/office_workbook_promotion_decisions.csv`
- `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/validation_source_consistency_report.csv`

Files changed:

- `src/dmdc/tamu_data.py`
- `tests/test_tamu_inventory_and_validation.py`

Commands run:

- `rg -n "office_workbook|consistency|repeated-source|not_audited|blocked_by_mismatch|validation_source_consistency|workbook" src/dmdc/tamu_data.py tests/test_tamu_inventory_and_validation.py`
- `sed -n '1,260p' src/dmdc/tamu_data.py`
- `sed -n '260,620p' src/dmdc/tamu_data.py`
- `sed -n '620,1100p' src/dmdc/tamu_data.py`
- `sed -n '1100,1215p' src/dmdc/tamu_data.py`
- `sed -n '1938,2045p' src/dmdc/tamu_data.py`
- `sed -n '2080,2168p' src/dmdc/tamu_data.py`
- `sed -n '1,340p' tests/test_tamu_inventory_and_validation.py`
- `sed -n '1,220p' tests/test_tamu_study_workflow.py`
- `sed -n '1,120p' outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/validation_source_index.csv`
- `sed -n '1,120p' outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/office_workbook_case_rows.csv`
- `sed -n '1,120p' outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/office_workbook_promotion_decisions.csv`
- `sed -n '1,120p' outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/validation_source_consistency_report.csv`
- `env PYTHONPATH=src .venv/bin/python -m pytest tests/test_tamu_inventory_and_validation.py tests/test_tamu_study_workflow.py`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-export --help`
- `env PYTHONPATH=src .venv/bin/python -m dmdc.cli tamu-validation-catalog --help`

Validation results:

- `pytest`: `13 passed`
- `tamu-validation-export --help`: passed
- `tamu-validation-catalog --help`: passed

Root cause fixed:

- Wide validation sources were not canonicalizing case names before the repeated-source audit, so names like `Salt Test 1` and `Salt 1` split into different audit groups.
- Office workbook repeated-row eligibility depended on the raw workbook column family classification, so extra non-case columns could suppress canonical single-phase workbook rows from the repeated-source audit even when parsed case rows were valid.

Implemented fix:

- Canonicalize wide-source case names in `_normalize_wide_validation_frame()`.
- Build workbook repeated-source rows from parsed canonical case names (`Salt N` / `Water N`) instead of relying on the raw workbook-wide `canonical_family_only` flag.
- Added regressions covering:
  - `Salt Test 1` collapsing onto canonical `Salt 1`
  - single-phase workbook rows remaining auditable when the workbook includes a non-case noise column

Unresolved issues:

- I did not rerun the real historical export roots under `outputs/tamu_validation_export_20260602_contract_audit_v3_workbook_reconcile/`; the fix is validated by scoped tests and CLI smoke checks only.
- The broader discrepancy-policy question for workbook precision and acceptable mismatch tolerance remains open and is outside this task.

Handoff notes:

- The next TAMU follow-up should rerun the maintained real-data export/catalog path and verify that the previously `not_audited` single-phase workbook rows now appear in `validation_source_consistency_report.csv` with repeated-source coverage.
- After that rerun, re-read `office_workbook_promotion_decisions.csv` and decide whether any remaining workbook mismatches are true data discrepancies or a policy/rounding issue.
