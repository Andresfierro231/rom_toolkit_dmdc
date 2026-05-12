"""Live Phase-5 Streamlit dashboard helpers.

This module is intentionally split into two layers:

1. **Pure Python data-loading helpers** that read the CSV outputs produced by
   Live Phases 1--4.  These helpers are dependency-light and are covered by
   pytest.  They make it easy for the rest of the repo, reports, or future
   dashboards to reuse the same live-run summary logic.

2. **A Streamlit app** that is imported lazily only when a user launches
   ``dmdc live-dashboard``.  Streamlit and Plotly are optional dependencies
   because the core ROM library should remain usable on servers and clusters
   that do not have dashboard packages installed.

The dashboard is read-only.  It never trains a model, never sends commands to
hardware, and never changes the live-run output directory.  It simply watches a
folder such as ``outputs/live_monitoring`` and renders the CSV logs written by
``dmdc live-replay-monitor`` or ``dmdc live-run-monitor``.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import subprocess
import sys

import numpy as np
import pandas as pd

from .live_archive import read_archive_manifest
from .operator_schematic import build_sensor_status_table, summarize_sensor_status


LIVE_DASHBOARD_TABLES: dict[str, str] = {
    "cleaned": "cleaned_stream_log.csv",
    "raw": "raw_stream_log.csv",
    "states": "live_state_estimates.csv",
    "modal": "live_modal_estimates.csv",
    "covariance": "live_estimate_covariance.csv",
    "innovations": "live_kalman_innovations.csv",
    "forecasts": "live_forecasts.csv",
    "forecasts_wide": "live_forecasts_wide.csv",
    "residuals": "live_forecast_residuals.csv",
    "alerts": "live_alerts.csv",
    "trust": "live_trust_score.csv",
    "warnings": "live_warnings.csv",
    "bias_events": "live_bias_update_events.csv",
    "bias_state": "live_bias_state_timeseries.csv",
    "bias_horizon": "live_bias_horizon_timeseries.csv",
    "bias_summary_state": "live_bias_summary_by_state.csv",
    "bias_summary_horizon": "live_bias_summary_by_horizon.csv",
    "bias_corrected_forecasts": "live_bias_corrected_forecasts.csv",
    "bias_corrected_residuals": "live_bias_corrected_forecast_residuals.csv",
    "bias_error_comparison": "live_bias_error_comparison.csv",
}


@dataclass
class LiveDashboardSummary:
    """Small, JSON-friendly summary displayed at the top of the dashboard."""

    run_dir: str
    status: str
    latest_time: float | None
    n_clean_samples: int
    n_state_estimates: int
    n_forecast_rows: int
    n_residual_rows: int
    n_alerts: int
    n_warning_alerts: int
    n_critical_alerts: int
    n_bias_update_events: int
    n_bias_updates_accepted: int
    latest_trust_score: float | None
    min_trust_score: float | None
    available_states: list[str]
    available_measurements: list[str]
    forecast_horizons_seconds: list[float]
    missing_tables: list[str]
    model_registry_name: str | None = None
    model_stage: str | None = None
    model_version: str | None = None
    model_path: str | None = None


@dataclass
class ArchiveDashboardSummary:
    """Small summary for long-term archive dashboard mode.

    Archive mode is intentionally summary-first.  It reads the manifest,
    windowed summary CSVs, alert summaries, and quicklook metadata without
    loading raw terabyte-scale stream files into memory.
    """

    archive_root: str
    status: str
    manifest_rows: int
    data_kinds: list[str]
    run_ids: list[str]
    n_summary_files: int
    n_quicklook_plots: int
    latest_window_start: float | None
    latest_mean_trust: float | None
    min_trust: float | None
    n_alert_summary_rows: int
    n_alerts_reported: int
    total_archived_rows: int
    total_archived_bytes: int
    window_label: str
    missing_summary_tables: list[str]



def read_live_dashboard_tables(run_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Read all known Live Phase 1--4 tables from ``run_dir``.

    Missing files are represented by empty data frames rather than exceptions.
    This is important for usability: users may open the dashboard while a live
    run is still starting, or they may point it at a Phase-2 prediction folder
    that does not contain Phase-4 alert tables yet.
    """

    root = Path(run_dir)
    tables: dict[str, pd.DataFrame] = {}
    for key, filename in LIVE_DASHBOARD_TABLES.items():
        path = root / filename
        if path.exists() and path.stat().st_size > 0:
            try:
                tables[key] = pd.read_csv(path)
            except Exception:
                tables[key] = pd.DataFrame()
        else:
            tables[key] = pd.DataFrame()
    return tables


def infer_time_column(tables: dict[str, pd.DataFrame], preferred: str | None = None) -> str | None:
    """Infer the physical-time column used by a live run.

    Most repo examples use ``time``.  The helper also recognizes common names so
    the dashboard works with current-data CSVs without requiring users to edit
    code.
    """

    candidates = [preferred, "time", "Time", "t", "seconds", "s"]
    for candidate in candidates:
        if not candidate:
            continue
        for df in tables.values():
            if candidate in df.columns:
                return str(candidate)
    return None


def infer_state_columns(tables: dict[str, pd.DataFrame], time_col: str | None = None) -> list[str]:
    """Infer full-state columns from live state estimates or cleaned stream logs."""

    # Prefer the Phase-3/4 state-estimate table, because it contains the full
    # reconstructed state even if the stream only measured a sparse subset.
    for key in ("states", "cleaned"):
        df = tables.get(key, pd.DataFrame())
        if df.empty:
            continue
        ignore = {
            time_col,
            "origin_time",
            "origin_row_index",
            "received_utc",
            "model_type",
            "_received_utc",
            "_stream_row_index",
            "case_id",
        }
        cols = [c for c in df.columns if c not in ignore and pd.api.types.is_numeric_dtype(df[c])]
        if cols:
            return cols
    # Fall back to state names appearing in long-form forecast/residual tables.
    states: set[str] = set()
    for key in ("forecasts", "residuals"):
        df = tables.get(key, pd.DataFrame())
        if not df.empty and "state" in df.columns:
            states.update(str(s) for s in df["state"].dropna().unique())
    return sorted(states)


