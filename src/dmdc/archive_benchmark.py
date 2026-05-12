"""Large-data archive benchmark tools.

The real archive may eventually see very high-rate streams.  The benchmark in
this module creates synthetic live-run outputs, archives them, summarizes them,
and records timing/size/memory metrics.  It is intentionally local-workstation
friendly by default, but the CLI parameters can be increased for stress tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
import json
import os
import tracemalloc

import numpy as np
import pandas as pd

from .live_archive import LiveArchiveConfig, archive_live_run
from .live_summaries import LiveSummaryConfig, summarize_live_archive
from .live_quicklooks import QuicklookConfig, make_archive_quicklooks
from .provenance import write_provenance


@dataclass
class ArchiveBenchmarkConfig:
    n_rows: int = 100_000
    n_states: int = 12
    n_inputs: int = 3
    chunk_files: int = 1
    outdir: str = "outputs/archive_benchmark"
    archive_root: str = "outputs/archive_benchmark/live_archive"
    archive_format: str = "csv"
    compression: str = "zstd"
    windows_seconds: list[float] | None = None
    make_quicklooks: bool = True
    random_seed: int = 7


@dataclass
class ArchiveBenchmarkResult:
    outdir: str
    archive_root: str
    n_rows: int
    n_states: int
    chunk_files: int
    generated_csv_mb: float
    archived_mb: float
    generate_seconds: float
    archive_seconds: float
    summarize_seconds: float
    quicklook_seconds: float
    archive_write_mb_per_sec: float
    summary_rows_per_sec: float
    peak_memory_mb: float
    metrics_csv: str
    summary_json: str


def run_archive_benchmark(config: ArchiveBenchmarkConfig) -> ArchiveBenchmarkResult:
    """Run a synthetic archive benchmark and persist metrics.

    The generated run directory mimics the most important live outputs:
    cleaned stream, forecasts/residuals, trust, and alerts.  This keeps the
    benchmark representative without requiring a real loop or model.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    run_dir = outdir / "synthetic_live_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    archive_root = Path(config.archive_root)

    tracemalloc.start()
    t0 = perf_counter()
    _write_synthetic_live_run(run_dir, config)
    generate_seconds = perf_counter() - t0
    generated_csv_mb = _directory_size_mb(run_dir)

    t1 = perf_counter()
    archive_result = archive_live_run(
        run_dir,
        LiveArchiveConfig(root=str(archive_root), format=config.archive_format, compression=config.compression),
    )
    archive_seconds = perf_counter() - t1
    archived_mb = _directory_size_mb(archive_root)

    windows = config.windows_seconds or [60.0, 300.0, 3600.0]
    t2 = perf_counter()
    summary_result = summarize_live_archive(
        LiveSummaryConfig(archive_root=str(archive_root), windows_seconds=windows, max_files_per_kind=None)
    )
    summarize_seconds = perf_counter() - t2

    quicklook_seconds = 0.0
    if config.make_quicklooks:
        t3 = perf_counter()
        make_archive_quicklooks(QuicklookConfig(archive_root=str(archive_root), window_label=_window_label(windows[0])))
        quicklook_seconds = perf_counter() - t3

    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = peak / (1024**2)

    result = ArchiveBenchmarkResult(
        outdir=str(outdir),
        archive_root=str(archive_root),
        n_rows=int(config.n_rows),
        n_states=int(config.n_states),
        chunk_files=int(config.chunk_files),
        generated_csv_mb=generated_csv_mb,
        archived_mb=archived_mb,
        generate_seconds=generate_seconds,
        archive_seconds=archive_seconds,
        summarize_seconds=summarize_seconds,
        quicklook_seconds=quicklook_seconds,
        archive_write_mb_per_sec=(generated_csv_mb / archive_seconds) if archive_seconds > 0 else float("inf"),
        summary_rows_per_sec=(archive_result.n_rows_archived / summarize_seconds) if summarize_seconds > 0 else float("inf"),
        peak_memory_mb=peak_memory_mb,
        metrics_csv=str(outdir / "archive_benchmark_metrics.csv"),
        summary_json=str(outdir / "archive_benchmark_summary.json"),
    )
    pd.DataFrame([asdict(result)]).to_csv(result.metrics_csv, index=False)
    Path(result.summary_json).write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    write_provenance(outdir, command=["archive_benchmark"], extra={"benchmark_config": asdict(config)})
    return result


def _write_synthetic_live_run(run_dir: Path, config: ArchiveBenchmarkConfig) -> None:
    rng = np.random.default_rng(config.random_seed)
    n = int(config.n_rows)
    time = np.cumsum(rng.uniform(0.08, 0.13, size=n))  # intentionally nonuniform
    states = [f"TP{i+1}" for i in range(max(0, config.n_states - 1))] + ["massFlowRate"]
    inputs = [f"u{i+1}" for i in range(config.n_inputs)]
    base = pd.DataFrame({"time": time})
    for j, state in enumerate(states):
        base[state] = 500.0 + 10.0 * np.sin(0.01 * time + j) + rng.normal(0, 0.1, size=n)
    for j, inp in enumerate(inputs):
        base[inp] = 1.0 + 0.1 * np.sin(0.003 * time + j)
    base.to_csv(run_dir / "cleaned_stream_log.csv", index=False)
    # A compact forecast/residual sample.  For very large n, keep every kth row
    # so the benchmark remains fast while still exercising long tables.
    stride = max(1, n // max(1000, min(n, 50_000)))
    sample = base.iloc[::stride].copy()
    rows = []
    residual_rows = []
    for h in [5.0, 10.0, 30.0]:
        for state in states[: min(8, len(states))]:
            pred = sample[state].to_numpy() + rng.normal(0, 0.5 + 0.02 * h, size=len(sample))
            for t, yhat, y in zip(sample["time"], pred, sample[state], strict=False):
                rows.append({"origin_time": t, "target_time": t + h, "forecast_horizon_s": h, "state": state, "predicted_value": yhat})
                residual_rows.append({"matched_time": t + h, "forecast_horizon_s": h, "state": state, "measured_value": y, "predicted_value": yhat, "residual": y - yhat, "abs_residual": abs(y - yhat)})
    pd.DataFrame(rows).to_csv(run_dir / "live_forecasts.csv", index=False)
    pd.DataFrame(residual_rows).to_csv(run_dir / "live_forecast_residuals.csv", index=False)
    trust = pd.DataFrame({"time": sample["time"], "trust_score": np.clip(0.95 - 0.02 * rng.standard_normal(len(sample)), 0, 1)})
    trust.to_csv(run_dir / "live_trust_score.csv", index=False)
    alerts = pd.DataFrame({"time": sample["time"].iloc[::50], "severity": "warning", "code": "BENCHMARK_SYNTHETIC", "message": "Synthetic benchmark alert"})
    alerts.to_csv(run_dir / "live_alerts.csv", index=False)


def _directory_size_mb(path: Path) -> float:
    total = 0
    if path.exists():
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass
    return total / (1024**2)


def _window_label(seconds: float) -> str:
    return f"{int(seconds)}s" if float(seconds).is_integer() else f"{seconds:g}s"
