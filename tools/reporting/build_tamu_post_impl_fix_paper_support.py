#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from dmdc.provenance import write_provenance
from dmdc.utils import ensure_dir


FIGURES = {
    "tamu_repeated_source_coverage": {
        "title": "Repeated-source audit participation by source",
        "caption": (
            "Repeated-source participation after the post-implementation TAMU audit fix. "
            "The single-phase office workbook now contributes eight repeated-source rows "
            "to the maintained consistency audit, rather than being parsed but left "
            "outside the audit path."
        ),
    },
    "tamu_single_phase_workbook_mismatch_counts": {
        "title": "Single-phase workbook mismatch counts by case",
        "caption": (
            "Per-case mismatch-field counts for the single-phase office workbook against "
            "the current canonical Fluid salt/water validation tables. The audit path is "
            "now functioning on real data; the remaining issue is substantive disagreement "
            "across maintained sources, not missing audit coverage."
        ),
    },
    "tamu_catalog_bucket_counts_post_impl_fix": {
        "title": "Current TAMU validation-catalog bucket counts",
        "caption": (
            "Current candidate-bucket counts from the post-fix TAMU validation catalog. "
            "These counts remain readiness and triage evidence rather than predictive "
            "validation evidence."
        ),
    },
}


def _write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _wrap_figure_tex(name: str, caption: str) -> str:
    return "\n".join(
        [
            r"\begin{figure}[htbp]",
            r"\centering",
            rf"\includegraphics[width=0.92\linewidth]{{{name}.pdf}}",
            rf"\caption{{{caption}}}",
            rf"\label{{fig:{name}}}",
            r"\end{figure}",
        ]
    )


