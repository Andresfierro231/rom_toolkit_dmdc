"""Live Phase-4 monitoring, residual alerts, and model-trust scoring.

This module is intentionally built *on top of* the Phase-3 live estimation
workflow.  It does not retrain the ROM and it does not actuate the loop.  The
monitoring layer reads the same live/replay stream, produces POD-Kalman state
estimates and optional forecasts, then post-processes the resulting logs into:

* forecast residuals, by matching old forecasts to later measurements;
* Kalman innovation alerts, which are often the fastest signal that the model
  and sensors disagree;
* operating-envelope alerts for known input/control ranges;
* covariance and forecast-divergence alerts; and
* a simple trust-score timeline.

The implementation is deliberately transparent and CSV-first so that a live
operator, a student, or a later dashboard can inspect exactly why an alert was
raised.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import shutil

import numpy as np
import pandas as pd

from .live_estimation import LiveEstimationConfig, LiveEstimationResult, run_live_estimation
from .provenance import write_provenance


@dataclass
class LiveMonitoringConfig(LiveEstimationConfig):
    """Configuration for Live Phase-4 monitoring.

    The fields inherited from :class:`LiveEstimationConfig` describe the stream,
    saved POD-DMDc model, measurement columns, Kalman noise settings, and optional
    forecast horizons.  The extra fields below control alert thresholds.

    Parameters
    ----------
    residual_abs_threshold:
        Absolute forecast residual threshold in physical state units.  A residual
        alert is raised when ``abs(measured - forecast)`` exceeds this value.
    innovation_abs_threshold:
        Absolute Kalman innovation threshold in measurement units.  Innovations
        compare measured sensors to what the predicted POD state expected.
    innovation_norm_threshold:
        Optional threshold on the total innovation vector norm.
    covariance_trace_threshold:
        Optional threshold on the trace of the modal covariance.  A high value
        means the filter is uncertain about the reduced state.
    forecast_match_tolerance_seconds:
        Time tolerance used to match forecast target times to later measurements.
        If omitted, an adaptive tolerance is inferred from the median live ``dt``.
    max_abs_forecast_value:
        Optional sanity bound for forecast values.  It is not a physics limit;
        it is a practical divergence guard.
    operating_ranges:
        Mapping from input/state name to ``(min, max)`` range.  Values outside
        this envelope raise alerts and reduce trust.
    """

    residual_abs_threshold: float = 5.0
    innovation_abs_threshold: float = 5.0
    innovation_norm_threshold: float | None = None
    covariance_trace_threshold: float | None = None
    forecast_match_tolerance_seconds: float | None = None
    max_abs_forecast_value: float | None = None
    operating_ranges: dict[str, tuple[float, float]] | None = None
    trust_warning_penalty: float = 0.10
    trust_critical_penalty: float = 0.25


@dataclass
class LiveMonitoringResult:
    """Summary returned by :func:`run_live_monitoring`."""

    outdir: str
    n_estimate_updates: int
    n_forecast_rows: int
    n_forecast_residuals: int
    n_alerts: int
    n_warning_alerts: int
    n_critical_alerts: int
    final_trust_score: float


def run_live_monitoring(config: LiveMonitoringConfig, *, config_path: str | Path | None = None) -> LiveMonitoringResult:
    """Run live/replay POD-Kalman estimation and generate monitoring alerts.

    The current implementation performs Phase-4 monitoring after each bounded
    replay/tail session.  When ``save_every_batch`` is enabled, Phase-3 logs are
    still written during the run; the final monitoring pass then creates the
    residual/alert/trust tables from the completed logs.  This keeps the logic
    easy to test and does not prevent a future dashboard from re-running the
    monitor repeatedly on growing CSV logs.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if config_path is not None:
        try:
            shutil.copyfile(config_path, outdir / "config_used.toml")
        except OSError:
            pass

    estimation_result: LiveEstimationResult = run_live_estimation(config, config_path=config_path)
    tables = build_live_monitoring_tables(outdir, config)

    alerts = tables["alerts"]
    residuals = tables["forecast_residuals"]
    trust = tables["trust"]
    summary = summarize_monitoring(estimation_result, alerts, residuals, trust)
    summary["config"] = _json_safe_config(config)
    summary["phase"] = "live_phase_4_monitoring_residual_alerts_and_trust_scoring"
    (outdir / "live_monitoring_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_provenance(outdir, config_path=config_path, extra={"command": "live-monitoring", "summary": summary})

    return LiveMonitoringResult(
        outdir=str(outdir),
        n_estimate_updates=int(estimation_result.n_estimate_updates),
        n_forecast_rows=int(estimation_result.n_forecast_rows),
        n_forecast_residuals=int(len(residuals)),
        n_alerts=int(len(alerts)),
        n_warning_alerts=int((alerts["severity"] == "warning").sum()) if not alerts.empty and "severity" in alerts else 0,
        n_critical_alerts=int((alerts["severity"] == "critical").sum()) if not alerts.empty and "severity" in alerts else 0,
        final_trust_score=float(trust["trust_score"].iloc[-1]) if not trust.empty else 1.0,
    )


def build_live_monitoring_tables(outdir: str | Path, config: LiveMonitoringConfig) -> dict[str, pd.DataFrame]:
    """Read live logs from ``outdir`` and write Phase-4 monitoring tables."""

    out = Path(outdir)
    clean = _read_csv(out / "cleaned_stream_log.csv")
    forecasts = _read_csv(out / "live_forecasts.csv")
    innovations = _read_csv(out / "live_kalman_innovations.csv")
    estimates = _read_csv(out / "live_state_estimates.csv")
    live_warnings = _read_csv(out / "live_warnings.csv")

    residuals = compute_forecast_residuals(
        clean,
        forecasts,
        time_col=config.time_col,
        measurement_cols=config.measurement_cols,
        tolerance_seconds=config.forecast_match_tolerance_seconds,
    )
    alerts = build_alerts(
        residuals=residuals,
        innovations=innovations,
        estimates=estimates,
        clean=clean,
        live_warnings=live_warnings,
        config=config,
    )
    trust = compute_trust_timeline(alerts, estimates, config=config)

    residuals.to_csv(out / "live_forecast_residuals.csv", index=False)
    alerts.to_csv(out / "live_alerts.csv", index=False)
    trust.to_csv(out / "live_trust_score.csv", index=False)
    _write_alerts_text(alerts, out / "live_alerts.txt")
    return {"forecast_residuals": residuals, "alerts": alerts, "trust": trust}


def compute_forecast_residuals(
    clean: pd.DataFrame,
    forecasts: pd.DataFrame,
    *,
    time_col: str | None,
    measurement_cols: list[str],
    tolerance_seconds: float | None = None,
) -> pd.DataFrame:
    """Match old forecasts to later measurements and compute residuals.

    Forecast rows are long-form: one row per origin/horizon/state.  If the
    forecast table has no ``target_time`` column, it is inferred as
    ``origin_time + forecast_horizon_s`` when possible.
    """

    if clean.empty or forecasts.empty or not time_col or time_col not in clean.columns:
        return pd.DataFrame()
    forecasts = forecasts.copy()
    if "target_time" not in forecasts.columns and {"origin_time", "forecast_horizon_s"}.issubset(forecasts.columns):
        forecasts["target_time"] = forecasts["origin_time"] + forecasts["forecast_horizon_s"]
    if "target_time" not in forecasts.columns or "state" not in forecasts.columns:
        return pd.DataFrame()

    clean = clean.sort_values(time_col).reset_index(drop=True)
    times = clean[time_col].to_numpy(dtype=float)
    if tolerance_seconds is None:
        if len(times) >= 2:
            dt = np.diff(times)
            positive = dt[dt > 0]
            tolerance_seconds = float(np.median(positive) * 0.55) if len(positive) else 1.0e-9
        else:
            tolerance_seconds = 1.0e-9

    rows: list[dict[str, Any]] = []
    measurement_set = set(measurement_cols)
    for _, row in forecasts.dropna(subset=["target_time"]).iterrows():
        state = str(row.get("state"))
        if state not in measurement_set or state not in clean.columns:
            continue
        target = float(row["target_time"])
        idx = int(np.argmin(np.abs(times - target)))
        matched_time = float(times[idx])
        time_error = abs(matched_time - target)
        if time_error > float(tolerance_seconds):
            continue
        measured = float(clean.iloc[idx][state])
        predicted = float(row["predicted_value"])
        residual = measured - predicted
        rows.append(
            {
                "origin_time": row.get("origin_time"),
                "origin_row_index": row.get("origin_row_index"),
                "forecast_horizon_s": row.get("forecast_horizon_s"),
                "effective_horizon_s": row.get("effective_horizon_s"),
                "target_time": target,
                "matched_time": matched_time,
                "time_error_s": time_error,
                "state": state,
                "measured_value": measured,
                "predicted_value": predicted,
                "residual": residual,
                "abs_residual": abs(residual),
            }
        )
    return pd.DataFrame(rows)


def build_alerts(
    *,
    residuals: pd.DataFrame,
    innovations: pd.DataFrame,
    estimates: pd.DataFrame,
    clean: pd.DataFrame,
    live_warnings: pd.DataFrame,
    config: LiveMonitoringConfig,
) -> pd.DataFrame:
    """Build a unified alert table from monitoring signals."""

    rows: list[dict[str, Any]] = []

    for _, r in residuals.iterrows() if not residuals.empty else []:
        threshold = float(config.residual_abs_threshold)
        if float(r["abs_residual"]) > threshold:
            rows.append(_alert(
                severity="critical" if float(r["abs_residual"]) > 2.0 * threshold else "warning",
                code="FORECAST_RESIDUAL_HIGH",
                time=r.get("matched_time", r.get("target_time")),
                state=r.get("state"),
                value=float(r["abs_residual"]),
                threshold=threshold,
                message=f"Forecast residual for {r.get('state')} exceeded threshold.",
                suggested_action="Check whether the loop is outside the training envelope, whether the sensor is drifting, or whether the ROM forecast is diverging.",
            ))

    if not innovations.empty:
        if "innovation" in innovations.columns:
            for _, r in innovations.iterrows():
                threshold = float(config.innovation_abs_threshold)
                value = abs(float(r["innovation"]))
                if value > threshold:
                    rows.append(_alert(
                        severity="critical" if value > 2.0 * threshold else "warning",
                        code="KALMAN_INNOVATION_HIGH",
                        time=r.get("origin_time"),
                        state=r.get("measurement"),
                        value=value,
                        threshold=threshold,
                        message=f"Kalman innovation for {r.get('measurement')} exceeded threshold.",
                        suggested_action="Check measurement noise settings, sensor health, and whether the operating point is outside validated conditions.",
                    ))
        if config.innovation_norm_threshold is not None and "innovation_norm" in innovations.columns:
            grouped = innovations.groupby("origin_row_index", dropna=False).first().reset_index()
            for _, r in grouped.iterrows():
                value = float(r["innovation_norm"])
                if value > float(config.innovation_norm_threshold):
                    rows.append(_alert(
                        severity="warning",
                        code="KALMAN_INNOVATION_NORM_HIGH",
                        time=r.get("origin_time"),
                        state=None,
                        value=value,
                        threshold=float(config.innovation_norm_threshold),
                        message="Total Kalman innovation norm exceeded threshold.",
                        suggested_action="Inspect live_kalman_innovations.csv to identify which measurement channels dominate the mismatch.",
                    ))

    if not estimates.empty:
        if config.covariance_trace_threshold is not None and "covariance_trace" in estimates.columns:
            for _, r in estimates.iterrows():
                value = float(r["covariance_trace"])
                if value > float(config.covariance_trace_threshold):
                    rows.append(_alert(
                        severity="warning",
                        code="STATE_ESTIMATE_UNCERTAINTY_HIGH",
                        time=r.get("origin_time"),
                        state=None,
                        value=value,
                        threshold=float(config.covariance_trace_threshold),
                        message="Kalman modal covariance trace exceeded threshold.",
                        suggested_action="Increase measurement coverage, tune process/measurement noise, or avoid trusting long forecasts until uncertainty decreases.",
                    ))
        if config.max_abs_forecast_value is not None:
            state_cols = [c for c in estimates.columns if c not in {"origin_time", "origin_row_index", "received_utc", "estimator_type", "covariance_trace", "innovation_norm", "initialized_from_measurement"} and c not in set(config.input_cols or [])]
            for _, r in estimates.iterrows():
                for state in state_cols:
                    try:
                        value = abs(float(r[state]))
                    except (TypeError, ValueError):
                        continue
                    if value > float(config.max_abs_forecast_value):
                        rows.append(_alert(
                            severity="critical",
                            code="STATE_ESTIMATE_MAGNITUDE_HIGH",
                            time=r.get("origin_time"),
                            state=state,
                            value=value,
                            threshold=float(config.max_abs_forecast_value),
                            message=f"Estimated state magnitude for {state} exceeded configured bound.",
                            suggested_action="Check sensor scaling/units and model stability before trusting forecasts.",
                        ))

    ranges = config.operating_ranges or {}
    if ranges and not clean.empty:
        for col, bounds in ranges.items():
            if col not in clean.columns:
                continue
            lo, hi = float(bounds[0]), float(bounds[1])
            for _, r in clean.iterrows():
                value = float(r[col])
                if value < lo or value > hi:
                    rows.append(_alert(
                        severity="warning",
                        code="OPERATING_CONDITION_OUT_OF_RANGE",
                        time=r.get(config.time_col) if config.time_col else None,
                        state=col,
                        value=value,
                        threshold=np.nan,
                        message=f"{col}={value:g} is outside configured operating envelope [{lo:g}, {hi:g}].",
                        suggested_action="Treat forecasts as extrapolations; consider training/validating a model that includes this operating regime.",
                    ))

    if not live_warnings.empty:
        for _, r in live_warnings.iterrows():
            rows.append(_alert(
                severity="warning",
                code=f"BUFFER_{r.get('code')}",
                time=None,
                state=None,
                value=np.nan,
                threshold=np.nan,
                message=str(r.get("message", "Live buffer warning.")),
                suggested_action=str(r.get("suggested_action", "Inspect live_warnings.csv.")),
            ))

    return pd.DataFrame(rows, columns=["time", "severity", "code", "state", "value", "threshold", "message", "suggested_action"])


def compute_trust_timeline(alerts: pd.DataFrame, estimates: pd.DataFrame, *, config: LiveMonitoringConfig) -> pd.DataFrame:
    """Compute a simple trust score in ``[0, 1]`` from alert history.

    This is intentionally a *diagnostic heuristic*, not a safety system.  It is
    meant to make live runs easy to scan: a lower trust score means the model,
    sensors, or operating conditions deserve attention.
    """

    times: list[float | None]
    if not estimates.empty and "origin_time" in estimates.columns:
        times = [None if pd.isna(v) else float(v) for v in estimates["origin_time"].tolist()]
    elif not alerts.empty and "time" in alerts.columns:
        times = [None if pd.isna(v) else float(v) for v in alerts["time"].tolist()]
    else:
        return pd.DataFrame([{"time": None, "trust_score": 1.0, "n_warning_alerts": 0, "n_critical_alerts": 0}])

    rows: list[dict[str, Any]] = []
    for t in times:
        if alerts.empty or "time" not in alerts.columns:
            subset = pd.DataFrame()
        elif t is None:
            subset = alerts[alerts["time"].isna()]
        else:
            subset = alerts[(alerts["time"].notna()) & (alerts["time"].astype(float) <= t)]
        n_warn = int((subset.get("severity", pd.Series(dtype=str)) == "warning").sum()) if not subset.empty else 0
        n_crit = int((subset.get("severity", pd.Series(dtype=str)) == "critical").sum()) if not subset.empty else 0
        score = 1.0 - n_warn * float(config.trust_warning_penalty) - n_crit * float(config.trust_critical_penalty)
        rows.append({"time": t, "trust_score": max(0.0, float(score)), "n_warning_alerts": n_warn, "n_critical_alerts": n_crit})
    return pd.DataFrame(rows)


def summarize_monitoring(
    estimation_result: LiveEstimationResult,
    alerts: pd.DataFrame,
    residuals: pd.DataFrame,
    trust: pd.DataFrame,
) -> dict[str, Any]:
    """Create a JSON summary for Phase-4 monitoring."""

    final_trust = float(trust["trust_score"].iloc[-1]) if not trust.empty else 1.0
    return {
        "estimation_result": asdict(estimation_result),
        "n_forecast_residuals": int(len(residuals)),
        "n_alerts": int(len(alerts)),
        "n_warning_alerts": int((alerts["severity"] == "warning").sum()) if not alerts.empty and "severity" in alerts else 0,
        "n_critical_alerts": int((alerts["severity"] == "critical").sum()) if not alerts.empty and "severity" in alerts else 0,
        "final_trust_score": final_trust,
        "outputs": {
            "live_forecast_residuals": "live_forecast_residuals.csv",
            "live_alerts": "live_alerts.csv",
            "live_trust_score": "live_trust_score.csv",
            "live_alerts_text": "live_alerts.txt",
        },
        "notes": [
            "Trust score is an advisory diagnostic, not a safety interlock.",
            "Phase-4 does not retrain the ROM and does not control hardware.",
        ],
    }


def _alert(*, severity: str, code: str, time: Any, state: Any, value: float, threshold: float, message: str, suggested_action: str) -> dict[str, Any]:
    return {
        "time": time,
        "severity": severity,
        "code": code,
        "state": state,
        "value": value,
        "threshold": threshold,
        "message": message,
        "suggested_action": suggested_action,
    }


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _write_alerts_text(alerts: pd.DataFrame, path: Path) -> None:
    if alerts.empty:
        path.write_text("No live monitoring alerts were emitted.\n", encoding="utf-8")
        return
    lines: list[str] = []
    for _, r in alerts.iterrows():
        lines.append(
            f"[{r.get('severity', 'warning').upper()}] {r.get('code')} at time={r.get('time')} state={r.get('state')}\n"
            f"Message: {r.get('message')}\n"
            f"Suggested action: {r.get('suggested_action')}"
        )
    path.write_text("\n\n".join(lines), encoding="utf-8")


def _json_safe_config(config: LiveMonitoringConfig) -> dict[str, Any]:
    data = asdict(config)
    if data.get("operating_ranges"):
        data["operating_ranges"] = {k: list(v) for k, v in data["operating_ranges"].items()}
    return data
