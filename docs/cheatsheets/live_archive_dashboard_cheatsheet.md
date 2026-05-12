# Live archive dashboard cheat sheet

## Install optional dashboard dependencies

```bash
python -m pip install -e '.[dashboard]'
```

## Launch archive dashboard

```bash
dmdc live-dashboard --archive-root live_archive --mode archive --window-label 60s
```

## Config-driven launch

```bash
dmdc live-dashboard --config configs/templates/live_dashboard_archive.toml
```

## Summary-only smoke test

```bash
dmdc live-dashboard --archive-root live_archive --mode archive --write-summary-only
```

This writes:

```text
live_archive/archive_dashboard_summary.json
```

## Build the data the dashboard expects

```bash
dmdc archive-run --run-dir outputs/live_adaptation_replay --archive-root live_archive
dmdc archive-summarize --archive-root live_archive --windows-seconds 60 300 3600
dmdc archive-quicklook --archive-root live_archive --window-label 60s
```

## Use this mode when

```text
You have many live runs.
You have days/weeks/months of data.
Raw files are too large to load interactively.
You want trust/residual/bias/alert summaries first.
You want quick visual triage before drilling into raw partitions.
```

## Related docs

- `docs/live/dashboard_archive_phase6_4.md`
- `docs/live/archive_phase6_2.md`
- `docs/live/summaries_quicklooks_phase6_3.md`
- `docs/cheatsheets/live_archive_cheatsheet.md`
