"""Best-model recommendation helpers for comparison and sweep dashboards."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def recommend_best_model(
    table: pd.DataFrame,
    *,
    error_col: str = "test_rollout_rmse",
    require_stable: bool = True,
    max_generalization_ratio: float | None = None,
) -> dict[str, object]:
    """Recommend a model/run from a comparison or sweep table.

    The recommendation is intentionally transparent: it records the filters used
    and the reason the selected row was chosen.
    """

    if table.empty:
        return {"status": "no_candidates", "recommendation": None, "reason": "The input table is empty."}
    df = table.copy()
    filters = []
    if "status" in df.columns:
        before = len(df)
        df = df[df["status"].fillna("ok") == "ok"]
        filters.append(f"kept {len(df)}/{before} candidates with status == ok")
    if require_stable and "stability_status" in df.columns:
        before = len(df)
        stable_mask = ~df["stability_status"].astype(str).str.contains("unstable", case=False, na=False)
        df = df[stable_mask]
        filters.append(f"kept {len(df)}/{before} candidates without unstable stability status")
    if max_generalization_ratio is not None and "generalization_ratio" in df.columns:
        before = len(df)
        df = df[pd.to_numeric(df["generalization_ratio"], errors="coerce") <= max_generalization_ratio]
        filters.append(f"kept {len(df)}/{before} candidates with generalization_ratio <= {max_generalization_ratio}")
    if df.empty:
        df = table.copy()
        filters.append("all filters removed all candidates; fell back to the full table")
    if error_col not in df.columns:
        return {"status": "missing_error_column", "recommendation": None, "reason": f"Column {error_col!r} was not found."}
    order = pd.to_numeric(df[error_col], errors="coerce")
    if order.notna().sum() == 0:
        return {"status": "no_finite_error", "recommendation": None, "reason": f"Column {error_col!r} has no finite values."}
    best = df.loc[order.idxmin()].to_dict()
    model_name = best.get("model_name", best.get("run_name", "candidate"))
    reason = f"Selected {model_name!r} because it has the lowest {error_col} among candidates after transparent filters."
    return {"status": "ok", "recommendation": best, "filters": filters, "reason": reason}


def write_recommendation(recommendation: dict[str, object], path: str | Path) -> None:
    """Write a human-readable recommendation text file."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["Best Model Recommendation", "=========================", ""]
    lines.append(f"Status: {recommendation.get('status')}")
    lines.append(f"Reason: {recommendation.get('reason')}")
    filters = recommendation.get("filters") or []
    if filters:
        lines.append("")
        lines.append("Filters used:")
        for item in filters:
            lines.append(f"- {item}")
    rec = recommendation.get("recommendation")
    if isinstance(rec, dict):
        lines.append("")
        lines.append("Selected row:")
        for key, value in rec.items():
            lines.append(f"- {key}: {value}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
