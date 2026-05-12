"""Unseen-case validation tools for ROM workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .data import TimeSeriesDataset
from .metrics import rmse, relative_frobenius_error, error_by_column
from .reduced import PODDMDcPipeline
from .utils import write_json


def evaluate_pod_dmdc_on_datasets(
    model: PODDMDcPipeline,
    datasets: Sequence[TimeSeriesDataset],
    *,
    split_name: str,
    forecast_horizons: Sequence[int] = (1, 5, 10),
) -> dict[str, Any]:
    """Evaluate a POD-DMDc model on multiple held-in or held-out trajectories."""

    case_rows: list[dict[str, Any]] = []
    state_rows: list[dict[str, Any]] = []
    horizon_rows: list[dict[str, Any]] = []
    residual_frames: list[pd.DataFrame] = []

    all_true: list[NDArray[np.float64]] = []
    all_pred: list[NDArray[np.float64]] = []
    state_names = datasets[0].state_cols if datasets else None

    for ds in datasets:
        X = ds.X
        U = ds.U if ds.U.shape[1] else None
        U_future = None
        if U is not None:
            U_future = U[:-1] if U.shape[0] == X.shape[0] else U
        pred = model.rollout(X[0], U_future=U_future, n_steps=X.shape[0] - 1)
        all_true.append(X)
        all_pred.append(pred)
        case_rmse = rmse(X, pred)
        case_rows.append(
            {
                "split": split_name,
                "case_id": ds.case_id,
                "n_snapshots": int(X.shape[0]),
                "rmse": case_rmse,
                "relative_frobenius_error": relative_frobenius_error(X, pred),
            }
        )
        for row in error_by_column(X, pred, ds.state_cols):
            row.update({"split": split_name, "case_id": ds.case_id})
            state_rows.append(row)
        for h in forecast_horizons:
            if h < X.shape[0]:
                horizon_rows.append(
                    {
                        "split": split_name,
                        "case_id": ds.case_id,
                        "horizon": int(h),
                        "rmse": rmse(X[h:], pred[h:]),
                        "relative_frobenius_error": relative_frobenius_error(X[h:], pred[h:]),
                    }
                )
        residual = X - pred
        res_df = pd.DataFrame(residual, columns=[f"residual_{c}" for c in ds.state_cols])
        res_df.insert(0, "split", split_name)
        res_df.insert(1, "case_id", ds.case_id)
        if ds.time is not None:
            res_df.insert(2, "time", ds.time)
        residual_frames.append(res_df)

    X_all = np.vstack(all_true)
    P_all = np.vstack(all_pred)
    return {
        "summary": {
            "split": split_name,
            "n_cases": len(datasets),
            "n_snapshots": int(X_all.shape[0]),
            "rmse": rmse(X_all, P_all),
            "relative_frobenius_error": relative_frobenius_error(X_all, P_all),
        },
        "case_metrics": pd.DataFrame(case_rows),
        "state_metrics": pd.DataFrame(state_rows),
        "horizon_metrics": pd.DataFrame(horizon_rows),
        "residuals": pd.concat(residual_frames, ignore_index=True) if residual_frames else pd.DataFrame(),
        "state_names": state_names,
    }


def run_pod_dmdc_validation(
    train_datasets: Sequence[TimeSeriesDataset],
    test_datasets: Sequence[TimeSeriesDataset],
    *,
    pod_rank: Any = 0.999,
    dmdc_rank: Any = "full",
    center: bool = True,
    scale: bool = False,
    forecast_horizons: Sequence[int] = (1, 5, 10),
    outdir: str | Path,
    plots: bool = True,
) -> dict[str, Any]:
    """Fit POD-DMDc on train cases and evaluate train/test performance."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    state_names = train_datasets[0].state_cols
    input_names = train_datasets[0].input_cols
    model = PODDMDcPipeline(pod_rank=pod_rank, dmdc_rank=dmdc_rank, center=center, scale=scale).fit_trajectories(
        [ds.X for ds in train_datasets],
        [ds.U for ds in train_datasets],
        state_names=state_names,
        input_names=input_names,
    )
    model.save(out / "pod_dmdc_model.pkl")
    write_json(model.to_dict(), out / "pod_dmdc_summary.json")

    train_eval = evaluate_pod_dmdc_on_datasets(model, train_datasets, split_name="train", forecast_horizons=forecast_horizons)
    test_eval = evaluate_pod_dmdc_on_datasets(model, test_datasets, split_name="test", forecast_horizons=forecast_horizons)

    train_rmse = float(train_eval["summary"]["rmse"])
    test_rmse = float(test_eval["summary"]["rmse"])
    summary = {
        "model_type": "pod_dmdc",
        "train_cases": [ds.case_id for ds in train_datasets],
        "test_cases": [ds.case_id for ds in test_datasets],
        "pod_rank": pod_rank,
        "pod_rank_used": model.summary_.pod_rank_used if model.summary_ else None,
        "dmdc_rank": dmdc_rank,
        "dmdc_rank_used": model.summary_.dmdc_rank_used if model.summary_ else None,
        "train_rollout_rmse": train_rmse,
        "test_rollout_rmse": test_rmse,
        "generalization_gap_rmse": test_rmse - train_rmse,
        "generalization_gap_ratio": float(test_rmse / train_rmse) if train_rmse > 0 else float("inf"),
        "forecast_horizons": list(map(int, forecast_horizons)),
    }
    warnings = []
    if summary["generalization_gap_ratio"] > 5:
        warnings.append(
            "[GENERALIZATION_GAP] Test rollout RMSE is more than 5x training RMSE. Try lower POD rank, add relevant inputs, inspect whether test cases are outside the training regime, or review forecast_horizon_errors.csv."
        )
    write_json(summary, out / "validation_summary.json")
    pd.DataFrame([summary]).to_csv(out / "validation_summary.csv", index=False)
    (out / "warnings.txt").write_text("\n".join(warnings) + ("\n" if warnings else ""), encoding="utf-8")

    pd.concat([train_eval["case_metrics"], test_eval["case_metrics"]], ignore_index=True).to_csv(out / "error_by_case.csv", index=False)
    pd.concat([train_eval["state_metrics"], test_eval["state_metrics"]], ignore_index=True).to_csv(out / "error_by_state.csv", index=False)
    pd.concat([train_eval["horizon_metrics"], test_eval["horizon_metrics"]], ignore_index=True).to_csv(out / "forecast_horizon_errors.csv", index=False)
    pd.concat([train_eval["residuals"], test_eval["residuals"]], ignore_index=True).to_csv(out / "residuals.csv", index=False)

    if plots:
        horizon_df = pd.concat([train_eval["horizon_metrics"], test_eval["horizon_metrics"]], ignore_index=True)
        plot_forecast_horizon_errors(horizon_df, out / "forecast_error_vs_horizon.pdf")
        plot_validation_case_errors(pd.concat([train_eval["case_metrics"], test_eval["case_metrics"]], ignore_index=True), out / "error_by_case.pdf")
        plot_first_test_case(model, test_datasets[0], out / "true_vs_pred_first_test_case.pdf")

    return summary


