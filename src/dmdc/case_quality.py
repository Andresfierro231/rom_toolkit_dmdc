"""Case-quality checks for large simulation or experiment batches.

SAM/CFD parameter sweeps often contain failed, short, or partially written cases.
The ROM workflows should make those failures explicit rather than silently using
bad trajectories.  This module summarizes case health in a CSV-friendly table.
"""

from __future__ import annotations

from typing import Sequence
import numpy as np
import pandas as pd


def summarize_case_quality(
    frame: pd.DataFrame,
    *,
    case_col: str | None,
    time_col: str | None = None,
    required_cols: Sequence[str] | None = None,
    min_samples: int = 3,
    expected_final_time: float | None = None,
    final_time_tol: float = 1e-6,
    status_col: str | None = None,
) -> pd.DataFrame:
    """Return one row per case describing whether it is usable for ROM fitting."""

    required_cols = list(required_cols or [])
    groups = frame.groupby(case_col, dropna=False) if case_col else [("__single_case__", frame)]
    rows: list[dict[str, object]] = []
    for cid, group in groups:
        g = group.copy()
        problems: list[str] = []
        n_rows = int(len(g))
        if n_rows < min_samples:
            problems.append("too_short")
        missing_counts = {c: int(g[c].isna().sum()) for c in required_cols if c in g.columns}
        missing_required_cols = [c for c in required_cols if c not in g.columns]
        if missing_required_cols:
            problems.append("missing_required_columns")
        if any(v > 0 for v in missing_counts.values()):
            problems.append("nan_in_required_columns")
        time_start = np.nan
        time_end = np.nan
        final_time_ok = None
        nonmonotonic_time = None
        if time_col and time_col in g.columns and n_rows:
            gt = g.sort_values(time_col)
            t = gt[time_col].to_numpy(dtype=float)
            time_start = float(np.min(t))
            time_end = float(np.max(t))
            if len(t) >= 2:
                nonmonotonic_time = bool(np.any(np.diff(t) <= 0))
                if nonmonotonic_time:
                    problems.append("nonmonotonic_or_duplicate_time")
            if expected_final_time is not None:
                final_time_ok = bool(abs(time_end - expected_final_time) <= final_time_tol)
                if not final_time_ok:
                    problems.append("missing_expected_final_time")
        explicit_status = None
        if status_col and status_col in g.columns:
            explicit_status = str(g[status_col].iloc[-1])
            if explicit_status.lower() not in {"ok", "success", "succeeded", "complete", "completed"}:
                problems.append("status_not_success")
        rows.append(
            {
                "case_id": cid,
                "n_rows": n_rows,
                "time_start": time_start,
                "time_end": time_end,
                "final_time_ok": final_time_ok,
                "nonmonotonic_time": nonmonotonic_time,
                "explicit_status": explicit_status,
                "n_missing_required_values": int(sum(missing_counts.values())),
                "problems": ";".join(sorted(set(problems))),
                "usable_for_rom": len(problems) == 0,
            }
        )
    return pd.DataFrame(rows)


def filter_usable_cases(frame: pd.DataFrame, quality: pd.DataFrame, *, case_col: str) -> pd.DataFrame:
    """Return rows belonging to cases marked usable in a quality table."""

    if "usable_for_rom" not in quality.columns or "case_id" not in quality.columns:
        raise ValueError("quality table must include case_id and usable_for_rom columns.")
    good = quality.loc[quality["usable_for_rom"], "case_id"].tolist()
    return frame[frame[case_col].isin(good)].copy()