def infer_measurement_columns(tables: dict[str, pd.DataFrame], time_col: str | None = None) -> list[str]:
    """Infer measured sensor columns from the cleaned live stream."""

    clean = tables.get("cleaned", pd.DataFrame())
    if clean.empty:
        return []
    ignore = {time_col, "_received_utc", "_stream_row_index", "case_id"}
    return [c for c in clean.columns if c not in ignore and pd.api.types.is_numeric_dtype(clean[c])]


def read_model_identity(run_dir: str | Path) -> dict[str, Any]:
    """Read model identity metadata for dashboard display."""
    path = Path(run_dir) / "model_identity.json"
    if path.exists() and path.stat().st_size > 0:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}
    return {}


def summarize_live_dashboard(run_dir: str | Path, *, time_col: str | None = None) -> LiveDashboardSummary:
    """Build the top-level dashboard summary for a live output folder."""

    root = Path(run_dir)
    tables = read_live_dashboard_tables(root)
    inferred_time = infer_time_column(tables, preferred=time_col)
    missing = [filename for key, filename in LIVE_DASHBOARD_TABLES.items() if tables[key].empty]

    clean = tables["cleaned"]
    states = tables["states"]
    forecasts = tables["forecasts"]
    residuals = tables["residuals"]
    alerts = tables["alerts"]
    trust = tables["trust"]
    bias_events = tables.get("bias_events", pd.DataFrame())

    latest_time: float | None = None
    if inferred_time and not clean.empty and inferred_time in clean.columns:
        numeric_time = pd.to_numeric(clean[inferred_time], errors="coerce").dropna()
        if len(numeric_time):
            latest_time = float(numeric_time.iloc[-1])

    if not trust.empty and "trust_score" in trust.columns:
        trust_values = pd.to_numeric(trust["trust_score"], errors="coerce").dropna()
        latest_trust = float(trust_values.iloc[-1]) if len(trust_values) else None
        min_trust = float(trust_values.min()) if len(trust_values) else None
    else:
        latest_trust = None
        min_trust = None

    if not alerts.empty and "severity" in alerts.columns:
        severity = alerts["severity"].astype(str).str.lower()
        n_warning = int((severity == "warning").sum())
        n_critical = int((severity == "critical").sum())
    else:
        n_warning = 0
        n_critical = 0

    if not bias_events.empty and "accepted" in bias_events.columns:
        n_bias_events = int(len(bias_events))
        n_bias_accepted = int(bias_events["accepted"].astype(bool).sum())
    else:
        n_bias_events = 0
        n_bias_accepted = 0

    horizons: list[float] = []
    if not forecasts.empty and "forecast_horizon_s" in forecasts.columns:
        horizons = sorted(
            float(v)
            for v in pd.to_numeric(forecasts["forecast_horizon_s"], errors="coerce").dropna().unique()
        )

    identity = read_model_identity(root)

    status = "healthy"
    if n_critical > 0 or (latest_trust is not None and latest_trust < 0.5):
        status = "critical"
    elif n_warning > 0 or (latest_trust is not None and latest_trust < 0.8):
        status = "warning"
    elif clean.empty and forecasts.empty and states.empty:
        status = "empty"

    return LiveDashboardSummary(
        run_dir=str(root),
        status=status,
        latest_time=latest_time,
        n_clean_samples=int(len(clean)),
        n_state_estimates=int(len(states)),
        n_forecast_rows=int(len(forecasts)),
        n_residual_rows=int(len(residuals)),
        n_alerts=int(len(alerts)),
        n_warning_alerts=n_warning,
        n_critical_alerts=n_critical,
        n_bias_update_events=n_bias_events,
        n_bias_updates_accepted=n_bias_accepted,
        latest_trust_score=latest_trust,
        min_trust_score=min_trust,
        available_states=infer_state_columns(tables, inferred_time),
        available_measurements=infer_measurement_columns(tables, inferred_time),
        forecast_horizons_seconds=horizons,
        missing_tables=missing,
        model_registry_name=identity.get("registry_name"),
        model_stage=identity.get("stage"),
        model_version=identity.get("version"),
        model_path=identity.get("model_path"),
    )


def read_archive_dashboard_tables(archive_root: str | Path, *, window_label: str = "60s") -> dict[str, pd.DataFrame]:
    """Read lightweight archive-dashboard inputs.

    This function deliberately avoids loading raw archived stream partitions.
    It reads only:

    - ``manifest.csv`` for what exists in the archive,
    - summary CSVs created by ``dmdc archive-summarize``,
    - quicklook metadata created by ``dmdc archive-quicklook``.

    That makes the dashboard usable for month-scale archives where raw files can
    be many gigabytes or terabytes.
    """

    root = Path(archive_root)
    summaries = root / "summaries"
    tables: dict[str, pd.DataFrame] = {"manifest": read_archive_manifest(root)}
    summary_files = {
        "state_summary": summaries / f"state_summary_{window_label}.csv",
        "state_estimate_summary": summaries / f"state_estimate_summary_{window_label}.csv",
        "residual_summary": summaries / f"residual_summary_{window_label}.csv",
        "bias_corrected_residual_summary": summaries / f"bias_corrected_residual_summary_{window_label}.csv",
        "trust_summary": summaries / f"trust_summary_{window_label}.csv",
        "bias_summary": summaries / f"bias_summary_{window_label}.csv",
        "alert_summary": summaries / "alert_summary.csv",
    }
    for key, path in summary_files.items():
        if path.exists() and path.stat().st_size > 0:
            try:
                tables[key] = pd.read_csv(path)
            except Exception:
                tables[key] = pd.DataFrame()
        else:
            tables[key] = pd.DataFrame()
    qmanifest = root / "quicklooks" / "quicklook_manifest.json"
    if qmanifest.exists():
        try:
            payload = json.loads(qmanifest.read_text(encoding="utf-8"))
            plots = payload.get("plots", []) if isinstance(payload, dict) else []
            tables["quicklooks"] = pd.DataFrame({"plot_path": plots})
        except Exception:
            tables["quicklooks"] = pd.DataFrame()
    else:
        tables["quicklooks"] = pd.DataFrame()
    return tables


