# Known limitations and current boundaries

This page summarizes the main limitations of the current alpha release. It is meant to make the repo easier to review honestly before using it for real experimental or live-loop work.

## Release status

Current version: `v0.1.0-alpha`

Description:

> A research-grade ROM and live monitoring toolkit for DMD/DMDc/POD workflows, with live replay, dashboarding, archive support, and model registry scaffolding. Not yet field-validated on live hardware.

## Live-system boundary

The live workflow is read-only and advisory. It can:

- ingest live or replayed data;
- maintain rolling buffers;
- estimate states;
- forecast;
- compute residuals and trust scores;
- apply bounded forecast-bias correction;
- archive data;
- visualize dashboards and reports.

It does **not**:

- control heaters, valves, pumps, or safety systems;
- replace independent safety instrumentation;
- make autonomous control decisions;
- guarantee safe operation.

Future advisory/control ideas are documented in `docs/future/advisory_control_mode.md` and should remain separated from hardware actuation until independently validated.

## Adapter maturity

CSV, Excel, Parquet, and folder-based importers are the most mature path. EPICS and LabVIEW/DAQ support is intentionally modular but still needs field validation. Expected future work includes:

- real EPICS PV name testing;
- reconnect behavior;
- monitor/callback mode;
- LabVIEW partial-file behavior;
- timestamp and unit checks;
- vendor metadata parsing.

## Model validation

The repo includes validation on unseen cases, forecast-horizon metrics, stability checks, model comparison, and sweeps. These tools support engineering decisions, but they do not replace domain validation. Before using a model in live monitoring, run at least:

```bash
dmdc inspect-data --config study_config.toml
dmdc compare --config study_config.toml
dmdc sweep --config study_config.toml
dmdc report --run outputs/<selected_run>
```

Then register and promote the model only after reviewing the plots, residuals, stability diagnostics, and operating-envelope summaries.

## Large data

The archive design is summary-first and partition-friendly, but high-throughput performance still needs benchmarking on the actual machine. Use:

```bash
dmdc benchmark-archive --config configs/templates/archive_benchmark.toml
```

and record write throughput, peak memory, summary generation time, dashboard load time, and archive size.

## Data management

Do not commit:

- raw/private data;
- generated outputs;
- long-term archives;
- model registries;
- large Parquet/HDF5/SQLite/DuckDB files;
- screenshots/reports that contain sensitive experimental information.

The `.gitignore` is designed to help, but users should still check file sizes and sensitive paths before the first commit.
