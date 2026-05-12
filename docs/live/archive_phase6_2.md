# Live Phase 6.2 — Partitioned archive storage and manifest

Live Phases 1--6.1 produce excellent run-folder artifacts such as
`cleaned_stream_log.csv`, `live_forecasts.csv`, `live_forecast_residuals.csv`,
`live_bias_update_events.csv`, and `live_trust_score.csv`. Those files are easy
to inspect for a demo or a short experiment, but they are not how you want to
store months of loop data.

**Live Phase 6.2 adds a long-term archive layer.** It copies live run outputs
into a partitioned archive and writes a manifest so the data can be indexed,
summarized, and searched later.

Related docs:

- Start live ingestion: [`docs/live/streaming_phase1.md`](streaming_phase1.md)
- Forecasting: [`docs/live/forecasting_phase2.md`](forecasting_phase2.md)
- Monitoring/alerts: [`docs/live/monitoring_phase4.md`](monitoring_phase4.md)
- Bias correction: [`docs/live/adaptation_phase6.md`](adaptation_phase6.md)
- Summaries/quicklooks: [`docs/live/summaries_quicklooks_phase6_3.md`](summaries_quicklooks_phase6_3.md)

---

## Why an archive layer?

For small runs, a single CSV is convenient. For large live systems, a single CSV
becomes a liability:

- it is slow to append and read after it becomes huge;
- a broken write can damage a very large file;
- dashboards cannot reasonably load it;
- months of data become hard to browse;
- you cannot quickly answer questions like “when did TP4 residuals exceed 5 K?”

The archive uses a **summary-first, partitioned layout**:

```text
live_archive/
├── manifest.csv
├── raw_stream/
│   └── date=relative/hour=0000/part-....csv or .parquet
├── cleaned_stream/
├── forecasts/
├── residuals/
├── bias_update_events/
├── bias_state_timeseries/
├── alerts/
├── trust_score/
├── summaries/
└── quicklooks/
```

For real high-volume work, install Parquet support:

```bash
python -m pip install -e '.[parquet]'
```

Then use `format = "parquet"` with compression. If `pyarrow` is unavailable,
the repo falls back to CSV unless strict mode is requested.

---

## Archive one live run

After a live run finishes, archive its outputs:

```bash
dmdc archive-run \
  --run-dir outputs/live_adaptation_replay \
  --archive-root live_archive \
  --format parquet
```

For a dependency-light test, use CSV:

```bash
dmdc archive-run \
  --run-dir outputs/live_adaptation_replay \
  --archive-root live_archive \
  --format csv
```

The command writes:

```text
live_archive/manifest.csv
live_archive/archive_run_summary.json
live_archive/provenance.json
live_archive/<data_kind>/date=.../hour=.../part-....csv or .parquet
```

---

## Config-driven archive

Add this to a live config:

```toml
[live_archive]
enabled = true
root = "live_archive"
format = "parquet"
compression = "zstd"
flush_rows = 10000
flush_seconds = 30
write_csv_mirrors = false
strict_format = false
```

Then run:

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt_with_archive.toml
```

When `[live_archive].enabled = true`, `live-replay-adapt` and `live-run-adapt`
will archive the run after the adaptation pass completes. This keeps the online
ROM logic clean while still giving you a durable long-term archive.

---

## Manifest

The manifest is the main index:

```bash
dmdc archive-index --archive-root live_archive
```

It tracks:

```text
schema_version
run_id
written_at_utc
data_kind
source_file
path
format
n_rows
n_columns
columns
time_col
min_time
max_time
file_size_bytes
date_partition
hour_partition
```

Export a copy:

```bash
dmdc archive-index --archive-root live_archive --out outputs/archive_manifest_copy.csv
```

---

## Data kinds currently archived

The archive recognizes these live-run files when they exist:

```text
raw_stream_log.csv                         -> raw_stream
cleaned_stream_log.csv                     -> cleaned_stream
live_state_estimates.csv                   -> state_estimates
live_modal_estimates.csv                   -> modal_estimates
live_estimate_covariance.csv               -> estimate_covariance
live_kalman_innovations.csv                -> kalman_innovations
live_forecasts.csv                         -> forecasts
live_forecast_residuals.csv                -> residuals
live_bias_corrected_forecasts.csv          -> bias_corrected_forecasts
live_bias_corrected_forecast_residuals.csv -> bias_corrected_residuals
live_bias_update_events.csv                -> bias_update_events
live_bias_state_timeseries.csv             -> bias_state_timeseries
live_bias_horizon_timeseries.csv           -> bias_horizon_timeseries
live_alerts.csv                            -> alerts
live_trust_score.csv                       -> trust_score
live_warnings.csv                          -> warnings
```

Missing files are skipped gracefully. This matters because a Phase-2 forecasting
run will not have Kalman files, and a Phase-4 monitoring run will not have
bias-correction files.

---

## Important design notes

1. **Do not use one giant CSV for a live loop.** Use the archive and summaries.
2. **Raw logs and cleaned logs are separate.** Never lose the raw stream.
3. **The manifest is part of reproducibility.** It tells you where each artifact
   came from and how many rows it contains.
4. **Parquet is recommended for serious runs.** CSV is fine for demos and tests.
5. **The archive is append-only.** New live runs add new partition files and
   manifest rows rather than rewriting old data.