def summarize_archive_dashboard(archive_root: str | Path, *, window_label: str = "60s") -> ArchiveDashboardSummary:
    """Build a summary for long-term archive dashboard mode."""

    root = Path(archive_root)
    tables = read_archive_dashboard_tables(root, window_label=window_label)
    manifest = tables["manifest"]
    missing = [k for k, df in tables.items() if k != "manifest" and df.empty]

    data_kinds: list[str] = []
    run_ids: list[str] = []
    total_rows = 0
    total_bytes = 0
    if not manifest.empty:
        if "data_kind" in manifest.columns:
            data_kinds = sorted(str(v) for v in manifest["data_kind"].dropna().unique())
        if "run_id" in manifest.columns:
            run_ids = sorted(str(v) for v in manifest["run_id"].dropna().unique())
        if "n_rows" in manifest.columns:
            total_rows = int(pd.to_numeric(manifest["n_rows"], errors="coerce").fillna(0).sum())
        if "file_size_bytes" in manifest.columns:
            total_bytes = int(pd.to_numeric(manifest["file_size_bytes"], errors="coerce").fillna(0).sum())

    trust = tables.get("trust_summary", pd.DataFrame())
    latest_window: float | None = None
    latest_mean_trust: float | None = None
    min_trust: float | None = None
    if not trust.empty:
        if "window_start" in trust.columns:
            ws = pd.to_numeric(trust["window_start"], errors="coerce").dropna()
            latest_window = float(ws.max()) if len(ws) else None
        if "mean" in trust.columns:
            vals = pd.to_numeric(trust["mean"], errors="coerce").dropna()
            latest_mean_trust = float(vals.iloc[-1]) if len(vals) else None
        if "min" in trust.columns:
            vals = pd.to_numeric(trust["min"], errors="coerce").dropna()
            min_trust = float(vals.min()) if len(vals) else None

    alerts = tables.get("alert_summary", pd.DataFrame())
    n_alert_summary_rows = int(len(alerts))
    n_alerts_reported = 0
    if not alerts.empty:
        count_cols = [c for c in ["alert_count", "count", "n"] if c in alerts.columns]
        if count_cols:
            n_alerts_reported = int(pd.to_numeric(alerts[count_cols[0]], errors="coerce").fillna(0).sum())
        else:
            n_alerts_reported = int(len(alerts))

    n_summary_files = sum(1 for k, df in tables.items() if k not in {"manifest", "quicklooks"} and not df.empty)
    n_quicklook_plots = int(len(tables.get("quicklooks", pd.DataFrame())))
    identity = read_model_identity(root)

    status = "healthy"
    if manifest.empty:
        status = "empty"
    elif min_trust is not None and min_trust < 0.5:
        status = "critical"
    elif n_alerts_reported > 0 or (min_trust is not None and min_trust < 0.8):
        status = "warning"

    return ArchiveDashboardSummary(
        archive_root=str(root),
        status=status,
        manifest_rows=int(len(manifest)),
        data_kinds=data_kinds,
        run_ids=run_ids,
        n_summary_files=n_summary_files,
        n_quicklook_plots=n_quicklook_plots,
        latest_window_start=latest_window,
        latest_mean_trust=latest_mean_trust,
        min_trust=min_trust,
        n_alert_summary_rows=n_alert_summary_rows,
        n_alerts_reported=n_alerts_reported,
        total_archived_rows=total_rows,
        total_archived_bytes=total_bytes,
        window_label=str(window_label),
        missing_summary_tables=missing,
    )


def write_archive_dashboard_summary(archive_root: str | Path, *, window_label: str = "60s") -> Path:
    """Write ``archive_dashboard_summary.json`` for archive dashboard mode."""

    root = Path(archive_root)
    root.mkdir(parents=True, exist_ok=True)
    summary = summarize_archive_dashboard(root, window_label=window_label)
    path = root / "archive_dashboard_summary.json"
    path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return path



def write_dashboard_summary(run_dir: str | Path, *, time_col: str | None = None) -> Path:
    """Write ``live_dashboard_summary.json`` for reports and smoke tests."""

    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = summarize_live_dashboard(root, time_col=time_col)
    path = root / "live_dashboard_summary.json"
    path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return path


def launch_streamlit_dashboard(
    *,
    run_dir: str | Path | None = None,
    archive_root: str | Path | None = None,
    mode: str = "auto",
    window_label: str = "60s",
    refresh_seconds: float = 2.0,
    host: str | None = None,
    port: int | None = None,
    theme: str | None = None,
    view: str = "operator",
    geometry_path: str | None = None,
    residual_warning_threshold: float = 2.0,
    residual_critical_threshold: float = 5.0,
) -> int:
    """Launch the Streamlit dashboard as a subprocess.

    The actual app lives in this module.  Calling Streamlit through
    ``python -m streamlit run`` is the most reliable way to get Streamlit's
    runtime context, file watcher, and browser integration.
    """

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(Path(__file__).resolve()),
    ]
    if host:
        cmd += ["--server.address", str(host)]
    if port is not None:
        cmd += ["--server.port", str(int(port))]
    cmd += [
        "--",
        "--run-dir",
        str(run_dir or "outputs/live_monitoring"),
        "--refresh-seconds",
        str(float(refresh_seconds)),
    ]
    if archive_root is not None:
        cmd += ["--archive-root", str(archive_root)]
    if mode:
        cmd += ["--mode", str(mode)]
    if window_label:
        cmd += ["--window-label", str(window_label)]
    if theme:
        cmd += ["--theme", theme]
    if view:
        cmd += ["--view", str(view)]
    if geometry_path:
        cmd += ["--geometry", str(geometry_path)]
    cmd += ["--residual-warning-threshold", str(float(residual_warning_threshold))]
    cmd += ["--residual-critical-threshold", str(float(residual_critical_threshold))]
    return subprocess.call(cmd)


# ---------------------------------------------------------------------------
# Streamlit application code
# ---------------------------------------------------------------------------

def _require_streamlit_and_plotly():
    """Import optional dashboard dependencies with a clear error message."""

    try:
        import streamlit as st  # type: ignore[import-not-found]
        import plotly.express as px  # type: ignore[import-not-found]
        import plotly.graph_objects as go  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError(
            "The live dashboard requires optional dashboard dependencies. Install with:\n"
            "    python -m pip install -e '.[dashboard]'\n"
            "or install streamlit and plotly manually."
        ) from exc
    return st, px, go


