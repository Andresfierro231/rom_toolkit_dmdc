# TAMU Data Intake And Validation

This workflow is for newly downloaded TAMU loop data that must be organized before modeling.

## Goals

- avoid overwriting prior campaigns or output folders
- create a durable table of contents for the raw download
- summarize what each subfolder contains
- normalize validation source tables into reusable case files
- generate nearest-fit suggestions without auto-accepting them

## Recommended steps

```bash
dmdc tamu-inventory \
  --root ../tamu_loop_data/Loop\ Operational\ Data \
  --outdir outputs/tamu_inventory

dmdc tamu-validation-export \
  --inventory-root ../tamu_loop_data/Loop\ Operational\ Data \
  --source-tables \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/salt_validation_source.csv \
    ../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/water_validation_source.csv \
  --outdir outputs/tamu_validation_export
```

If the sibling raw-data repo does not exist yet, recreate it first:

```bash
python tools/studies/init_tamu_loop_data_repo.py --target-root ../tamu_loop_data
```

The same workflow is scaffolded in:

```text
studies/tamu_loop_data_onboarding/
tools/studies/build_tamu_inventory.py
tools/studies/export_tamu_validation_cases.py
docs/workflows/tamu_loop_data_recovery.md
```

## Outputs

Inventory writes:

```text
outputs/tamu_inventory/top_level_contents.csv
outputs/tamu_inventory/case_inventory.csv
outputs/tamu_inventory/metadata_failures.csv
outputs/tamu_inventory/TABLE_OF_CONTENTS.md
outputs/tamu_inventory/folder_summaries.md
```

Validation export writes:

```text
outputs/tamu_validation_export/inventory_validation_candidates.csv
outputs/tamu_validation_export/validation_cases.csv
outputs/tamu_validation_export/validation_policy.yaml
outputs/tamu_validation_export/validation_data.csv
outputs/tamu_validation_export/nearest_fit_suggestions.csv
```

## Notes

- `meta_data.json` files are parsed tolerantly because several downloaded folders contain missing commas.
- nearest-fit suggestions are advisory only; they are never auto-accepted as validation cases
- `validation_cases.csv` is the canonical normalized output
- `validation_data.csv` is the PHYSOR-style wide export written when source tables provide enough fields
