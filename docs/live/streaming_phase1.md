# Live Streaming Phase 1: Replay Mode and Stream Abstraction

This phase adds the first online/digital-twin layer without changing the offline ROM workflows.
The goal is simple:

```text
stream rows -> validate required columns -> keep a rolling live buffer -> write durable logs
```

No model is required yet. This is intentional. Before a live loop forecasts anything, the repo
needs to prove that it can reliably ingest, clean, buffer, and log live data.

## Why start with replay?

A live-loop workflow should be tested on old data before it touches a real experiment. Replay mode
makes a normal CSV behave like a stream. Each poll emits the next row or chunk of rows.

```bash
dmdc live-replay --config configs/templates/live_replay_csv.toml
```

Outputs:

```text
outputs/live_replay_example/
├── raw_stream_log.csv
├── cleaned_stream_log.csv
├── live_warnings.csv
├── warnings.txt
├── live_buffer_summary.json
├── live_ingestion_summary.json
└── provenance.json
```

## CSV tail mode

For an actual local workstation, the first supported live source is a CSV file that a DAQ/logger
keeps appending to.

```bash
dmdc live-run --config configs/templates/live_csv_tail.toml
```

During development, keep `max_polls` or `max_samples` set so the command exits. For an open-ended
run, remove those limits and stop with Ctrl-C.

## Nonuniform/adaptive time is the default

Live timestamps are not assumed to be uniform. The buffer records `median_dt`, `min_dt`, `max_dt`,
and `dt_ratio_max_to_min`, but it does not reject variable time steps. Later forecasting layers
should use adaptive-time models or integrate with the actual `dt` between live samples.

## Stream adapter interface

All stream adapters implement:

```python
class StreamAdapter:
    def read_new_samples(self) -> list[LiveSample]: ...
```

Current adapters:

```text
CSVReplayAdapter    Replays a finished CSV file as a stream.
CSVTailAdapter      Polls a CSV file that is being appended by another process.
```

Future adapters can support EPICS, MQTT, ZeroMQ, TCP sockets, OPC-UA, LabVIEW logs, or serial DAQ
without changing the downstream buffer/predictor API.

## Python API

```python
from dmdc import LiveIngestionConfig, run_live_ingestion

cfg = LiveIngestionConfig(
    stream_type="csv_replay",
    path="data/my_loop.csv",
    time_col="time",
    case_col="case_id",
    state_cols=["TP1", "TP2", "TP3", "massFlowRate"],
    input_cols=["q_heater"],
    outdir="outputs/live_replay",
    chunk_size=5,
    max_samples=100,
)

result = run_live_ingestion(cfg)
print(result)
```

## How this connects to later live forecasting

Phase 1 writes clean logs and maintains `RollingLiveBuffer`. Later phases should plug in after each
buffer update:

```text
LiveBuffer.latest_state()
LiveBuffer.latest_input()
LiveBuffer.matrices()
```

Those are the natural hooks for:

```text
adaptive-time live forecasting
POD-Kalman state estimation
residual monitoring
alert generation
operator dashboards
```
