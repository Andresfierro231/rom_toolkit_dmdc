"""Preprocessing helpers for experimental time-series data."""

from __future__ import annotations

import pandas as pd


def resample_uniform(
    df: pd.DataFrame,
    *,
    time_col: str,
    dt: float,
    method: str = "linear",
) -> pd.DataFrame:
    """Resample numeric columns onto a uniform time grid using interpolation.

    This is intentionally simple. For production experimental data, inspect aliasing and sensor
    bandwidth before resampling.
    """

    import numpy as np

    if dt <= 0:
        raise ValueError("dt must be positive.")
    sorted_df = df.sort_values(time_col).reset_index(drop=True)
    t = sorted_df[time_col].to_numpy(dtype=float)
    t_new = np.arange(t[0], t[-1] + 0.5 * dt, dt)
    out = pd.DataFrame({time_col: t_new})
    numeric_cols = [c for c in sorted_df.columns if c != time_col and pd.api.types.is_numeric_dtype(sorted_df[c])]
    for col in numeric_cols:
        out[col] = np.interp(t_new, t, sorted_df[col].to_numpy(dtype=float))
    if method != "linear":
        raise NotImplementedError("Only linear interpolation is currently implemented.")
    return out