def _plot_repeated_source_coverage(data: pd.DataFrame, pdf_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    x = range(len(data))
    width = 0.38
    ax.bar([i - width / 2 for i in x], data["parsed_case_rows"], width=width, label="Parsed case rows", color="#355C7D")
    ax.bar([i + width / 2 for i in x], data["repeated_source_rows"], width=width, label="Repeated-source rows", color="#6C9A8B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(data["source_label"], rotation=20, ha="right")
    ax.set_ylabel("Rows")
    ax.set_title(FIGURES["tamu_repeated_source_coverage"]["title"])
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    plt.close(fig)


def _plot_single_phase_mismatch_counts(data: pd.DataFrame, pdf_path: Path, svg_path: Path) -> None:
    ordered = data.sort_values("mismatch_field_count", ascending=True)
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.barh(ordered["case_name"], ordered["mismatch_field_count"], color="#C06C84")
    ax.set_xlabel("Mismatch fields")
    ax.set_ylabel("Case")
    ax.set_title(FIGURES["tamu_single_phase_workbook_mismatch_counts"]["title"])
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    plt.close(fig)


def _plot_catalog_bucket_counts(data: pd.DataFrame, pdf_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    x = list(range(len(data)))
    ax.bar(x, data["count"], color=["#F67280", "#99B898", "#355C7D", "#F8B195"])
    ax.set_ylabel("Catalog rows")
    ax.set_title(FIGURES["tamu_catalog_bucket_counts_post_impl_fix"]["title"])
    ax.set_xticks(x)
    ax.set_xticklabels(data["bucket_label"], rotation=15, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    plt.close(fig)


def _source_label(source_profile: str, source_table: str) -> str:
    if source_profile == "wide_validation_source":
        name = Path(source_table).name
        if name == "salt_validation_source.csv":
            return "Fluid salt"
        if name == "water_validation_source.csv":
            return "Fluid water"
        if name == "validation_data.csv":
            return "PHYSOR wide"
    if source_profile == "jadyn_office_workbook_single_phase":
        return "Office single-phase"
    if source_profile == "jadyn_office_workbook_two_phase":
        return "Office two-phase"
    if source_profile == "jadyn_office_velocity_workbook":
        return "Office velocity"
    return source_profile


def build_package(export_dir: Path, catalog_dir: Path, outdir: Path) -> None:
    figures_dir = ensure_dir(outdir / "figures")
    data_dir = ensure_dir(outdir / "data")

    source_index = pd.read_csv(export_dir / "validation_source_index.csv")
    promotion = pd.read_csv(export_dir / "office_workbook_promotion_decisions.csv")
    catalog = pd.read_csv(catalog_dir / "validation_catalog.csv")

    coverage = source_index.copy()
    coverage["source_label"] = [
        _source_label(profile, table) for profile, table in zip(coverage["source_profile"], coverage["source_table"])
    ]
    coverage = coverage[["source_label", "parsed_case_rows", "repeated_source_rows", "source_profile", "source_table", "notes"]]
    coverage.to_csv(data_dir / "tamu_repeated_source_coverage.csv", index=False)

    single_phase = promotion[promotion["source_profile"] == "jadyn_office_workbook_single_phase"].copy()
    single_phase = single_phase[
        [
            "case_name",
            "promotion_status",
            "consistency_status",
            "mismatch_field_count",
            "mismatch_fields",
            "notes",
        ]
    ]
    single_phase.to_csv(data_dir / "tamu_single_phase_workbook_mismatch_counts.csv", index=False)

    bucket_counts = (
        catalog["candidate_bucket"]
        .value_counts()
        .rename_axis("candidate_bucket")
        .reset_index(name="count")
        .sort_values("candidate_bucket")
    )
    bucket_labels = {
        "steady_sensor_candidates": "Steady sensor",
        "transient_sensor_candidates": "Transient sensor",
        "steady_velocity_profile_candidates": "Velocity profile",
        "unknown_or_not_yet_interpretable": "Unknown",
    }
    bucket_counts["bucket_label"] = bucket_counts["candidate_bucket"].map(bucket_labels).fillna(bucket_counts["candidate_bucket"])
    bucket_counts.to_csv(data_dir / "tamu_catalog_bucket_counts_post_impl_fix.csv", index=False)

    _plot_repeated_source_coverage(
        coverage,
        figures_dir / "tamu_repeated_source_coverage.pdf",
        figures_dir / "tamu_repeated_source_coverage.svg",
    )
    _plot_single_phase_mismatch_counts(
        single_phase,
        figures_dir / "tamu_single_phase_workbook_mismatch_counts.pdf",
        figures_dir / "tamu_single_phase_workbook_mismatch_counts.svg",
    )
    _plot_catalog_bucket_counts(
        bucket_counts,
        figures_dir / "tamu_catalog_bucket_counts_post_impl_fix.pdf",
        figures_dir / "tamu_catalog_bucket_counts_post_impl_fix.svg",
    )

    for name, spec in FIGURES.items():
        _write_text(figures_dir / f"{name}.tex", _wrap_figure_tex(name, spec["caption"]))

    _write_text(
        outdir / "captions.md",
        "\n\n".join([f"## {name}\n\n{spec['caption']}" for name, spec in FIGURES.items()]),
    )

    _write_text(
        outdir / "README.md",
        "\n".join(
            [
                "# TAMU Post-Implementation Paper Support Update",
                "",
                "This package updates the manuscript-facing TAMU evidence after the real-data",
                "rerun completed on `2026-06-09`.",
                "",
                "## Inputs",
                "",
                f"- Validation export root: `{export_dir}`",
                f"- Validation catalog root: `{catalog_dir}`",
                "",
                "## Main interpretation",
                "",
                "- The single-phase office workbook now participates in the repeated-source audit.",
                "- The previous `not_audited` state is resolved.",
                "- The remaining issue is substantive disagreement across maintained sources, not missing audit coverage.",
                "",
                "## Artifacts",
                "",
                "- `data/*.csv`: figure source data",
                "- `figures/*.pdf`: manuscript-ready vector figures",
                "- `figures/*.svg`: editable vector figures",
                "- `figures/*.tex`: LaTeX wrappers",
                "- `captions.md`: proposed captions",
                "",
                "## Figure-level analysis",
                "",
                "### tamu_repeated_source_coverage",
                "",
                "The important update is not the absolute row count; it is that the office",
                "single-phase workbook now contributes eight repeated-source rows. That means",
                "the audit path is now working on real data.",
                "",
                "### tamu_single_phase_workbook_mismatch_counts",
                "",
                "These mismatch counts show that the remaining blocker is not missing audit",
                "coverage. It is a real source-disagreement problem concentrated in thermal",
                "state fields and some ancillary uncertainty/unlabeled fields.",
                "",
                "### tamu_catalog_bucket_counts_post_impl_fix",
                "",
                "The catalog remains a readiness artifact. It shows triage progress and source",
                "availability, but it still does not constitute unseen-case predictive validation.",
                "",
            ]
        ),
    )

    manifest = pd.DataFrame(
        [
            {
                "figure_name": name,
                "title": spec["title"],
                "data_csv": f"data/{name}.csv",
                "pdf": f"figures/{name}.pdf",
                "svg": f"figures/{name}.svg",
                "tex": f"figures/{name}.tex",
                "caption": spec["caption"],
            }
            for name, spec in FIGURES.items()
        ]
    )
    manifest.to_csv(outdir / "figure_manifest.csv", index=False)

    summary = {
        "export_dir": str(export_dir),
        "catalog_dir": str(catalog_dir),
        "outdir": str(outdir),
        "figures": list(FIGURES),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_provenance(outdir, extra={"command": "build_tamu_post_impl_fix_paper_support", "result": summary})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manuscript-facing TAMU paper-support figures after the post-implementation real-data rerun.")
    parser.add_argument("--export-dir", required=True, help="Validation export directory.")
    parser.add_argument("--catalog-dir", required=True, help="Validation catalog directory.")
    parser.add_argument("--outdir", required=True, help="Output package directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_package(Path(args.export_dir), Path(args.catalog_dir), Path(args.outdir))


if __name__ == "__main__":
    main()
