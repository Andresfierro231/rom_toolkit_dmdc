"""Simple archive search helpers for long live archives.

This module is intentionally lightweight.  It searches manifest metadata and a
small number of archived files for common triage questions: alert codes,
large residuals, low trust score, or rows involving a specific state.  For very
large archives, use ``max_files_per_kind`` first, then drill into exact manifest
paths returned by the search.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

import pandas as pd

from .live_archive import load_archive_kind, read_archive_manifest
from .provenance import write_provenance


@dataclass
class ArchiveSearchConfig:
    archive_root: str = "live_archive"
    outdir: str = "outputs/archive_search"
    data_kind: str | None = None
    alert_code: str | None = None
    severity: str | None = None
    state: str | None = None
    residual_above: float | None = None
    trust_below: float | None = None
    max_files_per_kind: int | None = None


@dataclass
class ArchiveSearchResult:
    archive_root: str
    outdir: str
    n_matching_rows: int
    n_matching_manifest_files: int
    results_csv: str
    matching_files_txt: str


def search_archive(config: ArchiveSearchConfig, *, config_path: str | Path | None = None) -> ArchiveSearchResult:
    """Search a live archive and write result tables."""

    out = Path(config.outdir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = read_archive_manifest(config.archive_root)
    manifest_matches = _filter_manifest(manifest, config)

    row_frames: list[pd.DataFrame] = []
    kinds = _kinds_to_scan(config)
    for kind in kinds:
        df = load_archive_kind(config.archive_root, kind, max_files=config.max_files_per_kind)
        if df.empty:
            continue
        filtered = _filter_rows(df, kind, config)
        if not filtered.empty:
            filtered.insert(0, "data_kind", kind)
            row_frames.append(filtered)
    rows = pd.concat(row_frames, ignore_index=True) if row_frames else pd.DataFrame()

    results_csv = out / "search_results.csv"
    rows.to_csv(results_csv, index=False)
    matching_files_txt = out / "matching_files.txt"
    paths = []
    if not manifest_matches.empty and "path" in manifest_matches.columns:
        paths = [str(Path(config.archive_root) / p) for p in manifest_matches["path"].astype(str).tolist()]
    matching_files_txt.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
    manifest_matches.to_csv(out / "matching_manifest_rows.csv", index=False)
    result = ArchiveSearchResult(
        archive_root=config.archive_root,
        outdir=str(out),
        n_matching_rows=int(len(rows)),
        n_matching_manifest_files=int(len(manifest_matches)),
        results_csv=str(results_csv),
        matching_files_txt=str(matching_files_txt),
    )
    (out / "search_summary.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    write_provenance(out, config_path=config_path, extra={"command": "archive-search", "result": asdict(result)})
    return result


def _kinds_to_scan(config: ArchiveSearchConfig) -> list[str]:
    if config.data_kind:
        return [config.data_kind]
    kinds: list[str] = []
    if config.alert_code or config.severity:
        kinds.append("alerts")
    if config.trust_below is not None:
        kinds.append("trust_score")
    if config.residual_above is not None:
        kinds.extend(["residuals", "bias_corrected_residuals"])
    if config.state and not kinds:
        kinds.extend(["cleaned_stream", "state_estimates", "residuals", "bias_state_timeseries"])
    if not kinds:
        kinds.append("alerts")
    return list(dict.fromkeys(kinds))


def _filter_manifest(manifest: pd.DataFrame, config: ArchiveSearchConfig) -> pd.DataFrame:
    if manifest.empty:
        return pd.DataFrame()
    out = manifest.copy()
    if config.data_kind and "data_kind" in out.columns:
        out = out[out["data_kind"].astype(str) == str(config.data_kind)]
    elif config.alert_code or config.severity:
        out = out[out.get("data_kind", pd.Series(dtype=str)).astype(str) == "alerts"]
    elif config.trust_below is not None:
        out = out[out.get("data_kind", pd.Series(dtype=str)).astype(str) == "trust_score"]
    elif config.residual_above is not None:
        out = out[out.get("data_kind", pd.Series(dtype=str)).astype(str).isin(["residuals", "bias_corrected_residuals"])]
    return out


def _filter_rows(df: pd.DataFrame, kind: str, config: ArchiveSearchConfig) -> pd.DataFrame:
    out = df.copy()
    if config.alert_code and "code" in out.columns:
        out = out[out["code"].astype(str) == str(config.alert_code)]
    if config.severity and "severity" in out.columns:
        out = out[out["severity"].astype(str).str.lower() == str(config.severity).lower()]
    if config.state:
        if "state" in out.columns:
            out = out[out["state"].astype(str) == str(config.state)]
        elif config.state in out.columns:
            # Wide cleaned_stream case: keep rows and include only time + requested state when possible.
            keep = [c for c in ["time", "timestamp", config.state] if c in out.columns]
            out = out[keep]
        else:
            out = out.iloc[0:0]
    if config.residual_above is not None:
        abs_cols = [c for c in ["abs_residual", "abs_bias_corrected_residual"] if c in out.columns]
        if abs_cols:
            mask = pd.Series(False, index=out.index)
            for col in abs_cols:
                mask = mask | (pd.to_numeric(out[col], errors="coerce") >= float(config.residual_above))
            out = out[mask]
        else:
            out = out.iloc[0:0]
    if config.trust_below is not None:
        if "trust_score" in out.columns:
            out = out[pd.to_numeric(out["trust_score"], errors="coerce") <= float(config.trust_below)]
        else:
            out = out.iloc[0:0]
    return out
