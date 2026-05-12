"""Streaming adapters for live and replayed time-series data.

This module is the first layer of the online/digital-twin workflow.  It is
intentionally independent of DMD/DMDc/POD models: a stream adapter only answers
one question:

    "What new timestamped samples have arrived since I last checked?"

Keeping the streaming interface small makes it easy to plug in different data
sources later (EPICS, MQTT, sockets, OPC-UA, LabVIEW logs, etc.) without
rewriting the ROM and validation code.  The initial implementation provides two
simple adapters that are useful immediately on a local workstation:

``CSVReplayAdapter``
    Reads an existing CSV file and yields rows as if they were arriving live.
    This is the safest way to test the online pipeline before connecting real
    hardware.

``CSVTailAdapter``
    Polls a CSV file that another process is appending to.  The first version is
    deliberately conservative: it re-reads the CSV and returns only rows whose
    integer row position has not been seen before.  This is adequate for modest
    live logs and easy to debug.  A later high-throughput adapter can track byte
    offsets while preserving this same public interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Protocol
import time as _time

import pandas as pd


@dataclass(slots=True)
class LiveSample:
    """One row/sample from a live or replayed data stream.

    Parameters
    ----------
    values:
        Mapping of column name to value exactly as read from the stream.
    source:
        Human-readable stream source name, for example ``"csv_replay"`` or
        ``"csv_tail"``.
    row_index:
        Integer row index in the source table when available.  This is useful
        for debugging and for verifying that tailing did not duplicate rows.
    received_utc:
        Timestamp recording when this sample was observed by the adapter.  This
        is intentionally separate from the physical experiment/simulation time
        column stored in ``values``.
    """

    values: dict[str, Any]
    source: str
    row_index: int | None = None
    received_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_record(self) -> dict[str, Any]:
        """Return a flat dictionary suitable for CSV logging."""

        record = dict(self.values)
        record["_stream_source"] = self.source
        record["_stream_row_index"] = self.row_index
        record["_received_utc"] = self.received_utc
        return record


class StreamAdapter(Protocol):
    """Minimal protocol implemented by all live-stream adapters."""

    def read_new_samples(self) -> list[LiveSample]:
        """Return all samples that arrived since the previous call."""


class CSVReplayAdapter:
    """Replay an existing CSV file as a deterministic stream of rows.

    The adapter is stateful.  Each call to :meth:`read_new_samples` returns the
    next ``chunk_size`` rows until the file is exhausted.  This makes offline CSV
    data behave like live data, which is invaluable for testing online buffers,
    warning logic, logging, and later forecasting/state-estimation components.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        chunk_size: int = 1,
        case_col: str | None = None,
        case_id: str | int | float | None = None,
        sort_by_time_col: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.chunk_size = max(1, int(chunk_size))
        self.case_col = case_col
        self.case_id = case_id
        self.sort_by_time_col = sort_by_time_col
        self._frame = self._load_frame()
        self._cursor = 0

    def _load_frame(self) -> pd.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"Replay CSV not found: {self.path}")
        frame = pd.read_csv(self.path)
        if self.case_col is not None and self.case_id is not None:
            if self.case_col not in frame.columns:
                raise ValueError(f"case_col={self.case_col!r} not found in replay CSV.")
            frame = frame[frame[self.case_col] == self.case_id].copy()
        if self.sort_by_time_col is not None:
            if self.sort_by_time_col not in frame.columns:
                raise ValueError(f"sort_by_time_col={self.sort_by_time_col!r} not found in replay CSV.")
            frame = frame.sort_values(self.sort_by_time_col).reset_index(drop=True)
        return frame.reset_index(drop=True)

    @property
    def exhausted(self) -> bool:
        """Whether every replay row has already been emitted."""

        return self._cursor >= len(self._frame)

    def read_new_samples(self) -> list[LiveSample]:
        if self.exhausted:
            return []
        start = self._cursor
        stop = min(len(self._frame), start + self.chunk_size)
        self._cursor = stop
        records: list[LiveSample] = []
        for idx in range(start, stop):
            values = self._frame.iloc[idx].to_dict()
            records.append(LiveSample(values=values, source="csv_replay", row_index=idx))
        return records


