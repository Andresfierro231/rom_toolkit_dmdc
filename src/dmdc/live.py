"""High-level live streaming workflows.

Phase Live-1 provides stream abstraction, replay/tail ingestion, rolling buffers,
and durable logs.  It intentionally does not require a fitted ROM model yet.
Later phases can import :func:`run_live_ingestion` and attach predictors or
Kalman filters after each buffer update.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import shutil

from .live_buffer import RollingLiveBuffer
from .streaming import make_stream_adapter, run_stream_until_done
from .provenance import write_provenance


@dataclass
class LiveIngestionConfig:
    """Configuration for model-agnostic live ingestion/replay."""

    stream_type: str
    path: str
    state_cols: list[str]
    input_cols: list[str]
    time_col: str | None = None
    case_col: str | None = None
    case_id: str | int | float | None = None
    outdir: str = "outputs/live_ingestion"
    chunk_size: int = 1
    poll_seconds: float = 0.0
    max_samples: int | None = None
    max_polls: int | None = None
    buffer_seconds: float | None = None
    buffer_max_samples: int | None = None
    start_at_end: bool = False
    save_every_batch: bool = False


@dataclass
class LiveIngestionResult:
    """Summary returned by :func:`run_live_ingestion`."""

    outdir: str
    n_batches: int
    n_samples_seen: int
    n_clean_samples_buffered: int
    n_warnings: int
    stream_type: str


def run_live_ingestion(config: LiveIngestionConfig, *, config_path: str | Path | None = None) -> LiveIngestionResult:
    """Run a live/replay ingestion session and write durable logs.

    This is the shared implementation behind ``dmdc live-replay`` and
    ``dmdc live-run``.  It creates a stream adapter, appends samples to a rolling
    buffer, and writes logs that downstream online ROM components can consume.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if config_path is not None:
        try:
            shutil.copyfile(config_path, outdir / "config_used.toml")
        except OSError:
            pass

    adapter = make_stream_adapter(
        stream_type=config.stream_type,
        path=config.path,
        chunk_size=config.chunk_size,
        start_at_end=config.start_at_end,
        case_col=config.case_col,
        case_id=config.case_id,
        time_col=config.time_col,
    )
    buffer = RollingLiveBuffer(
        state_cols=config.state_cols,
        input_cols=config.input_cols,
        time_col=config.time_col,
        case_col=config.case_col,
        buffer_seconds=config.buffer_seconds,
        max_samples=config.buffer_max_samples,
    )

    n_batches = 0
    n_samples_seen = 0
    for batch in run_stream_until_done(
        adapter,
        max_samples=config.max_samples,
        max_polls=config.max_polls,
        poll_seconds=config.poll_seconds,
    ):
        n_batches += 1
        n_samples_seen += len(batch)
        buffer.append(batch)
        if config.save_every_batch:
            buffer.save(outdir)

    buffer.save(outdir)
    result = LiveIngestionResult(
        outdir=str(outdir),
        n_batches=n_batches,
        n_samples_seen=n_samples_seen,
        n_clean_samples_buffered=int(buffer.summary()["n_clean_samples_buffered"]),
        n_warnings=int(buffer.summary()["n_warnings"]),
        stream_type=config.stream_type,
    )
    (outdir / "live_ingestion_summary.json").write_text(
        json.dumps({"config": asdict(config), "result": asdict(result), "buffer": buffer.summary()}, indent=2),
        encoding="utf-8",
    )
    write_provenance(outdir, config_path=config_path, extra={"command": "live-ingestion", "result": asdict(result)})
    return result
