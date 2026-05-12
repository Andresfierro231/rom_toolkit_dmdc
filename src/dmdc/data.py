"""Data loading and validation for DMDc time-series workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass
class TimeSeriesDataset:
    """Container for a DMDc-ready time-series dataset."""

    frame: pd.DataFrame
    X: NDArray[np.float64]
    U: NDArray[np.float64]
    time: NDArray[np.float64] | None
    state_cols: list[str]
    input_cols: list[str]
    output_cols: list[str]
    case_col: str | None = None
    case_id: str | int | None = None

    @property
    def dt(self) -> float | None:
        if self.time is None or len(self.time) < 2:
            return None
        return float(np.median(np.diff(self.time)))


def load_timeseries(
    path: str | Path,
    *,
    state_cols: Sequence[str],
    input_cols: Sequence[str] | None = None,
    time_col: str | None = None,
    output_cols: Sequence[str] | None = None,
    case_col: str | None = None,
    case_id: str | int | None = None,
    sort_by_time: bool = True,
) -> TimeSeriesDataset:
    """Load CSV, Excel, Parquet, or NumPy NPZ time-series data.

    CSV/Excel/Parquet files are expected to have named columns. NPZ files should contain arrays named
    X, U, and optionally time. For messy sources, prefer ``dmdc import-data`` first, then point modeling commands at the canonical CSV/Parquet output.
    """

    path = Path(path)
    input_cols = list(input_cols or [])
    output_cols = list(output_cols or [])
    state_cols = list(state_cols)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            df = pd.read_excel(path)
        except ImportError as exc:
            raise RuntimeError("Excel input requires openpyxl/xlrd. Install openpyxl or use dmdc import-data to convert to CSV/Parquet.") from exc
    elif path.suffix.lower() in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif path.suffix.lower() == ".npz":
        data = np.load(path)
        X = _ensure_2d(data["X"], "X")
        U = _ensure_2d(data["U"], "U") if "U" in data else np.zeros((X.shape[0], 0))
        time = np.asarray(data["time"], dtype=float) if "time" in data else None
        df = pd.DataFrame(X, columns=state_cols or [f"x{i}" for i in range(X.shape[1])])
        for j in range(U.shape[1]):
            df[f"u{j}"] = U[:, j]
        if time is not None:
            df[time_col or "time"] = time
            time_col = time_col or "time"
        input_cols = input_cols or [f"u{j}" for j in range(U.shape[1])]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}. Use .csv, .parquet, or .npz.")

    if case_col is not None and case_id is not None:
        if case_col not in df.columns:
            raise ValueError(f"case_col={case_col!r} not found in data.")
        df = df[df[case_col] == case_id].copy()
        if df.empty:
            raise ValueError(f"No rows found where {case_col} == {case_id!r}.")

    required = list(state_cols) + list(input_cols) + list(output_cols)
    if time_col:
        required.append(time_col)
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if sort_by_time and time_col:
        df = df.sort_values(time_col).reset_index(drop=True)

    selected = list(dict.fromkeys(required))
    nan_counts = df[selected].isna().sum()
    bad = nan_counts[nan_counts > 0]
    if not bad.empty:
        raise ValueError(f"Missing values found in required columns: {bad.to_dict()}")

    X = df[state_cols].to_numpy(dtype=float)
    U = df[input_cols].to_numpy(dtype=float) if input_cols else np.zeros((len(df), 0), dtype=float)
    time = df[time_col].to_numpy(dtype=float) if time_col else None

    validate_timeseries(X, U, time=time)
    return TimeSeriesDataset(
        frame=df,
        X=X,
        U=U,
        time=time,
        state_cols=state_cols,
        input_cols=input_cols,
        output_cols=output_cols,
        case_col=case_col,
        case_id=case_id,
    )


def validate_timeseries(
    X: NDArray[np.float64],
    U: NDArray[np.float64],
    *,
    time: NDArray[np.float64] | None = None,
    uniform_time_tol: float = 1e-6,
) -> dict[str, object]:
    """Validate a time-series dataset and return warnings/metadata."""

    warnings: list[str] = []
    if X.ndim != 2:
        raise ValueError("X must be 2D: (n_timesteps, n_states).")
    if U.ndim != 2:
        raise ValueError("U must be 2D: (n_timesteps, n_inputs).")
    if X.shape[0] != U.shape[0]:
        raise ValueError(f"X and U row counts must match; got {X.shape[0]} and {U.shape[0]}.")
    if X.shape[0] < 2:
        raise ValueError("At least two time steps are required.")
    if not np.all(np.isfinite(X)):
        raise ValueError("X contains NaN or infinite values.")
    if not np.all(np.isfinite(U)):
        raise ValueError("U contains NaN or infinite values.")

    if time is not None:
        if len(time) != X.shape[0]:
            raise ValueError("time length must match the number of rows in X.")
        dt = np.diff(time)
        if np.any(dt <= 0):
            raise ValueError("time column must be strictly increasing after sorting/filtering.")
        if np.max(np.abs(dt - np.median(dt))) > uniform_time_tol * max(abs(np.median(dt)), 1.0):
            warnings.append("Detected nonuniform/adaptive time steps. This is expected for many SAM and experimental logs. Ordinary DMDc will learn a sample-to-sample map; for physical-time dynamics use dmdc adaptive-fit or explicitly resample first.")

    return {"warnings": warnings, "n_timesteps": X.shape[0], "n_states": X.shape[1], "n_inputs": U.shape[1]}


def _ensure_2d(arr: object, name: str) -> NDArray[np.float64]:
    out = np.asarray(arr, dtype=float)
    if out.ndim == 1:
        out = out.reshape(-1, 1)
    if out.ndim != 2:
        raise ValueError(f"{name} must be 1D or 2D.")
    return out


def load_trajectories(
    path: str | Path,
    *,
    state_cols: Sequence[str],
    input_cols: Sequence[str] | None = None,
    time_col: str | None = None,
    output_cols: Sequence[str] | None = None,
    case_col: str,
    sort_by_time: bool = True,
) -> list[TimeSeriesDataset]:
    """Load a file containing multiple independent trajectories/cases.

    Parameters
    ----------
    path:
        CSV or Parquet file containing all trajectories stacked row-wise.
    state_cols, input_cols, time_col:
        Same meaning as :func:`load_timeseries`.
    case_col:
        Column identifying independent trajectories, experiments, runs, or simulation cases.

    Returns
    -------
    list[TimeSeriesDataset]
        One validated dataset per case. Each case can then be safely passed to
        ``DMDcModel.fit_trajectories``.

    Notes
    -----
    This helper is intentionally conservative: it uses ``case_col`` to split the data and never
    creates transitions between different case IDs. That is essential for parameter sweeps and
    repeated experiments.
    """

    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            df = pd.read_excel(path)
        except ImportError as exc:
            raise RuntimeError("Excel input requires openpyxl/xlrd. Install openpyxl or convert with dmdc import-data.") from exc
    elif path.suffix.lower() in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    else:
        raise ValueError("Multi-trajectory loading currently supports CSV, Excel, and Parquet files.")

    if case_col not in df.columns:
        raise ValueError(f"case_col={case_col!r} not found in data.")

    # Preserve sorted unique order for reproducibility.
    case_ids = sorted(df[case_col].dropna().unique().tolist())
    datasets: list[TimeSeriesDataset] = []
    for cid in case_ids:
        ds = load_timeseries(
            path,
            state_cols=state_cols,
            input_cols=input_cols,
            time_col=time_col,
            output_cols=output_cols,
            case_col=case_col,
            case_id=cid,
            sort_by_time=sort_by_time,
        )
        datasets.append(ds)

    if not datasets:
        raise ValueError(f"No trajectories found in case column {case_col!r}.")
    return datasets
