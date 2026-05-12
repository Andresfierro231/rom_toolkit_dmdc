"""Rank, delay, and model sweeps for ROM model selection.

Phase 8 adds a systematic way to answer practical ROM questions such as:

- How many POD modes should I keep?
- Does delay embedding help this loop/system?
- Which DMDc/POD-DMDc/POD-ML choice generalizes best to unseen cases?
- Which candidate is accurate *and* stable?

The implementation is intentionally simple and transparent.  Each candidate is
fit on the training cases, rolled out on both train and test cases, scored with
RMSE/generalization-gap metrics, and optionally diagnosed for linear stability.
The output is a set of portable CSV/Markdown/LaTeX dashboards plus plots.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .baselines import fit_baseline_or_rom
from .data import TimeSeriesDataset
from .dashboards import save_dashboard
from .delayed import make_delay_embedding
from .metrics import rmse, relative_frobenius_error
from .stability import analyze_transition_matrix
from .utils import write_json


def run_rank_delay_sweep(
    train_datasets: Sequence[TimeSeriesDataset],
    test_datasets: Sequence[TimeSeriesDataset],
    *,
    models: Sequence[str] = ("pod_dmdc",),
    pod_ranks: Sequence[Any] = (0.999,),
    dmdc_ranks: Sequence[Any] = ("full",),
    n_delays: Sequence[int] = (1,),
    center: bool = True,
    scale: bool = False,
    outdir: str | Path,
    plots: bool = True,
) -> pd.DataFrame:
    """Run a grid sweep over model type, POD rank, DMDc rank, and delay count.

    Parameters
    ----------
    train_datasets, test_datasets:
        Case-aware datasets.  Transitions are never created across case IDs.
    models:
        Model names understood by :func:`dmdc.baselines.fit_baseline_or_rom`, e.g.
        ``"dmdc"``, ``"pod_dmdc"``, ``"pod_ml_ridge"``, ``"persistence"``.
    pod_ranks, dmdc_ranks, n_delays:
        Candidate values.  Rank values may be integers, ``"full"``, or energy
        thresholds such as ``0.999``.
    center, scale:
        POD preprocessing options used for POD-based models.
    outdir:
        Directory where dashboards and per-candidate metadata are written.
    plots:
        If true, save sweep summary plots.

    Notes
    -----
    Delay embedding is applied *case by case* before fitting.  For POD-DMDc this
    means POD is fit on the delay-embedded state.  The resulting RMSE is therefore
    an embedded-state RMSE when ``n_delays > 1``.  This is useful for comparing
    delay choices, but final publication plots should still inspect the current
    ``lag0`` variables directly.
    """

    if not train_datasets:
        raise ValueError("At least one training case is required for a sweep.")
    if not test_datasets:
        raise ValueError("At least one test case is required for a sweep.")

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    run_root = out / "runs"
    run_root.mkdir(exist_ok=True)

    rows: list[dict[str, Any]] = []
    run_index = 0
    for model_name, pod_rank, dmdc_rank, delay in product(models, pod_ranks, dmdc_ranks, n_delays):
        run_index += 1
        run_name = _candidate_name(run_index, model_name, pod_rank, dmdc_rank, delay)
        run_dir = run_root / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        try:
            train_work = _delay_datasets(train_datasets, delay)
            test_work = _delay_datasets(test_datasets, delay)
            state_names = train_work[0].state_cols
            input_names = train_work[0].input_cols

            model = fit_baseline_or_rom(
                model_name,
                [ds.X for ds in train_work],
                [ds.U for ds in train_work],
                train_time=[ds.time for ds in train_work],
                state_names=state_names,
                input_names=input_names,
                dmdc_rank=dmdc_rank,
                pod_rank=pod_rank,
                center=center,
                scale=scale,
            )
            train_eval = _evaluate_rollouts(model, train_work)
            test_eval = _evaluate_rollouts(model, test_work)
            stability = _stability_summary(model)
            train_rmse = float(train_eval["rmse"])
            test_rmse = float(test_eval["rmse"])
            status = "ok"
            error_message = ""
        except Exception as exc:  # pragma: no cover - exercised by user data more often than tests
            train_rmse = np.nan
            test_rmse = np.nan
            stability = {"spectral_radius": np.nan, "n_unstable_eigenvalues": np.nan, "stability_status": "failed"}
            status = "failed"
            error_message = str(exc)
            train_eval = {"case_metrics": pd.DataFrame(), "rmse": np.nan, "relative_frobenius_error": np.nan}
            test_eval = {"case_metrics": pd.DataFrame(), "rmse": np.nan, "relative_frobenius_error": np.nan}

        row = {
            "run_name": run_name,
            "model_name": model_name,
            "pod_rank": pod_rank,
            "dmdc_rank": dmdc_rank,
            "n_delays": int(delay),
            "center": bool(center),
            "scale": bool(scale),
            "train_rollout_rmse": train_rmse,
            "test_rollout_rmse": test_rmse,
            "generalization_gap": test_rmse - train_rmse if np.isfinite(train_rmse) and np.isfinite(test_rmse) else np.nan,
            "generalization_ratio": test_rmse / train_rmse if np.isfinite(train_rmse) and train_rmse > 0 else np.nan,
            "spectral_radius": stability.get("spectral_radius"),
            "n_unstable_eigenvalues": stability.get("n_unstable_eigenvalues"),
            "stability_status": stability.get("stability_status"),
            "status": status,
            "error_message": error_message,
        }
        rows.append(row)
        write_json(row, run_dir / "candidate_summary.json")
        train_eval["case_metrics"].to_csv(run_dir / "train_error_by_case.csv", index=False)
        test_eval["case_metrics"].to_csv(run_dir / "test_error_by_case.csv", index=False)

    results = pd.DataFrame(rows)
    if not results.empty:
        # Put successful, accurate candidates first. Failed candidates remain visible at the bottom.
        results = results.sort_values(["status", "test_rollout_rmse"], na_position="last").reset_index(drop=True)

    save_dashboard(results, out, "sweep_results", caption="Rank/delay/model sweep results")
    best = results[results["status"] == "ok"].sort_values("test_rollout_rmse").head(10)
    save_dashboard(best, out, "best_models", caption="Best sweep candidates by held-out test RMSE")
    write_json(
        {
            "n_candidates": int(len(results)),
            "n_successful": int((results["status"] == "ok").sum()) if not results.empty else 0,
            "best_run": None if best.empty else str(best.iloc[0]["run_name"]),
            "best_model": None if best.empty else str(best.iloc[0]["model_name"]),
        },
        out / "sweep_summary.json",
    )
    if plots:
        plot_rank_vs_error(results, out / "rank_vs_error.pdf")
        plot_delay_vs_error(results, out / "delay_vs_error.pdf")
        plot_stability_vs_error(results, out / "stability_vs_error.pdf")
    return results


def parse_sweep_values(values: Iterable[str] | None, *, default: Sequence[Any]) -> list[Any]:
    """Parse CLI/config sweep values into rank/delay Python objects.

    Strings such as ``"full"`` remain strings, integer-looking values become
    ``int``, and decimal-looking values become ``float``.  This keeps configs
    readable while preserving the rank conventions used elsewhere in the repo.
    """

    if values is None:
        return list(default)
    parsed: list[Any] = []
    for value in values:
        if isinstance(value, (int, float)):
            parsed.append(value)
            continue
        text = str(value)
        if text.lower() in {"full", "auto"}:
            parsed.append(text.lower())
        else:
            try:
                parsed.append(float(text) if "." in text else int(text))
            except ValueError:
                parsed.append(text)
    return parsed or list(default)


def _candidate_name(index: int, model_name: str, pod_rank: Any, dmdc_rank: Any, n_delay: int) -> str:
    def clean(v: Any) -> str:
        return str(v).replace(".", "p").replace("/", "-")

    return f"run_{index:03d}__{model_name}__pod{clean(pod_rank)}__dmdc{clean(dmdc_rank)}__delay{n_delay}"


def _delay_datasets(datasets: Sequence[TimeSeriesDataset], n_delays: int) -> list[TimeSeriesDataset]:
    if n_delays == 1:
        return list(datasets)
    out: list[TimeSeriesDataset] = []
    for ds in datasets:
        U_in = ds.U if ds.U.shape[1] else None
        Z, U_aligned, z_names = make_delay_embedding(ds.X, U_in, n_delays=n_delays, state_names=ds.state_cols)
        if U_aligned is None:
            U_aligned = np.zeros((Z.shape[0], 0), dtype=float)
        time = None if ds.time is None else ds.time[n_delays - 1 :]
        # ``replace`` preserves frame/case metadata while substituting the arrays
        # that downstream model APIs actually consume.
        out.append(replace(ds, X=Z, U=U_aligned, time=time, state_cols=z_names))
    return out


def _evaluate_rollouts(model: object, datasets: Sequence[TimeSeriesDataset]) -> dict[str, Any]:
    case_rows: list[dict[str, Any]] = []
    true_all: list[np.ndarray] = []
    pred_all: list[np.ndarray] = []
    for ds in datasets:
        U = ds.U if ds.U.shape[1] else None
        U_future = None if U is None else (U[:-1] if U.shape[0] == ds.X.shape[0] else U)
        if hasattr(model, "rollout"):
            if ds.time is not None and model.__class__.__name__ == "AdaptiveDMDcModel":
                pred = model.rollout(ds.X[0], U_future=U_future, time_future=ds.time)  # type: ignore[attr-defined]
            else:
                pred = model.rollout(ds.X[0], U_future=U_future, n_steps=ds.X.shape[0] - 1)  # type: ignore[attr-defined]
        elif hasattr(model, "simulate"):
            pred = model.simulate(ds.X[0], U_future=U_future, n_steps=ds.X.shape[0] - 1)  # type: ignore[attr-defined]
        else:
            raise TypeError(f"Model {type(model)!r} has neither rollout nor simulate.")
        true_all.append(ds.X)
        pred_all.append(pred)
        case_rows.append(
            {
                "case_id": ds.case_id,
                "n_snapshots": int(ds.X.shape[0]),
                "rmse": rmse(ds.X, pred),
                "relative_frobenius_error": relative_frobenius_error(ds.X, pred),
            }
        )
    X = np.vstack(true_all)
    P = np.vstack(pred_all)
    return {
        "rmse": rmse(X, P),
        "relative_frobenius_error": relative_frobenius_error(X, P),
        "case_metrics": pd.DataFrame(case_rows),
    }


def _transition_matrix_for_model(model: object):
    if hasattr(model, "A_") and getattr(model, "A_") is not None:
        return getattr(model, "A_")
    if hasattr(model, "A_c_") and getattr(model, "A_c_") is not None:
        return getattr(model, "A_c_")
    if hasattr(model, "model_") and getattr(model, "model_") is not None:
        inner = getattr(model, "model_")
        if hasattr(inner, "A_"):
            return getattr(inner, "A_")
    return None


def _stability_summary(model: object) -> dict[str, Any]:
    A = _transition_matrix_for_model(model)
    if A is None:
        return {"spectral_radius": np.nan, "n_unstable_eigenvalues": np.nan, "stability_status": "not_applicable"}
    analysis = analyze_transition_matrix(A)
    summary = analysis["summary"]
    return {
        "spectral_radius": summary.get("spectral_radius"),
        "n_unstable_eigenvalues": summary.get("n_unstable_eigenvalues"),
        "stability_status": summary.get("status"),
    }


def plot_rank_vs_error(results: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots()
    ok = results[results["status"] == "ok"].copy()
    if ok.empty:
        ax.text(0.5, 0.5, "No successful sweep candidates", ha="center")
    else:
        for model_name, group in ok.groupby("model_name"):
            x = np.arange(len(group))
            ax.plot(x, group["test_rollout_rmse"], marker="o", label=str(model_name))
        ax.set_xticks(np.arange(len(ok)))
        ax.set_xticklabels([str(v) for v in ok["pod_rank"]], rotation=45, ha="right")
        ax.set_xlabel("POD rank candidates, ordered by sweep row")
        ax.set_ylabel("test rollout RMSE")
        ax.set_title("Sweep: rank vs held-out error")
        ax.legend(fontsize="small")
        ax.grid(True)
    _save(fig, path)


def plot_delay_vs_error(results: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots()
    ok = results[results["status"] == "ok"].copy()
    if ok.empty:
        ax.text(0.5, 0.5, "No successful sweep candidates", ha="center")
    else:
        avg = ok.groupby(["model_name", "n_delays"], as_index=False)["test_rollout_rmse"].mean()
        for model_name, group in avg.groupby("model_name"):
            ax.plot(group["n_delays"], group["test_rollout_rmse"], marker="o", label=str(model_name))
        ax.set_xlabel("number of delay blocks")
        ax.set_ylabel("mean test rollout RMSE")
        ax.set_title("Sweep: delay embedding vs held-out error")
        ax.legend(fontsize="small")
        ax.grid(True)
    _save(fig, path)


def plot_stability_vs_error(results: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots()
    ok = results[(results["status"] == "ok") & np.isfinite(results["spectral_radius"])].copy()
    if ok.empty:
        ax.text(0.5, 0.5, "No linear stability data", ha="center")
    else:
        ax.scatter(ok["spectral_radius"], ok["test_rollout_rmse"])
        for row in ok.itertuples():
            ax.annotate(str(row.model_name), (row.spectral_radius, row.test_rollout_rmse), fontsize="x-small")
        ax.axvline(1.0, linestyle="--")
        ax.set_xlabel("spectral radius")
        ax.set_ylabel("test rollout RMSE")
        ax.set_title("Sweep: stability vs held-out error")
        ax.grid(True)
    _save(fig, path)


def _save(fig: plt.Figure, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
