# Data importers and adapters

Start here when your data is not already a clean CSV/Parquet table.

The repo expects a tidy table for ROM workflows:

```text
one row per sample
one time column
optional case_id column
state columns such as TP1, TP2, TP3, massFlowRate
input/control columns such as q_heater, T_amb, h_amb
```

Use `dmdc import-data` to convert current exports into that shape.

## Common commands

Single CSV/Excel/Parquet file:

```bash
dmdc import-data \
  --source data/raw/current_loop_export.xlsx \
  --source-type excel \
  --sheet Sheet1 \
  --rename-col TC01=TP1 TC02=TP2 Heater_W=q_heater \
  --out data/processed/current_loop.parquet
```

Folder of DAQ/LabVIEW chunks:

```bash
dmdc import-data \
  --source data/raw/labview_chunks \
  --source-type labview_daq \
  --pattern "*.csv" \
  --case-from-filename \
  --out data/processed/labview_cases.parquet
```

Config-first import:

```bash
dmdc import-data --config configs/templates/import_csv_excel_folder.toml
```

EPICS snapshot, if `pyepics` and network access are available:

```bash
dmdc import-data --config configs/templates/import_epics_snapshot.toml
```

## Modular adapter design

Importers return a tidy `pandas.DataFrame` plus metadata/warnings.  New adapters should implement the same idea:

```python
class MyImporter:
    def import_data(self) -> ImportResult:
        ...
```

The current modules are:

```text
src/dmdc/importers/base.py       # ImportResult and interface
src/dmdc/importers/tabular.py    # CSV, Excel, Parquet, folder, LabVIEW/DAQ chunks
src/dmdc/importers/epics.py      # optional EPICS PV snapshot scaffold
```

For streaming adapters, see `src/dmdc/streaming.py`; for long-term storage, see `docs/live/archive_phase6_2.md`.

## Recommended flow

```bash
dmdc import-data --config my_study.toml
dmdc inspect-data --config my_study.toml
dmdc compare --config my_study.toml
dmdc live-replay-adapt --config my_study.toml
dmdc live-dashboard --config my_study.toml
```

A single central config is the recommended way to keep source paths, canonical names, model settings, live settings, and archive settings together.
