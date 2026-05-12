# Archive Benchmarking and Metrics Tracking

The repo includes a local benchmark command for archive write throughput,
summary-generation time, quicklook-generation time, and peak memory.

```bash
dmdc benchmark-archive \
  --n-rows 1000000 \
  --n-states 32 \
  --format parquet \
  --outdir outputs/archive_benchmark
```

For quick CI/smoke tests, use a small run:

```bash
dmdc benchmark-archive --n-rows 10000 --format csv --no-quicklooks
```

## Outputs

```text
outputs/archive_benchmark/
├── synthetic_live_run/
├── live_archive/
├── archive_benchmark_metrics.csv
├── archive_benchmark_summary.json
└── provenance.json
```

Important metrics:

| Metric | Meaning |
|---|---|
| `archive_write_mb_per_sec` | synthetic live-run size divided by archive time |
| `summary_rows_per_sec` | archived rows divided by summary time |
| `peak_memory_mb` | peak Python allocation from `tracemalloc` |
| `summarize_seconds` | wall time for `archive-summarize` equivalent |
| `quicklook_seconds` | wall time for quicklook PNG generation |

## Large-data testing still needed

The benchmark command is a starting point. Before claiming terabyte-scale
readiness, run staged tests:

1. 1 million rows, local CSV archive.
2. 10 million rows, Parquet archive with `pyarrow`.
3. Many small files, to test manifest/index overhead.
4. Long archive dashboard mode, to verify summary-first loading.
5. Interrupted archive write and recovery tests.
6. Memory profiling on the workstation that will collect the live loop data.

See `TODO_TESTING_AND_ROADMAP.md` for the broader testing roadmap.
