"""Live Phase-6.2: partitioned archive storage and manifest utilities.

The live CSV files produced by ``live-replay-*`` and ``live-run-*`` are good for
small demonstrations, but they are not the right long-term storage format for a
workstation that may run for days, weeks, or months.  This module provides a
small, dependency-light archive layer that can copy live run artifacts into a
partitioned layout:

    archive_root/
      manifest.csv
      raw_stream/date=2026-05-12/hour=14/part-....parquet
      forecasts/date=2026-05-12/hour=14/part-....parquet
      residuals/date=2026-05-12/hour=14/part-....parquet
      bias/date=2026-05-12/hour=14/part-....parquet

When Parquet support is unavailable, the writer automatically falls back to CSV
unless ``strict_format=True`` is requested.  The public API is intentionally
simple so the live workflow can use it after a run, while future versions can
flush batches incrementally during a long live session.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import shutil
import uuid

import numpy as np
import pandas as pd

from .provenance import write_provenance

SCHEMA_VERSION = "live_archive_v1"

# Canonical mapping from live-run filenames to archive data kinds.  Keeping the
# map here makes the archive layer easy to extend without touching the live
# monitor/adaptation code.
LIVE_FILE_KIND_MAP: dict[str, str] = {
    "raw_stream_log.csv": "raw_stream",
    "cleaned_stream_log.csv": "cleaned_stream",
    "live_state_estimates.csv": "state_estimates",
    "live_modal_estimates.csv": "modal_estimates",
    "live_estimate_covariance.csv": "estimate_covariance",
    "live_kalman_innovations.csv": "kalman_innovations",
    "live_forecasts.csv": "forecasts",
    "live_forecasts_wide.csv": "forecasts_wide",
    "live_forecast_residuals.csv": "residuals",
    "live_bias_corrected_forecasts.csv": "bias_corrected_forecasts",
    "live_bias_corrected_forecast_residuals.csv": "bias_corrected_residuals",
    "live_bias_update_events.csv": "bias_update_events",
    "live_bias_state_timeseries.csv": "bias_state_timeseries",
    "live_bias_horizon_timeseries.csv": "bias_horizon_timeseries",
    "live_alerts.csv": "alerts",
    "live_trust_score.csv": "trust_score",
    "live_warnings.csv": "warnings",
}

KIND_TIME_COLUMNS: dict[str, list[str]] = {
    "raw_stream": ["time", "timestamp"],
    "cleaned_stream": ["time", "timestamp"],
    "state_estimates": ["time", "timestamp"],
    "modal_estimates": ["time", "timestamp"],
    "estimate_covariance": ["time", "timestamp"],
    "kalman_innovations": ["time", "timestamp"],
    "forecasts": ["origin_time", "target_time", "time", "timestamp"],
    "forecasts_wide": ["origin_time", "target_time", "time", "timestamp"],
    "residuals": ["matched_time", "target_time", "origin_time", "time", "timestamp"],
    "bias_corrected_forecasts": ["origin_time", "target_time", "time", "timestamp"],
    "bias_corrected_residuals": ["matched_time", "target_time", "origin_time", "time", "timestamp"],
    "bias_update_events": ["time", "matched_time", "target_time", "origin_time"],
    "bias_state_timeseries": ["time", "timestamp"],
    "bias_horizon_timeseries": ["time", "timestamp"],
    "alerts": ["time", "timestamp"],
    "trust_score": ["time", "timestamp"],
    "warnings": ["time", "timestamp"],
}


@dataclass
class LiveArchiveConfig:
    """Configuration for partitioned live archive storage.

    Parameters
    ----------
    root:
        Archive root directory.
    format:
        Preferred file format: ``"parquet"`` or ``"csv"``.  Parquet is best for
        real high-volume runs; CSV is useful for demos/tests.
    compression:
        Parquet compression, usually ``"zstd"`` or ``"snappy"``.
    partition_by:
        Logical partition keys.  The current writer supports ``date`` and
        ``hour`` partitions derived from the best available time column.
    flush_rows, flush_seconds:
        Recorded in metadata now and reserved for future incremental writers.
    write_csv_mirrors:
        If true and Parquet is requested, also write CSV copies next to Parquet
        files.  Keep false for large data.
    strict_format:
        If true, fail when Parquet cannot be written.  If false, fall back to CSV.
    """

    root: str = "live_archive"
    format: str = "parquet"
    compression: str = "zstd"
    partition_by: list[str] = field(default_factory=lambda: ["date", "hour"])
    flush_rows: int = 10_000
    flush_seconds: float = 30.0
    write_csv_mirrors: bool = False
    strict_format: bool = False

    def __post_init__(self) -> None:
        fmt = str(self.format).lower()
        if fmt not in {"parquet", "csv"}:
            raise ValueError("LiveArchiveConfig.format must be 'parquet' or 'csv'.")
        self.format = fmt


@dataclass
class ArchiveRunResult:
    """Summary returned by :func:`archive_live_run`."""

    archive_root: str
    run_dir: str
    n_files_archived: int
    n_rows_archived: int
    manifest_path: str
    format_requested: str
    format_used: str


class LiveManifest:
    """Append-only manifest for archive files.

    The manifest is intentionally a CSV so it remains inspectable without a
    database.  A future heavy-duty deployment can mirror it into DuckDB, but the
    CSV manifest is enough for indexing, searching, and reproducibility.
    """

    def __init__(self, archive_root: str | Path) -> None:
        self.archive_root = Path(archive_root)
        self.path = self.archive_root / "manifest.csv"
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def append(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        df = pd.DataFrame(rows)
        if self.path.exists() and self.path.stat().st_size > 0:
            old = pd.read_csv(self.path)
            df = pd.concat([old, df], ignore_index=True)
        df.to_csv(self.path, index=False)

    def read(self) -> pd.DataFrame:
        if self.path.exists() and self.path.stat().st_size > 0:
            return pd.read_csv(self.path)
        return pd.DataFrame()


class LiveArchiveWriter:
    """Write live records to partitioned CSV/Parquet storage.

    The writer accepts already-materialized DataFrames.  For terabyte-scale runs,
    the same class can be used by future streaming code to flush micro-batches
    every ``flush_rows`` or ``flush_seconds``.
    """

    def __init__(self, config: LiveArchiveConfig, *, run_id: str | None = None) -> None:
        self.config = config
        self.root = Path(config.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        self.manifest = LiveManifest(self.root)
        self.format_used = self.config.format

    def write_records(self, kind: str, df: pd.DataFrame, *, source_file: str | None = None, time_col: str | None = None) -> list[dict[str, Any]]:
        """Write records for one data kind and return manifest rows."""

        if df is None or df.empty:
            return []
        df = df.copy()
        inferred_time_col = time_col or infer_time_column(df, kind)
        df["_archive_date"], df["_archive_hour"] = partition_values(df, inferred_time_col)
        rows: list[dict[str, Any]] = []
        for (date, hour), part in df.groupby(["_archive_date", "_archive_hour"], dropna=False):
            rel_dir = Path(kind) / f"date={date}" / f"hour={hour}"
            out_dir = self.root / rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = f"part-{self.run_id}-{uuid.uuid4().hex[:8]}"
            part_to_write = part.drop(columns=["_archive_date", "_archive_hour"], errors="ignore")
            out_path, fmt_used = self._write_frame(part_to_write, out_dir / stem)
            self.format_used = fmt_used if self.format_used == self.config.format else self.format_used
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": self.run_id,
                    "written_at_utc": datetime.now(timezone.utc).isoformat(),
                    "data_kind": kind,
                    "source_file": source_file or "",
                    "path": str(out_path.relative_to(self.root)),
                    "format": fmt_used,
                    "n_rows": int(len(part_to_write)),
                    "n_columns": int(part_to_write.shape[1]),
                    "columns": json.dumps(list(part_to_write.columns)),
                    "time_col": inferred_time_col or "",
                    "min_time": _safe_min(part_to_write[inferred_time_col]) if inferred_time_col in part_to_write.columns else "",
                    "max_time": _safe_max(part_to_write[inferred_time_col]) if inferred_time_col in part_to_write.columns else "",
                    "file_size_bytes": int(out_path.stat().st_size),
                    "date_partition": str(date),
                    "hour_partition": str(hour),
                }
            )
        self.manifest.append(rows)
        return rows

    def _write_frame(self, df: pd.DataFrame, stem_path: Path) -> tuple[Path, str]:
        if self.config.format == "csv":
            out = stem_path.with_suffix(".csv")
            df.to_csv(out, index=False)
            return out, "csv"
        out = stem_path.with_suffix(".parquet")
        try:
            df.to_parquet(out, index=False, compression=self.config.compression)
            if self.config.write_csv_mirrors:
                df.to_csv(stem_path.with_suffix(".csv"), index=False)
            return out, "parquet"
        except Exception as exc:
            if self.config.strict_format:
                raise RuntimeError("Could not write Parquet archive. Install pyarrow or use format='csv'.") from exc
            out = stem_path.with_suffix(".csv")
            df.to_csv(out, index=False)
            return out, "csv"


def archive_live_run(run_dir: str | Path, config: LiveArchiveConfig, *, config_path: str | Path | None = None) -> ArchiveRunResult:
    """Archive known live-run CSV outputs into partitioned storage."""

    run = Path(run_dir)
    if not run.exists():
        raise FileNotFoundError(f"Live run directory not found: {run}")
    writer = LiveArchiveWriter(config)
    all_rows: list[dict[str, Any]] = []
    n_rows = 0
    for filename, kind in LIVE_FILE_KIND_MAP.items():
        path = run / filename
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        rows = writer.write_records(kind, df, source_file=str(path), time_col=infer_time_column(df, kind))
        all_rows.extend(rows)
        n_rows += int(sum(r.get("n_rows", 0) for r in rows))
    # Copy lightweight metadata/config files for traceability.
    meta_dir = Path(config.root) / "run_metadata" / writer.run_id
    meta_dir.mkdir(parents=True, exist_ok=True)
    for name in ["config_used.toml", "provenance.json", "live_adaptation_summary.json", "live_monitoring_summary.json", "live_prediction_summary.json"]:
        src = run / name
        if src.exists():
            try:
                shutil.copy2(src, meta_dir / name)
            except OSError:
                pass
    summary = ArchiveRunResult(
        archive_root=str(Path(config.root)),
        run_dir=str(run),
        n_files_archived=len(all_rows),
        n_rows_archived=n_rows,
        manifest_path=str(Path(config.root) / "manifest.csv"),
        format_requested=config.format,
        format_used=writer.format_used,
    )
    (Path(config.root) / "archive_run_summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    write_provenance(Path(config.root), config_path=config_path, extra={"command": "archive-live-run", "result": asdict(summary)})
    return summary


def read_archive_manifest(archive_root: str | Path) -> pd.DataFrame:
    """Read the archive manifest if it exists."""

    return LiveManifest(archive_root).read()


def load_archive_kind(archive_root: str | Path, kind: str, *, max_files: int | None = None) -> pd.DataFrame:
    """Load archived records of one kind from manifest-listed files.

    This helper is intended for summaries/quicklooks, not for loading terabytes
    into memory.  For large archives, use it with ``max_files`` or add filters in
    a future DuckDB/Polars backend.
    """

    root = Path(archive_root)
    manifest = read_archive_manifest(root)
    if manifest.empty or "data_kind" not in manifest.columns:
        return pd.DataFrame()
    rows = manifest[manifest["data_kind"].astype(str) == kind]
    if max_files is not None:
        rows = rows.tail(int(max_files))
    frames: list[pd.DataFrame] = []
    for _, row in rows.iterrows():
        path = root / str(row.get("path"))
        if not path.exists():
            continue
        try:
            if path.suffix.lower() == ".parquet":
                frames.append(pd.read_parquet(path))
            else:
                frames.append(pd.read_csv(path))
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def infer_time_column(df: pd.DataFrame, kind: str | None = None) -> str | None:
    """Infer the best time column for a data kind."""

    candidates = KIND_TIME_COLUMNS.get(str(kind), []) + ["time", "timestamp", "origin_time", "target_time", "matched_time"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def partition_values(df: pd.DataFrame, time_col: str | None) -> tuple[pd.Series, pd.Series]:
    """Return date/hour partitions from a numeric or datetime-like time column."""

    if time_col is None or time_col not in df.columns:
        n = len(df)
        return pd.Series(["unknown"] * n, index=df.index), pd.Series(["unknown"] * n, index=df.index)
    raw = df[time_col]
    # Try datetime first.  Numeric relative seconds should not become 1970 dates,
    # so only accept datetime parsing when the raw column is not numeric-like.
    numeric = pd.to_numeric(raw, errors="coerce")
    if numeric.notna().mean() < 0.8:
        dt = pd.to_datetime(raw, errors="coerce", utc=False)
        if dt.notna().any():
            return dt.dt.strftime("%Y-%m-%d").fillna("unknown"), dt.dt.strftime("%H").fillna("unknown")
    sec = numeric.fillna(0.0).astype(float)
    hour_index = np.floor(sec / 3600.0).astype(int)
    return pd.Series(["relative"] * len(df), index=df.index), hour_index.map(lambda h: f"{h:04d}")


def _safe_min(series: pd.Series) -> Any:
    try:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            return numeric.min()
        return series.min()
    except Exception:
        return ""


def _safe_max(series: pd.Series) -> Any:
    try:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            return numeric.max()
        return series.max()
    except Exception:
        return ""
