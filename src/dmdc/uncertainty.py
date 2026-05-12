"""Bootstrap uncertainty estimates for ROM metrics.

The goal is not to provide a full statistical inference framework.  Instead, the
helpers here give practical confidence intervals by resampling cases or residual
rows, which is useful for reports and model-comparison dashboards.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Sequence
import numpy as np
import pandas as pd


@dataclass
class BootstrapCI:
    metric: str
    estimate: float
    ci_low: float
    ci_high: float
    n_bootstrap: int
    confidence: float
    method: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    metric_name: str = "mean",
    n_bootstrap: int = 500,
    confidence: float = 0.95,
    random_state: int = 123,
) -> BootstrapCI:
    """Bootstrap a confidence interval for the mean of a sequence."""

    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return BootstrapCI(metric_name, np.nan, np.nan, np.nan, n_bootstrap, confidence, "bootstrap_mean")
    rng = np.random.default_rng(random_state)
    samples = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        draw = rng.choice(arr, size=arr.size, replace=True)
        samples[i] = float(np.mean(draw))
    alpha = 1.0 - confidence
    return BootstrapCI(
        metric=metric_name,
        estimate=float(np.mean(arr)),
        ci_low=float(np.quantile(samples, alpha / 2)),
        ci_high=float(np.quantile(samples, 1 - alpha / 2)),
        n_bootstrap=int(n_bootstrap),
        confidence=float(confidence),
        method="case_or_row_bootstrap_mean",
    )


def bootstrap_metric_ci(
    true: np.ndarray,
    pred: np.ndarray,
    metric_func: Callable[[np.ndarray, np.ndarray], float],
    *,
    metric_name: str,
    n_bootstrap: int = 500,
    confidence: float = 0.95,
    random_state: int = 123,
) -> BootstrapCI:
    """Bootstrap a metric by resampling rows of aligned true/pred arrays."""

    true = np.asarray(true, dtype=float)
    pred = np.asarray(pred, dtype=float)
    if true.shape != pred.shape:
        raise ValueError(f"true and pred must have matching shapes, got {true.shape} and {pred.shape}.")
    n = true.shape[0]
    if n == 0:
        return BootstrapCI(metric_name, np.nan, np.nan, np.nan, n_bootstrap, confidence, "row_bootstrap")
    rng = np.random.default_rng(random_state)
    vals = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        vals[i] = float(metric_func(true[idx], pred[idx]))
    alpha = 1.0 - confidence
    return BootstrapCI(
        metric=metric_name,
        estimate=float(metric_func(true, pred)),
        ci_low=float(np.quantile(vals, alpha / 2)),
        ci_high=float(np.quantile(vals, 1 - alpha / 2)),
        n_bootstrap=n_bootstrap,
        confidence=confidence,
        method="row_bootstrap",
    )


def uncertainty_table_from_case_metrics(case_metrics: pd.DataFrame, *, value_col: str = "rmse") -> pd.DataFrame:
    """Create train/test bootstrap CIs from an error-by-case table."""

    rows = []
    if case_metrics.empty or value_col not in case_metrics.columns:
        return pd.DataFrame(rows)
    group_cols = [c for c in ["model_name", "split"] if c in case_metrics.columns]
    if not group_cols:
        group_cols = [None]
        iterator = [((), case_metrics)]
    else:
        iterator = case_metrics.groupby(group_cols, dropna=False)
    for key, group in iterator:
        ci = bootstrap_mean_ci(group[value_col].to_numpy(dtype=float), metric_name=f"mean_{value_col}")
        row = ci.to_dict()
        if group_cols != [None]:
            if not isinstance(key, tuple):
                key = (key,)
            row.update({col: val for col, val in zip(group_cols, key, strict=False)})
        rows.append(row)
    return pd.DataFrame(rows)