def _plot_state_history(st: Any, px: Any, tables: dict[str, pd.DataFrame], time_col: str | None, states: list[str]) -> None:
    """Render measured and estimated states with interactive Plotly lines."""

    st.subheader("State history: measured stream and estimated full state")
    clean = tables.get("cleaned", pd.DataFrame())
    estimates = tables.get("states", pd.DataFrame())
    if not time_col:
        st.info("No time column detected yet. The dashboard will populate once live data includes time stamps.")
        return

    selected = st.multiselect("States/sensors to plot", options=states, default=states[: min(4, len(states))])
    if not selected:
        st.info("Select at least one state to plot.")
        return

    plot_frames: list[pd.DataFrame] = []
    if not clean.empty and time_col in clean.columns:
        meas_cols = [c for c in selected if c in clean.columns]
        if meas_cols:
            tmp = clean[[time_col] + meas_cols].melt(id_vars=time_col, var_name="state", value_name="value")
            tmp["source"] = "measured stream"
            plot_frames.append(tmp)
    est_time_col = "origin_time" if "origin_time" in estimates.columns else time_col
    if not estimates.empty and est_time_col in estimates.columns:
        est_cols = [c for c in selected if c in estimates.columns]
        if est_cols:
            tmp = estimates[[est_time_col] + est_cols].rename(columns={est_time_col: time_col})
            tmp = tmp.melt(id_vars=time_col, var_name="state", value_name="value")
            tmp["source"] = "Kalman/full-state estimate"
            plot_frames.append(tmp)
    if not plot_frames:
        st.info("No measured or estimated state columns available yet.")
        return
    plot_df = pd.concat(plot_frames, ignore_index=True).dropna(subset=["value"])
    fig = px.line(
        plot_df,
        x=time_col,
        y="value",
        color="state",
        line_dash="source",
        markers=False,
        title="Measured vs. estimated state history",
    )
    fig.update_layout(hovermode="x unified", legend_title_text="State / source")
    st.plotly_chart(fig, use_container_width=True)


def _plot_forecasts(st: Any, px: Any, tables: dict[str, pd.DataFrame], states: list[str]) -> None:
    """Render live forecast trajectories by state and horizon."""

    st.subheader("Forecasts")
    forecasts = tables.get("forecasts", pd.DataFrame())
    if forecasts.empty:
        st.info("No forecast rows yet. Run live-replay-predict, live-run-predict, live-replay-estimate, or live-replay-monitor.")
        return
    if "state" not in forecasts.columns or "predicted_value" not in forecasts.columns:
        st.warning("Forecast file exists but does not have the expected long-form columns.")
        st.dataframe(forecasts.tail(20), use_container_width=True)
        return
    state_options = sorted(str(s) for s in forecasts["state"].dropna().unique()) or states
    selected_state = st.selectbox("Forecast state", options=state_options, index=0)
    df = forecasts[forecasts["state"].astype(str) == selected_state].copy()
    x_col = "target_time" if "target_time" in df.columns and df["target_time"].notna().any() else "origin_time"
    if x_col not in df.columns:
        st.dataframe(df.tail(50), use_container_width=True)
        return
    color = "forecast_horizon_s" if "forecast_horizon_s" in df.columns else None
    fig = px.line(
        df,
        x=x_col,
        y="predicted_value",
        color=color,
        markers=False,
        title=f"Forecast values for {selected_state}",
    )
    fig.update_layout(hovermode="x unified", legend_title_text="Horizon [s]")
    st.plotly_chart(fig, use_container_width=True)


