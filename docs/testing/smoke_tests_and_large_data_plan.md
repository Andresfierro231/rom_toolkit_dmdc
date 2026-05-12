# Smoke tests and large-data testing plan

The repo includes unit tests and CLI smoke tests, but large-data validation still
needs to be run on real infrastructure.

## Existing smoke-test targets

- `dmdc --help`
- `dmdc import-data --help`
- `dmdc campaign --dry-run`
- `dmdc model-register / model-list / model-promote / model-resolve`
- `dmdc validate-archive-schema`
- `dmdc live-dashboard --write-summary-only`

## Large-data performance tests still needed

Planned benchmark command:

```bash
dmdc benchmark-archive --n-rows 10000000 --n-states 50 --outdir outputs/archive_benchmark
```

Metrics to record:

- archive write MB/sec
- rows/sec imported
- summary generation time
- peak memory
- dashboard archive-load time
- manifest indexing time
- compression ratio
- number of partition files
- failure recovery after interrupted writes

These metrics should be archived with the run, then summarized in dashboard and
operator reports.