def plot_forecast_horizon_errors(horizon_df: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots()
    if horizon_df.empty:
        ax.text(0.5, 0.5, "No horizon data", ha="center")
    else:
        for split, group in horizon_df.groupby("split"):
            avg = group.groupby("horizon", as_index=False)["rmse"].mean()
            ax.plot(avg["horizon"], avg["rmse"], marker="o", label=str(split))
        ax.set_xlabel("forecast horizon [steps]")
        ax.set_ylabel("RMSE")
        ax.set_title("Forecast horizon error")
        ax.legend()
        ax.grid(True)
    _save(fig, path)


def plot_validation_case_errors(case_df: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots()
    labels = [f"{r.split}:{r.case_id}" for r in case_df.itertuples()]
    ax.bar(np.arange(len(case_df)), case_df["rmse"].to_numpy())
    ax.set_xticks(np.arange(len(case_df)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("RMSE")
    ax.set_title("Rollout error by case")
    ax.grid(True, axis="y")
    _save(fig, path)


def plot_first_test_case(model: PODDMDcPipeline, ds: TimeSeriesDataset, path: str | Path) -> None:
    U = ds.U if ds.U.shape[1] else None
    U_future = None if U is None else (U[:-1] if U.shape[0] == ds.X.shape[0] else U)
    pred = model.rollout(ds.X[0], U_future=U_future, n_steps=ds.X.shape[0] - 1)
    t = ds.time if ds.time is not None else np.arange(ds.X.shape[0])
    fig, ax = plt.subplots()
    n_plot = min(ds.X.shape[1], 6)
    for i in range(n_plot):
        ax.plot(t, ds.X[:, i], label=f"true {ds.state_cols[i]}")
        ax.plot(t, pred[:, i], linestyle="--", label=f"pred {ds.state_cols[i]}")
    ax.set_xlabel("time" if ds.time is not None else "sample")
    ax.set_ylabel("state")
    ax.set_title(f"First test case rollout: {ds.case_id}")
    ax.legend(ncol=2, fontsize="small")
    ax.grid(True)
    _save(fig, path)


def _save(fig: plt.Figure, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
