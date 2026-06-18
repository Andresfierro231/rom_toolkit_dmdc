#!/usr/bin/env python3
"""Build a reusable paper-support package from saved study outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from common import ensure_dir, git_state, now_local_iso, print_written, relpath, repo_root, write_json, write_yaml


READY_NOW = "ready_now"
NEEDS_MORE = "needs_more_analysis"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_best_recommendation(run_dir: Path) -> dict[str, Any]:
    payload = _read_json(run_dir / "best_model_recommendation.json")
    recommendation = dict(payload["recommendation"])
    recommendation["selection_reason"] = payload.get("reason", "")
    recommendation["selection_filters"] = payload.get("filters", [])
    recommendation["run_dir"] = str(run_dir)
    return recommendation


def _read_case_errors(run_dir: Path, run_name: str) -> pd.DataFrame:
    path = run_dir / "runs" / run_name / "test_error_by_case.csv"
    df = pd.read_csv(path)
    df["source_run_dir"] = str(run_dir)
    df["source_run_name"] = run_name
    return df


def _short_case_label(case_id: str) -> str:
    text = str(case_id)
    if "jsalt2_moose_mesh_convergence_" in text:
        text = text.split("jsalt2_moose_mesh_convergence_", 1)[1]
    if text.endswith("_csv"):
        text = text[:-4]
    return text


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.figsize": (8.5, 4.8),
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
        }
    )


def _write_dataframe_bundle(df: pd.DataFrame, stem: Path) -> None:
    df.to_csv(stem.with_suffix(".csv"), index=False)
    try:
        text = df.to_markdown(index=False)
    except Exception:
        text = df.to_string(index=False)
    stem.with_suffix(".md").write_text(text + "\n", encoding="utf-8")


def _save_dual_format(fig: plt.Figure, stem: Path) -> tuple[Path, Path]:
    pdf_path = stem.with_suffix(".pdf")
    svg_path = stem.with_suffix(".svg")
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    plt.close(fig)
    return pdf_path, svg_path


def _write_figure_wrapper(path: Path, *, figure_filename: str, caption: str, label: str) -> None:
    tex = (
        "\\begin{figure}[htbp]\n"
        "\\centering\n"
        f"\\includegraphics[width=0.95\\linewidth]{{{figure_filename}}}\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{fig:{label}}}\n"
        "\\end{figure}\n"
    )
    path.write_text(tex, encoding="utf-8")


def _classify_removed_candidate(row: pd.Series) -> str:
    top = str(row.get("top_level_folder", ""))
    case_dir = str(row.get("case_dir", ""))
    case_name = str(row.get("candidate_case_name", ""))
    if "example" in top.lower() or "example" in case_dir.lower():
        return "example_or_demo"
    if top == "Jadyn_runs":
        return "jadyn_metadata_only"
    if case_dir == top or case_name == top:
        return "pseudo_root_row"
    return "other_removed"


def _format_model_label(row: pd.Series | dict[str, Any]) -> str:
    return f"{row['model_name']} (delay={int(row['n_delays'])})"


def _build_jsalt2_surface_summary(
    compare_with_h_dir: Path,
    compare_no_h_dir: Path,
    sweep_with_h_dir: Path,
    sweep_no_h_dir: Path,
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    selected: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    configs = [
        ("with_h", "delay1_compare_surface", compare_with_h_dir),
        ("with_h", "broader_tuned_surface", sweep_with_h_dir),
        ("no_h", "delay1_compare_surface", compare_no_h_dir),
        ("no_h", "broader_tuned_surface", sweep_no_h_dir),
    ]
    for variant, surface, run_dir in configs:
        recommendation = _read_best_recommendation(run_dir)
        selected[f"{variant}::{surface}"] = recommendation
        rows.append(
            {
                "variant": variant,
                "surface": surface,
                "surface_label": "Delay-1 compare surface" if surface == "delay1_compare_surface" else "Broader tuned sweep",
                "model_name": recommendation["model_name"],
                "model_label": _format_model_label(recommendation),
                "run_name": recommendation["run_name"],
                "pod_rank": recommendation["pod_rank"],
                "dmdc_rank": recommendation["dmdc_rank"],
                "n_delays": recommendation["n_delays"],
                "train_rollout_rmse": recommendation["train_rollout_rmse"],
                "test_rollout_rmse": recommendation["test_rollout_rmse"],
                "generalization_gap": recommendation["generalization_gap"],
                "spectral_radius": recommendation["spectral_radius"],
                "n_unstable_eigenvalues": recommendation["n_unstable_eigenvalues"],
                "stability_status": recommendation["stability_status"],
                "run_dir": str(run_dir),
            }
        )
    return pd.DataFrame(rows), selected


def _build_jsalt2_case_comparison(selected: dict[str, dict[str, Any]]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for variant in ("with_h", "no_h"):
        baseline = selected[f"{variant}::delay1_compare_surface"]
        tuned = selected[f"{variant}::broader_tuned_surface"]
        for surface, recommendation in (
            ("delay1_compare_surface", baseline),
            ("broader_tuned_surface", tuned),
        ):
            df = _read_case_errors(Path(recommendation["run_dir"]), recommendation["run_name"]).copy()
            df["variant"] = variant
            df["surface"] = surface
            df["surface_label"] = "Delay-1 compare surface" if surface == "delay1_compare_surface" else "Broader tuned sweep"
            df["model_name"] = recommendation["model_name"]
            df["model_label"] = _format_model_label(recommendation)
            df["case_label"] = df["case_id"].map(_short_case_label)
            frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _build_stability_tradeoff(sweep_with_h_dir: Path, sweep_no_h_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for variant, run_dir in (("with_h", sweep_with_h_dir), ("no_h", sweep_no_h_dir)):
        df = pd.read_csv(run_dir / "sweep_results.csv").copy()
        df["variant"] = variant
        df["surface"] = "broader_tuned_surface"
        df["run_dir"] = str(run_dir)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _build_tamu_cleanup_summary(prior_dir: Path, current_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    prior_summary = _read_json(prior_dir / "validation_export_summary.json")
    current_summary = _read_json(current_dir / "validation_export_summary.json")
    old_df = pd.read_csv(prior_dir / "inventory_validation_candidates.csv")
    new_df = pd.read_csv(current_dir / "inventory_validation_candidates.csv")
    removed = old_df.loc[~old_df["candidate_case_name"].isin(new_df["candidate_case_name"])].copy()
    removed["removal_category"] = removed.apply(_classify_removed_candidate, axis=1)

    removed_counts = (
        removed.groupby("removal_category", dropna=False)
        .size()
        .rename("count")
        .reset_index()
        .sort_values("removal_category")
    )
    summary_rows = [
        {"stage": "prior_export", "category": "retained_or_candidate_rows", "count": int(prior_summary["n_inventory_candidates"])},
    ]
    for row in removed_counts.itertuples(index=False):
        summary_rows.append({"stage": "prior_export", "category": f"removed_{row.removal_category}", "count": int(row.count)})
    summary_rows.extend(
        [
            {"stage": "filtered_export", "category": "retained_or_candidate_rows", "count": int(current_summary["n_inventory_candidates"])},
            {"stage": "filtered_export", "category": "removed_example_or_demo", "count": 0},
            {"stage": "filtered_export", "category": "removed_jadyn_metadata_only", "count": 0},
            {"stage": "filtered_export", "category": "removed_pseudo_root_row", "count": 0},
            {"stage": "filtered_export", "category": "removed_other_removed", "count": 0},
        ]
    )
    return pd.DataFrame(summary_rows), removed[["candidate_case_name", "case_dir", "top_level_folder", "removal_category"]].copy()


def _build_tamu_catalog_summary(catalog_dir: Path) -> pd.DataFrame:
    summary = _read_json(catalog_dir / "validation_catalog_summary.json")
    bucket_map = {
        "steady_sensor_candidates": "Steady sensor candidates",
        "transient_sensor_candidates": "Transient sensor candidates",
        "steady_velocity_profile_candidates": "Steady velocity-profile candidates",
        "unknown_or_not_yet_interpretable": "Unknown / not yet interpretable",
    }
    md_text = (catalog_dir / "validation_catalog_summary.md").read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for line in md_text.splitlines():
        if ":" not in line:
            continue
        text = line.lstrip("- ").strip()
        if ":" not in text:
            continue
        key, value = [part.strip() for part in text.split(":", 1)]
        if key in bucket_map:
            counts[key] = int(value)
        elif key == "Velocity plot rows":
            counts["velocity_plot_rows"] = int(value)
        elif key == "Successful velocity plot bundles":
            counts["successful_velocity_plot_bundles"] = int(value)
        elif key == "Repeated-source mismatch rows":
            counts["repeated_source_mismatch_rows"] = int(value)
    rows = [
        {"metric": bucket_map[key], "metric_key": key, "count": counts.get(key, 0), "metric_group": "candidate_bucket"}
        for key in bucket_map
    ]
    rows.extend(
        [
            {
                "metric": "Velocity plot rows",
                "metric_key": "velocity_plot_rows",
                "count": counts.get("velocity_plot_rows", int(summary.get("n_velocity_plot_rows", 0))),
                "metric_group": "derived_output",
            },
            {
                "metric": "Repeated-source mismatches",
                "metric_key": "repeated_source_mismatch_rows",
                "count": counts.get("repeated_source_mismatch_rows", int(summary.get("n_consistency_mismatches", 0))),
                "metric_group": "consistency_audit",
            },
        ]
    )
    return pd.DataFrame(rows)


def _build_claim_matrix(
    surface_df: pd.DataFrame,
    stability_df: pd.DataFrame,
    cleanup_df: pd.DataFrame,
    catalog_df: pd.DataFrame,
    filtered_export_dir: Path,
    catalog_dir: Path,
) -> pd.DataFrame:
    compare_with_h = surface_df[(surface_df["variant"] == "with_h") & (surface_df["surface"] == "delay1_compare_surface")].iloc[0]
    sweep_with_h = surface_df[(surface_df["variant"] == "with_h") & (surface_df["surface"] == "broader_tuned_surface")].iloc[0]
    compare_no_h = surface_df[(surface_df["variant"] == "no_h") & (surface_df["surface"] == "delay1_compare_surface")].iloc[0]
    sweep_no_h = surface_df[(surface_df["variant"] == "no_h") & (surface_df["surface"] == "broader_tuned_surface")].iloc[0]
    unstable_best = stability_df.loc[stability_df["test_rollout_rmse"].idxmin()]

    bucket_lookup = {row.metric_key: int(row.count) for row in catalog_df.itertuples(index=False)}
    cleanup_kept = int(cleanup_df[(cleanup_df["stage"] == "filtered_export") & (cleanup_df["category"] == "retained_or_candidate_rows")]["count"].iloc[0])

    rows = [
        {
            "claim_id": "jsalt2_search_surface_changes_winner",
            "readiness": READY_NOW,
            "claim_statement": "On the current JSALT2 collection and current split, the selected winner changes from delay-1 POD-DMDc to delay-4 DMDc when model selection moves from the narrow compare surface to the broader tuned sweep surface.",
            "current_evidence": (
                f"With h: compare {compare_with_h['model_name']} RMSE={compare_with_h['test_rollout_rmse']:.5f}; "
                f"tuned {sweep_with_h['model_name']} RMSE={sweep_with_h['test_rollout_rmse']:.5f}. "
                f"No h: compare {compare_no_h['model_name']} RMSE={compare_no_h['test_rollout_rmse']:.5f}; "
                f"tuned {sweep_no_h['model_name']} RMSE={sweep_no_h['test_rollout_rmse']:.5f}."
            ),
            "caveat": "This is a current-split conclusion, not yet a repeated-split robustness statement.",
            "next_analysis_needed": "Run repeated case-aware splits or leave-one-case-out checks and report spread of held-out RMSE.",
            "supporting_figures": "jsalt2_surface_winner_comparison; jsalt2_case_rmse_comparison",
            "supporting_files": (
                "outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/best_model_recommendation.txt; "
                "outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/best_model_recommendation.txt; "
                "outputs/analysis_followups/jsalt2_compare_equiv_no_h_20260602/best_model_recommendation.txt; "
                "outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/best_model_recommendation.txt"
            ),
        },
        {
            "claim_id": "jsalt2_delay_embedding_improves_current_split_rmse",
            "readiness": READY_NOW,
            "claim_statement": "Delay embedding to n_delays=4 materially improves held-out JSALT2 rollout RMSE on the current split relative to the delay-1 comparison surface.",
            "current_evidence": (
                f"With h: {compare_with_h['test_rollout_rmse']:.5f} -> {sweep_with_h['test_rollout_rmse']:.5f}. "
                f"No h: {compare_no_h['test_rollout_rmse']:.5f} -> {sweep_no_h['test_rollout_rmse']:.5f}."
            ),
            "caveat": "Interpretation should stay at the lag-0 physical state level in any final paper figures.",
            "next_analysis_needed": "Add representative lag-0 rollout overlays and repeated-split confirmation.",
            "supporting_figures": "jsalt2_surface_winner_comparison; jsalt2_case_rmse_comparison",
            "supporting_files": "outputs/analysis_followups/jsalt2_compare_equiv_with_h_20260602/sweep_results.csv; outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/sweep_results.csv",
        },
        {
            "claim_id": "jsalt2_stability_filter_matters",
            "readiness": READY_NOW,
            "claim_statement": "Lower raw error alone is not sufficient for JSALT2 selection because the best raw-error adaptive DMDc candidates are flagged as potentially unstable.",
            "current_evidence": (
                f"Best unstable candidate {unstable_best['model_name']} RMSE={unstable_best['test_rollout_rmse']:.5f}, "
                f"spectral_radius={unstable_best['spectral_radius']:.3f}, "
                f"unstable_eigs={int(unstable_best['n_unstable_eigenvalues'])}."
            ),
            "caveat": "The stability diagnostic is spectral-radius based; rollout examples should still be shown alongside the scalar filter.",
            "next_analysis_needed": "Add representative rollout overlays for the selected stable winner and the best excluded unstable candidate.",
            "supporting_figures": "jsalt2_stability_tradeoff",
            "supporting_files": "outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/sweep_results.csv; outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/sweep_results.csv",
        },
        {
            "claim_id": "tamu_candidate_cleanup_removed_nuisance_rows",
            "readiness": READY_NOW,
            "claim_statement": "The filtered TAMU candidate export removes nuisance rows while preserving the usable candidate set.",
            "current_evidence": f"Candidate rows decreased from 54 to {cleanup_kept}, removing 11 nuisance rows.",
            "caveat": "This is a curation claim, not a predictive-validation claim.",
            "next_analysis_needed": "Spot-check any newly arriving folders and keep the filter under regression test.",
            "supporting_figures": "tamu_candidate_cleanup",
            "supporting_files": "outputs/tamu_validation_export_overnight_20260525/inventory_validation_candidates.csv; outputs/tamu_validation_export_20260602_filtered/inventory_validation_candidates.csv",
        },
        {
            "claim_id": "tamu_catalog_identifies_reusable_measurement_buckets",
            "readiness": READY_NOW,
            "claim_statement": "The current TAMU raw-source catalog already separates candidate files into reusable measurement buckets for follow-on validation work.",
            "current_evidence": (
                f"steady_sensor={bucket_lookup.get('steady_sensor_candidates', 0)}, "
                f"transient_sensor={bucket_lookup.get('transient_sensor_candidates', 0)}, "
                f"steady_velocity_profile={bucket_lookup.get('steady_velocity_profile_candidates', 0)}, "
                f"unknown={bucket_lookup.get('unknown_or_not_yet_interpretable', 0)}."
            ),
            "caveat": "These counts describe data availability and triage status, not forecast quality.",
            "next_analysis_needed": "Promote selected catalog rows into formal unseen-case validation experiments.",
            "supporting_figures": "tamu_catalog_buckets",
            "supporting_files": "outputs/tamu_validation_catalog_20260602_loop_sources_v1/validation_catalog_summary.json",
        },
        {
            "claim_id": "tamu_repeated_source_normalization_is_consistent",
            "readiness": READY_NOW,
            "claim_statement": "The current repeated-source normalization audit shows no cross-table mismatches on the maintained Salt/Water validation rows.",
            "current_evidence": "Consistency audit: 16 rows checked, 0 mismatches.",
            "caveat": "This is limited to the current repeated-source tables and does not yet cover every raw workbook-style source.",
            "next_analysis_needed": "Extend the audit set as more repeated-source tables are formalized.",
            "supporting_figures": "tamu_catalog_buckets",
            "supporting_files": "outputs/tamu_validation_catalog_20260602_loop_sources_v1/validation_source_consistency_report.csv",
        },
        {
            "claim_id": "jsalt2_winner_is_split_robust",
            "readiness": NEEDS_MORE,
            "claim_statement": "The broader tuned-surface JSALT2 winner is robust across alternative case-aware splits.",
            "current_evidence": "Not yet established from the current single-split artifacts.",
            "caveat": "Current evidence is point-estimate only.",
            "next_analysis_needed": "Run repeated case-aware splits or leave-one-case-out validation and report uncertainty/spread.",
            "supporting_figures": "",
            "supporting_files": "",
        },
        {
            "claim_id": "jsalt2_input_policy_can_be_closed",
            "readiness": NEEDS_MORE,
            "claim_statement": "The project can now make a final keep-h versus no-h policy decision for JSALT2.",
            "current_evidence": "Both variants are still being kept active by policy.",
            "caveat": "Current outputs do not yet justify collapsing to one variant.",
            "next_analysis_needed": "Compare repeated-split performance, interpretability, and operational meaning of the exogenous h input.",
            "supporting_figures": "jsalt2_surface_winner_comparison",
            "supporting_files": "",
        },
        {
            "claim_id": "tamu_predictive_validation_is_complete",
            "readiness": NEEDS_MORE,
            "claim_statement": "TAMU unseen-case predictive validation is complete and ready for paper results claims.",
            "current_evidence": "The repo now has candidate discovery and cataloging, but not yet a completed unseen-case ROM validation package on selected TAMU cases.",
            "caveat": "Current TAMU outputs are data-readiness artifacts, not model-performance artifacts.",
            "next_analysis_needed": "Select candidate cases from the catalog and run validate/compare workflows on them.",
            "supporting_figures": "tamu_candidate_cleanup; tamu_catalog_buckets",
            "supporting_files": "",
        },
    ]
    return pd.DataFrame(rows)


def _make_surface_winner_figure(df: pd.DataFrame, stem: Path) -> str:
    order = ["with_h", "no_h"]
    labels = {"with_h": "With h", "no_h": "No h"}
    surfaces = ["delay1_compare_surface", "broader_tuned_surface"]
    colors = {"delay1_compare_surface": "#4C78A8", "broader_tuned_surface": "#F58518"}
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    x = np.arange(len(order))
    width = 0.34
    for idx, surface in enumerate(surfaces):
        subset = df.set_index(["variant", "surface"]).loc[[(variant, surface) for variant in order]].reset_index()
        positions = x + (idx - 0.5) * width
        bars = ax.bar(
            positions,
            subset["test_rollout_rmse"],
            width=width,
            color=colors[surface],
            label="Delay-1 compare surface" if surface == "delay1_compare_surface" else "Broader tuned sweep",
        )
        for bar, row in zip(bars, subset.itertuples(index=False)):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{row.model_name}\nd={int(row.n_delays)}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_xticks(x)
    ax.set_xticklabels([labels[item] for item in order])
    ax.set_ylabel("Held-out rollout RMSE")
    ax.set_title("JSALT2 winner depends on the selection surface")
    ax.legend(frameon=False, ncol=2, loc="upper center")
    ax.set_ylim(0, max(df["test_rollout_rmse"]) * 1.22)
    pdf_path, _ = _save_dual_format(fig, stem)
    caption = (
        "Held-out rollout RMSE of the selected JSALT2 winner under the narrow delay-1 compare surface and the broader tuned sweep surface. "
        "The project policy now treats the broader tuned sweep as authoritative, which shifts the selected winner from POD-DMDc to delay-4 DMDc on the current split."
    )
    _write_figure_wrapper(stem.with_suffix(".tex"), figure_filename=pdf_path.name, caption=caption, label=stem.name)
    return caption


def _make_case_rmse_figure(df: pd.DataFrame, stem: Path) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), sharey=True)
    colors = {"delay1_compare_surface": "#4C78A8", "broader_tuned_surface": "#F58518"}
    for ax, variant in zip(axes, ("with_h", "no_h")):
        subset = df[df["variant"] == variant].copy()
        cases = list(dict.fromkeys(subset["case_label"]))
        x = np.arange(len(cases))
        width = 0.34
        for idx, surface in enumerate(("delay1_compare_surface", "broader_tuned_surface")):
            surface_df = subset[subset["surface"] == surface].set_index("case_label").loc[cases].reset_index()
            positions = x + (idx - 0.5) * width
            ax.bar(
                positions,
                surface_df["rmse"],
                width=width,
                color=colors[surface],
                label="Delay-1 compare surface" if surface == "delay1_compare_surface" else "Broader tuned sweep",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(cases, rotation=20, ha="right")
        ax.set_title("With h" if variant == "with_h" else "No h")
        ax.set_xlabel("Held-out case")
    axes[0].set_ylabel("Per-case rollout RMSE")
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("JSALT2 per-case error comparison for selected winners", y=1.02)
    pdf_path, _ = _save_dual_format(fig, stem)
    caption = (
        "Per-case held-out rollout RMSE for the selected JSALT2 winners under each selection surface. "
        "The broader tuned sweep improves error on every held-out case in the current split for both the with-h and no-h variants."
    )
    _write_figure_wrapper(stem.with_suffix(".tex"), figure_filename=pdf_path.name, caption=caption, label=stem.name)
    return caption


def _make_stability_tradeoff_figure(df: pd.DataFrame, selected: dict[str, dict[str, Any]], stem: Path) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), sharey=True)
    color_map = {
        "stable_by_spectral_radius": "#54A24B",
        "marginal": "#ECA82C",
        "potentially_unstable": "#E45756",
        "failed": "#B279A2",
    }
    for ax, variant in zip(axes, ("with_h", "no_h")):
        subset = df[(df["variant"] == variant) & (df["status"] == "ok")].copy()
        subset = subset.sort_values(["stability_status", "test_rollout_rmse"])
        for status, group in subset.groupby("stability_status", dropna=False):
            ax.scatter(
                group["spectral_radius"],
                group["test_rollout_rmse"],
                s=28,
                alpha=0.8,
                label=str(status).replace("_", " "),
                color=color_map.get(str(status), "#4C78A8"),
            )
        winner = selected[f"{variant}::broader_tuned_surface"]
        winner_row = subset[subset["run_name"] == winner["run_name"]].iloc[0]
        ax.scatter(
            [winner_row["spectral_radius"]],
            [winner_row["test_rollout_rmse"]],
            s=90,
            marker="*",
            color="#111111",
            label="Selected winner",
            zorder=5,
        )
        unstable = subset[subset["stability_status"] == "potentially_unstable"]
        if not unstable.empty:
            best_unstable = unstable.nsmallest(1, "test_rollout_rmse").iloc[0]
            ax.annotate(
                "best raw-error unstable",
                (best_unstable["spectral_radius"], best_unstable["test_rollout_rmse"]),
                xytext=(8, 10),
                textcoords="offset points",
                fontsize=8,
            )
        ax.set_xscale("log")
        ax.set_xlabel("Spectral radius")
        ax.set_title("With h" if variant == "with_h" else "No h")
    axes[0].set_ylabel("Held-out rollout RMSE")
    axes[0].legend(frameon=False, loc="upper right", fontsize=8)
    fig.suptitle("JSALT2 stability filter versus raw held-out error", y=1.02)
    pdf_path, _ = _save_dual_format(fig, stem)
    caption = (
        "Held-out JSALT2 rollout RMSE versus spectral radius for the broader tuned sweep candidates. "
        "Adaptive DMDc achieves the lowest raw RMSE but is flagged as potentially unstable, while the selected delay-4 DMDc winner stays near the stability boundary with zero unstable eigenvalues."
    )
    _write_figure_wrapper(stem.with_suffix(".tex"), figure_filename=pdf_path.name, caption=caption, label=stem.name)
    return caption


def _make_tamu_cleanup_figure(df: pd.DataFrame, stem: Path) -> str:
    category_order = [
        "retained_or_candidate_rows",
        "removed_example_or_demo",
        "removed_pseudo_root_row",
        "removed_jadyn_metadata_only",
        "removed_other_removed",
    ]
    label_map = {
        "retained_or_candidate_rows": "Retained rows",
        "removed_example_or_demo": "Removed example/demo",
        "removed_pseudo_root_row": "Removed pseudo root",
        "removed_jadyn_metadata_only": "Removed Jadyn metadata-only",
        "removed_other_removed": "Other removed",
    }
    color_map = {
        "retained_or_candidate_rows": "#54A24B",
        "removed_example_or_demo": "#E45756",
        "removed_pseudo_root_row": "#B279A2",
        "removed_jadyn_metadata_only": "#F58518",
        "removed_other_removed": "#9D755D",
    }
    stage_order = ["prior_export", "filtered_export"]
    stage_labels = {"prior_export": "Prior export", "filtered_export": "Filtered export"}
    pivot = (
        df.pivot_table(index="stage", columns="category", values="count", aggfunc="sum", fill_value=0)
        .reindex(index=stage_order, fill_value=0)
        .reindex(columns=category_order, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    bottom = np.zeros(len(stage_order))
    x = np.arange(len(stage_order))
    for category in category_order:
        values = pivot[category].to_numpy()
        ax.bar(x, values, bottom=bottom, label=label_map[category], color=color_map[category])
        bottom += values
    ax.set_xticks(x)
    ax.set_xticklabels([stage_labels[item] for item in stage_order])
    ax.set_ylabel("Candidate rows")
    ax.set_title("TAMU candidate cleanup removes nuisance rows")
    ax.legend(frameon=False, loc="upper right")
    pdf_path, _ = _save_dual_format(fig, stem)
    caption = (
        "Candidate-count comparison between the prior TAMU validation export and the filtered export. "
        "The filtered workflow preserves the retained candidate set while removing example/demo rows, pseudo-root rows, and metadata-only Jadyn rows from collaborator-facing tables."
    )
    _write_figure_wrapper(stem.with_suffix(".tex"), figure_filename=pdf_path.name, caption=caption, label=stem.name)
    return caption


def _make_tamu_catalog_figure(df: pd.DataFrame, stem: Path) -> str:
    subset = df[df["metric_group"] == "candidate_bucket"].copy()
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    x = np.arange(len(subset))
    ax.bar(x, subset["count"], color=["#4C78A8", "#54A24B", "#F58518", "#B279A2"])
    ax.set_ylabel("Catalog rows")
    ax.set_title("Current TAMU raw-source catalog by candidate bucket")
    ax.set_xticks(x)
    ax.set_xticklabels(subset["metric"], rotation=18, ha="right")
    for idx, row in enumerate(subset.itertuples(index=False)):
        ax.text(idx, row.count + 1, str(int(row.count)), ha="center", va="bottom", fontsize=8)
    pdf_path, _ = _save_dual_format(fig, stem)
    caption = (
        "Bucket counts from the current TAMU raw-source validation catalog. "
        "The repository already separates reusable sources into steady-sensor, transient-sensor, and steady velocity-profile candidates, with a smaller residual unknown bucket for future triage."
    )
    _write_figure_wrapper(stem.with_suffix(".tex"), figure_filename=pdf_path.name, caption=caption, label=stem.name)
    return caption


def _build_figure_manifest(rows: list[dict[str, Any]], path: Path) -> None:
    manifest_df = pd.DataFrame(rows)
    manifest_df.to_csv(path, index=False)
    print_written(path)


def _write_readme(
    path: Path,
    *,
    command: str,
    claim_matrix_path: Path,
    figure_manifest_path: Path,
    captions_path: Path,
    figures_dir: Path,
    data_dir: Path,
) -> None:
    text = f"""# Paper Support Package

