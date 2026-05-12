"""Live Phase-6.3: compact summaries for large live archives.

The archive stores detailed records, but most users should browse summaries
first.  This module computes small, windowed CSV tables for states, residuals,
trust scores, alerts, and bias histories.  The summaries are designed to be
small enough for dashboards, reports, and quick looks even when raw data grows
for months.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd

from .live_archive import load_archive_kind, infer_time_column
from .provenance import write_provenance


@dataclass
class LiveSummaryConfig:
    """Configuration for archive summaries.

    ``windows_seconds`` controls downsampling windows.  For example, ``60``
    produces one row per minute per state/residual group.  Use short windows for
    live dashboards and longer windows for month-scale browsing.
    """

    archive_root: str = "live_archive"
    outdir: str | None = None
    windows_seconds: list[float] = field(default_factory=lambda: [60.0, 300.0, 3600.0])
    max_files_per_kind: int | None = None
    state_cols: list[str] | None = None


@dataclass
class LiveSummaryResult:
    """Summary returned by :func:`summarize_live_archive`."""

    archive_root: str
    outdir: str
    n_summary_files: int
    summary_files: list[str]


def summarize_live_archive(config: LiveSummaryConfig, *, config_path: str | Path | None = None) -> LiveSummaryResult:
    """Build compact windowed summary tables from an archive."""

    outdir = Path(config.outdir or Path(config.archive_root) / "summaries")
    outdir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    for window in config.windows_seconds:
        suffix = _window_label(window)
        cleaned = load_archive_kind(config.archive_root, "cleaned_stream", max_files=config.max_files_per_kind)
        if not cleaned.empty:
            summary = summarize_wide_numeric(cleaned, window_seconds=window, preferred_cols=config.state_cols)
            path = outdir / f"state_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
        estimates = load_archive_kind(config.archive_root, "state_estimates", max_files=config.max_files_per_kind)
        if not estimates.empty:
            summary = summarize_long_state_values(estimates, window_seconds=window, value_col="estimated_value")
            path = outdir / f"state_estimate_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
        residuals = load_archive_kind(config.archive_root, "residuals", max_files=config.max_files_per_kind)
        if not residuals.empty:
            summary = summarize_residuals(residuals, window_seconds=window)
            path = outdir / f"residual_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
        corrected = load_archive_kind(config.archive_root, "bias_corrected_residuals", max_files=config.max_files_per_kind)
        if not corrected.empty:
            summary = summarize_residuals(corrected, window_seconds=window, residual_col="bias_corrected_residual", abs_col="abs_bias_corrected_residual")
            path = outdir / f"bias_corrected_residual_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
        trust = load_archive_kind(config.archive_root, "trust_score", max_files=config.max_files_per_kind)
        if not trust.empty:
            summary = summarize_trust(trust, window_seconds=window)
            path = outdir / f"trust_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
        bias = load_archive_kind(config.archive_root, "bias_state_timeseries", max_files=config.max_files_per_kind)
        if not bias.empty:
            summary = summarize_bias(bias, window_seconds=window)
            path = outdir / f"bias_summary_{suffix}.csv"
            summary.to_csv(path, index=False)
            files.append(str(path))
    alerts = load_archive_kind(config.archive_root, "alerts", max_files=config.max_files_per_kind)
    if not alerts.empty:
        path = outdir / "alert_summary.csv"
        summarize_alerts(alerts).to_csv(path, index=False)
        files.append(str(path))
    result = LiveSummaryResult(config.archive_root, str(outdir), len(files), files)
    (outdir / "summary_manifest.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    write_provenance(outdir, config_path=config_path, extra={"command": "archive-summarize", "result": asdict(result)})
    return result


def summarize_wide_numeric(df: pd.DataFrame, *, window_seconds: float, preferred_cols: list[str] | None = None) -> pd.DataFrame:
    time_col = infer_time_column(df, "cleaned_stream") or "time"
    if time_col not in df.columns:
        return pd.DataFrame()
    numeric_cols = preferred_cols or [c for c in df.columns if c not in {time_col, "case_id"} and pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce"))]
    rows: list[dict[str, Any]] = []
    bins = _window_bins(df[time_col], window_seconds)
    for state in numeric_cols:
        if state not in df.columns:
            continue
        values = pd.to_numeric(df[state], errors="coerce")
        tmp = pd.DataFrame({"window_start": bins, "value": values})
        for w, g in tmp.groupby("window_start", dropna=False):
            rows.append(_numeric_summary_row(w, state, g["value"], prefix="state"))
    return pd.DataFrame(rows)


def summarize_long_state_values(df: pd.DataFrame, *, window_seconds: float, value_col: str) -> pd.DataFrame:
    if value_col not in df.columns or "state" not in df.columns:
        return pd.DataFrame()
    time_col = infer_time_column(df, "state_estimates") or "time"
    bins = _window_bins(df[time_col], window_seconds) if time_col in df.columns else pd.Series([0.0] * len(df))
    tmp = df.copy()
    tmp["window_start"] = bins
    rows: list[dict[str, Any]] = []
    for (w, state), g in tmp.groupby(["window_start", "state"], dropna=False):
        rows.append(_numeric_summary_row(w, state, pd.to_numeric(g[value_col], errors="coerce"), prefix="state"))
    return pd.DataFrame(rows)


def summarize_residuals(df: pd.DataFrame, *, window_seconds: float, residual_col: str = "residual", abs_col: str = "abs_residual") -> pd.DataFrame:
    if "state" not in df.columns:
        return pd.DataFrame()
    if abs_col not in df.columns and residual_col in df.columns:
        df = df.copy()
        df[abs_col] = pd.to_numeric(df[residual_col], errors="coerce").abs()
    time_col = infer_time_column(df, "residuals") or "matched_time"
    bins = _window_bins(df[time_col], window_seconds) if time_col in df.columns else pd.Series([0.0] * len(df))
    tmp = df.copy()
    tmp["window_start"] = bins
    rows: list[dict[str, Any]] = []
    for (w, state), g in tmp.groupby(["window_start", "state"], dropna=False):
        residual = pd.to_numeric(g.get(residual_col), errors="coerce") if residual_col in g else pd.Series(dtype=float)
        abs_resid = pd.to_numeric(g.get(abs_col), errors="coerce") if abs_col in g else residual.abs()
        rows.append(
            {
                "window_start": w,
                "state": state,
                "n": int(abs_resid.notna().sum()),
                "rmse": float(np.sqrt(np.nanmean(np.square(residual)))) if residual.notna().any() else np.nan,
                "mae": float(np.nanmean(abs_resid)) if abs_resid.notna().any() else np.nan,
                "max_abs": float(np.nanmax(abs_resid)) if abs_resid.notna().any() else np.nan,
                "bias_mean": float(np.nanmean(residual)) if residual.notna().any() else np.nan,
                "p95_abs": float(np.nanpercentile(abs_resid.dropna(), 95)) if abs_resid.notna().any() else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize_trust(df: pd.DataFrame, *, window_seconds: float) -> pd.DataFrame:
    if "trust_score" not in df.columns:
        return pd.DataFrame()
    time_col = infer_time_column(df, "trust_score") or "time"
    bins = _window_bins(df[time_col], window_seconds) if time_col in df.columns else pd.Series([0.0] * len(df))
    tmp = pd.DataFrame({"window_start": bins, "trust_score": pd.to_numeric(df["trust_score"], errors="coerce")})
    rows = []
    for w, g in tmp.groupby("window_start", dropna=False):
        vals = g["trust_score"].dropna()
        rows.append({"window_start": w, "n": int(len(vals)), "mean": vals.mean() if len(vals) else np.nan, "min": vals.min() if len(vals) else np.nan, "p05": np.percentile(vals, 5) if len(vals) else np.nan, "time_below_0p5_samples": int((vals < 0.5).sum())})
    return pd.DataFrame(rows)


def summarize_bias(df: pd.DataFrame, *, window_seconds: float) -> pd.DataFrame:
    if "state" not in df.columns or "bias_value" not in df.columns:
        return pd.DataFrame()
    time_col = infer_time_column(df, "bias_state_timeseries") or "time"
    bins = _window_bins(df[time_col], window_seconds) if time_col in df.columns else pd.Series([0.0] * len(df))
    tmp = df.copy()
    tmp["window_start"] = bins
    rows = []
    for (w, state), g in tmp.groupby(["window_start", "state"], dropna=False):
        vals = pd.to_numeric(g["bias_value"], errors="coerce").dropna()
        rows.append({"window_start": w, "state": state, "n": int(len(vals)), "mean_bias": vals.mean() if len(vals) else np.nan, "last_bias": vals.iloc[-1] if len(vals) else np.nan, "max_abs_bias": vals.abs().max() if len(vals) else np.nan})
    return pd.DataFrame(rows)


def summarize_alerts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [c for c in ["severity", "code"] if c in df.columns]
    if not group_cols:
        return pd.DataFrame({"alert_count": [len(df)]})
    return df.groupby(group_cols, dropna=False).size().reset_index(name="alert_count").sort_values("alert_count", ascending=False)


def _window_bins(series: pd.Series, window_seconds: float) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    return np.floor(values / float(window_seconds)) * float(window_seconds)


def _numeric_summary_row(window_start: Any, state: Any, values: pd.Series, *, prefix: str) -> dict[str, Any]:
    vals = pd.to_numeric(values, errors="coerce")
    clean = vals.dropna()
    return {
        "window_start": window_start,
        prefix: state,
        "n": int(len(clean)),
        "missing_fraction": float(vals.isna().mean()) if len(vals) else 0.0,
        "mean": float(clean.mean()) if len(clean) else np.nan,
        "std": float(clean.std(ddof=0)) if len(clean) else np.nan,
        "min": float(clean.min()) if len(clean) else np.nan,
        "max": float(clean.max()) if len(clean) else np.nan,
        "median": float(clean.median()) if len(clean) else np.nan,
        "p05": float(np.percentile(clean, 5)) if len(clean) else np.nan,
        "p95": float(np.percentile(clean, 95)) if len(clean) else np.nan,
        "last": float(clean.iloc[-1]) if len(clean) else np.nan,
    }


def _window_label(seconds: float) -> str:
    if float(seconds).is_integer():
        return f"{int(seconds)}s"
    return f"{seconds:g}s".replace(".", "p")
