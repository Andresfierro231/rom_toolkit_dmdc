"""Data inspection and irregular time-step handling utilities.

DMD/DMDc learns a discrete map between samples.  If a case has nonuniform time steps, duplicate
sampling times, or large gaps, the learned operator may mix several physical time intervals into
one map.  Nonuniform time steps are treated as the default real-data expectation, not an error. These helpers make such issues explicit and provide opt-in resampling or guidance toward adaptive-fit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from .utils import write_json
from .warnings import FriendlyWarning, write_warnings, warnings_to_dicts


@dataclass
class InspectionResult:
    """Structured result from inspecting a time-series table."""

    summary: dict[str, object]
    columns_summary: pd.DataFrame
    missing_values: pd.DataFrame
    dt_summary_by_case: pd.DataFrame
    case_lengths: pd.DataFrame
    state_variance: pd.DataFrame
    input_variance: pd.DataFrame
    large_time_gaps: pd.DataFrame
    warnings: list[FriendlyWarning]

    def save(self, outdir: str | Path) -> None:
        """Write all inspection artifacts to ``outdir``."""

        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        write_json({**self.summary, "warnings": warnings_to_dicts(self.warnings)}, out / "inspection_summary.json")
        self.columns_summary.to_csv(out / "columns_summary.csv", index=False)
        self.missing_values.to_csv(out / "missing_values.csv", index=False)
        self.dt_summary_by_case.to_csv(out / "dt_summary_by_case.csv", index=False)
        self.case_lengths.to_csv(out / "case_lengths.csv", index=False)
        self.state_variance.to_csv(out / "state_variance.csv", index=False)
        self.input_variance.to_csv(out / "input_variance.csv", index=False)
        self.large_time_gaps.to_csv(out / "large_time_gaps.csv", index=False)
        write_warnings(self.warnings, out / "warnings.txt")
        _write_inspection_tex(self, out / "inspection_report.tex")


def read_table(path: str | Path) -> pd.DataFrame:
    """Read CSV, Excel, or Parquet input data."""

    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            return pd.read_excel(path)
        except ImportError as exc:
            raise RuntimeError("Excel input requires openpyxl/xlrd. Install openpyxl or convert with dmdc import-data.") from exc
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported table type {path.suffix!r}. Use CSV, Excel, or Parquet for inspection/resampling.")


def inspect_table(
    frame: pd.DataFrame,
    *,
    time_col: str | None = None,
    case_col: str | None = None,
    state_cols: Sequence[str] | None = None,
    input_cols: Sequence[str] | None = None,
    uniform_time_rtol: float = 1e-3,
    large_gap_factor: float = 5.0,
) -> InspectionResult:
    """Inspect a data table and emit actionable warnings.

    Parameters
    ----------
    frame:
        Raw data table.
    time_col, case_col:
        Time and case columns.  ``case_col`` is optional; if absent, the table is treated as one case.
    state_cols, input_cols:
        Columns that will be used by ROM workflows.  These are emphasized in missing-value and
        variance diagnostics.
    uniform_time_rtol:
        Relative tolerance used when deciding whether a case has irregular time steps.
    large_gap_factor:
        A gap is marked large when ``dt > large_gap_factor * median_dt`` for that case.
    """

    state_cols = list(state_cols or [])
    input_cols = list(input_cols or [])
    warnings: list[FriendlyWarning] = []
    required = state_cols + input_cols + ([time_col] if time_col else []) + ([case_col] if case_col else [])
    missing_required = [c for c in required if c not in frame.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")

    columns_summary = pd.DataFrame(
        {
            "column": frame.columns,
            "dtype": [str(frame[c].dtype) for c in frame.columns],
            "n_missing": [int(frame[c].isna().sum()) for c in frame.columns],
            "n_unique": [int(frame[c].nunique(dropna=True)) for c in frame.columns],
        }
    )
    inspect_cols = list(dict.fromkeys(required)) if required else list(frame.columns)
    missing_values = pd.DataFrame(
        {"column": inspect_cols, "n_missing": [int(frame[c].isna().sum()) for c in inspect_cols]}
    )
    bad_missing = missing_values[missing_values["n_missing"] > 0]
    if not bad_missing.empty:
        warnings.append(
            FriendlyWarning(
                code="MISSING_VALUES",
                message=f"Required/modeling columns contain missing values: {bad_missing.to_dict(orient='records')}",
                why_it_matters="Most DMD/DMDc/POD workflows use dense linear algebra and cannot interpret NaN values.",
                suggested_actions=("Interpolate short gaps if justified.", "Drop bad rows/cases.", "Fill inputs only when the value is physically known."),
            )
        )

    if time_col:
        dt_summary, large_gaps, time_warnings = summarize_dt_by_case(
            frame,
            time_col=time_col,
            case_col=case_col,
            uniform_time_rtol=uniform_time_rtol,
            large_gap_factor=large_gap_factor,
        )
        warnings.extend(time_warnings)
    else:
        dt_summary = pd.DataFrame()
        large_gaps = pd.DataFrame()
        warnings.append(
            FriendlyWarning(
                code="NO_TIME_COLUMN",
                message="No time column was provided.",
                why_it_matters="The model can still use sample index, but time-step diagnostics and resampling are unavailable.",
                suggested_actions=("Provide --time-col when your data has physical time.",),
            )
        )

    if case_col:
        case_lengths = frame.groupby(case_col, dropna=False).size().reset_index(name="n_rows")
    else:
        case_lengths = pd.DataFrame({"case_id": ["__single_case__"], "n_rows": [len(frame)]})

    state_variance = _variance_frame(frame, state_cols)
    input_variance = _variance_frame(frame, input_cols)
    near_zero_states = state_variance[state_variance["variance"] <= 1e-14]["column"].tolist()
    near_zero_inputs = input_variance[input_variance["variance"] <= 1e-14]["column"].tolist()
    if near_zero_states:
        warnings.append(
            FriendlyWarning(
                code="NEAR_ZERO_STATE_VARIANCE",
                message=f"Some state columns have near-zero variance: {near_zero_states}",
                why_it_matters="Near-constant states can make scaling, POD energy, and error metrics misleading.",
                suggested_actions=("Check whether these columns are real states or constants.", "Consider excluding constant states."),
            )
        )
    if near_zero_inputs:
        warnings.append(
            FriendlyWarning(
                code="NEAR_ZERO_INPUT_VARIANCE",
                message=f"Some input columns are constant or nearly constant: {near_zero_inputs}",
                why_it_matters="A constant input can still encode operating condition across cases, but within one case it may be hard to identify dynamic input effects.",
                suggested_actions=("Keep constant inputs for multi-case studies if values differ by case.", "Do not over-interpret B columns from a single constant-input run."),
            )
        )

    summary = {
        "time_step_policy": "nonuniform/adaptive time steps are expected; use adaptive-fit for physical-time models or resample explicitly if a fixed discrete map is desired",
        "n_rows": int(len(frame)),
        "n_columns": int(frame.shape[1]),
        "n_cases": int(frame[case_col].nunique()) if case_col else 1,
        "time_col": time_col,
        "case_col": case_col,
        "state_cols": state_cols,
        "input_cols": input_cols,
    }
    return InspectionResult(
        summary=summary,
        columns_summary=columns_summary,
        missing_values=missing_values,
        dt_summary_by_case=dt_summary,
        case_lengths=case_lengths,
        state_variance=state_variance,
        input_variance=input_variance,
        large_time_gaps=large_gaps,
        warnings=warnings,
    )


def summarize_dt_by_case(
    frame: pd.DataFrame,
    *,
    time_col: str,
    case_col: str | None = None,
    uniform_time_rtol: float = 1e-3,
    large_gap_factor: float = 5.0,
) -> tuple[pd.DataFrame, pd.DataFrame, list[FriendlyWarning]]:
    """Summarize time-step quality case by case."""

    warnings: list[FriendlyWarning] = []
    rows: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    groups = frame.groupby(case_col, dropna=False) if case_col else [("__single_case__", frame)]
    for cid, group in groups:
        g = group.sort_values(time_col)
        t = g[time_col].to_numpy(dtype=float)
        n = len(t)
        if n < 2:
            rows.append({"case_id": cid, "n_samples": n, "median_dt": np.nan, "min_dt": np.nan, "max_dt": np.nan, "is_strictly_increasing": False, "is_uniform": False})
            warnings.append(FriendlyWarning("TOO_FEW_SAMPLES", f"Case {cid!r} has fewer than two samples."))
            continue
        dt = np.diff(t)
        duplicate_count = int(np.sum(dt == 0))
        nonmonotonic_count = int(np.sum(dt <= 0))
        strictly_increasing = nonmonotonic_count == 0
        positive_dt = dt[dt > 0]
        median_dt = float(np.median(positive_dt)) if positive_dt.size else float("nan")
        max_dev = float(np.max(np.abs(positive_dt - median_dt))) if positive_dt.size else float("nan")
        tol = uniform_time_rtol * max(abs(median_dt), 1.0)
        is_uniform = bool(positive_dt.size and max_dev <= tol and strictly_increasing)
        rows.append(
            {
                "case_id": cid,
                "n_samples": n,
                "time_start": float(np.min(t)),
                "time_end": float(np.max(t)),
                "median_dt": median_dt,
                "min_dt": float(np.min(dt)),
                "max_dt": float(np.max(dt)),
                "dt_std": float(np.std(positive_dt)) if positive_dt.size else np.nan,
                "duplicate_time_count": duplicate_count,
                "nonmonotonic_dt_count": nonmonotonic_count,
                "is_strictly_increasing": strictly_increasing,
                "is_uniform": is_uniform,
            }
        )
        if duplicate_count:
            warnings.append(
                FriendlyWarning(
                    "DUPLICATE_TIME_VALUES",
                    f"Case {cid!r} has {duplicate_count} duplicate time step(s).",
                    "Duplicate times make it ambiguous which sample comes first in a discrete map.",
                    ("Remove duplicates.", "Average repeated measurements if that is physically justified."),
                )
            )
        if not strictly_increasing:
            warnings.append(
                FriendlyWarning(
                    "NON_MONOTONIC_TIME",
                    f"Case {cid!r} has non-increasing time values before/after sorting.",
                    "DMD/DMDc transitions require a clear ordering in time.",
                    ("Sort each case by time.", "Remove duplicate or reversed timestamps."),
                )
            )
        if strictly_increasing and not is_uniform:
            warnings.append(
                FriendlyWarning(
                    "IRREGULAR_TIME_STEP",
                    f"Case {cid!r} has nonuniform dt. median_dt={median_dt:.6g}, max_dt={np.max(dt):.6g}.",
                    "Nonuniform dt is common in adaptive SAM/experimental data. A single discrete A matrix is a sample-to-sample map unless you use a time-aware model.",
                    ("Use dmdc adaptive-fit for a physical-time continuous generator.", "Resample explicitly only if a fixed-step discrete map is required.", "Inspect large gaps before deciding whether interpolation is physically justified."),
                )
            )
        if positive_dt.size and np.isfinite(median_dt):
            large_idx = np.where(dt > large_gap_factor * median_dt)[0]
            for idx in large_idx:
                gaps.append({"case_id": cid, "row_before_sorted": int(idx), "time_before": float(t[idx]), "time_after": float(t[idx + 1]), "dt": float(dt[idx]), "median_dt": median_dt})
            if len(large_idx):
                warnings.append(
                    FriendlyWarning(
                        "LARGE_TIME_GAPS",
                        f"Case {cid!r} has {len(large_idx)} gap(s) larger than {large_gap_factor:g}× median dt.",
                        "Large gaps can dominate rollout error and make interpolation unreliable.",
                        ("Inspect large_time_gaps.csv.", "Drop large-gap segments or resample only within continuous regions."),
                    )
                )
    return pd.DataFrame(rows), pd.DataFrame(gaps), warnings


def resample_all_cases(
    frame: pd.DataFrame,
    *,
    time_col: str,
    dt: float,
    method: str = "linear",
    case_col: str | None = None,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Resample one or more cases to a uniform time grid.

    Resampling is explicit and opt-in.  Non-numeric columns other than ``case_col`` are not
    interpolated unless they are listed in ``columns`` and can be converted to numeric values.
    """

    if dt <= 0:
        raise ValueError("dt must be positive.")
    if method != "linear":
        raise ValueError("Only linear interpolation is currently supported.")
    columns = list(columns or [c for c in frame.columns if c not in {time_col, case_col} and pd.api.types.is_numeric_dtype(frame[c])])
    groups = frame.groupby(case_col, dropna=False) if case_col else [(None, frame)]
    out_frames: list[pd.DataFrame] = []
    for cid, group in groups:
        g = group.sort_values(time_col).drop_duplicates(subset=[time_col], keep="first")
        t = g[time_col].to_numpy(dtype=float)
        if len(t) < 2:
            continue
        new_t = np.arange(t[0], t[-1] + 0.5 * dt, dt)
        out = pd.DataFrame({time_col: new_t})
        if case_col:
            out[case_col] = cid
        for col in columns:
            out[col] = np.interp(new_t, t, g[col].to_numpy(dtype=float))
        out_frames.append(out)
    if not out_frames:
        raise ValueError("No cases had enough points to resample.")
    ordered_cols = ([case_col] if case_col else []) + [time_col] + [c for c in columns if c not in {case_col, time_col}]
    return pd.concat(out_frames, ignore_index=True)[ordered_cols]


def _variance_frame(frame: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        values = pd.to_numeric(frame[col], errors="coerce")
        rows.append({"column": col, "variance": float(values.var(ddof=0)), "std": float(values.std(ddof=0)), "min": float(values.min()), "max": float(values.max())})
    return pd.DataFrame(rows)


def _write_inspection_tex(result: InspectionResult, path: str | Path) -> None:
    """Write a tiny LaTeX inspection report without requiring a TeX installation."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    warning_items = "\n".join(f"\\item \texttt{{{w.code}}}: {w.message}" for w in result.warnings) or "\\item No warnings emitted."
    tex = r"""\documentclass{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\title{DMDc/ROM Data Inspection Report}
\date{}
\begin{document}
\maketitle
\section*{Summary}
"""
    tex += "\n".join(f"\\textbf{{{k}}}: {v}\\\\" for k, v in result.summary.items())
    tex += r"""
\section*{Warnings}
\begin{itemize}
""" + warning_items + r"""
\end{itemize}
\section*{Notes}
This report is generated as plain \LaTeX. Compile with \texttt{pdflatex inspection\_report.tex} if desired.
\end{document}
"""
    path.write_text(tex, encoding="utf-8")