def _plot_residuals(st: Any, px: Any, tables: dict[str, pd.DataFrame]) -> None:
    """Render forecast residual diagnostics."""

    st.subheader("Forecast residuals")
    residuals = tables.get("residuals", pd.DataFrame())
    if residuals.empty:
        st.info("No matched forecast residuals yet. Phase-4 monitor creates these after forecasts mature.")
        return
    if {"matched_time", "abs_residual", "state"}.issubset(residuals.columns):
        selected_states = st.multiselect(
            "Residual states",
            options=sorted(str(s) for s in residuals["state"].dropna().unique()),
            default=sorted(str(s) for s in residuals["state"].dropna().unique())[:4],
        )
        df = residuals[residuals["state"].astype(str).isin(selected_states)] if selected_states else residuals
        fig = px.line(
            df,
            x="matched_time",
            y="abs_residual",
            color="state",
            markers=True,
            title="Absolute forecast residual by state",
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    if {"state", "abs_residual"}.issubset(residuals.columns):
        summary = (
            residuals.groupby("state", as_index=False)["abs_residual"]
            .agg(["mean", "max", "count"])
            .reset_index()
            .sort_values("max", ascending=False)
        )
        st.dataframe(summary, use_container_width=True)


def _plot_trust_and_alerts(st: Any, px: Any, tables: dict[str, pd.DataFrame]) -> None:
    """Render trust-score timeline and alert table."""

    st.subheader("Trust score and alerts")
    trust = tables.get("trust", pd.DataFrame())
    alerts = tables.get("alerts", pd.DataFrame())
    col1, col2 = st.columns([2, 3])
    with col1:
        if not trust.empty and "trust_score" in trust.columns:
            x_col = "time" if "time" in trust.columns else trust.columns[0]
            fig = px.line(trust, x=x_col, y="trust_score", markers=True, title="Model trust score")
            fig.update_yaxes(range=[0, 1.05])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trust score file yet.")
    with col2:
        if not alerts.empty:
            show = alerts.tail(100).copy()
            # Put the most operator-relevant columns first when present.
            priority = ["time", "severity", "code", "state", "value", "threshold", "message", "suggested_action"]
            cols = [c for c in priority if c in show.columns] + [c for c in show.columns if c not in priority]
            st.dataframe(show[cols], use_container_width=True, height=350)
        else:
            st.success("No alerts recorded in this run folder.")


def _plot_kalman(st: Any, px: Any, tables: dict[str, pd.DataFrame]) -> None:
    """Render Kalman innovations and covariance diagnostics."""

    st.subheader("Kalman diagnostics")
    innovations = tables.get("innovations", pd.DataFrame())
    covariance = tables.get("covariance", pd.DataFrame())
    col1, col2 = st.columns(2)
    with col1:
        if not innovations.empty:
            value_col = "innovation" if "innovation" in innovations.columns else None
            time_col = "time" if "time" in innovations.columns else "origin_time" if "origin_time" in innovations.columns else None
            if value_col and time_col and "measurement" in innovations.columns:
                fig = px.line(
                    innovations,
                    x=time_col,
                    y=value_col,
                    color="measurement",
                    markers=True,
                    title="Kalman innovation by measurement",
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(innovations.tail(50), use_container_width=True)
        else:
            st.info("No Kalman innovation table yet.")
    with col2:
        if not covariance.empty:
            if "covariance_trace" in covariance.columns:
                time_col = "time" if "time" in covariance.columns else covariance.columns[0]
                fig = px.line(covariance, x=time_col, y="covariance_trace", markers=True, title="POD-state covariance trace")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.dataframe(covariance.tail(50), use_container_width=True)
        else:
            st.info("No covariance table yet.")



def _plot_adaptation(st: Any, px: Any, tables: dict[str, pd.DataFrame]) -> None:
    """Render Phase-6.1 bias-correction diagnostics."""

    st.subheader("Bias correction / online adaptation")
    events = tables.get("bias_events", pd.DataFrame())
    bias_state = tables.get("bias_state", pd.DataFrame())
    comparison = tables.get("bias_error_comparison", pd.DataFrame())
    corrected = tables.get("bias_corrected_residuals", pd.DataFrame())

    if events.empty and bias_state.empty:
        st.info("No bias-correction tables found yet. Run `dmdc live-replay-adapt` or `dmdc live-run-adapt`.")
        return

    c1, c2, c3, c4 = st.columns(4)
    n_events = len(events) if not events.empty else 0
    n_accepted = int(events["accepted"].astype(bool).sum()) if not events.empty and "accepted" in events.columns else 0
    max_bias = float(pd.to_numeric(events.get("new_bias", pd.Series(dtype=float)), errors="coerce").abs().max()) if not events.empty and "new_bias" in events.columns else 0.0
    c1.metric("Bias events", n_events)
    c2.metric("Accepted", n_accepted)
    c3.metric("Skipped", n_events - n_accepted)
    c4.metric("Max |bias|", f"{max_bias:.3g}")

    if not bias_state.empty and {"time", "bias_value", "state"}.issubset(bias_state.columns):
        selected_states = st.multiselect(
            "Bias states",
            options=sorted(str(s) for s in bias_state["state"].dropna().unique()),
            default=sorted(str(s) for s in bias_state["state"].dropna().unique())[:6],
        )
        df = bias_state[bias_state["state"].astype(str).isin(selected_states)] if selected_states else bias_state
        color = "state"
        line_dash = "forecast_horizon_s" if "forecast_horizon_s" in df.columns else None
        fig = px.line(df, x="time", y="bias_value", color=color, line_dash=line_dash, markers=True, title="Learned bias over time")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    if not comparison.empty:
        st.markdown("**Raw vs bias-corrected residual comparison**")
        st.dataframe(comparison, use_container_width=True)
        if {"state", "raw_mean_abs_residual", "corrected_mean_abs_residual"}.issubset(comparison.columns):
            melted = comparison.melt(
                id_vars=[c for c in ["state", "forecast_horizon_s"] if c in comparison.columns],
                value_vars=["raw_mean_abs_residual", "corrected_mean_abs_residual"],
                var_name="series",
                value_name="mean_abs_residual",
            )
            fig = px.bar(melted, x="state", y="mean_abs_residual", color="series", barmode="group", facet_col="forecast_horizon_s" if "forecast_horizon_s" in melted.columns else None, title="Mean absolute residual before/after bias correction")
            st.plotly_chart(fig, use_container_width=True)

    if not corrected.empty:
        with st.expander("Bias-corrected residual rows", expanded=False):
            st.dataframe(corrected.tail(200), use_container_width=True)
    if not events.empty:
        with st.expander("Bias update audit log", expanded=False):
            priority = ["time", "state", "forecast_horizon_s", "old_bias", "new_bias", "raw_residual", "trust_score", "accepted", "rejection_reason"]
            cols = [c for c in priority if c in events.columns] + [c for c in events.columns if c not in priority]
            st.dataframe(events[cols].tail(300), use_container_width=True, height=400)



def _status_badge_markdown(status: str) -> str:
    """Return a simple HTML badge for executive/operator dashboard status."""

    colors = {"healthy": "#15803d", "warning": "#ca8a04", "critical": "#b91c1c", "empty": "#6b7280"}
    labels = {"healthy": "NOMINAL", "warning": "WATCH", "critical": "ATTENTION", "empty": "WAITING FOR DATA"}
    color = colors.get(status, "#6b7280")
    label = labels.get(status, status.upper())
    return f"<div style='padding:0.75rem 1rem;border-radius:0.75rem;background:{color};color:white;font-size:1.4rem;font-weight:700;text-align:center'>{label}</div>"



def _plot_operator_loop_schematic(
    st: Any,
    go: Any,
    tables: dict[str, pd.DataFrame],
    states: list[str],
    *,
    geometry_path: str | None = None,
    warning_threshold: float = 2.0,
    critical_threshold: float = 5.0,
) -> None:
    """Render a presentation-grade loop schematic colored by residual.

    The plot is deliberately simple: a one-dimensional loop coordinate with
    sensor markers colored green/yellow/red/gray.  Reviewers can immediately see
    which locations disagree with the live forecast without reading residual
    tables.
    """

    if not states:
        st.info("No state names are available yet for the loop schematic.")
        return
    residuals = tables.get("residuals", pd.DataFrame())
    cleaned = tables.get("cleaned", pd.DataFrame())
    status = build_sensor_status_table(
        state_names=states,
        residuals=residuals,
        cleaned_stream=cleaned,
        geometry_path=geometry_path,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
    )
    summary = summarize_sensor_status(
        status,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
        geometry_description=str(geometry_path or "auto geometry"),
    )
    st.markdown("### Loop schematic: sensors colored by latest forecast residual")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nominal", summary.n_nominal)
    c2.metric("Warning", summary.n_warning)
    c3.metric("Critical", summary.n_critical)
    c4.metric("Unknown", summary.n_unknown)
    if status.empty:
        st.info("No schematic status rows available.")
        return
    fig = go.Figure()
    x = status["position_m"].to_numpy(dtype=float)
    fig.add_trace(go.Scatter(
        x=[float(x.min()) if len(x) else 0.0, float(x.max()) if len(x) else 1.0],
        y=[0, 0],
        mode="lines",
        line=dict(color="#334155", width=3),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=status["position_m"],
        y=[0] * len(status),
        mode="markers+text",
        marker=dict(size=22, color=status["color"], line=dict(color="white", width=2)),
        text=status["state"],
        textposition="top center",
        customdata=np.stack([
            status["status"].astype(str),
            status["abs_residual"].fillna(np.nan),
            status["measurement_available"].astype(str),
        ], axis=-1),
        hovertemplate="Sensor=%{text}<br>Status=%{customdata[0]}<br>|residual|=%{customdata[1]:.4g}<br>Measured=%{customdata[2]}<extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Loop position [m] or display order",
        yaxis=dict(visible=False, range=[-0.25, 0.45]),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Loop schematic data", expanded=False):
        st.dataframe(status, use_container_width=True)


def _render_executive_run_view(
    st: Any,
    px: Any,
    go: Any,
    tables: dict[str, pd.DataFrame],
    summary: LiveDashboardSummary,
    *,
    geometry_path: str | None = None,
    residual_warning_threshold: float = 2.0,
    residual_critical_threshold: float = 5.0,
) -> None:
    """Render a concise, scrutiny-friendly operator/executive overview.

    This view is meant for meetings, demos, and non-specialist reviews.  It
    emphasizes current status, trust, alerts, forecast/residual health, and
    whether adaptation is improving errors.  Technical tables remain available
    in the detailed tabs below.
    """

    st.markdown(_status_badge_markdown(summary.status), unsafe_allow_html=True)
    if getattr(summary, "model_registry_name", None) or getattr(summary, "model_path", None):
        model_label = summary.model_registry_name or Path(str(summary.model_path)).name
        stage = f" ({summary.model_stage})" if summary.model_stage else ""
        version = f" v={summary.model_version}" if summary.model_version else ""
        st.info(f"Live model: **{model_label}**{stage}{version}")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Latest loop time", "—" if summary.latest_time is None else f"{summary.latest_time:.3g}")
    k2.metric("Trust score", "—" if summary.latest_trust_score is None else f"{summary.latest_trust_score:.2f}")
    k3.metric("Critical alerts", summary.n_critical_alerts)
    k4.metric("Warnings", summary.n_warning_alerts)
    k5.metric("Bias updates accepted", summary.n_bias_updates_accepted)

    st.markdown("### Operator view")
    _plot_operator_loop_schematic(
        st,
        go,
        tables,
        summary.available_states,
        geometry_path=geometry_path,
        warning_threshold=residual_warning_threshold,
        critical_threshold=residual_critical_threshold,
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        trust = tables.get("trust", pd.DataFrame())
        if not trust.empty and "trust_score" in trust.columns:
            x_col = "time" if "time" in trust.columns else trust.columns[0]
            fig = px.line(trust, x=x_col, y="trust_score", markers=True, title="Model trust score")
            fig.update_yaxes(range=[0, 1.05])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Trust score will appear after live monitoring starts.")
    with c2:
        alerts = tables.get("alerts", pd.DataFrame())
        if alerts.empty:
            st.success("No live alerts recorded.")
        else:
            priority = ["time", "severity", "code", "state", "message", "suggested_action"]
            cols = [c for c in priority if c in alerts.columns] + [c for c in alerts.columns if c not in priority]
            st.dataframe(alerts[cols].tail(10), use_container_width=True, height=330)

    residuals = tables.get("residuals", pd.DataFrame())
    if not residuals.empty and {"state", "abs_residual"}.issubset(residuals.columns):
        st.markdown("### Largest current forecast residuals")
        latest_col = "matched_time" if "matched_time" in residuals.columns else None
        df = residuals.copy()
        if latest_col:
            latest = pd.to_numeric(df[latest_col], errors="coerce").max()
            df = df[pd.to_numeric(df[latest_col], errors="coerce") == latest]
        top = df.sort_values("abs_residual", ascending=False).head(10)
        fig = px.bar(top, x="state", y="abs_residual", color="forecast_horizon_s" if "forecast_horizon_s" in top.columns else None, title="Top residuals at latest matched time")
        st.plotly_chart(fig, use_container_width=True)

    comparison = tables.get("bias_error_comparison", pd.DataFrame())
    if not comparison.empty and {"raw_mean_abs_residual", "corrected_mean_abs_residual"}.issubset(comparison.columns):
        st.markdown("### Bias correction effect")
        raw = pd.to_numeric(comparison["raw_mean_abs_residual"], errors="coerce").mean()
        cor = pd.to_numeric(comparison["corrected_mean_abs_residual"], errors="coerce").mean()
        delta = None if pd.isna(raw) or pd.isna(cor) else cor - raw
        st.metric("Mean absolute residual after correction", "—" if pd.isna(cor) else f"{cor:.3g}", delta=None if delta is None else f"{delta:+.3g}")


def _render_executive_archive_view(st: Any, px: Any, tables: dict[str, pd.DataFrame], summary: ArchiveDashboardSummary) -> None:
    """Render a high-level archive executive overview."""

    st.markdown(_status_badge_markdown(summary.status), unsafe_allow_html=True)
    if getattr(summary, "model_registry_name", None) or getattr(summary, "model_path", None):
        model_label = summary.model_registry_name or Path(str(summary.model_path)).name
        stage = f" ({summary.model_stage})" if summary.model_stage else ""
        version = f" v={summary.model_version}" if summary.model_version else ""
        st.info(f"Live model: **{model_label}**{stage}{version}")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Archived rows", f"{summary.total_archived_rows:,}")
    k2.metric("Data kinds", len(summary.data_kinds))
    k3.metric("Runs", len(summary.run_ids))
    k4.metric("Alerts", summary.n_alerts_reported)
    k5.metric("Min trust", "—" if summary.min_trust is None else f"{summary.min_trust:.2f}")

    c1, c2 = st.columns([3, 2])
    with c1:
        trust = tables.get("trust_summary", pd.DataFrame())
        if not trust.empty and "window_start" in trust.columns:
            y_cols = [c for c in ["mean", "min", "p05"] if c in trust.columns]
            if y_cols:
                fig = px.line(trust, x="window_start", y=y_cols, markers=True, title="Archive trust summary")
                fig.update_yaxes(range=[0, 1.05])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run archive-summarize to populate trust summaries.")
    with c2:
        alerts = tables.get("alert_summary", pd.DataFrame())
        if alerts.empty:
            st.success("No archived alert summary found.")
        else:
            st.dataframe(alerts.tail(20), use_container_width=True, height=350)


def _plot_archive_summaries(st: Any, px: Any, tables: dict[str, pd.DataFrame]) -> None:
    """Render archive summaries without loading raw partition files."""

    st.subheader("Summary-first archive plots")
    trust = tables.get("trust_summary", pd.DataFrame())
    residuals = tables.get("residual_summary", pd.DataFrame())
    bias = tables.get("bias_summary", pd.DataFrame())
    state = tables.get("state_summary", pd.DataFrame())

    if not trust.empty and "window_start" in trust.columns:
        y_cols = [c for c in ["mean", "min", "p05"] if c in trust.columns]
        if y_cols:
            fig = px.line(trust, x="window_start", y=y_cols, markers=True, title="Trust score summary")
            fig.update_yaxes(range=[0, 1.05])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trust summary found. Run `dmdc archive-summarize` first.")

    if not residuals.empty and {"window_start", "state"}.issubset(residuals.columns):
        y_col = "mae" if "mae" in residuals.columns else "rmse" if "rmse" in residuals.columns else None
        if y_col:
            states = sorted(str(s) for s in residuals["state"].dropna().unique())
            selected = st.multiselect("Residual summary states", states, default=states[: min(6, len(states))])
            df = residuals[residuals["state"].astype(str).isin(selected)] if selected else residuals
            fig = px.line(df, x="window_start", y=y_col, color="state", markers=False, title=f"Residual summary ({y_col})")
            st.plotly_chart(fig, use_container_width=True)

    if not bias.empty and {"window_start", "state"}.issubset(bias.columns):
        y_col = "last_bias" if "last_bias" in bias.columns else "mean_bias" if "mean_bias" in bias.columns else None
        if y_col:
            states = sorted(str(s) for s in bias["state"].dropna().unique())
            selected = st.multiselect("Bias summary states", states, default=states[: min(6, len(states))], key="archive_bias_states")
            df = bias[bias["state"].astype(str).isin(selected)] if selected else bias
            fig = px.line(df, x="window_start", y=y_col, color="state", markers=False, title="Bias correction summary")
            st.plotly_chart(fig, use_container_width=True)

    if not state.empty and "window_start" in state.columns:
        state_col = "state" if "state" in state.columns else "variable" if "variable" in state.columns else None
        if state_col and "mean" in state.columns:
            states = sorted(str(s) for s in state[state_col].dropna().unique())
            selected = st.multiselect("State summary variables", states, default=states[: min(6, len(states))], key="archive_state_vars")
            df = state[state[state_col].astype(str).isin(selected)] if selected else state
            fig = px.line(df, x="window_start", y="mean", color=state_col, markers=False, title="Cleaned stream summary mean")
            st.plotly_chart(fig, use_container_width=True)


def _render_archive_dashboard(st: Any, px: Any, archive_root: str, window_label: str, *, view: str = "operator") -> None:
    """Render the long-term archive dashboard."""

    tables = read_archive_dashboard_tables(archive_root, window_label=window_label)
    summary = summarize_archive_dashboard(archive_root, window_label=window_label)
    write_archive_dashboard_summary(archive_root, window_label=window_label)

    status_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴", "empty": "⚪"}.get(summary.status, "⚪")
    st.subheader(f"{status_color} Archive status: {summary.status.upper()}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Manifest rows", summary.manifest_rows)
    c2.metric("Archived rows", f"{summary.total_archived_rows:,}")
    c3.metric("Data kinds", len(summary.data_kinds))
    c4.metric("Summary files", summary.n_summary_files)
    c5.metric("Alerts", summary.n_alerts_reported)
    c6.metric("Min trust", "—" if summary.min_trust is None else f"{summary.min_trust:.2f}")

    if view == "operator":
        _render_executive_archive_view(st, px, tables, summary)

    tabs = st.tabs(["Overview", "Summary plots", "Quicklooks", "Manifest", "Alerts", "Raw summary tables"])
    with tabs[0]:
        st.markdown(
            """
            Archive mode is designed for long-running live-loop studies.  It reads
            the manifest, compact summaries, and quicklook plots first instead of
            opening raw stream partitions.  Use this mode when you have days,
            weeks, or months of live outputs.
            """
        )
        st.json(asdict(summary))
        if summary.missing_summary_tables:
            st.warning("Some summary tables are missing. Run `dmdc archive-summarize` and `dmdc archive-quicklook` for the richest dashboard.")
            st.write(summary.missing_summary_tables)
    with tabs[1]:
        _plot_archive_summaries(st, px, tables)
    with tabs[2]:
        quicklooks = tables.get("quicklooks", pd.DataFrame())
        if quicklooks.empty:
            st.info("No quicklook manifest found. Run `dmdc archive-quicklook` first.")
        else:
            for plot in quicklooks.get("plot_path", []):
                path = Path(str(plot))
                if not path.is_absolute():
                    path = Path(archive_root) / path
                if path.exists():
                    st.image(str(path), caption=path.name, use_container_width=True)
            st.dataframe(quicklooks, use_container_width=True)
    with tabs[3]:
        manifest = tables.get("manifest", pd.DataFrame())
        if manifest.empty:
            st.info("No manifest rows found.")
        else:
            kinds = sorted(str(k) for k in manifest.get("data_kind", pd.Series(dtype=str)).dropna().unique())
            selected = st.multiselect("Manifest data kinds", kinds, default=kinds[: min(8, len(kinds))])
            df = manifest[manifest["data_kind"].astype(str).isin(selected)] if selected and "data_kind" in manifest.columns else manifest
            st.dataframe(df.tail(500), use_container_width=True, height=500)
    with tabs[4]:
        alerts = tables.get("alert_summary", pd.DataFrame())
        if alerts.empty:
            st.success("No alert summary found or no alerts were archived.")
        else:
            st.dataframe(alerts, use_container_width=True)
            if "alert_count" in alerts.columns:
                x = "code" if "code" in alerts.columns else "severity" if "severity" in alerts.columns else None
                if x:
                    fig = px.bar(alerts, x=x, y="alert_count", color="severity" if "severity" in alerts.columns else None, title="Alert summary")
                    st.plotly_chart(fig, use_container_width=True)
    with tabs[5]:
        table_name = st.selectbox("Summary table", options=[k for k in tables if k != "quicklooks"])
        st.dataframe(tables.get(table_name, pd.DataFrame()), use_container_width=True, height=500)



def _streamlit_app() -> None:  # pragma: no cover - exercised manually with Streamlit
    """Main Streamlit app entry point."""

    import argparse

    st, px, go = _require_streamlit_and_plotly()
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-dir", default="outputs/live_monitoring")
    parser.add_argument("--archive-root", default=None)
    parser.add_argument("--mode", default="auto", choices=["auto", "run", "archive"])
    parser.add_argument("--window-label", default="60s")
    parser.add_argument("--refresh-seconds", type=float, default=2.0)
    parser.add_argument("--theme", default=None)
    parser.add_argument("--view", default="operator", choices=["operator", "technical"], help="operator shows a presentation-friendly overview first; technical focuses on detailed tabs.")
    parser.add_argument("--geometry", default=None, help="Optional loop geometry JSON/TOML for the operator schematic.")
    parser.add_argument("--residual-warning-threshold", type=float, default=2.0, help="Residual magnitude where schematic sensors turn warning/amber.")
    parser.add_argument("--residual-critical-threshold", type=float, default=5.0, help="Residual magnitude where schematic sensors turn critical/red.")
    known, _ = parser.parse_known_args()

    st.set_page_config(
        page_title="ROM Live Digital Twin Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Optional auto-refresh.  Streamlit versions differ in rerun APIs, so keep it
    # simple: the dashboard has a manual refresh button and, when available, a
    # lightweight timed rerun using st_autorefresh if the user has that component.
    st.title("Live ROM / Digital Twin Dashboard")
    st.caption(
        "Read-only dashboard for live streaming, POD-Kalman estimation, forecasts, residual alerts, trust scoring, bias correction, and archive summaries."
    )

    with st.sidebar:
        st.header("Data source")
        mode = st.selectbox("Dashboard mode", options=["auto", "run", "archive"], index=["auto", "run", "archive"].index(str(known.mode)))
        run_dir = st.text_input("Live output directory", value=str(known.run_dir))
        archive_root = st.text_input("Archive root", value=str(known.archive_root or ""))
        window_label = st.text_input("Archive summary window label", value=str(known.window_label))
        refresh_seconds = st.number_input("Suggested refresh interval [s]", min_value=0.5, max_value=60.0, value=float(known.refresh_seconds), step=0.5)
        view = st.selectbox("View", options=["operator", "technical"], index=0 if str(known.view) == "operator" else 1)
        geometry_path = st.text_input("Loop geometry file", value=str(known.geometry or ""))
        residual_warning_threshold = st.number_input("Residual warning threshold", min_value=0.0, value=float(known.residual_warning_threshold), step=0.5)
        residual_critical_threshold = st.number_input("Residual critical threshold", min_value=0.0, value=float(known.residual_critical_threshold), step=0.5)
        if st.button("Refresh now", use_container_width=True):
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        st.caption("Tip: run `dmdc live-run-monitor ... --save-every-batch` so this dashboard updates while data arrives.")

    selected_mode = mode
    if selected_mode == "auto":
        selected_mode = "archive" if archive_root else "run"
    if selected_mode == "archive":
        root = archive_root or run_dir
        _render_archive_dashboard(st, px, root, window_label, view=view)
        st.caption(f"Suggested refresh interval: {refresh_seconds:g} s. Press Refresh now after new archive summaries are written.")
        return

    tables = read_live_dashboard_tables(run_dir)
    time_col = infer_time_column(tables)
    summary = summarize_live_dashboard(run_dir, time_col=time_col)
    write_dashboard_summary(run_dir, time_col=time_col)

    status_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴", "empty": "⚪"}.get(summary.status, "⚪")
    st.subheader(f"{status_color} Current status: {summary.status.upper()}")

    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Latest time", "—" if summary.latest_time is None else f"{summary.latest_time:.3g}")
    m2.metric("Clean samples", summary.n_clean_samples)
    m3.metric("Forecast rows", summary.n_forecast_rows)
    m4.metric("Alerts", summary.n_alerts, delta=f"crit {summary.n_critical_alerts}")
    m5.metric("Trust", "—" if summary.latest_trust_score is None else f"{summary.latest_trust_score:.2f}")
    m6.metric("Bias events", summary.n_bias_update_events, delta=f"ok {summary.n_bias_updates_accepted}")
    m7.metric("States", len(summary.available_states))

    if view == "operator":
        _render_executive_run_view(
            st,
            px,
            go,
            tables,
            summary,
            geometry_path=geometry_path or None,
            residual_warning_threshold=float(residual_warning_threshold),
            residual_critical_threshold=float(residual_critical_threshold),
        )

    if summary.missing_tables:
        with st.expander("Missing or not-yet-created live output tables", expanded=False):
            st.write(summary.missing_tables)

    states = summary.available_states
    tabs = st.tabs([
        "Overview",
        "States",
        "Forecasts",
        "Residuals",
        "Alerts & trust",
        "Kalman",
        "Adaptation",
        "Raw tables",
    ])

    with tabs[0]:
        st.markdown(
            """
            This dashboard expects outputs from the live commands:

            - `dmdc live-replay-monitor` for replay/demo studies.
            - `dmdc live-run-monitor` for a CSV file being appended by a local logger.
            - Earlier live commands also work, but some panels may be empty until estimation/monitoring is enabled.
            """
        )
        st.json(asdict(summary))
    with tabs[1]:
        _plot_state_history(st, px, tables, time_col, states)
    with tabs[2]:
        _plot_forecasts(st, px, tables, states)
    with tabs[3]:
        _plot_residuals(st, px, tables)
    with tabs[4]:
        _plot_trust_and_alerts(st, px, tables)
    with tabs[5]:
        _plot_kalman(st, px, tables)
    with tabs[6]:
        _plot_adaptation(st, px, tables)
    with tabs[7]:
        table_name = st.selectbox("Table", options=list(LIVE_DASHBOARD_TABLES.keys()))
        st.dataframe(tables[table_name], use_container_width=True, height=500)

    st.caption(f"Suggested refresh interval: {refresh_seconds:g} s. Press Refresh now after a new batch is written.")


if __name__ == "__main__":  # pragma: no cover - launched by Streamlit
    _streamlit_app()
