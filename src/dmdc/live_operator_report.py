"""Generate compact operator reports from live run folders or archives.

This report is not a substitute for the full LaTeX research reports.  It is a
short, meeting-friendly summary intended for supervisors, operators, and review
meetings: what happened, what the model thought, what alerts fired, how trust
changed, whether bias correction helped, and where to look next.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import html
import json

import pandas as pd

from .live_dashboard import (
    summarize_live_dashboard,
    summarize_archive_dashboard,
    read_live_dashboard_tables,
    read_archive_dashboard_tables,
)


def _table_md(df: pd.DataFrame, max_rows: int = 12) -> str:
    if df.empty:
        return "_No rows available._"
    return df.head(max_rows).to_markdown(index=False)


def _write_html_from_markdown(markdown_text: str, html_path: Path) -> None:
    """Write a simple standalone HTML wrapper for markdown-like text."""

    body = html.escape(markdown_text)
    body = body.replace("\n", "<br>\n")
    html_path.write_text(
        "<html><head><meta charset='utf-8'><title>Live Operator Report</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:1100px;margin:2rem auto;line-height:1.45}"
        "code,pre{background:#f3f4f6;padding:0.2rem;border-radius:0.25rem}"
        "h1,h2,h3{color:#111827}</style></head><body>"
        + body
        + "</body></html>",
        encoding="utf-8",
    )


def generate_live_operator_report(
    *,
    run_dir: str | Path | None = None,
    archive_root: str | Path | None = None,
    outdir: str | Path = "outputs/live_operator_report",
    window_label: str = "60s",
) -> dict[str, str]:
    """Generate Markdown/HTML operator report from a live run or archive."""

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if archive_root:
        archive_root = Path(archive_root)
        summary = summarize_archive_dashboard(archive_root, window_label=window_label)
        tables = read_archive_dashboard_tables(archive_root, window_label=window_label)
        lines = [
            "# Live ROM Operator Report — Archive",
            "",
            f"**Archive root:** `{archive_root}`",
            f"**Status:** {summary.status}",
            f"**Archived rows:** {summary.total_archived_rows:,}",
            f"**Data kinds:** {', '.join(summary.data_kinds) if summary.data_kinds else 'none'}",
            f"**Runs:** {', '.join(summary.run_ids) if summary.run_ids else 'none'}",
            f"**Alerts reported:** {summary.n_alerts_reported}",
            f"**Minimum trust:** {summary.min_trust if summary.min_trust is not None else 'n/a'}",
            "",
            "## Alert summary",
            _table_md(tables.get("alert_summary", pd.DataFrame()), 20),
            "",
            "## Trust summary sample",
            _table_md(tables.get("trust_summary", pd.DataFrame()), 20),
            "",
            "## Residual summary sample",
            _table_md(tables.get("residual_summary", pd.DataFrame()), 20),
            "",
            "## Recommended next actions",
            "- Open the Streamlit archive dashboard for interactive filtering.",
            "- Inspect low-trust windows and large residual states first.",
            "- Use `dmdc archive-search` to locate source files for events of interest.",
        ]
        payload = asdict(summary)
    else:
        run_dir = Path(run_dir or "outputs/live_monitoring")
        summary = summarize_live_dashboard(run_dir)
        tables = read_live_dashboard_tables(run_dir)
        alerts = tables.get("alerts", pd.DataFrame())
        residuals = tables.get("residuals", pd.DataFrame())
        comparison = tables.get("bias_error_comparison", pd.DataFrame())
        if not residuals.empty and "abs_residual" in residuals.columns:
            residuals = residuals.sort_values("abs_residual", ascending=False)
        lines = [
            "# Live ROM Operator Report — Run",
            "",
            f"**Run directory:** `{run_dir}`",
            f"**Status:** {summary.status}",
            f"**Latest time:** {summary.latest_time if summary.latest_time is not None else 'n/a'}",
            f"**Latest trust score:** {summary.latest_trust_score if summary.latest_trust_score is not None else 'n/a'}",
            f"**Alerts:** {summary.n_alerts} total; {summary.n_critical_alerts} critical; {summary.n_warning_alerts} warning",
            f"**Bias updates:** {summary.n_bias_updates_accepted}/{summary.n_bias_update_events} accepted",
            "",
            "## Latest / highest-priority alerts",
            _table_md(alerts.tail(20), 20),
            "",
            "## Largest matched forecast residuals",
            _table_md(residuals, 20),
            "",
            "## Bias correction effect",
            _table_md(comparison, 20),
            "",
            "## Recommended next actions",
            "- Use the dashboard operator view for interactive plots.",
            "- Investigate states with repeated high residuals or growing bias.",
            "- If trust remains low, review operating-envelope warnings and compare against offline validation ranges.",
            "- Do not use this report as autonomous control logic; it is advisory monitoring output.",
        ]
        payload = asdict(summary)
    md = "\n".join(lines) + "\n"
    md_path = outdir / "live_operator_report.md"
    html_path = outdir / "live_operator_report.html"
    json_path = outdir / "live_operator_report_summary.json"
    md_path.write_text(md, encoding="utf-8")
    _write_html_from_markdown(md, html_path)
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return {"markdown": str(md_path), "html": str(html_path), "summary": str(json_path)}
