# CI and testing plan

The CI pipeline should protect command-line usability and documentation discoverability, not just unit-test math routines.

## Unit tests

Current tests should cover importers, live buffer, live forecasting, Kalman state estimation, monitoring, bias correction, archive summaries, dashboard summaries, and core ROM models.

## CLI checks

Every command should support useful `--help` text.  CI should run a smoke check over commands such as:

```text
import-data, inspect-data, fit, pod, pod-dmdc, validate, compare, sweep,
live-replay, live-replay-predict, live-replay-estimate, live-replay-monitor,
live-replay-adapt, live-dashboard, live-operator-report,
archive-run, archive-summarize, archive-quicklook, archive-search
```

## Config-template checks

Every file under `configs/templates/*.toml` should parse.  Selected templates should smoke-run on toy data.

## Large-data performance tests

These should run outside ordinary CI at first:

- 1M/10M/100M row import tests;
- folder imports with thousands of chunks;
- archive summarization memory profiling;
- dashboard archive summary load time;
- interrupted archive write/reindex tests.

See `TODO_TESTING_AND_ROADMAP.md`.


## Latest hardening-test coverage

See [`test_hardening_added.md`](test_hardening_added.md) for the new packaging, importer, archive-schema, dashboard, bias-safeguard, model-registry, HPC-planning, math-consistency, and benchmark-metrics tests.
