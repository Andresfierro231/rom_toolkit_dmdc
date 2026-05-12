# Live Phase 6.3 — Summaries and quicklook plots

Live Phase 6.2 gives you partitioned storage. Live Phase 6.3 makes that archive
**easy to browse** by generating compact summaries and small static plots.

This is critical for long experiments. People should not need to load raw months
of data to answer first-pass questions like:

- Did the trust score drop today?
- Which sensor had the largest residual?
- Did bias correction drift over time?
- When did alerts occur?
- Are there short windows worth investigating in detail?

Related docs:

- Archive storage: [`docs/live/archive_phase6_2.md`](archive_phase6_2.md)
- Dashboard: [`docs/live/dashboard_phase5.md`](dashboard_phase5.md)
- Bias correction: [`docs/live/adaptation_phase6.md`](adaptation_phase6.md)
- Monitoring: [`docs/live/monitoring_phase4.md`](monitoring_phase4.md)

---

## Create summaries

```bash
dmdc archive-summarize \
  --archive-root live_archive \
  --windows-seconds 60 300 3600
```

This writes files such as:

```text
live_archive/summaries/state_summary_60s.csv
live_archive/summaries/state_estimate_summary_60s.csv
live_archive/summaries/residual_summary_60s.csv
live_archive/summaries/bias_corrected_residual_summary_60s.csv
live_archive/summaries/trust_summary_60s.csv
live_archive/summaries/bias_summary_60s.csv
live_archive/summaries/alert_summary.csv
live_archive/summaries/summary_manifest.json
```

For huge archives, summarize only the most recent files first:

```bash
dmdc archive-summarize \
  --archive-root live_archive \
  --windows-seconds 60 \
  --max-files-per-kind 20
```

---

## What the summaries contain

### State summaries

For cleaned stream states, each window stores:

```text
mean, std, min, max, median, p05, p95, last, n, missing_fraction
```

This is useful for quickly browsing trends without plotting every raw sample.

### Residual summaries

For forecast residuals:

```text
rmse, mae, max_abs, bias_mean, p95_abs, n
```

This is the fastest way to see which states and time windows the ROM struggled
with.

### Trust summaries

For live trust score:

```text
mean, min, p05, number of samples below 0.5
```

### Bias summaries

For bias correction:

```text
mean_bias, last_bias, max_abs_bias
```

### Alert summaries

Alerts are grouped by severity and code.

---

## Generate quicklook plots

```bash
dmdc archive-quicklook \
  --archive-root live_archive \
  --window-label 60s
```

This writes plots like:

```text
live_archive/quicklooks/trust_summary_60s.png
live_archive/quicklooks/residual_summary_60s.png
live_archive/quicklooks/bias_summary_60s.png
live_archive/quicklooks/state_summary_60s.png
```

Quicklooks are deliberately small. Their purpose is not publication-quality
figures; their purpose is **triage**.

---

## Config-driven summaries and quicklooks

```toml
[summaries]
enabled = true
windows_seconds = [60, 300, 3600]
max_files_per_kind = 100

[quicklooks]
enabled = true
window_label = "60s"
```

When combined with:

```toml
[live_archive]
enabled = true
root = "live_archive"
format = "parquet"
```

then `dmdc live-replay-adapt --config ...` will archive the run and then create
summaries/quicklooks automatically.

---

## Recommended browsing workflow

```text
1. Open quicklooks first.
2. Inspect summary CSVs around interesting windows.
3. Use manifest paths to find detailed partition files.
4. Only load raw stream partitions for the short time windows that matter.
```

This is the workflow that scales to months of data.


---

## Search the archive

For quick triage, use `archive-search`:

```bash
# Find large residual windows/rows.
dmdc archive-search --archive-root live_archive --residual-above 5.0

# Find low-trust regions.
dmdc archive-search --archive-root live_archive --trust-below 0.5

# Find a specific alert code.
dmdc archive-search --archive-root live_archive --alert-code FORECAST_RESIDUAL_HIGH

# Focus on one state.
dmdc archive-search --archive-root live_archive --state TP4 --residual-above 5.0
```

Outputs:

```text
outputs/archive_search/search_results.csv
outputs/archive_search/matching_manifest_rows.csv
outputs/archive_search/matching_files.txt
outputs/archive_search/search_summary.json
```

This is intentionally a lightweight search layer. For very large archives, use
`--max-files-per-kind` while exploring, then use the manifest paths to drill into
small time partitions.
