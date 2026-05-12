"""Steady-state and transient window selection utilities.

Thermal-hydraulic loops often contain startup transients, intermediate response,
and late quasi-steady behavior.  A single ROM study may need to exclude startup,
train only on transients, or validate only on steady-state portions.  These
helpers provide explicit, auditable time-window filtering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import pandas as pd


@dataclass(frozen=True)
class TimeWindow:
    """Closed interval used to filter a time-series table."""

    name: str
    t_min: float | None = None
    t_max: float | None = None

    def contains(self, values: pd.Series) -> pd.Series:
        mask = pd.Series(True, index=values.index)
        if self.t_min is not None:
            mask &= values >= self.t_min
        if self.t_max is not None:
            mask &= values <= self.t_max
        return mask


def filter_time_window(
    frame: pd.DataFrame,
    *,
    time_col: str,
    t_min: float | None = None,
    t_max: float | None = None,
) -> pd.DataFrame:
    """Return rows satisfying ``t_min <= time <= t_max``.

    The function never silently modifies the original dataframe.  The returned
    dataframe is copied and sorted by time, which keeps downstream transition
    construction reproducible.
    """

    if time_col not in frame.columns:
        raise ValueError(f"time_col={time_col!r} not found in dataframe.")
    window = TimeWindow(name="custom", t_min=t_min, t_max=t_max)
    out = frame.loc[window.contains(frame[time_col])].copy()
    return out.sort_values(time_col).reset_index(drop=True)


def split_transient_steady_windows(
    frame: pd.DataFrame,
    *,
    time_col: str,
    steady_start: float,
    case_col: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Split a table into transient and steady-state portions.

    ``transient`` contains rows with ``time < steady_start`` and ``steady``
    contains rows with ``time >= steady_start``.  The logic is applied to each
    case consistently when ``case_col`` is supplied because the same physical
    threshold is normally desired across a parameter sweep.
    """

    if time_col not in frame.columns:
        raise ValueError(f"time_col={time_col!r} not found in dataframe.")
    transient = frame[frame[time_col] < steady_start].copy()
    steady = frame[frame[time_col] >= steady_start].copy()
    for df in (transient, steady):
        sort_cols = [case_col, time_col] if case_col and case_col in df.columns else [time_col]
        df.sort_values(sort_cols, inplace=True)
        df.reset_index(drop=True, inplace=True)
    return {"transient": transient, "steady": steady}


def describe_window(frame_before: pd.DataFrame, frame_after: pd.DataFrame, *, time_col: str, case_col: str | None = None) -> dict[str, Any]:
    """Summarize how many rows/cases remain after time-window filtering."""

    return {
        "n_rows_before": int(len(frame_before)),
        "n_rows_after": int(len(frame_after)),
        "n_cases_before": int(frame_before[case_col].nunique()) if case_col and case_col in frame_before.columns else 1,
        "n_cases_after": int(frame_after[case_col].nunique()) if case_col and case_col in frame_after.columns else 1,
        "time_start_after": None if frame_after.empty else float(frame_after[time_col].min()),
        "time_end_after": None if frame_after.empty else float(frame_after[time_col].max()),
    }
