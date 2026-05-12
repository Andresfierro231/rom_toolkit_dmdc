"""Archive schema validation and human-readable context index tables."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import pandas as pd
from .live_archive import read_archive_manifest

ARCHIVE_SCHEMA_VERSION = "archive_schema_v1"
REQUIRED_MANIFEST_COLUMNS = {"schema_version","run_id","data_kind","path","format","n_rows","columns","file_size_bytes"}
RECOMMENDED_COLUMNS_BY_KIND = {
    "cleaned_stream": {"time"},
    "state_estimates": {"time"},
    "forecasts": {"origin_time","forecast_horizon_s","state","predicted_value"},
    "residuals": {"state","residual","abs_residual"},
    "bias_update_events": {"state","old_bias","new_bias","accepted"},
    "alerts": {"severity","code"},
    "trust_score": {"trust_score"},
}
@dataclass
class ArchiveValidationResult:
    archive_root: str; status: str; manifest_rows: int; n_errors: int; n_warnings: int; validation_report: str; context_index_csv: str; data_kind_summary_csv: str; json_summary: str

def _parse_columns(value: Any) -> set[str]:
    if isinstance(value, list): return set(map(str,value))
    if pd.isna(value): return set()
    text = str(value)
    try:
        payload = json.loads(text)
        if isinstance(payload, list): return set(map(str,payload))
    except Exception: pass
    return {p.strip().strip("'\"") for p in text.strip("[]").split(",") if p.strip()}

def build_archive_context_index(archive_root: str | Path, *, outdir: str | Path | None = None) -> dict[str, Path]:
    root=Path(archive_root); out=Path(outdir) if outdir else root/"context"; out.mkdir(parents=True, exist_ok=True)
    manifest=read_archive_manifest(root)
    context=out/"archive_context_index.csv"; summary_path=out/"archive_data_kind_summary.csv"
    if manifest.empty:
        pd.DataFrame().to_csv(context,index=False); pd.DataFrame().to_csv(summary_path,index=False)
        return {"context_index_csv":context,"data_kind_summary_csv":summary_path}
    cols=[c for c in ["run_id","data_kind","date","hour","min_time","max_time","n_rows","file_size_bytes","path","source_file","format","schema_version"] if c in manifest.columns]
    df=manifest[cols].copy()
    if "file_size_bytes" in df: df["file_size_mb"]=pd.to_numeric(df["file_size_bytes"],errors="coerce").fillna(0)/1e6
    df.to_csv(context,index=False)
    if {"run_id","data_kind"}.issubset(manifest.columns):
        summ=manifest.groupby(["run_id","data_kind"], as_index=False).agg(files=("path","count"), rows=("n_rows", lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum()), bytes=("file_size_bytes", lambda s: pd.to_numeric(s, errors="coerce").fillna(0).sum()))
        summ["size_mb"]=summ["bytes"]/1e6
    else: summ=pd.DataFrame()
    summ.to_csv(summary_path,index=False)
    return {"context_index_csv":context,"data_kind_summary_csv":summary_path}

def validate_archive_schema(archive_root: str | Path, *, outdir: str | Path | None = None) -> ArchiveValidationResult:
    root=Path(archive_root); out=Path(outdir) if outdir else root/"schema_validation"; out.mkdir(parents=True, exist_ok=True)
    errors=[]; warnings=[]; manifest=read_archive_manifest(root)
    if manifest.empty: errors.append(f"No manifest rows found under {root}.")
    else:
        missing=sorted(REQUIRED_MANIFEST_COLUMNS-set(manifest.columns))
        if missing: errors.append(f"Manifest missing required columns: {missing}")
        if "path" in manifest:
            # Archive manifests intentionally store paths relative to archive_root
            # so archives can be moved between workstations/HPC filesystems.
            # Treat absolute paths as-is and relative paths as archive-root relative.
            for path in manifest["path"].dropna().astype(str).head(2000):
                candidate = Path(path)
                if not candidate.is_absolute():
                    candidate = root / candidate
                if not candidate.exists():
                    errors.append(f"Manifest references missing file: {path}")
                if len(errors)>50:
                    warnings.append("Stopped missing-file checks after 50 errors.")
                    break
        if {"data_kind","columns"}.issubset(manifest.columns):
            for kind, req in RECOMMENDED_COLUMNS_BY_KIND.items():
                rows=manifest[manifest["data_kind"].astype(str)==kind]
                if rows.empty: warnings.append(f"Recommended data kind not present: {kind}"); continue
                avail=set().union(*(_parse_columns(v) for v in rows["columns"].head(20)))
                miss=sorted(req-avail)
                if miss: warnings.append(f"Data kind {kind!r} may be missing recommended columns: {miss}")
    ctx=build_archive_context_index(root,outdir=root/"context")
    status="failed" if errors else "warning" if warnings else "passed"
    report=out/"archive_schema_validation.md"
    report.write_text("\n".join(["# Archive Schema Validation","",f"Archive root: `{root}`",f"Status: **{status}**",f"Manifest rows: {len(manifest)}",f"Errors: {len(errors)}",f"Warnings: {len(warnings)}","","## Errors",*(f"- {e}" for e in errors or ["None"]),"","## Warnings",*(f"- {w}" for w in warnings or ["None"]),"","## Context files",f"- `{ctx['context_index_csv']}`",f"- `{ctx['data_kind_summary_csv']}`"]), encoding="utf-8")
    js=out/"archive_schema_validation_summary.json"
    js.write_text(json.dumps({"schema_version":ARCHIVE_SCHEMA_VERSION,"archive_root":str(root),"status":status,"manifest_rows":int(len(manifest)),"errors":errors,"warnings":warnings,"context_index_csv":str(ctx["context_index_csv"]),"data_kind_summary_csv":str(ctx["data_kind_summary_csv"])}, indent=2), encoding="utf-8")
    return ArchiveValidationResult(str(root),status,int(len(manifest)),len(errors),len(warnings),str(report),str(ctx["context_index_csv"]),str(ctx["data_kind_summary_csv"]),str(js))
