"""Live Phase-6.1: conservative online bias correction and audit logs.

This module adds the first **online adaptation** layer to the live ROM stack.
It deliberately does *not* retrain the saved ROM, change the POD basis, change
Kalman-filter matrices, or modify any hardware/control setting.  Instead, it
learns a small additive correction from already-matched forecast residuals:

    corrected forecast = raw ROM forecast + learned bias

Two bias modes are supported:

``state_bias``
    One slowly learned bias per state variable.  This is the safest/default
    option when you want a single persistent offset such as ``TP4 + 2 K``.

``horizon_state_bias``
    One bias per ``(state, forecast_horizon_s)`` pair.  This is useful because
    forecast errors often grow with horizon: a 5-second forecast may need a
    small correction while a 60-second forecast may need a larger one.

Every update is recorded with old bias, new bias, residual, trust score, and the
reason the update was accepted or skipped.  The goal is to make adaptation
visually useful while staying auditable and reversible.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import math
import shutil

import numpy as np
import pandas as pd

from .live_monitoring import (
    LiveMonitoringConfig,
    LiveMonitoringResult,
    compute_forecast_residuals,
    run_live_monitoring,
)
from .provenance import write_provenance


@dataclass
class LiveAdaptationConfig(LiveMonitoringConfig):
    """Configuration for Live Phase-6.1 bias correction.

    This extends the Phase-4 monitoring configuration.  The live run first
    produces estimates, forecasts, matched residuals, alerts, and trust scores.
    The adaptation pass then uses those residuals to update a bounded bias model
    and to create bias-corrected forecast/residual files.

    Parameters
    ----------
    adaptation_enabled:
        If false, Phase-4 monitoring still runs but no bias updates are applied.
    adaptation_method:
        ``"state_bias"`` for one bias per state, or ``"horizon_state_bias"``
        for one bias per state and forecast horizon.
    bias_learning_rate:
        Exponential-smoothing rate ``alpha``.  Small values are intentionally
        preferred for live systems; for example ``0.01`` means slow adaptation.
    max_abs_bias:
        Hard bound on the magnitude of any learned bias value.
    max_update_step:
        Hard bound on the amount by which a single update may change a bias.
    update_only_when_trust_above:
        Skip bias updates when the Phase-4 trust score is below this threshold.
    skip_when_outside_training_envelope:
        If true, do not update when an operating-condition alert is present at
        the same time as the residual being considered.
    skip_on_alert_severity:
        Alert severities that block updates at the same time.  The default
        blocks ``critical`` alerts, which prevents learning from extreme events.
    clip_residual_abs:
        Optional residual clipping before the smoothing update.  This prevents a
        single bad sensor spike from producing a large correction.
    apply_bias_to_forecasts:
        If true, write ``live_bias_corrected_forecasts.csv`` and corrected
        residual diagnostics.  The raw forecast file is never overwritten.
    """

    adaptation_enabled: bool = True
    adaptation_method: str = "horizon_state_bias"
    bias_learning_rate: float = 0.01
    max_abs_bias: float = 10.0
    max_update_step: float = 0.25
    update_only_when_trust_above: float = 0.70
    skip_when_outside_training_envelope: bool = True
    skip_on_alert_severity: list[str] = field(default_factory=lambda: ["critical"])
    clip_residual_abs: float | None = 20.0
    apply_bias_to_forecasts: bool = True

    def __post_init__(self) -> None:
        if self.adaptation_method not in {"state_bias", "horizon_state_bias"}:
            raise ValueError("adaptation_method must be 'state_bias' or 'horizon_state_bias'.")
        if not 0.0 <= float(self.bias_learning_rate) <= 1.0:
            raise ValueError("bias_learning_rate must be between 0 and 1.")
        if float(self.max_abs_bias) < 0:
            raise ValueError("max_abs_bias must be nonnegative.")
        if float(self.max_update_step) < 0:
            raise ValueError("max_update_step must be nonnegative.")
        if not 0.0 <= float(self.update_only_when_trust_above) <= 1.0:
            raise ValueError("update_only_when_trust_above must be between 0 and 1.")


@dataclass
class LiveAdaptationResult:
    """Summary returned by :func:`run_live_adaptation`."""

    outdir: str
    n_estimate_updates: int
    n_forecast_rows: int
    n_forecast_residuals: int
    n_bias_update_events: int
    n_bias_updates_accepted: int
    n_bias_updates_skipped: int
    final_trust_score: float
    adaptation_method: str


class BiasCorrector:
    """Small, bounded additive bias model.

    The corrector stores bias values in a dictionary keyed either by ``state`` or
    by ``(state, forecast_horizon_s)`` depending on the configured method.  The
    update is exponential smoothing toward the observed residual:

    ``new_bias = old_bias + alpha * (residual - old_bias)``

    The proposed change is then bounded by ``max_update_step`` and the final
    bias by ``max_abs_bias``.  This keeps adaptation intentionally conservative.
    """

    def __init__(self, config: LiveAdaptationConfig) -> None:
        self.config = config
        self.bias: dict[tuple[str, float | None], float] = {}

    def key_for(self, state: str, horizon: float | None) -> tuple[str, float | None]:
        """Return the internal bias key for a state/horizon pair."""

        if self.config.adaptation_method == "state_bias":
            return (str(state), None)
        return (str(state), None if horizon is None or pd.isna(horizon) else float(horizon))

    def current_bias(self, state: str, horizon: float | None = None) -> float:
        """Get the current bias for a forecast row."""

        return float(self.bias.get(self.key_for(state, horizon), 0.0))

    def update(
        self,
        *,
        state: str,
        horizon: float | None,
        residual: float,
        trust_score: float,
        update_allowed: bool,
        rejection_reason: str | None,
    ) -> dict[str, Any]:
        """Update one bias value or record why the update was skipped."""

        key = self.key_for(state, horizon)
        old = float(self.bias.get(key, 0.0))
        clipped_residual = float(residual)
        if self.config.clip_residual_abs is not None:
            limit = abs(float(self.config.clip_residual_abs))
            clipped_residual = float(np.clip(clipped_residual, -limit, limit))

        accepted = bool(update_allowed)
        if accepted:
            desired_step = float(self.config.bias_learning_rate) * (clipped_residual - old)
            bounded_step = float(np.clip(desired_step, -float(self.config.max_update_step), float(self.config.max_update_step)))
            new = float(np.clip(old + bounded_step, -float(self.config.max_abs_bias), float(self.config.max_abs_bias)))
            self.bias[key] = new
            reason = "accepted"
        else:
            bounded_step = 0.0
            new = old
            reason = rejection_reason or "update_not_allowed"

        return {
            "state": str(state),
            "forecast_horizon_s": np.nan if horizon is None else float(horizon),
            "old_bias": old,
            "new_bias": new,
            "delta_bias": new - old,
            "raw_residual": float(residual),
            "residual_used": clipped_residual if accepted else np.nan,
            "trust_score": float(trust_score),
            "accepted": bool(accepted),
            "rejection_reason": reason,
        }


def run_live_adaptation(config: LiveAdaptationConfig, *, config_path: str | Path | None = None) -> LiveAdaptationResult:
    """Run live/replay monitoring and then apply conservative bias correction.

    This function intentionally reuses Phase-4 monitoring as the source of truth
    for forecast residuals, alerts, and trust scores.  The adaptation pass is a
    post-processing step over those tables, which makes the first implementation
    very easy to audit.  A later live implementation can call the same
    ``BiasCorrector`` class incrementally as batches arrive.
    """

    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if config_path is not None:
        try:
            shutil.copyfile(config_path, outdir / "config_used.toml")
        except OSError:
            pass

    monitoring_result: LiveMonitoringResult = run_live_monitoring(config, config_path=config_path)
    tables = build_live_adaptation_tables(outdir, config)

    events = tables["bias_update_events"]
    accepted = int(events["accepted"].sum()) if not events.empty and "accepted" in events else 0
    skipped = int((~events["accepted"].astype(bool)).sum()) if not events.empty and "accepted" in events else 0

    summary = {
        "phase": "live_phase_6_1_bias_correction_and_adaptation_records",
        "adaptation_enabled": bool(config.adaptation_enabled),
        "adaptation_method": config.adaptation_method,
        "monitoring_result": asdict(monitoring_result),
        "n_bias_update_events": int(len(events)),
        "n_bias_updates_accepted": int(accepted),
        "n_bias_updates_skipped": int(skipped),
        "outputs": {
            "bias_update_events": "live_bias_update_events.csv",
            "bias_state_timeseries": "live_bias_state_timeseries.csv",
            "bias_horizon_timeseries": "live_bias_horizon_timeseries.csv",
            "bias_summary_by_state": "live_bias_summary_by_state.csv",
            "bias_summary_by_horizon": "live_bias_summary_by_horizon.csv",
            "bias_corrected_forecasts": "live_bias_corrected_forecasts.csv",
            "bias_corrected_residuals": "live_bias_corrected_forecast_residuals.csv",
            "bias_error_comparison": "live_bias_error_comparison.csv",
        },
        "notes": [
            "Bias correction is additive and bounded; the saved ROM is not modified.",
            "Raw forecasts are preserved in live_forecasts.csv.",
            "Every accepted/skipped bias update is recorded for auditability.",
        ],
        "config": _json_safe_config(config),
    }
    (outdir / "live_adaptation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_bias_summary_text(outdir / "live_bias_summary.txt", summary, events)
    write_provenance(outdir, config_path=config_path, extra={"command": "live-adaptation", "summary": summary})

    return LiveAdaptationResult(
        outdir=str(outdir),
        n_estimate_updates=int(monitoring_result.n_estimate_updates),
        n_forecast_rows=int(monitoring_result.n_forecast_rows),
        n_forecast_residuals=int(monitoring_result.n_forecast_residuals),
        n_bias_update_events=int(len(events)),
        n_bias_updates_accepted=int(accepted),
        n_bias_updates_skipped=int(skipped),
        final_trust_score=float(monitoring_result.final_trust_score),
        adaptation_method=config.adaptation_method,
    )


def build_live_adaptation_tables(outdir: str | Path, config: LiveAdaptationConfig) -> dict[str, pd.DataFrame]:
    """Read Phase-4 logs and write Phase-6.1 bias-correction tables."""

    out = Path(outdir)
    residuals = _read_csv(out / "live_forecast_residuals.csv")
    forecasts = _read_csv(out / "live_forecasts.csv")
    clean = _read_csv(out / "cleaned_stream_log.csv")
    alerts = _read_csv(out / "live_alerts.csv")
    trust = _read_csv(out / "live_trust_score.csv")

    if not config.adaptation_enabled:
        events = pd.DataFrame(columns=_event_columns())
    else:
        events = compute_bias_update_events(residuals=residuals, alerts=alerts, trust=trust, config=config)

    state_ts = make_bias_state_timeseries(events)
    horizon_ts = make_bias_horizon_timeseries(events)
    state_summary = summarize_bias_by_state(events)
    horizon_summary = summarize_bias_by_horizon(events)

    corrected_forecasts = apply_bias_history_to_forecasts(forecasts, events, method=config.adaptation_method) if config.apply_bias_to_forecasts else pd.DataFrame()
    corrected_residuals = pd.DataFrame()
    error_comparison = pd.DataFrame()
    if not corrected_forecasts.empty and not clean.empty:
        tmp = corrected_forecasts.copy()
        tmp["predicted_value"] = tmp["bias_corrected_predicted_value"]
        corrected_residuals = compute_forecast_residuals(
            clean,
            tmp,
            time_col=config.time_col,
            measurement_cols=list(config.measurement_cols),
            tolerance_seconds=config.forecast_match_tolerance_seconds,
        )
        if not corrected_residuals.empty:
            corrected_residuals = corrected_residuals.rename(
                columns={
                    "predicted_value": "bias_corrected_predicted_value",
                    "residual": "bias_corrected_residual",
                    "abs_residual": "abs_bias_corrected_residual",
                }
            )
        error_comparison = compare_raw_and_bias_corrected_errors(residuals, corrected_residuals)

    events.to_csv(out / "live_bias_update_events.csv", index=False)
    state_ts.to_csv(out / "live_bias_state_timeseries.csv", index=False)
    horizon_ts.to_csv(out / "live_bias_horizon_timeseries.csv", index=False)
    state_summary.to_csv(out / "live_bias_summary_by_state.csv", index=False)
    horizon_summary.to_csv(out / "live_bias_summary_by_horizon.csv", index=False)
    corrected_forecasts.to_csv(out / "live_bias_corrected_forecasts.csv", index=False)
    corrected_residuals.to_csv(out / "live_bias_corrected_forecast_residuals.csv", index=False)
    error_comparison.to_csv(out / "live_bias_error_comparison.csv", index=False)

    return {
        "bias_update_events": events,
        "bias_state_timeseries": state_ts,
        "bias_horizon_timeseries": horizon_ts,
        "bias_summary_by_state": state_summary,
        "bias_summary_by_horizon": horizon_summary,
        "bias_corrected_forecasts": corrected_forecasts,
        "bias_corrected_residuals": corrected_residuals,
        "bias_error_comparison": error_comparison,
    }


def compute_bias_update_events(
    *,
    residuals: pd.DataFrame,
    alerts: pd.DataFrame,
    trust: pd.DataFrame,
    config: LiveAdaptationConfig,
) -> pd.DataFrame:
    """Compute the full audit log of accepted/skipped bias updates."""

    if residuals.empty:
        return pd.DataFrame(columns=_event_columns())

    corrector = BiasCorrector(config)
    rows: list[dict[str, Any]] = []
    residuals = residuals.sort_values([c for c in ["matched_time", "origin_time", "state"] if c in residuals.columns]).reset_index(drop=True)

    for _, r in residuals.iterrows():
        state = str(r.get("state"))
        horizon = _maybe_float(r.get("forecast_horizon_s"))
        event_time = _maybe_float(r.get("matched_time", r.get("target_time")))
        residual_value = float(r.get("residual", 0.0))
        trust_score = lookup_trust_score(trust, event_time)
        allowed, reason = decide_bias_update_allowed(
            event_time=event_time,
            trust_score=trust_score,
            alerts=alerts,
            config=config,
        )
        update = corrector.update(
            state=state,
            horizon=horizon,
            residual=residual_value,
            trust_score=trust_score,
            update_allowed=allowed,
            rejection_reason=reason,
        )
        update.update(
            {
                "time": event_time,
                "origin_time": r.get("origin_time"),
                "origin_row_index": r.get("origin_row_index"),
                "target_time": r.get("target_time"),
                "matched_time": r.get("matched_time"),
                "measured_value": r.get("measured_value"),
                "raw_predicted_value": r.get("predicted_value"),
                "abs_raw_residual": r.get("abs_residual"),
            }
        )
        rows.append(update)
    return pd.DataFrame(rows, columns=_event_columns())


def decide_bias_update_allowed(
    *,
    event_time: float | None,
    trust_score: float,
    alerts: pd.DataFrame,
    config: LiveAdaptationConfig,
) -> tuple[bool, str | None]:
    """Return whether a residual may update the bias and why not."""

    if trust_score < float(config.update_only_when_trust_above):
        return False, "trust_score_below_threshold"
    matching_alerts = alerts_at_time(alerts, event_time)
    if not matching_alerts.empty and config.skip_when_outside_training_envelope:
        if "code" in matching_alerts and (matching_alerts["code"].astype(str) == "OPERATING_CONDITION_OUT_OF_RANGE").any():
            return False, "outside_training_or_operating_envelope"
    blocked = {s.lower() for s in config.skip_on_alert_severity}
    if blocked and not matching_alerts.empty and "severity" in matching_alerts:
        severities = set(matching_alerts["severity"].astype(str).str.lower())
        if severities.intersection(blocked):
            return False, "blocked_by_alert_severity_" + "+".join(sorted(severities.intersection(blocked)))
    return True, None


def lookup_trust_score(trust: pd.DataFrame, event_time: float | None) -> float:
    """Return the latest trust score at or before ``event_time``."""

    if trust.empty or "trust_score" not in trust.columns:
        return 1.0
    if event_time is None or pd.isna(event_time) or "time" not in trust.columns:
        vals = pd.to_numeric(trust["trust_score"], errors="coerce").dropna()
        return float(vals.iloc[-1]) if len(vals) else 1.0
    t = pd.to_numeric(trust["time"], errors="coerce")
    mask = t.notna() & (t.astype(float) <= float(event_time) + 1.0e-12)
    vals = pd.to_numeric(trust.loc[mask, "trust_score"], errors="coerce").dropna()
    if len(vals):
        return float(vals.iloc[-1])
    vals = pd.to_numeric(trust["trust_score"], errors="coerce").dropna()
    return float(vals.iloc[0]) if len(vals) else 1.0


def alerts_at_time(alerts: pd.DataFrame, event_time: float | None, *, tolerance: float = 1.0e-9) -> pd.DataFrame:
    """Return alerts at the same physical time as a residual event."""

    if alerts.empty or event_time is None or pd.isna(event_time) or "time" not in alerts.columns:
        return pd.DataFrame()
    t = pd.to_numeric(alerts["time"], errors="coerce")
    mask = t.notna() & (np.abs(t.astype(float) - float(event_time)) <= tolerance)
    return alerts.loc[mask].copy()


def apply_bias_history_to_forecasts(forecasts: pd.DataFrame, events: pd.DataFrame, *, method: str) -> pd.DataFrame:
    """Apply only bias values known at each forecast origin time.

    This avoids leaking future residual information into past forecast origins.
    A forecast generated at time ``t`` uses the most recent accepted bias update
    with ``update_time <= t`` for the relevant state/horizon key.
    """

    if forecasts.empty:
        return pd.DataFrame()
    corrected = forecasts.copy()
    corrected["raw_predicted_value"] = pd.to_numeric(corrected.get("predicted_value"), errors="coerce")
    corrected["applied_bias"] = 0.0
    corrected["bias_corrected_predicted_value"] = corrected["raw_predicted_value"]
    corrected["bias_key"] = ""

    accepted = events.copy()
    if accepted.empty or "accepted" not in accepted.columns:
        return corrected
    accepted = accepted[accepted["accepted"].astype(bool)].copy()
    if accepted.empty:
        return corrected
    accepted["time"] = pd.to_numeric(accepted["time"], errors="coerce")
    accepted = accepted.dropna(subset=["time"]).sort_values("time")

    histories: dict[tuple[str, float | None], list[tuple[float, float]]] = {}
    for _, e in accepted.iterrows():
        key = _bias_key(str(e["state"]), _maybe_float(e.get("forecast_horizon_s")), method)
        histories.setdefault(key, []).append((float(e["time"]), float(e["new_bias"])))

    for idx, row in corrected.iterrows():
        state = str(row.get("state"))
        horizon = _maybe_float(row.get("forecast_horizon_s"))
        origin = _maybe_float(row.get("origin_time"))
        key = _bias_key(state, horizon, method)
        bias = _latest_bias_before(histories.get(key, []), origin)
        corrected.at[idx, "applied_bias"] = bias
        corrected.at[idx, "bias_corrected_predicted_value"] = float(corrected.at[idx, "raw_predicted_value"]) + bias
        corrected.at[idx, "bias_key"] = _format_key(key)
    return corrected


def make_bias_state_timeseries(events: pd.DataFrame) -> pd.DataFrame:
    """Return accepted/skipped bias history, normalized to state-level columns."""

    if events.empty:
        return pd.DataFrame(columns=["time", "state", "bias_value", "forecast_horizon_s", "residual_used", "trust_score", "update_allowed", "reason_if_skipped"])
    return pd.DataFrame(
        {
            "time": events.get("time"),
            "state": events.get("state"),
            "forecast_horizon_s": events.get("forecast_horizon_s"),
            "bias_value": events.get("new_bias"),
            "residual_used": events.get("residual_used"),
            "trust_score": events.get("trust_score"),
            "update_allowed": events.get("accepted"),
            "reason_if_skipped": events.get("rejection_reason"),
        }
    )


def make_bias_horizon_timeseries(events: pd.DataFrame) -> pd.DataFrame:
    """Return bias history grouped by state and forecast horizon."""

    if events.empty:
        return pd.DataFrame(columns=["time", "forecast_horizon_s", "state", "bias_value", "residual_used", "update_allowed"])
    cols = ["time", "forecast_horizon_s", "state", "new_bias", "residual_used", "accepted", "rejection_reason"]
    out = events[[c for c in cols if c in events.columns]].copy()
    return out.rename(columns={"new_bias": "bias_value", "accepted": "update_allowed", "rejection_reason": "reason_if_skipped"})


def summarize_bias_by_state(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize final/current bias and update counts by state."""

    if events.empty:
        return pd.DataFrame(columns=["state", "n_events", "n_accepted", "n_skipped", "final_bias_mean", "max_abs_bias", "mean_abs_raw_residual"])
    rows: list[dict[str, Any]] = []
    for state, g in events.groupby("state", dropna=False):
        accepted = g[g["accepted"].astype(bool)] if "accepted" in g else pd.DataFrame()
        final_bias_mean = float(accepted.groupby("forecast_horizon_s", dropna=False)["new_bias"].last().mean()) if not accepted.empty else 0.0
        rows.append(
            {
                "state": state,
                "n_events": int(len(g)),
                "n_accepted": int(g["accepted"].astype(bool).sum()) if "accepted" in g else 0,
                "n_skipped": int((~g["accepted"].astype(bool)).sum()) if "accepted" in g else int(len(g)),
                "final_bias_mean": final_bias_mean,
                "max_abs_bias": float(pd.to_numeric(g["new_bias"], errors="coerce").abs().max()) if "new_bias" in g else 0.0,
                "mean_abs_raw_residual": float(pd.to_numeric(g["raw_residual"], errors="coerce").abs().mean()) if "raw_residual" in g else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("max_abs_bias", ascending=False)


def summarize_bias_by_horizon(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize bias activity by forecast horizon."""

    if events.empty or "forecast_horizon_s" not in events.columns:
        return pd.DataFrame(columns=["forecast_horizon_s", "n_events", "n_accepted", "n_skipped", "mean_abs_bias", "mean_abs_raw_residual"])
    rows: list[dict[str, Any]] = []
    for horizon, g in events.groupby("forecast_horizon_s", dropna=False):
        rows.append(
            {
                "forecast_horizon_s": horizon,
                "n_events": int(len(g)),
                "n_accepted": int(g["accepted"].astype(bool).sum()) if "accepted" in g else 0,
                "n_skipped": int((~g["accepted"].astype(bool)).sum()) if "accepted" in g else int(len(g)),
                "mean_abs_bias": float(pd.to_numeric(g["new_bias"], errors="coerce").abs().mean()) if "new_bias" in g else 0.0,
                "mean_abs_raw_residual": float(pd.to_numeric(g["raw_residual"], errors="coerce").abs().mean()) if "raw_residual" in g else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("forecast_horizon_s")


def compare_raw_and_bias_corrected_errors(raw: pd.DataFrame, corrected: pd.DataFrame) -> pd.DataFrame:
    """Compare mean/max absolute residuals before and after bias correction."""

    if raw.empty or corrected.empty:
        return pd.DataFrame()

    raw_key_cols = [c for c in ["state", "forecast_horizon_s"] if c in raw.columns]
    corr_key_cols = [c for c in ["state", "forecast_horizon_s"] if c in corrected.columns]
    if raw_key_cols != corr_key_cols or not raw_key_cols:
        return pd.DataFrame()

    raw_summary = raw.groupby(raw_key_cols, dropna=False).agg(
        raw_mean_abs_residual=("abs_residual", "mean"),
        raw_max_abs_residual=("abs_residual", "max"),
        n_raw=("abs_residual", "count"),
    ).reset_index()
    corr_summary = corrected.groupby(corr_key_cols, dropna=False).agg(
        corrected_mean_abs_residual=("abs_bias_corrected_residual", "mean"),
        corrected_max_abs_residual=("abs_bias_corrected_residual", "max"),
        n_corrected=("abs_bias_corrected_residual", "count"),
    ).reset_index()
    out = raw_summary.merge(corr_summary, on=raw_key_cols, how="outer")
    out["mean_abs_residual_improvement"] = out["raw_mean_abs_residual"] - out["corrected_mean_abs_residual"]
    out["max_abs_residual_improvement"] = out["raw_max_abs_residual"] - out["corrected_max_abs_residual"]
    return out.sort_values(raw_key_cols)


def _latest_bias_before(history: list[tuple[float, float]], origin_time: float | None) -> float:
    if not history:
        return 0.0
    if origin_time is None or pd.isna(origin_time):
        return 0.0
    value = 0.0
    for t, bias in history:
        if t <= float(origin_time) + 1.0e-12:
            value = float(bias)
        else:
            break
    return value


def _bias_key(state: str, horizon: float | None, method: str) -> tuple[str, float | None]:
    return (str(state), None) if method == "state_bias" else (str(state), horizon)


def _format_key(key: tuple[str, float | None]) -> str:
    return key[0] if key[1] is None else f"{key[0]}@{key[1]:g}s"


def _maybe_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def _event_columns() -> list[str]:
    return [
        "time",
        "origin_time",
        "origin_row_index",
        "target_time",
        "matched_time",
        "forecast_horizon_s",
        "state",
        "measured_value",
        "raw_predicted_value",
        "raw_residual",
        "abs_raw_residual",
        "old_bias",
        "new_bias",
        "delta_bias",
        "residual_used",
        "trust_score",
        "accepted",
        "rejection_reason",
    ]


def _json_safe_config(config: LiveAdaptationConfig) -> dict[str, Any]:
    raw = asdict(config)
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            out[k] = {str(kk): list(vv) if isinstance(vv, tuple) else vv for kk, vv in v.items()}
        else:
            out[k] = v
    return out


def _write_bias_summary_text(path: Path, summary: dict[str, Any], events: pd.DataFrame) -> None:
    lines = [
        "Live Phase 6.1 Bias Correction Summary",
        "=======================================",
        "",
        f"Adaptation enabled: {summary.get('adaptation_enabled')}",
        f"Method: {summary.get('adaptation_method')}",
        f"Events: {summary.get('n_bias_update_events')}",
        f"Accepted: {summary.get('n_bias_updates_accepted')}",
        f"Skipped: {summary.get('n_bias_updates_skipped')}",
        "",
        "Interpretation:",
        "Bias correction adds a bounded offset to forecasts only. The validated ROM is not modified.",
        "Use live_bias_update_events.csv to audit every accepted/skipped update.",
    ]
    if not events.empty and "rejection_reason" in events.columns:
        reasons = events.loc[~events.get("accepted", pd.Series(dtype=bool)).astype(bool), "rejection_reason"].value_counts()
        if len(reasons):
            lines += ["", "Top skipped-update reasons:"]
            lines += [f"- {reason}: {count}" for reason, count in reasons.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
