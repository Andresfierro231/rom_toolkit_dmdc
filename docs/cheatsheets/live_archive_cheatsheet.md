# Live archive cheat sheet

## Archive a completed live run

```bash
dmdc archive-run \
  --run-dir outputs/live_adaptation_replay \
  --archive-root live_archive \
  --format parquet
```

CSV fallback/demo:

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive --format csv
```

## Show archive manifest

```bash
dmdc archive-index --archive-root live_archive
```

## Build summaries

```bash
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
```

## Build quicklook plots

```bash
dmdc archive-quicklook --archive-root live_archive --window-label 60s
```

## One-config workflow

Use:

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt_with_archive.toml
```

with:

```toml
[live_archive]
enabled = true
root = "live_archive"
format = "parquet"
compression = "zstd"

[summaries]
enabled = true
windows_seconds = [60, 300, 3600]

[quicklooks]
enabled = true
window_label = "60s"
```

## Read next

- `docs/live/archive_phase6_2.md`
- `docs/live/summaries_quicklooks_phase6_3.md`
- `docs/live/adaptation_phase6.md`
- `docs/live/dashboard_phase5.md`

## Search common conditions

```bash
# Large residuals
dmdc archive-search --archive-root live_archive --residual-above 5.0

# Low trust score
dmdc archive-search --archive-root live_archive --trust-below 0.5

# Alert code
dmdc archive-search --archive-root live_archive --alert-code FORECAST_RESIDUAL_HIGH

# State-specific issue
dmdc archive-search --archive-root live_archive --state TP4 --residual-above 5.0
```
