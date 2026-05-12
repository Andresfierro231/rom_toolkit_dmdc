"""Train/test operating-condition summaries and extrapolation warnings."""

from __future__ import annotations

from typing import Sequence
import numpy as np
import pandas as pd


def summarize_operating_conditions(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    *,
    condition_cols: Sequence[str],
) -> pd.DataFrame:
    """Compare train and test ranges for operating-condition columns.

    A test case whose heater power, ambient temperature, or boundary condition is
    outside the training range is extrapolating.  This table makes that explicit
    so high test error is not misinterpreted as only a model deficiency.
    """

    rows: list[dict[str, object]] = []
    for col in condition_cols:
        if col not in train_frame.columns or col not in test_frame.columns:
            continue
        train = pd.to_numeric(train_frame[col], errors="coerce").dropna()
        test = pd.to_numeric(test_frame[col], errors="coerce").dropna()
        if train.empty or test.empty:
            rows.append({"condition": col, "status": "missing_numeric_values"})
            continue
        train_min = float(train.min())
        train_max = float(train.max())
        test_min = float(test.min())
        test_max = float(test.max())
        outside = bool(test_min < train_min or test_max > train_max)
        margin_low = test_min - train_min
        margin_high = test_max - train_max
        rows.append(
            {
                "condition": col,
                "train_min": train_min,
                "train_max": train_max,
                "test_min": test_min,
                "test_max": test_max,
                "test_outside_train_range": outside,
                "low_margin_test_minus_train_min": margin_low,
                "high_margin_test_minus_train_max": margin_high,
                "status": "extrapolation" if outside else "interpolation_or_overlap",
            }
        )
    return pd.DataFrame(rows)


def operating_condition_warnings(summary: pd.DataFrame) -> list[str]:
    """Return human-readable warnings from an operating-condition summary."""

    if summary.empty or "test_outside_train_range" not in summary.columns:
        return []
    warnings: list[str] = []
    for row in summary[summary["test_outside_train_range"] == True].itertuples(index=False):  # noqa: E712
        warnings.append(
            f"Test operating condition {row.condition!r} is outside the training range: "
            f"train=[{row.train_min:.6g}, {row.train_max:.6g}], "
            f"test=[{row.test_min:.6g}, {row.test_max:.6g}]. Treat this as extrapolation."
        )
    return warnings