class CSVTailAdapter:
    """Poll a CSV file that is being appended to by another process.

    This first implementation favors robustness and transparency over raw speed:
    every poll reads the full CSV and returns rows beyond the last row count that
    this adapter has already observed.  For live loop logs with tens to hundreds
    of columns and moderate polling rates, this is typically sufficient.  For
    very high-rate streams, implement a byte-offset tail adapter later while
    keeping the same :class:`StreamAdapter` protocol.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        start_at_end: bool = False,
        case_col: str | None = None,
        case_id: str | int | float | None = None,
    ) -> None:
        self.path = Path(path)
        self.case_col = case_col
        self.case_id = case_id
        self._last_total_rows = 0
        if start_at_end and self.path.exists():
            self._last_total_rows = len(pd.read_csv(self.path))

    def read_new_samples(self) -> list[LiveSample]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return []
        try:
            frame = pd.read_csv(self.path)
        except pd.errors.EmptyDataError:
            return []
        total_rows = len(frame)
        if total_rows <= self._last_total_rows:
            return []
        new = frame.iloc[self._last_total_rows : total_rows].copy()
        offset = self._last_total_rows
        self._last_total_rows = total_rows
        if self.case_col is not None and self.case_id is not None:
            if self.case_col not in new.columns:
                raise ValueError(f"case_col={self.case_col!r} not found in tailed CSV.")
            mask = new[self.case_col] == self.case_id
            new = new[mask]
        records: list[LiveSample] = []
        for local_i, (_, row) in enumerate(new.iterrows()):
            records.append(
                LiveSample(values=row.to_dict(), source="csv_tail", row_index=offset + local_i)
            )
        return records


def make_stream_adapter(
    *,
    stream_type: str,
    path: str | Path,
    chunk_size: int = 1,
    start_at_end: bool = False,
    case_col: str | None = None,
    case_id: str | int | float | None = None,
    time_col: str | None = None,
) -> StreamAdapter:
    """Factory used by CLI/config workflows to create a stream adapter."""

    key = stream_type.strip().lower().replace("-", "_")
    if key in {"csv_replay", "replay"}:
        return CSVReplayAdapter(
            path,
            chunk_size=chunk_size,
            case_col=case_col,
            case_id=case_id,
            sort_by_time_col=time_col,
        )
    if key in {"csv_tail", "tail"}:
        return CSVTailAdapter(path, start_at_end=start_at_end, case_col=case_col, case_id=case_id)
    raise ValueError(
        f"Unsupported stream type {stream_type!r}. Supported types: csv_replay, csv_tail."
    )


def run_stream_until_done(
    adapter: StreamAdapter,
    *,
    max_samples: int | None = None,
    max_polls: int | None = None,
    poll_seconds: float = 0.0,
) -> Iterable[list[LiveSample]]:
    """Yield batches from an adapter until limits are reached.

    This helper is shared by replay and tail commands.  It deliberately does not
    know about buffers, models, or logging; it simply manages the polling loop.
    """

    n_samples = 0
    n_polls = 0
    empty_polls = 0
    while True:
        if max_polls is not None and n_polls >= max_polls:
            break
        if max_samples is not None and n_samples >= max_samples:
            break
        batch = adapter.read_new_samples()
        n_polls += 1
        if batch:
            if max_samples is not None and n_samples + len(batch) > max_samples:
                batch = batch[: max_samples - n_samples]
            n_samples += len(batch)
            empty_polls = 0
            yield batch
        else:
            empty_polls += 1
            # Replay adapters expose ``exhausted``.  Tail adapters do not; they
            # may receive more rows later, so they rely on max_polls or Ctrl-C.
            if getattr(adapter, "exhausted", False):
                break
            if max_polls is None and empty_polls >= 1:
                break
        if poll_seconds > 0:
            _time.sleep(float(poll_seconds))
