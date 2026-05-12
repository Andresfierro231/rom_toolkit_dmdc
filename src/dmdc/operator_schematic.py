"""Presentation-grade operator loop schematic helpers.

The Streamlit dashboard should make the live ROM easy to understand before a
reviewer reads any documentation.  This module turns optional loop-geometry
metadata and live residual tables into a compact schematic data model:

    sensor name -> physical position -> latest residual -> green/yellow/red

The implementation is dependency-light and testable without Streamlit.  The
Streamlit dashboard imports these helpers and renders the schematic with Plotly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence
import json

import numpy as np
import pandas as pd

from .loop_geometry import LoopGeometry


@dataclass
class SensorStatus:
    """Display-ready status for one sensor on the operator schematic."""

    state: str
    position_m: float
    residual: float | None = None
    abs_residual: float | None = None
    status: str = "unknown"
    color: str = "#9ca3af"
    latest_time: float | None = None
    measurement_available: bool = False


@dataclass
class LoopSchematicSummary:
    """JSON-friendly summary of the operator schematic."""

    n_sensors: int
    n_nominal: int
    n_warning: int
    n_critical: int
    n_unknown: int
    warning_threshold: float
    critical_threshold: float
    geometry_description: str = ""


def default_loop_geometry(state_names: Sequence[str]) -> LoopGeometry:
    """Create a simple evenly spaced geometry when no geometry file is supplied.

    This fallback makes the dashboard immediately useful for a new user.  A real
    loop should later provide ``[positions_m]`` metadata so the schematic reflects
    actual thermocouple locations.
    """

    names = [str(s) for s in state_names]
    positions = {name: float(i) for i, name in enumerate(names)}
    return LoopGeometry.from_mapping(positions, description="Auto-generated evenly spaced display geometry")


def load_geometry_or_default(geometry_path: str | Path | None, state_names: Sequence[str]) -> LoopGeometry:
    """Load loop geometry from JSON/TOML, or fall back to an even spacing."""

    if geometry_path:
        path = Path(geometry_path)
        if path.exists():
            geom = LoopGeometry.load(path)
            if geom.positions_m:
                return geom
    return default_loop_geometry(state_names)


def latest_residual_by_state(residuals: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    """Return latest matched forecast residual information by state.

    Expected columns are flexible.  Phase-4 residuals normally include
    ``state``, ``residual``, ``abs_residual``, and ``matched_time``.  This helper
    also works when only ``abs_residual`` or another time column is present.
    """

    if residuals is None or residuals.empty or "state" not in residuals.columns:
        return {}
    df = residuals.copy()
    time_col = None
    for candidate in ("matched_time", "target_time", "time", "origin_time"):
        if candidate in df.columns:
            time_col = candidate
            df[candidate] = pd.to_numeric(df[candidate], errors="coerce")
            break
    if "abs_residual" not in df.columns:
        if "residual" in df.columns:
            df["abs_residual"] = pd.to_numeric(df["residual"], errors="coerce").abs()
        else:
            return {}
    df["abs_residual"] = pd.to_numeric(df["abs_residual"], errors="coerce")
    if "residual" in df.columns:
        df["residual"] = pd.to_numeric(df["residual"], errors="coerce")
    else:
        df["residual"] = np.nan
    out: dict[str, dict[str, float | None]] = {}
    for state, group in df.dropna(subset=["abs_residual"]).groupby(df["state"].astype(str)):
        if time_col:
            group = group.sort_values(time_col)
        row = group.iloc[-1]
        out[str(state)] = {
            "residual": _safe_float(row.get("residual")),
            "abs_residual": _safe_float(row.get("abs_residual")),
            "latest_time": _safe_float(row.get(time_col)) if time_col else None,
        }
    return out


def build_sensor_status_table(
    *,
    state_names: Sequence[str],
    residuals: pd.DataFrame | None = None,
    cleaned_stream: pd.DataFrame | None = None,
    geometry_path: str | Path | None = None,
    warning_threshold: float = 2.0,
    critical_threshold: float = 5.0,
) -> pd.DataFrame:
    """Build a long-form table used by dashboard schematic plots.

    Parameters
    ----------
    state_names:
        Model states/sensors to place on the schematic.
    residuals:
        Matched forecast residual rows from live monitoring.
    cleaned_stream:
        Optional latest measured stream.  Used only to mark whether each sensor
        is present in the live stream.
    geometry_path:
        Optional JSON/TOML with loop positions.  If omitted, states are shown on
        an evenly spaced line.
    warning_threshold, critical_threshold:
        Residual thresholds used for green/yellow/red sensor coloring.
    """

    geom = load_geometry_or_default(geometry_path, state_names)
    residual_map = latest_residual_by_state(residuals if residuals is not None else pd.DataFrame())
    measured_cols = set(cleaned_stream.columns) if cleaned_stream is not None and not cleaned_stream.empty else set()
    records: list[SensorStatus] = []
    for state in geom.ordered_states(state_names) or list(state_names):
        if state not in geom.positions_m:
            # If a user supplied a geometry file with partial coverage, append
            # missing states at the end rather than hiding them.
            geom.positions_m[state] = float(len(geom.positions_m))
        info = residual_map.get(str(state), {})
        abs_res = info.get("abs_residual")
        status, color = residual_to_status(abs_res, warning_threshold, critical_threshold)
        records.append(
            SensorStatus(
                state=str(state),
                position_m=float(geom.positions_m[str(state)]),
                residual=info.get("residual"),
                abs_residual=abs_res,
                status=status,
                color=color,
                latest_time=info.get("latest_time"),
                measurement_available=str(state) in measured_cols,
            )
        )
    return pd.DataFrame([asdict(r) for r in records]).sort_values("position_m")


def residual_to_status(abs_residual: float | None, warning_threshold: float, critical_threshold: float) -> tuple[str, str]:
    """Map residual magnitude to operator status and color."""

    if abs_residual is None or pd.isna(abs_residual):
        return "unknown", "#9ca3af"  # gray
    value = float(abs_residual)
    if value >= critical_threshold:
        return "critical", "#dc2626"  # red
    if value >= warning_threshold:
        return "warning", "#f59e0b"  # amber
    return "nominal", "#16a34a"  # green


def summarize_sensor_status(status_table: pd.DataFrame, *, warning_threshold: float, critical_threshold: float, geometry_description: str = "") -> LoopSchematicSummary:
    """Summarize schematic health for JSON/report outputs."""

    status = status_table.get("status", pd.Series(dtype=str)).astype(str)
    return LoopSchematicSummary(
        n_sensors=int(len(status_table)),
        n_nominal=int((status == "nominal").sum()),
        n_warning=int((status == "warning").sum()),
        n_critical=int((status == "critical").sum()),
        n_unknown=int((status == "unknown").sum()),
        warning_threshold=float(warning_threshold),
        critical_threshold=float(critical_threshold),
        geometry_description=geometry_description,
    )


def write_schematic_status_outputs(status_table: pd.DataFrame, outdir: str | Path, *, warning_threshold: float, critical_threshold: float, geometry_description: str = "") -> dict[str, str]:
    """Write schematic table and summary sidecars for audits/reports."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    table_path = out / "operator_loop_schematic_status.csv"
    summary_path = out / "operator_loop_schematic_summary.json"
    status_table.to_csv(table_path, index=False)
    summary = summarize_sensor_status(
        status_table,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
        geometry_description=geometry_description,
    )
    summary_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    return {"table": str(table_path), "summary": str(summary_path)}


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None