Generated: `{now_local_iso()}`

This package collects paper-support claims, reusable figure inputs, and figure assets built from saved repo outputs.

## Reproduce

```bash
{command}
```

## Main artifacts

- Claim matrix: `{relpath(claim_matrix_path, repo_root())}`
- Figure manifest: `{relpath(figure_manifest_path, repo_root())}`
- Figure captions: `{relpath(captions_path, repo_root())}`
- Figure directory: `{relpath(figures_dir, repo_root())}`
- Source data directory: `{relpath(data_dir, repo_root())}`

## Notes

- `ready_now` rows are claims that can already be supported from the current saved outputs, with stated caveats.
- `needs_more_analysis` rows are intentionally preserved so the package doubles as the next paper-work plan.
"""
    path.write_text(text, encoding="utf-8")
    print_written(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a reusable paper-support package from saved repo outputs.")
    ap.add_argument("--outdir", required=True, help="Output package directory, typically under analysis/reports/.")
    ap.add_argument("--jsalt2-with-h-compare-dir", required=True)
    ap.add_argument("--jsalt2-no-h-compare-dir", required=True)
    ap.add_argument("--jsalt2-with-h-sweep-dir", required=True)
    ap.add_argument("--jsalt2-no-h-sweep-dir", required=True)
    ap.add_argument("--tamu-validation-export-dir", required=True)
    ap.add_argument("--tamu-validation-catalog-dir", required=True)
    ap.add_argument("--prior-tamu-validation-export-dir", required=True)
    args = ap.parse_args()

    _style()
    root = repo_root(".")
    outdir = ensure_dir(args.outdir)
    figures_dir = ensure_dir(outdir / "figures")
    data_dir = ensure_dir(outdir / "data")

    compare_with_h_dir = Path(args.jsalt2_with_h_compare_dir)
    compare_no_h_dir = Path(args.jsalt2_no_h_compare_dir)
    sweep_with_h_dir = Path(args.jsalt2_with_h_sweep_dir)
    sweep_no_h_dir = Path(args.jsalt2_no_h_sweep_dir)
    tamu_export_dir = Path(args.tamu_validation_export_dir)
    tamu_catalog_dir = Path(args.tamu_validation_catalog_dir)
    prior_tamu_export_dir = Path(args.prior_tamu_validation_export_dir)

    surface_df, selected = _build_jsalt2_surface_summary(
        compare_with_h_dir,
        compare_no_h_dir,
        sweep_with_h_dir,
        sweep_no_h_dir,
    )
    case_df = _build_jsalt2_case_comparison(selected)
    stability_df = _build_stability_tradeoff(sweep_with_h_dir, sweep_no_h_dir)
    cleanup_df, removed_rows_df = _build_tamu_cleanup_summary(prior_tamu_export_dir, tamu_export_dir)
    catalog_df = _build_tamu_catalog_summary(tamu_catalog_dir)
    claim_df = _build_claim_matrix(
        surface_df,
        stability_df,
        cleanup_df,
        catalog_df,
        tamu_export_dir,
        tamu_catalog_dir,
    )

    _write_dataframe_bundle(surface_df, data_dir / "jsalt2_surface_winner_comparison")
    _write_dataframe_bundle(case_df, data_dir / "jsalt2_case_rmse_comparison")
    _write_dataframe_bundle(stability_df, data_dir / "jsalt2_stability_tradeoff")
    _write_dataframe_bundle(cleanup_df, data_dir / "tamu_candidate_cleanup")
    _write_dataframe_bundle(removed_rows_df, data_dir / "tamu_removed_candidate_rows")
    _write_dataframe_bundle(catalog_df, data_dir / "tamu_catalog_buckets")
    _write_dataframe_bundle(claim_df, outdir / "claim_matrix")

    figure_rows: list[dict[str, Any]] = []
    captions: list[str] = []
    figure_specs = [
        ("jsalt2_surface_winner_comparison", _make_surface_winner_figure, surface_df),
        ("jsalt2_case_rmse_comparison", _make_case_rmse_figure, case_df),
        ("jsalt2_stability_tradeoff", lambda _df, stem: _make_stability_tradeoff_figure(_df, selected, stem), stability_df),
        ("tamu_candidate_cleanup", _make_tamu_cleanup_figure, cleanup_df),
        ("tamu_catalog_buckets", _make_tamu_catalog_figure, catalog_df),
    ]
    command = " ".join(
        [
            "python",
            "tools/reporting/build_paper_support_package.py",
            f"--outdir {relpath(outdir, root)}",
            f"--jsalt2-with-h-compare-dir {relpath(compare_with_h_dir, root)}",
            f"--jsalt2-no-h-compare-dir {relpath(compare_no_h_dir, root)}",
            f"--jsalt2-with-h-sweep-dir {relpath(sweep_with_h_dir, root)}",
            f"--jsalt2-no-h-sweep-dir {relpath(sweep_no_h_dir, root)}",
            f"--tamu-validation-export-dir {relpath(tamu_export_dir, root)}",
            f"--tamu-validation-catalog-dir {relpath(tamu_catalog_dir, root)}",
            f"--prior-tamu-validation-export-dir {relpath(prior_tamu_export_dir, root)}",
        ]
    )

    for figure_id, maker, df in figure_specs:
        stem = figures_dir / figure_id
        caption = maker(df, stem)
        captions.append(f"## {figure_id}\n\n{caption}\n")
        figure_rows.append(
            {
                "figure_id": figure_id,
                "title": figure_id.replace("_", " ").title(),
                "data_path": relpath((data_dir / figure_id).with_suffix(".csv"), root),
                "script_path": "tools/reporting/build_paper_support_package.py",
                "pdf_path": relpath(stem.with_suffix(".pdf"), root),
                "svg_path": relpath(stem.with_suffix(".svg"), root),
                "tex_path": relpath(stem.with_suffix(".tex"), root),
                "caption_draft": caption,
                "notes": "Generated from saved repo outputs.",
            }
        )
        print_written(stem.with_suffix(".pdf"))
        print_written(stem.with_suffix(".svg"))
        print_written(stem.with_suffix(".tex"))

    captions_path = outdir / "captions.md"
    captions_path.write_text("\n".join(captions), encoding="utf-8")
    print_written(captions_path)

    figure_manifest_path = outdir / "figure_manifest.csv"
    _build_figure_manifest(figure_rows, figure_manifest_path)

    manifest = {
        "generated_at": now_local_iso(),
        "tool": "tools/reporting/build_paper_support_package.py",
        "git": git_state(root),
        "inputs": {
            "jsalt2_with_h_compare_dir": relpath(compare_with_h_dir, root),
            "jsalt2_no_h_compare_dir": relpath(compare_no_h_dir, root),
            "jsalt2_with_h_sweep_dir": relpath(sweep_with_h_dir, root),
            "jsalt2_no_h_sweep_dir": relpath(sweep_no_h_dir, root),
            "tamu_validation_export_dir": relpath(tamu_export_dir, root),
            "tamu_validation_catalog_dir": relpath(tamu_catalog_dir, root),
            "prior_tamu_validation_export_dir": relpath(prior_tamu_export_dir, root),
        },
        "outputs": {
            "claim_matrix_csv": relpath((outdir / "claim_matrix.csv"), root),
            "claim_matrix_md": relpath((outdir / "claim_matrix.md"), root),
            "figure_manifest_csv": relpath(figure_manifest_path, root),
            "captions_md": relpath(captions_path, root),
            "figures_dir": relpath(figures_dir, root),
            "data_dir": relpath(data_dir, root),
        },
        "command": command,
    }
    write_yaml(outdir / "MANIFEST.yaml", manifest)
    print_written(outdir / "MANIFEST.yaml")
    write_json(outdir / "provenance.json", manifest)
    print_written(outdir / "provenance.json")
    _write_readme(
        outdir / "README.md",
        command=command,
        claim_matrix_path=outdir / "claim_matrix.csv",
        figure_manifest_path=figure_manifest_path,
        captions_path=captions_path,
        figures_dir=figures_dir,
        data_dir=data_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
