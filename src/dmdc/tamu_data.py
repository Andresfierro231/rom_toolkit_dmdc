"""Inventory, validation-export, and catalog helpers for TAMU loop datasets."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import math
import re

import numpy as np
import pandas as pd

from .provenance import write_provenance


RAW_CASE_FIELDS = {
    "X": ("x_csv", re.compile(r"^(?:X|NC\d+_X)\.csv$", re.IGNORECASE)),
    "U": ("u_csv", re.compile(r"^(?:U|NC\d+_U)\.csv$", re.IGNORECASE)),
    "V": ("v_csv", re.compile(r"^(?:V|NC\d+_V)\.csv$", re.IGNORECASE)),
    "Y": ("y_csv", re.compile(r"^(?:Y|NC\d+_Y)\.csv$", re.IGNORECASE)),
}

WIDE_MEASUREMENT_MAP = {
    "Air T inlet": "air_T_inlet_C",
    "Air T outlet": "air_T_outlet_C",
    "Air flow": "air_flow_Lpm",
    "Heater Power": "heater_power_W",
    "Heat Removed": "heat_removed_W",
    "TP1": "TP1_C",
    "TP2": "TP2_C",
    "TP3": "TP3_C",
    "TP4": "TP4_C",
    "TP5": "TP5_C",
    "TP6": "TP6_C",
    "TW1": "TW1_C",
    "TW2": "TW2_C",
    "TW3": "TW3_C",
    "TW4": "TW4_C",
    "TW5": "TW5_C",
    "TW6": "TW6_C",
    "TW7": "TW7_C",
    "TW8": "TW8_C",
    "TW9": "TW9_C",
    "TW10 (on shell of HX)": "TW10_C",
    "TW11": "TW11_C",
    "TW11 (K) unlabeled": "unlabeled_TW11_K_excluded",
    "Area-weighted mean velocity": "measured_area_weighted_mean_velocity_m_s",
    "Mass Flow rate": "measured_mass_flow_rate_kg_s",
}

NORMALIZED_CASE_COLUMNS = [
    "case_name",
    "fluid",
    "air_T_inlet_C",
    "air_T_outlet_C",
    "air_flow_Lpm",
    "heater_power_W",
    "heat_removed_W",
    "TP1_C",
    "TP2_C",
    "TP3_C",
    "TP4_C",
    "TP5_C",
    "TP6_C",
    "TW1_C",
    "TW2_C",
    "TW3_C",
    "TW4_C",
    "TW5_C",
    "TW6_C",
    "TW7_C",
    "TW8_C",
    "TW9_C",
    "TW10_C",
    "TW11_C",
    "measured_area_weighted_mean_velocity_m_s",
    "measured_mass_flow_rate_kg_s",
    "temperature_uncertainty_C",
    "air_flow_uncertainty_pct",
    "power_uncertainty_pct",
    "unlabeled_TW11_K_excluded",
    "source_table",
    "source_profile",
]

CATALOG_BUCKETS = [
    "steady_sensor_candidates",
    "transient_sensor_candidates",
    "steady_velocity_profile_candidates",
    "unknown_or_not_yet_interpretable",
]
CONSISTENCY_COMPARE_COLUMNS = [column for column in NORMALIZED_CASE_COLUMNS if column not in {"source_table", "source_profile"}]
WORKBOOK_MEASUREMENT_UNIT_PATTERN = re.compile(r"\s+\((?:°C|W|L/min|m/s|kg/s|m3/s)\)\s*$")
CANONICAL_CASE_NAME_PATTERN = re.compile(r"^(Salt|Water)\s+Test\s+(\d+)$", re.IGNORECASE)
SIMPLE_CASE_NAME_PATTERN = re.compile(r"^(Salt|Water)\s+(\d+)$", re.IGNORECASE)
TEST_CASE_WITH_SUFFIX_PATTERN = re.compile(r"^(Salt|Water)\s+Test\s+(\d+)\s+(.+)$", re.IGNORECASE)
OFFICE_WORKBOOK_SOURCE_PROFILES = {
    "single_phase": "jadyn_office_workbook_single_phase",
    "two_phase": "jadyn_office_workbook_two_phase",
}
CANONICAL_SOURCE_PROFILES = {"wide_validation_source"}
MANUAL_VALIDATION_CASE_OVERRIDES = {
    "2024_05_04/2": ("Salt 1", "collaborator-confirmed 2024_05_04 subfolder mapping"),
    "2024_05_04/3": ("Salt 2", "collaborator-confirmed 2024_05_04 subfolder mapping"),
    "2024_05_04/4": ("Salt 3", "collaborator-confirmed 2024_05_04 subfolder mapping"),
    "2024_05_04/6": ("Salt 4", "collaborator-confirmed 2024_05_04 subfolder mapping"),
}


@dataclass
class TamuInventoryResult:
    root: str
    outdir: str
    executive_summary_md: str
    top_level_csv: str
    folder_comparison_csv: str
    subfolder_inventory_csv: str
    case_inventory_csv: str
    metadata_failures_csv: str
    readme_md: str
    table_of_contents_md: str
    folder_summaries_md: str
    summary_json: str
    n_top_level_items: int
    n_directories_indexed: int
    n_case_dirs: int
    n_metadata_failures: int


@dataclass
class TamuValidationExportResult:
    outdir: str
    inventory_candidates_csv: str | None
    normalized_cases_csv: str | None
    policy_yaml: str | None
    physor_wide_csv: str | None
    nearest_fit_csv: str | None
    source_index_csv: str | None
    office_workbook_rows_csv: str | None
    office_workbook_promotion_csv: str | None
    summary_json: str
    n_inventory_candidates: int
    n_normalized_cases: int
    n_nearest_fit_rows: int
    n_office_workbook_rows: int
    n_office_workbook_blocked: int


@dataclass
class TamuValidationCatalogResult:
    outdir: str
    validation_catalog_csv: str
    steady_sensor_csv: str
    transient_sensor_csv: str
    steady_velocity_csv: str
    unknown_csv: str
    source_provenance_index_csv: str
    velocity_plot_index_csv: str | None
    consistency_report_csv: str | None
    consistency_summary_md: str | None
    discrepancies_only_csv: str | None
    office_workbook_rows_csv: str | None
    office_workbook_promotion_csv: str | None
    summary_md: str
    summary_json: str
    n_catalog_rows: int
    n_velocity_plot_rows: int
    n_consistency_rows: int
    n_consistency_mismatches: int
    n_office_workbook_rows: int
    n_office_workbook_blocked: int


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _is_dated_folder(name: str) -> bool:
    return bool(re.match(r"^\d{4}_\d{2}_\d{2}(?:$|_)", name))


def _top_level_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    if path.suffix.lower() == ".zip":
        return "archive_zip"
    if path.suffix.lower() in {".txt", ".md", ".docx"}:
        return "reference_doc"
    if path.suffix.lower() in {".m", ".py"}:
        return "script"
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return "spreadsheet"
    return "file"


def _csv_shape(path: Path) -> tuple[int, int]:
    rows = 0
    cols = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.rstrip("\n")
            if not stripped:
                continue
            rows += 1
            if cols == 0:
                cols = len(stripped.split(","))
    return rows, cols


def _repair_meta_json(text: str) -> str:
    repaired = text.replace("\r\n", "\n")
    repaired = re.sub(r"([0-9\]}\"])(\s*\n\s*\")", r"\1,\2", repaired)
    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
    return repaired


def _load_metadata(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(raw), "valid", None
    except json.JSONDecodeError as exc:
        repaired = _repair_meta_json(raw)
        try:
            return json.loads(repaired), "repaired", str(exc)
        except json.JSONDecodeError as repaired_exc:
            return None, "invalid", str(repaired_exc)


def _flatten_meta(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    settings = payload.get("system_settings", {}) if isinstance(payload, dict) else {}
    power = settings.get("power", {}) if isinstance(settings, dict) else {}
    temperature = settings.get("temperature", {}) if isinstance(settings, dict) else {}
    flow = settings.get("volumetric_flow_rate", {}) if isinstance(settings, dict) else {}
    return {
        "start_date": payload.get("start_date"),
        "start_time": payload.get("start_time"),
        "measurement_date": payload.get("measurement_date"),
        "measurement_time": payload.get("measurment_time", payload.get("measurement_time")),
        "metadata_power_hot_1_W": power.get("hot_1"),
        "metadata_power_hot_2_W": power.get("hot_2"),
        "metadata_power_cold_1_2_W": power.get("cold_1_2"),
        "metadata_test_section_power_W": power.get("Test_Section"),
        "metadata_temperature_hot_1_C": temperature.get("hot_1"),
        "metadata_temperature_hot_2_C": temperature.get("hot_2"),
        "metadata_temperature_cold_1_2_C": temperature.get("cold_1_2"),
        "metadata_volumetric_flow_rate_Lpm": flow.get("flow_rate"),
    }


def _find_case_dirs(root: Path) -> list[Path]:
    case_dirs: list[Path] = []
    for directory in sorted(p for p in root.rglob("*") if p.is_dir()):
        names = {child.name for child in directory.iterdir() if child.is_file()}
        if "meta_data.json" in names:
            case_dirs.append(directory)
            continue
        if any(pattern.search(name) for name in names for _, pattern in RAW_CASE_FIELDS.values()):
            case_dirs.append(directory)
    return case_dirs


def _split_items(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [item for item in text.split(";") if item]


def _preview(items: list[str], *, limit: int = 8) -> str:
    if not items:
        return "none"
    if len(items) <= limit:
        return ", ".join(f"`{item}`" for item in items)
    shown = ", ".join(f"`{item}`" for item in items[:limit])
    return f"{shown} (+{len(items) - limit} more)"


def _format_number(value: Any) -> str:
    number = _to_float(value)
    if number is None:
        return ""
    if float(number).is_integer():
        return str(int(number))
    return f"{number:.6g}"


def _format_range(frame: pd.DataFrame, column: str, unit: str = "") -> str:
    if column not in frame.columns:
        return "not available"
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return "not available"
    lo = float(values.min())
    hi = float(values.max())
    if abs(lo - hi) < 1.0e-12:
        return f"{_format_number(lo)}{unit}"
    return f"{_format_number(lo)} to {_format_number(hi)}{unit}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["_No entries._"]
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return [header, divider, *body]


def _status_counts_text(frame: pd.DataFrame) -> str:
    if "metadata_parse_status" not in frame.columns:
        return ""
    counts = frame["metadata_parse_status"].fillna("missing").value_counts()
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _build_directory_inventory(root: Path, case_dirs: list[Path]) -> pd.DataFrame:
    case_rel = {_rel(path, root) for path in case_dirs}
    directories = [root, *sorted(path for path in root.rglob("*") if path.is_dir())]
    rows: list[dict[str, Any]] = []
    for directory in directories:
        rel = "." if directory == root else _rel(directory, root)
        parts = [] if directory == root else list(directory.relative_to(root).parts)
        children = sorted(directory.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower()))
        immediate_dirs = [child.name for child in children if child.is_dir()]
        immediate_files = [child.name for child in children if child.is_file()]
        recursive_dirs = [path for path in directory.rglob("*") if path.is_dir()]
        recursive_files = [path for path in directory.rglob("*") if path.is_file()]
        suffix_counts = Counter((path.suffix.lower() or "[no_ext]") for path in recursive_files)
        rows.append(
            {
                "relative_path": rel,
                "parent_relative_path": "" if directory == root else ("." if len(parts) == 1 else _rel(directory.parent, root)),
                "top_level_folder": "." if directory == root else parts[0],
                "depth": len(parts),
                "is_case_dir": rel in case_rel,
                "n_immediate_dirs": len(immediate_dirs),
                "n_immediate_files": len(immediate_files),
                "n_recursive_dirs": len(recursive_dirs),
                "n_recursive_files": len(recursive_files),
                "immediate_subdirs": ";".join(immediate_dirs),
                "immediate_files": ";".join(immediate_files),
                "recursive_suffix_counts_json": json.dumps(dict(sorted(suffix_counts.items())), sort_keys=True),
            }
        )
    return pd.DataFrame(rows).sort_values(["depth", "relative_path"]).reset_index(drop=True)


def _render_inventory_readme(
    root: Path,
    top_df: pd.DataFrame,
    dir_df: pd.DataFrame,
    case_df: pd.DataFrame,
    failures_df: pd.DataFrame,
) -> list[str]:
    lines = [
        "# TAMU Loop Data Inventory README",
        "",
        f"Root: `{root}`",
        "",
        "## Overview",
        "",
        f"- Top-level items: {len(top_df)}",
        f"- Directories indexed recursively: {len(dir_df)}",
        f"- Case-like subfolders detected: {len(case_df)}",
        f"- Metadata parse failures: {len(failures_df)}",
        "",
        "## Generated Artifacts",
        "",
        "- `README.md`: this high-level report",
        "- `EXECUTIVE_SUMMARY.md`: shorter summary focused on dated folders",
        "- `TABLE_OF_CONTENTS.md`: nested table of contents for root items, folders, and direct subfolders",
        "- `folder_summaries.md`: detailed folder-by-folder and case-by-case report",
        "- `folder_comparison.csv`: per-top-level-folder comparison table derived from the inventories",
        "- `top_level_contents.csv`: top-level inventory table",
        "- `subfolder_inventory.csv`: recursive directory inventory for every folder/subfolder",
        "- `case_inventory.csv`: detected case-level inventory with file and metadata fields",
        "- `metadata_failures.csv`: any metadata parse failures",
        "",
        "## Top-Level Snapshot",
        "",
    ]
    rows: list[list[str]] = []
    for _, row in top_df.sort_values("name").iterrows():
        note = row["kind"]
        if bool(row.get("is_dir", False)):
            folder_cases = case_df[case_df["top_level_folder"] == row["name"]] if not case_df.empty else pd.DataFrame()
            note = f"{len(folder_cases)} case dirs; {int(row.get('n_recursive_files') or 0)} recursive files"
        rows.append(
            [
                f"`{row['name']}`",
                str(row["kind"]),
                str(int(row.get("n_immediate_children") or 0)) if bool(row.get("is_dir", False)) else "",
                str(int(row.get("n_recursive_files") or 0)) if bool(row.get("is_dir", False)) else "",
                note,
            ]
        )
    lines.extend(_markdown_table(["item", "kind", "immediate_children", "recursive_files", "notes"], rows))
    lines.extend(["", "## Key Observations", ""])
    if not case_df.empty:
        folder_counts = case_df.groupby("top_level_folder").size().sort_values(ascending=False)
        largest = folder_counts.index[0]
        lines.append(f"- Largest detected case collection: `{largest}` with {int(folder_counts.iloc[0])} case-like subfolders.")
    if not failures_df.empty:
        lines.append(f"- Metadata parse failures were detected in {len(failures_df)} case folders; review `metadata_failures.csv`.")
    else:
        lines.append("- No unrepaired metadata parse failures were detected.")
    files_only = top_df[top_df["is_dir"] == False]
    if not files_only.empty:
        archives = int((files_only["kind"] == "archive_zip").sum())
        docs = int(files_only["kind"].isin(["reference_doc", "spreadsheet", "script"]).sum())
        lines.append(f"- Root-level non-directory items include {archives} ZIP archives and {docs} direct reference/script/spreadsheet files.")
    return lines


def _build_folder_comparison(top_df: pd.DataFrame, dir_df: pd.DataFrame, case_df: pd.DataFrame) -> pd.DataFrame:
    dir_lookup = {str(row["relative_path"]): row for _, row in dir_df.iterrows()}
    rows: list[dict[str, Any]] = []
    for _, row in top_df[top_df["is_dir"] == True].sort_values("name").iterrows():
        folder = str(row["name"])
        folder_dir = dir_lookup.get(folder)
        folder_cases = case_df[case_df["top_level_folder"] == folder] if not case_df.empty else pd.DataFrame()
        suffix_counts = json.loads(folder_dir["recursive_suffix_counts_json"]) if folder_dir is not None and folder_dir.get("recursive_suffix_counts_json") else {}
        rows.append(
            {
                "folder_name": folder,
                "is_dated_folder": _is_dated_folder(folder),
                "case_like_subfolders": int(len(folder_cases)),
                "immediate_subdirs": int(folder_dir.get("n_immediate_dirs") or 0) if folder_dir is not None else 0,
                "direct_files": int(folder_dir.get("n_immediate_files") or 0) if folder_dir is not None else 0,
                "recursive_dirs": int(folder_dir.get("n_recursive_dirs") or 0) if folder_dir is not None else 0,
                "recursive_files": int(folder_dir.get("n_recursive_files") or 0) if folder_dir is not None else 0,
                "metadata_files": int(folder_cases["has_meta_data_json"].fillna(False).sum()) if not folder_cases.empty else 0,
                "metadata_status_counts": _status_counts_text(folder_cases),
                "mat_case_dirs": int(folder_cases["has_mat_file"].fillna(False).sum()) if not folder_cases.empty else 0,
                "recursive_csv_files": int(suffix_counts.get(".csv", 0)),
                "recursive_json_files": int(suffix_counts.get(".json", 0)),
                "recursive_mat_files": int(suffix_counts.get(".mat", 0)),
                "recursive_txt_files": int(suffix_counts.get(".txt", 0)),
                "recursive_xlsx_files": int(suffix_counts.get(".xlsx", 0)),
                "recursive_docx_files": int(suffix_counts.get(".docx", 0)),
                "heater_power_min_W": _format_number(pd.to_numeric(folder_cases.get("candidate_heater_power_W"), errors="coerce").min()) if not folder_cases.empty else "",
                "heater_power_max_W": _format_number(pd.to_numeric(folder_cases.get("candidate_heater_power_W"), errors="coerce").max()) if not folder_cases.empty else "",
                "air_flow_min_Lpm": _format_number(pd.to_numeric(folder_cases.get("candidate_air_flow_Lpm"), errors="coerce").min()) if not folder_cases.empty else "",
                "air_flow_max_Lpm": _format_number(pd.to_numeric(folder_cases.get("candidate_air_flow_Lpm"), errors="coerce").max()) if not folder_cases.empty else "",
                "test_section_power_min_W": _format_number(pd.to_numeric(folder_cases.get("candidate_test_section_power_W"), errors="coerce").min()) if not folder_cases.empty else "",
                "test_section_power_max_W": _format_number(pd.to_numeric(folder_cases.get("candidate_test_section_power_W"), errors="coerce").max()) if not folder_cases.empty else "",
                "direct_subdir_names": str(folder_dir.get("immediate_subdirs") or "") if folder_dir is not None else "",
                "direct_file_names": str(folder_dir.get("immediate_files") or "") if folder_dir is not None else "",
            }
        )
    return pd.DataFrame(rows).sort_values(["is_dated_folder", "folder_name"], ascending=[False, True]).reset_index(drop=True)


def _render_executive_summary(root: Path, comparison_df: pd.DataFrame) -> list[str]:
    lines = [
        "# TAMU Dated Folder Executive Summary",
        "",
        f"Root: `{root}`",
        "",
        "## Scope",
        "",
        "This summary focuses on top-level dated folders and highlights the main structural differences between them.",
        "",
    ]
    dated = comparison_df[comparison_df["is_dated_folder"] == True].copy()
    if dated.empty:
        lines.append("No dated folders were detected.")
        return lines
    lines.extend(["## Dated Folder Comparison", ""])
    table_rows: list[list[str]] = []
    for _, row in dated.iterrows():
        heater = row["heater_power_min_W"]
        if row["heater_power_min_W"] and row["heater_power_max_W"] and row["heater_power_min_W"] != row["heater_power_max_W"]:
            heater = f"{row['heater_power_min_W']} to {row['heater_power_max_W']}"
        airflow = row["air_flow_min_Lpm"]
        if row["air_flow_min_Lpm"] and row["air_flow_max_Lpm"] and row["air_flow_min_Lpm"] != row["air_flow_max_Lpm"]:
            airflow = f"{row['air_flow_min_Lpm']} to {row['air_flow_max_Lpm']}"
        table_rows.append(
            [
                f"`{row['folder_name']}`",
                str(int(row["case_like_subfolders"])),
                str(int(row["recursive_files"])),
                str(row["metadata_status_counts"] or "none"),
                heater or "n/a",
                airflow or "n/a",
            ]
        )
    lines.extend(_markdown_table(["folder", "case_dirs", "recursive_files", "metadata_status", "heater_W", "air_flow_Lpm"], table_rows))
    lines.extend(["", "## Folder Notes", ""])
    for _, row in dated.iterrows():
        lines.extend(
            [
                f"### {row['folder_name']}",
                "",
                f"- Case-like subfolders: {int(row['case_like_subfolders'])}",
                f"- Recursive files: {int(row['recursive_files'])} across {int(row['recursive_dirs'])} nested directories",
                f"- Metadata status: {row['metadata_status_counts'] or 'none'}",
                f"- Recursive file mix: `.csv` x {int(row['recursive_csv_files'])}, `.json` x {int(row['recursive_json_files'])}, `.mat` x {int(row['recursive_mat_files'])}, `.txt` x {int(row['recursive_txt_files'])}, `.xlsx` x {int(row['recursive_xlsx_files'])}",
            ]
        )
        if int(row["case_like_subfolders"]) > 0:
            heater = row["heater_power_min_W"] or "n/a"
            if row["heater_power_min_W"] and row["heater_power_max_W"] and row["heater_power_min_W"] != row["heater_power_max_W"]:
                heater = f"{row['heater_power_min_W']} to {row['heater_power_max_W']} W"
            elif row["heater_power_min_W"]:
                heater = f"{row['heater_power_min_W']} W"
            airflow = row["air_flow_min_Lpm"] or "n/a"
            if row["air_flow_min_Lpm"] and row["air_flow_max_Lpm"] and row["air_flow_min_Lpm"] != row["air_flow_max_Lpm"]:
                airflow = f"{row['air_flow_min_Lpm']} to {row['air_flow_max_Lpm']} L/min"
            elif row["air_flow_min_Lpm"]:
                airflow = f"{row['air_flow_min_Lpm']} L/min"
            lines.extend(
                [
                    f"- Heater-power range: {heater}",
                    f"- Air-flow range: {airflow}",
                    f"- Direct subfolders: {_preview(_split_items(row['direct_subdir_names']), limit=12)}",
                    f"- Direct files: {_preview(_split_items(row['direct_file_names']), limit=8)}",
                ]
            )
        else:
            lines.extend(
                [
                    "- No case-like subfolders were detected by the metadata/CSV heuristic.",
                    f"- Direct files: {_preview(_split_items(row['direct_file_names']), limit=12)}",
                ]
            )
        lines.append("")
    nondated = comparison_df[comparison_df["is_dated_folder"] == False]
    if not nondated.empty:
        lines.extend(["## Additional Non-Dated Top-Level Folders", ""])
        extra_rows = [
            [f"`{row['folder_name']}`", str(int(row["case_like_subfolders"])), str(int(row["recursive_files"]))]
            for _, row in nondated.iterrows()
        ]
        lines.extend(_markdown_table(["folder", "case_dirs", "recursive_files"], extra_rows))
    return lines


def _render_inventory_toc(root: Path, top_df: pd.DataFrame, dir_df: pd.DataFrame) -> list[str]:
    dir_lookup = {
        str(row["relative_path"]): row
        for _, row in dir_df.iterrows()
    }
    lines = ["# TAMU Loop Data Table of Contents", "", f"Root: `{root}`", "", "## Root Items", ""]
    for _, row in top_df.sort_values("name").iterrows():
        rel = str(row["relative_path"])
        if not bool(row["is_dir"]):
            lines.append(f"- `{row['name']}`: {row['kind']}")
            continue
        lines.append(
            f"- `{row['name']}/`: directory; immediate subdirs={int(row.get('n_immediate_dirs') or 0)}, direct files={int(row.get('n_immediate_files') or 0)}, recursive files={int(row.get('n_recursive_files') or 0)}"
        )
        subdirs = _split_items(row.get("immediate_subdirs"))
        for subdir in subdirs:
            sub_rel = f"{rel}/{subdir}"
            sub_row = dir_lookup.get(sub_rel)
            if sub_row is None:
                lines.append(f"  - `{sub_rel}/`: directory")
                continue
            kind = "case-like folder" if bool(sub_row.get("is_case_dir")) else "directory"
            lines.append(
                f"  - `{sub_rel}/`: {kind}; direct files={int(sub_row.get('n_immediate_files') or 0)}, recursive files={int(sub_row.get('n_recursive_files') or 0)}"
            )
        direct_files = _split_items(row.get("immediate_files"))
        for file_name in direct_files:
            lines.append(f"  - `{rel}/{file_name}`: file")
    return lines


def _render_folder_summaries(top_df: pd.DataFrame, dir_df: pd.DataFrame, case_df: pd.DataFrame) -> list[str]:
    dir_lookup = {
        str(row["relative_path"]): row
        for _, row in dir_df.iterrows()
    }
    lines = ["# TAMU Folder Summaries", ""]
    file_rows = top_df[top_df["is_dir"] == False].sort_values("name")
    if not file_rows.empty:
        lines.extend(["## Root-Level Files And Archives", ""])
        root_rows = [[f"`{row['name']}`", str(row["kind"])] for _, row in file_rows.iterrows()]
        lines.extend(_markdown_table(["name", "kind"], root_rows))
        lines.append("")
    directory_rows = top_df[top_df["is_dir"] == True].sort_values("name")
    for _, row in directory_rows.iterrows():
        folder = str(row["name"])
        folder_dir = dir_lookup.get(folder)
        folder_cases = case_df[case_df["top_level_folder"] == folder] if not case_df.empty else pd.DataFrame()
        direct_files = _split_items(folder_dir.get("immediate_files")) if folder_dir is not None else []
        direct_subdirs = _split_items(folder_dir.get("immediate_subdirs")) if folder_dir is not None else []
        suffix_counts = json.loads(folder_dir["recursive_suffix_counts_json"]) if folder_dir is not None and folder_dir.get("recursive_suffix_counts_json") else {}
        suffix_summary = ", ".join(f"`{suffix}` x {count}" for suffix, count in suffix_counts.items()) if suffix_counts else "none"
        lines.extend(
            [
                f"## {folder}",
                "",
                f"- Relative path: `{folder}`",
                f"- Immediate subfolders ({len(direct_subdirs)}): {_preview(direct_subdirs, limit=12)}",
                f"- Direct files ({len(direct_files)}): {_preview(direct_files, limit=12)}",
                f"- Recursive subfolders: {int(folder_dir.get('n_recursive_dirs') or 0) if folder_dir is not None else 0}",
                f"- Recursive files: {int(folder_dir.get('n_recursive_files') or 0) if folder_dir is not None else 0}",
                f"- Recursive file types: {suffix_summary}",
            ]
        )
        if folder_cases.empty:
            child_rows = dir_df[(dir_df["parent_relative_path"] == folder) & (dir_df["relative_path"] != folder)].sort_values("relative_path")
            lines.append("- No case-like folders detected by the current metadata/CSV heuristic.")
            if not child_rows.empty:
                lines.extend(["", "### Direct Subfolder Inventory", ""])
                sub_rows = []
                for _, child in child_rows.iterrows():
                    sub_rows.append(
                        [
                            f"`{child['relative_path']}`",
                            "yes" if bool(child["is_case_dir"]) else "no",
                            str(int(child["n_immediate_files"])),
                            str(int(child["n_recursive_files"])),
                        ]
                    )
                lines.extend(_markdown_table(["subfolder", "case_like", "direct_files", "recursive_files"], sub_rows))
            lines.append("")
            continue
        parse_counts = folder_cases.get("metadata_parse_status", pd.Series(dtype=str)).fillna("missing").value_counts()
        lines.extend(
            [
                f"- Case directories: {len(folder_cases)}",
                f"- Metadata files: {int(folder_cases['has_meta_data_json'].fillna(False).sum())}",
                f"- Metadata status counts: {', '.join(f'{key}={value}' for key, value in parse_counts.items())}",
                f"- MAT files present: {int(folder_cases['has_mat_file'].fillna(False).sum())}",
                f"- Heater power range: {_format_range(folder_cases, 'candidate_heater_power_W', ' W')}",
                f"- Air flow range: {_format_range(folder_cases, 'candidate_air_flow_Lpm', ' L/min')}",
                f"- Test-section power range: {_format_range(folder_cases, 'candidate_test_section_power_W', ' W')}",
                "",
                "### Case Inventory",
                "",
            ]
        )
        case_rows_md: list[list[str]] = []
        for _, case_row in folder_cases.sort_values("case_dir").iterrows():
            case_rows_md.append(
                [
                    f"`{case_row['case_folder_name']}`",
                    str(int(case_row.get("file_count", 0))),
                    str(case_row.get("metadata_parse_status", "")),
                    "yes" if bool(case_row.get("has_mat_file", False)) else "no",
                    _format_number(case_row.get("candidate_heater_power_W")),
                    _format_number(case_row.get("candidate_air_flow_Lpm")),
                    _format_number(case_row.get("candidate_test_section_power_W")),
                    _preview(_split_items(case_row.get("files")), limit=6),
                ]
            )
        lines.extend(
            _markdown_table(
                ["case", "files", "metadata", "mat", "heater_W", "air_flow_Lpm", "test_section_W", "direct_files"],
                case_rows_md,
            )
        )
        lines.append("")
    return lines


def build_tamu_inventory(root: str | Path, outdir: str | Path, *, config_path: str | Path | None = None) -> TamuInventoryResult:
    root_path = Path(root)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    case_dirs = _find_case_dirs(root_path)
    dir_df = _build_directory_inventory(root_path, case_dirs)
    dir_lookup = {str(row["relative_path"]): row for _, row in dir_df.iterrows()}

    top_level_rows: list[dict[str, Any]] = []
    for child in sorted(root_path.iterdir()):
        rel = _rel(child, root_path)
        top_level_rows.append(
            {
                "name": child.name,
                "kind": _top_level_kind(child),
                "relative_path": rel,
                "is_dir": child.is_dir(),
                "n_immediate_children": len(list(child.iterdir())) if child.is_dir() else None,
                "n_immediate_dirs": int(dir_lookup[rel]["n_immediate_dirs"]) if child.is_dir() and rel in dir_lookup else None,
                "n_immediate_files": int(dir_lookup[rel]["n_immediate_files"]) if child.is_dir() and rel in dir_lookup else None,
                "n_recursive_dirs": int(dir_lookup[rel]["n_recursive_dirs"]) if child.is_dir() and rel in dir_lookup else None,
                "n_recursive_files": int(dir_lookup[rel]["n_recursive_files"]) if child.is_dir() and rel in dir_lookup else None,
                "immediate_subdirs": str(dir_lookup[rel]["immediate_subdirs"]) if child.is_dir() and rel in dir_lookup else "",
                "immediate_files": str(dir_lookup[rel]["immediate_files"]) if child.is_dir() and rel in dir_lookup else "",
            }
        )

    case_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for case_dir in case_dirs:
        row: dict[str, Any] = {
            "case_dir": _rel(case_dir, root_path),
            "top_level_folder": case_dir.relative_to(root_path).parts[0],
            "case_folder_name": case_dir.name,
            "has_meta_data_json": False,
            "has_mat_file": False,
            "file_count": 0,
        }
        names = []
        for file_path in sorted(p for p in case_dir.iterdir() if p.is_file()):
            row["file_count"] += 1
            names.append(file_path.name)
            if file_path.suffix.lower() == ".mat":
                row["has_mat_file"] = True
            if file_path.name == "meta_data.json":
                row["has_meta_data_json"] = True
                payload, status, error = _load_metadata(file_path)
                row["metadata_path"] = _rel(file_path, root_path)
                row["metadata_parse_status"] = status
                row["metadata_parse_error"] = error
                row.update(_flatten_meta(payload))
                if status == "invalid":
                    failure_rows.append(
                        {
                            "case_dir": row["case_dir"],
                            "metadata_path": row["metadata_path"],
                            "parse_status": status,
                            "error": error,
                        }
                    )
            if file_path.suffix.lower() == ".csv":
                csv_rows, csv_cols = _csv_shape(file_path)
                row[f"{file_path.stem}_rows"] = csv_rows
                row[f"{file_path.stem}_cols"] = csv_cols
            for label, pattern in RAW_CASE_FIELDS.values():
                if pattern.search(file_path.name):
                    row[label] = _rel(file_path, root_path)
        row["files"] = ";".join(names)
        row["candidate_heater_power_W"] = row.get("metadata_power_hot_1_W")
        row["candidate_air_flow_Lpm"] = row.get("metadata_volumetric_flow_rate_Lpm")
        row["candidate_test_section_power_W"] = row.get("metadata_test_section_power_W")
        row["ready_for_validation_export"] = False
        row["review_status"] = "metadata_only"
        case_rows.append(row)

    top_df = pd.DataFrame(top_level_rows).sort_values("name").reset_index(drop=True)
    case_df = pd.DataFrame(case_rows).sort_values("case_dir").reset_index(drop=True) if case_rows else pd.DataFrame()
    failures_df = pd.DataFrame(failure_rows).sort_values("case_dir").reset_index(drop=True) if failure_rows else pd.DataFrame(columns=["case_dir", "metadata_path", "parse_status", "error"])
    comparison_df = _build_folder_comparison(top_df, dir_df, case_df)

    executive_summary_md = out / "EXECUTIVE_SUMMARY.md"
    top_csv = out / "top_level_contents.csv"
    comparison_csv = out / "folder_comparison.csv"
    subfolder_csv = out / "subfolder_inventory.csv"
    case_csv = out / "case_inventory.csv"
    failures_csv = out / "metadata_failures.csv"
    top_df.to_csv(top_csv, index=False)
    comparison_df.to_csv(comparison_csv, index=False)
    dir_df.to_csv(subfolder_csv, index=False)
    case_df.to_csv(case_csv, index=False)
    failures_df.to_csv(failures_csv, index=False)

    readme_lines = _render_inventory_readme(root_path, top_df, dir_df, case_df, failures_df)
    readme_md = out / "README.md"
    readme_md.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    executive_lines = _render_executive_summary(root_path, comparison_df)
    executive_summary_md.write_text("\n".join(executive_lines) + "\n", encoding="utf-8")

    toc_lines = _render_inventory_toc(root_path, top_df, dir_df)
    toc_md = out / "TABLE_OF_CONTENTS.md"
    toc_md.write_text("\n".join(toc_lines) + "\n", encoding="utf-8")

    summary_lines = _render_folder_summaries(top_df, dir_df, case_df)
    folder_md = out / "folder_summaries.md"
    folder_md.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    summary_json = out / "inventory_summary.json"
    summary_payload = {
        "root": str(root_path),
        "outdir": str(out),
        "n_top_level_items": int(len(top_df)),
        "n_directories_indexed": int(len(dir_df)),
        "n_case_dirs": int(len(case_df)),
        "n_metadata_failures": int(len(failures_df)),
        "readme_md": str(readme_md),
        "executive_summary_md": str(executive_summary_md),
        "folder_comparison_csv": str(comparison_csv),
        "subfolder_inventory_csv": str(subfolder_csv),
    }
    summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_provenance(out, config_path=config_path, extra={"command": "tamu-inventory", "result": summary_payload})
    return TamuInventoryResult(
        root=str(root_path),
        outdir=str(out),
        executive_summary_md=str(executive_summary_md),
        top_level_csv=str(top_csv),
        folder_comparison_csv=str(comparison_csv),
        subfolder_inventory_csv=str(subfolder_csv),
        case_inventory_csv=str(case_csv),
        metadata_failures_csv=str(failures_csv),
        readme_md=str(readme_md),
        table_of_contents_md=str(toc_md),
        folder_summaries_md=str(folder_md),
        summary_json=str(summary_json),
        n_top_level_items=int(len(top_df)),
        n_directories_indexed=int(len(dir_df)),
        n_case_dirs=int(len(case_df)),
        n_metadata_failures=int(len(failures_df)),
    )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _values_equal(a: Any, b: Any) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    a_number = _to_float(a)
    b_number = _to_float(b)
    if a_number is not None and b_number is not None:
        return a_number == b_number
    return str(a).strip() == str(b).strip()


def _infer_fluid(case_name: str, source_path: Path) -> str:
    text = f"{case_name} {source_path.name}".lower()
    if "salt" in text:
        return "salt"
    if "water" in text:
        return "water"
    return "unknown"


def _canonicalize_case_name(case_name: str) -> str:
    text = " ".join(str(case_name).strip().split())
    match = TEST_CASE_WITH_SUFFIX_PATTERN.match(text)
    if match:
        return f"{match.group(1).title()} {match.group(2)} {match.group(3)}"
    match = CANONICAL_CASE_NAME_PATTERN.match(text)
    if match:
        return f"{match.group(1).title()} {match.group(2)}"
    match = SIMPLE_CASE_NAME_PATTERN.match(text)
    if match:
        return f"{match.group(1).title()} {match.group(2)}"
    return text


def _normalize_workbook_measurement_label(label: Any) -> str:
    text = " ".join(str(label).strip().split())
    if not text or text.lower().startswith("unnamed:"):
        return ""
    return WORKBOOK_MEASUREMENT_UNIT_PATTERN.sub("", text)


def _default_uncertainty_fields(heater_power: float | None) -> dict[str, float]:
    return {
        "temperature_uncertainty_C": 1.1,
        "air_flow_uncertainty_pct": 1.0,
        "power_uncertainty_pct": 0.93 if heater_power is not None and heater_power >= 100.0 else 1.0,
    }


def _finalize_normalized_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    out = pd.DataFrame(rows)
    for column in NORMALIZED_CASE_COLUMNS:
        if column not in out.columns:
            out[column] = pd.NA
    return out[NORMALIZED_CASE_COLUMNS].sort_values(["case_name", "source_table", "source_profile"]).reset_index(drop=True)


def _normalize_wide_validation_frame(frame: pd.DataFrame, source_path: Path, *, source_profile: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    measurement_col = "measurement" if "measurement" in frame.columns else frame.columns[0]
    case_columns = [column for column in frame.columns if column not in {measurement_col, "units"}]
    for case_name_raw in case_columns:
        case_name = _canonicalize_case_name(str(case_name_raw).strip())
        heater_row = frame.loc[frame[measurement_col].astype(str).str.strip() == "Heater Power", case_name_raw]
        heater_power = _to_float(heater_row.iloc[0]) if not heater_row.empty else None
        row: dict[str, Any] = {
            "case_name": case_name,
            "fluid": _infer_fluid(case_name, source_path),
            "source_table": str(source_path),
            "source_profile": source_profile,
            **_default_uncertainty_fields(heater_power),
        }
        for _, source_row in frame.iterrows():
            label = str(source_row.get(measurement_col, "")).strip()
            key = WIDE_MEASUREMENT_MAP.get(label)
            if not key:
                continue
            row[key] = _to_float(source_row.get(case_name_raw))
        rows.append(row)
    return _finalize_normalized_rows(rows)


def _office_workbook_dir(root_path: Path) -> Path:
    return root_path / "Jadyn_runs" / "Jadyn_runs_Office"


def _normalize_office_workbook_sheet(path: Path, *, source_profile: str) -> tuple[pd.DataFrame, bool]:
    frame = pd.read_excel(path, sheet_name=0)
    if frame.empty:
        return pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS), False

    measurement_col = frame.columns[0]
    subcase_row = frame.iloc[0]
    measurement_cell = subcase_row.get(measurement_col)
    has_subcases = (
        (pd.isna(measurement_cell) or not str(measurement_cell).strip())
        and any(str(value).strip() for value in subcase_row.iloc[1:] if pd.notna(value))
    )
    subcase_labels = {
        column: str(subcase_row.get(column)).strip()
        for column in frame.columns[1:]
        if pd.notna(subcase_row.get(column)) and str(subcase_row.get(column)).strip()
    } if has_subcases else {}
    if has_subcases:
        frame = frame.iloc[1:].reset_index(drop=True)

    rows: list[dict[str, Any]] = []
    canonical_family_only = True
    for column in frame.columns[1:]:
        column_name = str(column).strip()
        if not column_name or column_name.lower().startswith("unnamed:"):
            continue
        case_name_raw = column_name
        if has_subcases and subcase_labels.get(column):
            case_name_raw = f"{column_name} {subcase_labels[column]}"
        case_name = _canonicalize_case_name(case_name_raw)
        canonical_match = CANONICAL_CASE_NAME_PATTERN.match(column_name) is not None
        canonical_family_only &= canonical_match and not subcase_labels.get(column)
        row: dict[str, Any] = {
            "case_name": case_name,
            "fluid": _infer_fluid(case_name_raw, path),
            "source_table": str(path),
            "source_profile": source_profile,
        }
        mapped_measurement = False
        for _, source_row in frame.iterrows():
            label = _normalize_workbook_measurement_label(source_row.get(measurement_col))
            key = WIDE_MEASUREMENT_MAP.get(label)
            if not key:
                continue
            mapped_measurement = True
            row[key] = _to_float(source_row.get(column))
        comparable_values = [value for key, value in row.items() if key in WIDE_MEASUREMENT_MAP.values() and _to_float(value) is not None]
        if not mapped_measurement or not comparable_values:
            continue
        heater_power = _to_float(row.get("heater_power_W"))
        row.update(_default_uncertainty_fields(heater_power))
        rows.append(row)
    return _finalize_normalized_rows(rows), canonical_family_only


def normalize_office_workbook_sources(root_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    office_dir = _office_workbook_dir(Path(root_path))
    workbook_rows: list[pd.DataFrame] = []
    repeated_rows: list[pd.DataFrame] = []
    index_rows: list[dict[str, Any]] = []
    if not office_dir.exists():
        return (
            pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS),
            pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS),
            pd.DataFrame(columns=["source_table", "source_profile", "status", "parsed_case_rows", "repeated_source_rows", "notes"]),
        )

    workbook_specs = [
        ("SinglePhaseDataBase.xlsx", OFFICE_WORKBOOK_SOURCE_PROFILES["single_phase"], "single-phase office workbook repeated against canonical Salt/Water steady cases"),
        ("TwoPhaseDataBase.xlsx", OFFICE_WORKBOOK_SOURCE_PROFILES["two_phase"], "two-phase office workbook kept as a separate noncanonical case family"),
    ]
    for filename, source_profile, notes in workbook_specs:
        path = office_dir / filename
        if not path.exists():
            continue
        parsed_rows, canonical_family_only = _normalize_office_workbook_sheet(path, source_profile=source_profile)
        repeated_case_rows = parsed_rows[parsed_rows["case_name"].astype(str).str.fullmatch(r"(Salt|Water)\s+\d+", case=False, na=False)].copy() if not parsed_rows.empty else pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
        if not parsed_rows.empty:
            workbook_rows.append(parsed_rows)
            if not repeated_case_rows.empty:
                repeated_rows.append(repeated_case_rows)
        index_rows.append(
            {
                "source_table": str(path),
                "source_profile": source_profile,
                "status": "parsed",
                "parsed_case_rows": int(len(parsed_rows)),
                "repeated_source_rows": int(len(repeated_case_rows)),
                "notes": notes,
            }
        )

    velocity_workbook = office_dir / "Full Velocity Profiles.xlsx"
    if velocity_workbook.exists():
        index_rows.append(
            {
                "source_table": str(velocity_workbook),
                "source_profile": "jadyn_office_velocity_workbook",
                "status": "indexed_only",
                "parsed_case_rows": 0,
                "repeated_source_rows": 0,
                "notes": "Velocity workbook kept in the raw-source catalog; it is not normalized into steady sensor rows.",
            }
        )

    return (
        pd.concat(workbook_rows, ignore_index=True) if workbook_rows else pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS),
        pd.concat(repeated_rows, ignore_index=True) if repeated_rows else pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS),
        pd.DataFrame(index_rows),
    )


def normalize_wide_validation_sources(source_tables: list[str | Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source_table in source_tables:
        path = Path(source_table)
        frame = pd.read_csv(path)
        frames.append(_normalize_wide_validation_frame(frame, path, source_profile="wide_validation_source"))
    if not frames:
        return pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    out = pd.concat(frames, ignore_index=True)
    for column in NORMALIZED_CASE_COLUMNS:
        if column not in out.columns:
            out[column] = pd.NA
    return out[NORMALIZED_CASE_COLUMNS].sort_values(["case_name", "source_table"]).reset_index(drop=True)


def build_validation_source_consistency_audit(
    normalized_cases: pd.DataFrame,
    *,
    canonical_source_profiles: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if normalized_cases.empty:
        return pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS), pd.DataFrame()

    canonical_rows: list[pd.Series] = []
    report_rows: list[dict[str, Any]] = []
    for case_name, group in normalized_cases.sort_values(["case_name", "source_table"]).groupby("case_name", dropna=False, sort=True):
        sorted_group = group.reset_index(drop=True)
        canonical = sorted_group.iloc[0]
        if canonical_source_profiles:
            preferred = sorted_group[sorted_group["source_profile"].isin(canonical_source_profiles)]
            if not preferred.empty:
                canonical = preferred.reset_index(drop=True).iloc[0]
        canonical_rows.append(canonical)
        repeated = len(sorted_group) > 1
        for idx, row in sorted_group.iterrows():
            mismatches: list[str] = []
            for column in CONSISTENCY_COMPARE_COLUMNS:
                if not _values_equal(canonical.get(column), row.get(column)):
                    mismatches.append(column)
            report_rows.append(
                {
                    "case_name": case_name,
                    "source_table": row.get("source_table"),
                    "source_profile": row.get("source_profile"),
                    "canonical_source_table": canonical.get("source_table"),
                    "canonical_source_profile": canonical.get("source_profile"),
                    "is_canonical_row": _values_equal(canonical.get("source_table"), row.get("source_table")) and _values_equal(canonical.get("source_profile"), row.get("source_profile")),
                    "repeated_source_case": repeated,
                    "status": "mismatch" if mismatches else ("match" if repeated else "single_source"),
                    "mismatch_field_count": len(mismatches),
                    "mismatch_fields": ";".join(mismatches),
                }
            )

    canonical_df = pd.DataFrame(canonical_rows)
    if canonical_df.empty:
        canonical_df = pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    else:
        for column in NORMALIZED_CASE_COLUMNS:
            if column not in canonical_df.columns:
                canonical_df[column] = pd.NA
        canonical_df = canonical_df[NORMALIZED_CASE_COLUMNS].sort_values("case_name").reset_index(drop=True)
    report_df = pd.DataFrame(report_rows).sort_values(["case_name", "source_table"]).reset_index(drop=True) if report_rows else pd.DataFrame()
    return canonical_df, report_df


def _render_consistency_summary(report_df: pd.DataFrame) -> str:
    if report_df.empty:
        return "# Validation Source Consistency Summary\n\nNo normalized validation rows were available.\n"

    repeated = report_df[report_df["repeated_source_case"] == True]
    mismatches = report_df[report_df["status"] == "mismatch"]
    lines = [
        "# Validation Source Consistency Summary",
        "",
        f"- Case rows audited: {len(report_df)}",
        f"- Repeated-source rows: {len(repeated)}",
        f"- Mismatch rows: {len(mismatches)}",
        "",
    ]
    if mismatches.empty:
        lines.append("All repeated Salt/Water case rows matched exactly after normalization.")
        lines.append("")
    else:
        lines.extend(["## Mismatches", ""])
        for case_name, group in mismatches.groupby("case_name", dropna=False, sort=True):
            fields = sorted({field for value in group["mismatch_fields"].fillna("") for field in str(value).split(";") if field})
            lines.append(f"- `{case_name}`: {', '.join(fields)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _collect_validation_source_rows(
    source_tables: list[str | Path],
    *,
    inventory_root: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    wide_rows = normalize_wide_validation_sources(source_tables) if source_tables else pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    workbook_rows = pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    repeated_workbook_rows = pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)
    workbook_index = pd.DataFrame(columns=["source_table", "source_profile", "status", "parsed_case_rows", "repeated_source_rows", "notes"])
    if inventory_root:
        workbook_rows, repeated_workbook_rows, workbook_index = normalize_office_workbook_sources(inventory_root)

    frames = [frame for frame in (wide_rows, repeated_workbook_rows) if not frame.empty]
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=NORMALIZED_CASE_COLUMNS)

    index_rows: list[dict[str, Any]] = []
    for source_table in source_tables:
        path = Path(source_table)
        parsed_rows = int((wide_rows["source_table"] == str(path)).sum()) if not wide_rows.empty else 0
        index_rows.append(
            {
                "source_table": str(path),
                "source_profile": "wide_validation_source",
                "status": "parsed",
                "parsed_case_rows": parsed_rows,
                "repeated_source_rows": parsed_rows,
                "notes": "Canonical wide validation source table.",
            }
        )
    if not workbook_index.empty:
        index_rows.extend(workbook_index.to_dict(orient="records"))
    source_index = pd.DataFrame(index_rows)
    return combined, source_index, workbook_rows


def _build_office_workbook_promotion_decisions(
    workbook_rows: pd.DataFrame,
    consistency_report: pd.DataFrame,
) -> pd.DataFrame:
    if workbook_rows.empty:
        return pd.DataFrame(
            columns=[
                "case_name",
                "source_table",
                "source_profile",
                "promotion_status",
                "consistency_status",
                "mismatch_field_count",
                "mismatch_fields",
                "notes",
            ]
        )

    report_lookup = {
        (str(row["case_name"]), str(row["source_table"]), str(row["source_profile"])): row
        for _, row in consistency_report.iterrows()
    } if not consistency_report.empty else {}
    decisions: list[dict[str, Any]] = []
    for _, row in workbook_rows.sort_values(["source_profile", "case_name", "source_table"]).iterrows():
        key = (str(row["case_name"]), str(row["source_table"]), str(row["source_profile"]))
        report_row = report_lookup.get(key)
        source_profile = str(row["source_profile"])
        if source_profile == OFFICE_WORKBOOK_SOURCE_PROFILES["single_phase"]:
            consistency_status = str(report_row["status"]) if report_row is not None else "not_audited"
            mismatch_count = int(report_row["mismatch_field_count"]) if report_row is not None else 0
            mismatch_fields = str(report_row["mismatch_fields"]) if report_row is not None else ""
            promotion_status = "duplicate_consistent" if consistency_status == "match" else "blocked_by_mismatch"
            notes = (
                "Exact-match clean against canonical wide tables."
                if promotion_status == "duplicate_consistent"
                else "Workbook values differ from the canonical wide tables; keep blocked until the discrepancy is resolved."
            )
        else:
            consistency_status = "noncanonical_case_family"
            mismatch_count = 0
            mismatch_fields = ""
            promotion_status = "noncanonical_case_family"
            notes = "Parsed office workbook row is not part of the maintained Salt 1-4 / Water 1-4 repeated-source contract."
        decisions.append(
            {
                "case_name": row["case_name"],
                "source_table": row["source_table"],
                "source_profile": source_profile,
                "promotion_status": promotion_status,
                "consistency_status": consistency_status,
                "mismatch_field_count": mismatch_count,
                "mismatch_fields": mismatch_fields,
                "notes": notes,
            }
        )
    return pd.DataFrame(decisions)


def _is_example_like(path_text: str) -> bool:
    return "example" in path_text.lower()


def _manual_validation_case_override(case_dir: Any) -> tuple[str, str]:
    key = str(case_dir or "").strip().replace("\\", "/")
    case_name, basis = MANUAL_VALIDATION_CASE_OVERRIDES.get(key, ("", ""))
    return case_name, basis


def _split_path_list(value: Any) -> list[str]:
    return [item for item in _split_items(value) if item]


def _primary_velocity_source(row: pd.Series) -> str | None:
    for key in ("u_csv", "v_csv", "x_csv", "y_csv"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _velocity_bundle_paths(row: pd.Series) -> list[str]:
    bundle = []
    for key in ("x_csv", "y_csv", "u_csv", "v_csv"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            bundle.append(value)
    return bundle


def _classify_run_log(path: Path) -> tuple[str, str, str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    steady_mentions = len(re.findall(r"steady state", text, flags=re.IGNORECASE))
    transient_mentions = len(re.findall(r"transient", text, flags=re.IGNORECASE))
    nc_mentions = len(re.findall(r"\bNC\d+\b", text))
    note = (
        f"Run log with {steady_mentions} steady-state mentions, "
        f"{transient_mentions} transient mentions, and {nc_mentions} NC case labels. "
        "Useful for provenance and case mapping, but not a direct sensor-value table."
    )
    return (
        "unknown_or_not_yet_interpretable",
        "run_log_or_description_file",
        "direct_from_description_file",
        note,
    )


def _classify_top_level_file(path: Path) -> tuple[str, str, str, str, str, str]:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == ".xlsx" and "singlephase" in name and "database" in name:
        return (
            "steady_sensor_candidates",
            "steady_state_summary_workbook",
            "case-level steady measurements and operating conditions",
            "mixed tabular workbook units; parse workbook columns before adoption",
            "inferred_from_filename_and_structure",
            "Workbook name indicates a single-phase case database; likely usable as a steady-state validation summary source after column-level parsing.",
        )
    if suffix == ".xlsx" and "twophase" in name and "database" in name:
        return (
            "steady_sensor_candidates",
            "two_phase_summary_workbook",
            "case-level summary measurements; exact channels require workbook parsing",
            "mixed tabular workbook units; parse workbook columns before adoption",
            "inferred_from_filename_and_structure",
            "Workbook name indicates a two-phase case database; likely a repeated summary source, but exact validation fields still need workbook parsing.",
        )
    if suffix == ".xlsx" and "velocity" in name:
        return (
            "steady_velocity_profile_candidates",
            "compiled_velocity_profile_workbook",
            "compiled velocity-profile columns",
            "expected position/velocity columns; verify sheet schema before adoption",
            "inferred_from_filename_and_structure",
            "Workbook name indicates curated velocity profiles; treat as a compiled steady-profile source pending workbook parsing.",
        )
    if suffix == ".mat" and "fiberopticworkspace" in name:
        return (
            "transient_sensor_candidates",
            "fiber_optic_transient_axial_temperatures",
            "time, axial hot-leg temperatures, TP2, TP3",
            "seconds/minutes/hours and degC",
            "inferred_from_filename_and_structure",
            "Filename matches FiberOpticWorkspace and the repository description file documents time-indexed axial fiber temperatures.",
        )
    if suffix == ".mat" and "transientworkspace" in name:
        return (
            "transient_sensor_candidates",
            "transient_thermocouple_workspace",
            "time, Tc, TW, T_HXin, T_HXout, dT, T_lm",
            "time and degC",
            "inferred_from_filename_and_structure",
            "Filename matches TransientWorkspace and the repository description file documents time-series thermocouple and heat-exchanger channels.",
        )
    if suffix == ".txt":
        bucket, family, confidence, note = _classify_run_log(path)
        return (bucket, family, "case labels, operating notes, procedural notes", "text narrative", confidence, note)
    if suffix == ".zip":
        return (
            "unknown_or_not_yet_interpretable",
            "compressed_raw_bundle",
            "unknown until unpacked",
            "archive",
            "unclear_manual_review_needed",
            "ZIP archive present in the raw mirror. It may duplicate extracted data or contain additional raw content, but it is not directly cataloged as an adoptable validation source.",
        )
    if suffix in {".docx", ".m"}:
        return (
            "unknown_or_not_yet_interpretable",
            "supporting_reference_or_script",
            "supporting context only",
            "document or script",
            "unclear_manual_review_needed",
            "Supporting document/script kept for provenance and interpretation, not direct validation adoption.",
        )
    return (
        "unknown_or_not_yet_interpretable",
        "unclassified_file",
        "unknown",
        suffix.lstrip(".") or "file",
        "unclear_manual_review_needed",
        "File does not match a maintained first-pass validation classification rule.",
    )


def _make_inventory_candidates(case_inventory: pd.DataFrame) -> pd.DataFrame:
    if case_inventory.empty:
        return pd.DataFrame()
    keep = [
        "case_dir",
        "top_level_folder",
        "case_folder_name",
        "metadata_path",
        "metadata_parse_status",
        "candidate_heater_power_W",
        "candidate_air_flow_Lpm",
        "candidate_test_section_power_W",
        "metadata_temperature_hot_1_C",
        "metadata_temperature_hot_2_C",
        "metadata_temperature_cold_1_2_C",
        "ready_for_validation_export",
        "review_status",
    ]
    existing = [column for column in keep if column in case_inventory.columns]
    candidates = case_inventory[existing].copy()
    example_mask = (
        candidates.get("top_level_folder", pd.Series("", index=candidates.index)).astype(str).str.contains("example", case=False, na=False)
        | candidates.get("case_dir", pd.Series("", index=candidates.index)).astype(str).str.contains("example", case=False, na=False)
    )
    comparable_cols = [
        "candidate_heater_power_W",
        "candidate_air_flow_Lpm",
        "candidate_test_section_power_W",
        "metadata_temperature_hot_1_C",
        "metadata_temperature_hot_2_C",
        "metadata_temperature_cold_1_2_C",
    ]
    has_matching_metadata = pd.Series(False, index=candidates.index)
    for column in comparable_cols:
        if column in candidates.columns:
            has_matching_metadata |= pd.to_numeric(candidates[column], errors="coerce").notna()
    if "metadata_path" in candidates.columns:
        has_matching_metadata |= candidates["metadata_path"].fillna("").astype(str).str.strip().ne("")
    candidates = candidates.loc[~example_mask & has_matching_metadata].copy()
    candidates.insert(0, "candidate_case_name", candidates["case_dir"].astype(str).str.replace("/", "__", regex=False))
    recognized = candidates["case_dir"].apply(_manual_validation_case_override)
    candidates.insert(1, "recognized_case_name", recognized.map(lambda item: item[0]))
    candidates.insert(2, "recognition_basis", recognized.map(lambda item: item[1]))
    return candidates


def _percent_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) / scale


def build_nearest_fit_table(case_inventory: pd.DataFrame, normalized_cases: pd.DataFrame, *, top_n: int = 5) -> pd.DataFrame:
    if case_inventory.empty or normalized_cases.empty:
        return pd.DataFrame()
    candidates = _make_inventory_candidates(case_inventory)
    rows: list[dict[str, Any]] = []
    for _, target in normalized_cases.iterrows():
        target_case_name = _canonicalize_case_name(str(target["case_name"]))
        exact_matches = candidates[
            candidates.get("recognized_case_name", pd.Series("", index=candidates.index)).astype(str) == target_case_name
        ].copy()
        if not exact_matches.empty:
            for _, candidate in exact_matches.sort_values("candidate_case_name").iterrows():
                rows.append(
                    {
                        "target_case_name": target_case_name,
                        "candidate_case_name": candidate["candidate_case_name"],
                        "recognized_case_name": candidate.get("recognized_case_name", ""),
                        "recognition_basis": candidate.get("recognition_basis", ""),
                        "candidate_case_dir": candidate["case_dir"],
                        "candidate_top_level_folder": candidate["top_level_folder"],
                        "distance_score": 0.0,
                        "compared_fields": "manual_case_map",
                        "review_status": "known_case_subfolder",
                    }
                )
            continue
        scored: list[dict[str, Any]] = []
        for _, candidate in candidates.iterrows():
            deltas = {
                "heater_power_W": _percent_delta(_to_float(target.get("heater_power_W")), _to_float(candidate.get("candidate_heater_power_W"))),
                "air_flow_Lpm": _percent_delta(_to_float(target.get("air_flow_Lpm")), _to_float(candidate.get("candidate_air_flow_Lpm"))),
                "test_section_power_W": _percent_delta(_to_float(target.get("heat_removed_W")), _to_float(candidate.get("candidate_test_section_power_W"))),
            }
            usable = [value for value in deltas.values() if value is not None]
            if not usable:
                continue
            scored.append(
                {
                    "target_case_name": target_case_name,
                    "candidate_case_name": candidate["candidate_case_name"],
                    "recognized_case_name": candidate.get("recognized_case_name", ""),
                    "recognition_basis": candidate.get("recognition_basis", ""),
                    "candidate_case_dir": candidate["case_dir"],
                    "candidate_top_level_folder": candidate["top_level_folder"],
                    "distance_score": round(sum(usable) / len(usable), 6),
                    "compared_fields": ",".join(key for key, value in deltas.items() if value is not None),
                    "review_status": "advisory_only",
                }
            )
        scored = sorted(scored, key=lambda item: item["distance_score"])
        rows.extend(scored[:top_n])
    return pd.DataFrame(rows).sort_values(["target_case_name", "distance_score"]).reset_index(drop=True) if rows else pd.DataFrame()


def _build_policy_yaml(normalized_cases: pd.DataFrame) -> str:
    fluids = sorted(str(value) for value in normalized_cases["fluid"].dropna().unique()) if not normalized_cases.empty else []
    lines = [
        "policy_name: tamu_validation_export_default",
        "source_profile: wide_validation_source",
        "active_solver_inputs:",
        "  - heater_power_W",
        "  - air_T_inlet_C",
        "  - air_flow_Lpm",
        "validation_only_channels:",
        "  - TP1",
        "  - TP2",
        "  - TP3",
        "  - TP4",
        "  - TP5",
        "  - TP6",
        "  - TW1",
        "  - TW2",
        "  - TW3",
        "  - TW4",
        "  - TW5",
        "  - TW6",
        "  - TW7",
        "  - TW8",
        "  - TW9",
        "  - TW10",
        "  - TW11",
        "  - measured_mass_flow_rate_kg_s",
        "  - measured_area_weighted_mean_velocity_m_s",
        "fluids_seen:",
    ]
    if fluids:
        lines.extend([f"  - {fluid}" for fluid in fluids])
    else:
        lines.append("  - none")
    lines.extend(
        [
            "matching_policy:",
            "  mode: metadata_rules_with_advisory_nearest_fit",
            "  auto_accept_matches: false",
        ]
    )
    return "\n".join(lines) + "\n"


def build_physor_wide_table(normalized_cases: pd.DataFrame) -> pd.DataFrame:
    if normalized_cases.empty:
        return pd.DataFrame()
    cases = normalized_cases.sort_values("case_name").reset_index(drop=True)
    columns = ["Kelvin", *cases["case_name"].tolist()]

    def case_values(column: str, *, offset: float = 0.0, transform: Any | None = None) -> list[Any]:
        values: list[Any] = []
        for _, row in cases.iterrows():
            value = _to_float(row.get(column))
            if value is None and transform is None:
                values.append("")
                continue
            if transform is not None:
                value = transform(row)
                if value is None:
                    values.append("")
                    continue
            else:
                value += offset
            values.append(round(float(value), 5))
        return values

    def derived_average_temp(row: pd.Series) -> float | None:
        temps = [_to_float(row.get(f"TP{i}_C")) for i in range(1, 7)]
        keep = [value for value in temps if value is not None]
        return (sum(keep) / len(keep) + 273.15) if keep else None

    def derived_max_temp_diff(row: pd.Series) -> float | None:
        temps = [_to_float(row.get(f"TP{i}_C")) for i in range(1, 7)]
        keep = [value for value in temps if value is not None]
        return max(keep) - min(keep) if keep else None

    rows = [
        ["TP1", *case_values("TP1_C", offset=273.15)],
        ["TP2", *case_values("TP2_C", offset=273.15)],
        ["TP3", *case_values("TP3_C", offset=273.15)],
        ["TP4", *case_values("TP4_C", offset=273.15)],
        ["TP5", *case_values("TP5_C", offset=273.15)],
        ["TP6", *case_values("TP6_C", offset=273.15)],
        ["TW1", *case_values("TW1_C", offset=273.15)],
        ["TW2", *case_values("TW2_C", offset=273.15)],
        ["TW3", *case_values("TW3_C", offset=273.15)],
        ["TW4", *case_values("TW4_C", offset=273.15)],
        ["TW5", *case_values("TW5_C", offset=273.15)],
        ["TW6", *case_values("TW6_C", offset=273.15)],
        ["TW7", *case_values("TW7_C", offset=273.15)],
        ["TW8", *case_values("TW8_C", offset=273.15)],
        ["TW9", *case_values("TW9_C", offset=273.15)],
        ["TW10 (on shell of HX)", *case_values("TW10_C", offset=273.15)],
        ["TW11", *case_values("TW11_C", offset=273.15)],
        ["", *([""] * len(cases))],
        ["Heater Power (W)", *case_values("heater_power_W", offset=0.0)],
        ["Heat Removed (W)", *case_values("heat_removed_W", offset=0.0)],
        ["", *([""] * len(cases))],
        ["TS_vel", *([""] * len(cases))],
        ["massFlowRate", *case_values("measured_mass_flow_rate_kg_s", offset=0.0)],
        ["", *([""] * len(cases))],
        ["Q'' Heat (W/m^2)", *([""] * len(cases))],
        ["", *([""] * len(cases))],
        ["Average Velocity Air (m/s)", *case_values("measured_area_weighted_mean_velocity_m_s", offset=0.0)],
        ["", *([""] * len(cases))],
        ["Average temp", *case_values("TP1_C", transform=derived_average_temp)],
        ["Pr associated", *([""] * len(cases))],
        ["", *([""] * len(cases))],
        ["Max Temp Diff", *case_values("TP1_C", transform=derived_max_temp_diff)],
    ]
    return pd.DataFrame(rows, columns=columns)


def _catalog_case_rows(root_path: Path, case_inventory: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if case_inventory.empty:
        return rows
    for _, case in case_inventory.iterrows():
        case_dir = str(case.get("case_dir", ""))
        if not case_dir or _is_example_like(case_dir):
            continue
        metadata_status = str(case.get("metadata_parse_status", "") or "")
        metadata_exists = bool(case.get("has_meta_data_json", False))
        metadata_repaired = metadata_status == "repaired"
        recognized_case_name, recognition_basis = _manual_validation_case_override(case_dir)
        primary_velocity = _primary_velocity_source(case)
        bundle_paths = _velocity_bundle_paths(case)
        if primary_velocity and len(bundle_paths) == 4:
            rows.append(
                {
                    "candidate_bucket": "steady_velocity_profile_candidates",
                    "candidate_case_name": case_dir.replace("/", "__"),
                    "recognized_case_name": recognized_case_name,
                    "recognition_basis": recognition_basis,
                    "top_level_folder": case.get("top_level_folder"),
                    "case_dir": case_dir,
                    "source_file_path": str(root_path / primary_velocity),
                    "source_bundle_paths": ";".join(str(root_path / rel) for rel in bundle_paths),
                    "measurement_family": "piv_velocity_field_bundle",
                    "usable_channels": "X, Y, U, V",
                    "inferred_units": "meters and m/s",
                    "metadata_exists": metadata_exists,
                    "metadata_repaired": metadata_repaired,
                    "confidence": "direct_from_description_file",
                    "provenance_notes": "Velocity_Files_Description.txt documents X/Y/U/V CSV bundles as a single velocity field intended for magnitude and vector plotting.",
                    "plot_expected": True,
                }
            )
        case_path = root_path / case_dir
        for file_path in sorted(path for path in case_path.iterdir() if path.is_file()):
            name = file_path.name.lower()
            if name == "meta_data.json" or file_path.suffix.lower() == ".csv":
                continue
            if "transientworkspace" in name:
                rows.append(
                    {
                        "candidate_bucket": "transient_sensor_candidates",
                        "candidate_case_name": case_dir.replace("/", "__"),
                        "top_level_folder": case.get("top_level_folder"),
                        "case_dir": case_dir,
                        "source_file_path": str(file_path),
                        "source_bundle_paths": "",
                        "measurement_family": "transient_thermocouple_workspace",
                        "usable_channels": "time, Tc, TW, T_HXin, T_HXout, dT, T_lm",
                        "inferred_units": "time and degC",
                        "metadata_exists": metadata_exists,
                        "metadata_repaired": metadata_repaired,
                        "confidence": "direct_from_description_file",
                        "provenance_notes": "MATLAB_Files_Description.txt documents transient thermocouple workspaces with time-indexed thermal channels.",
                        "plot_expected": False,
                    }
                )
            elif "fiberopticworkspace" in name:
                rows.append(
                    {
                        "candidate_bucket": "transient_sensor_candidates",
                        "candidate_case_name": case_dir.replace("/", "__"),
                        "top_level_folder": case.get("top_level_folder"),
                        "case_dir": case_dir,
                        "source_file_path": str(file_path),
                        "source_bundle_paths": "",
                        "measurement_family": "fiber_optic_transient_axial_temperatures",
                        "usable_channels": "second, minutes, hours, T_Hot, TP2, TP3, X_hot, HotTest",
                        "inferred_units": "time, axial position, and degC",
                        "metadata_exists": metadata_exists,
                        "metadata_repaired": metadata_repaired,
                        "confidence": "direct_from_description_file",
                        "provenance_notes": "FiberOptic_File_Description.txt documents time-resolved axial fiber temperatures and associated thermocouple channels.",
                        "plot_expected": False,
                    }
                )
            elif file_path.suffix.lower() == ".mat":
                rows.append(
                    {
                        "candidate_bucket": "unknown_or_not_yet_interpretable",
                        "candidate_case_name": case_dir.replace("/", "__"),
                        "top_level_folder": case.get("top_level_folder"),
                        "case_dir": case_dir,
                        "source_file_path": str(file_path),
                        "source_bundle_paths": "",
                        "measurement_family": "unclassified_mat_workspace",
                        "usable_channels": "unknown until parsed",
                        "inferred_units": "unknown",
                        "metadata_exists": metadata_exists,
                        "metadata_repaired": metadata_repaired,
                        "confidence": "unclear_manual_review_needed",
                        "provenance_notes": "MAT workspace is present in a case folder but does not match a maintained first-pass filename rule.",
                        "plot_expected": False,
                    }
                )
    return rows


def _catalog_non_case_files(root_path: Path, case_inventory: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case_dirs = {
        str((root_path / str(case_dir)).resolve())
        for case_dir in case_inventory.get("case_dir", pd.Series(dtype=str)).dropna().astype(str)
    } if not case_inventory.empty else set()
    for file_path in sorted(path for path in root_path.rglob("*") if path.is_file()):
        parent_resolved = str(file_path.parent.resolve())
        if parent_resolved in case_dirs:
            continue
        rel = _rel(file_path, root_path)
        if _is_example_like(rel):
            continue
        bucket, family, channels, units, confidence, note = _classify_top_level_file(file_path)
        rows.append(
            {
                "candidate_bucket": bucket,
                "candidate_case_name": file_path.stem,
                "recognized_case_name": "",
                "recognition_basis": "",
                "top_level_folder": file_path.relative_to(root_path).parts[0],
                "case_dir": "",
                "source_file_path": str(file_path),
                "source_bundle_paths": "",
                "measurement_family": family,
                "usable_channels": channels,
                "inferred_units": units,
                "metadata_exists": False,
                "metadata_repaired": False,
                "confidence": confidence,
                "provenance_notes": note,
                "plot_expected": False,
            }
        )
    return rows


def _build_validation_catalog(root_path: Path, case_inventory: pd.DataFrame) -> pd.DataFrame:
    rows = [*_catalog_case_rows(root_path, case_inventory), *_catalog_non_case_files(root_path, case_inventory)]
    if not rows:
        columns = [
            "candidate_bucket",
            "candidate_case_name",
            "recognized_case_name",
            "recognition_basis",
            "top_level_folder",
            "case_dir",
            "source_file_path",
            "source_bundle_paths",
            "measurement_family",
            "usable_channels",
            "inferred_units",
            "metadata_exists",
            "metadata_repaired",
            "confidence",
            "provenance_notes",
            "plot_expected",
        ]
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows).sort_values(["candidate_bucket", "top_level_folder", "candidate_case_name", "source_file_path"]).reset_index(drop=True)


def _write_velocity_profile_outputs(catalog: pd.DataFrame, outdir: Path) -> pd.DataFrame:
    if catalog.empty:
        return pd.DataFrame()
    plot_rows: list[dict[str, Any]] = []
    velocity_rows = catalog[
        (catalog["candidate_bucket"] == "steady_velocity_profile_candidates")
        & (catalog.get("plot_expected", pd.Series(False, index=catalog.index)).fillna(False))
    ].copy()
    if velocity_rows.empty:
        return pd.DataFrame()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plots_root = outdir / "velocity_profile_plots"
    plots_root.mkdir(parents=True, exist_ok=True)
    for _, row in velocity_rows.iterrows():
        bundle = _split_path_list(row.get("source_bundle_paths"))
        if len(bundle) != 4:
            plot_rows.append(
                {
                    "candidate_case_name": row["candidate_case_name"],
                    "recognized_case_name": recognized_case_name,
                    "status": "skipped_missing_bundle",
                    "plot_root": "",
                    "flattened_csv": "",
                    "contour_png": "",
                    "quiver_png": "",
                    "provenance_md": "",
                }
            )
            continue
        bundle_map = {}
        for item in bundle:
            lower = Path(item).name.lower()
            if lower.endswith("_x.csv") or lower == "x.csv":
                bundle_map["x"] = Path(item)
            elif lower.endswith("_y.csv") or lower == "y.csv":
                bundle_map["y"] = Path(item)
            elif lower.endswith("_u.csv") or lower == "u.csv":
                bundle_map["u"] = Path(item)
            elif lower.endswith("_v.csv") or lower == "v.csv":
                bundle_map["v"] = Path(item)
        if set(bundle_map) != {"x", "y", "u", "v"}:
            plot_rows.append(
                {
                    "candidate_case_name": row["candidate_case_name"],
                    "recognized_case_name": recognized_case_name,
                    "status": "skipped_unresolved_bundle",
                    "plot_root": "",
                    "flattened_csv": "",
                    "contour_png": "",
                    "quiver_png": "",
                    "provenance_md": "",
                }
            )
            continue
        x = pd.read_csv(bundle_map["x"], header=None).to_numpy(dtype=float)
        y = pd.read_csv(bundle_map["y"], header=None).to_numpy(dtype=float)
        u = pd.read_csv(bundle_map["u"], header=None).to_numpy(dtype=float)
        v = pd.read_csv(bundle_map["v"], header=None).to_numpy(dtype=float)
        min_rows = min(x.shape[0], y.shape[0], u.shape[0], v.shape[0])
        min_cols = min(x.shape[1], y.shape[1], u.shape[1], v.shape[1])
        if min_rows == 0 or min_cols == 0:
            plot_rows.append(
                {
                    "candidate_case_name": row["candidate_case_name"],
                    "recognized_case_name": recognized_case_name,
                    "status": "skipped_empty_bundle",
                    "plot_root": "",
                    "flattened_csv": "",
                    "contour_png": "",
                    "quiver_png": "",
                    "provenance_md": "",
                }
            )
            continue
        cropped = any(array.shape != (min_rows, min_cols) for array in (x, y, u, v))
        x = x[:min_rows, :min_cols]
        y = y[:min_rows, :min_cols]
        u = u[:min_rows, :min_cols]
        v = v[:min_rows, :min_cols]
        mag = np.sqrt(u ** 2 + v ** 2)
        recognized_case_name = str(row.get("recognized_case_name") or "").strip()
        plot_label = recognized_case_name or str(row["candidate_case_name"])
        if recognized_case_name:
            plot_label = f"{recognized_case_name} ({row['candidate_case_name']})"

        case_root = plots_root / str(row["candidate_case_name"])
        case_root.mkdir(parents=True, exist_ok=True)
        flattened_csv = case_root / "flattened_velocity_field.csv"
        contour_png = case_root / "velocity_magnitude_contour.png"
        quiver_png = case_root / "velocity_quiver.png"
        provenance_md = case_root / "PLOT_PROVENANCE.md"

        flat = pd.DataFrame(
            {
                "x_m": x.reshape(-1),
                "y_m": y.reshape(-1),
                "u_m_s": u.reshape(-1),
                "v_m_s": v.reshape(-1),
                "mag_m_s": mag.reshape(-1),
            }
        )
        flat.to_csv(flattened_csv, index=False)

        contour_fig, contour_ax = plt.subplots(figsize=(7, 5))
        contour = contour_ax.pcolormesh(x, y, mag, shading="auto")
        contour_ax.set_xlabel("x [m]")
        contour_ax.set_ylabel("y [m]")
        contour_ax.set_title(f"{plot_label} velocity magnitude")
        contour_fig.colorbar(contour, ax=contour_ax, label="|V| [m/s]")
        contour_fig.tight_layout()
        contour_fig.savefig(contour_png, dpi=180)
        plt.close(contour_fig)

        stride_r = max(1, x.shape[0] // 25)
        stride_c = max(1, x.shape[1] // 25)
        quiver_fig, quiver_ax = plt.subplots(figsize=(7, 5))
        quiver_ax.quiver(
            x[::stride_r, ::stride_c],
            y[::stride_r, ::stride_c],
            u[::stride_r, ::stride_c],
            v[::stride_r, ::stride_c],
            mag[::stride_r, ::stride_c],
            cmap="viridis",
        )
        quiver_ax.set_xlabel("x [m]")
        quiver_ax.set_ylabel("y [m]")
        quiver_ax.set_title(f"{plot_label} velocity vectors")
        quiver_fig.tight_layout()
        quiver_fig.savefig(quiver_png, dpi=180)
        plt.close(quiver_fig)

        provenance_lines = [
            "# Velocity Plot Provenance",
            "",
            f"- Candidate case: `{row['candidate_case_name']}`",
            f"- Recognized case name: `{recognized_case_name}`" if recognized_case_name else "- Recognized case name: none",
            f"- Primary source file: `{row['source_file_path']}`",
            "- Bundle source files:",
            *(f"  - `{item}`" for item in bundle),
            f"- Flattened plotting data: `{flattened_csv}`",
            f"- Contour plot: `{contour_png}`",
            f"- Quiver plot: `{quiver_png}`",
            "- Units: X/Y in meters, U/V in m/s, magnitude in m/s.",
            f"- Quiver subsampling rule: every {stride_r} rows and {stride_c} columns.",
            f"- Grid harmonization: {'cropped all arrays to the common overlapping shape before plotting.' if cropped else 'no cropping required; all arrays matched natively.'}",
            "- Interpretation basis: `Velocity_Files_Description.txt` documents X/Y/U/V bundles as a single velocity field for plotting.",
            "- Assumption: treat this bundle as a steady representative velocity field unless a stronger transient interpretation is documented elsewhere.",
        ]
        provenance_md.write_text("\n".join(provenance_lines) + "\n", encoding="utf-8")

        plot_rows.append(
            {
                "candidate_case_name": row["candidate_case_name"],
                "recognized_case_name": recognized_case_name,
                "status": "plotted",
                "plot_root": str(case_root),
                "flattened_csv": str(flattened_csv),
                "contour_png": str(contour_png),
                "quiver_png": str(quiver_png),
                "provenance_md": str(provenance_md),
            }
        )
    return pd.DataFrame(plot_rows).sort_values("candidate_case_name").reset_index(drop=True)


def _render_validation_catalog_summary(catalog: pd.DataFrame, plot_index: pd.DataFrame, consistency_report: pd.DataFrame) -> str:
    counts = catalog["candidate_bucket"].value_counts() if not catalog.empty else pd.Series(dtype=int)
    mismatches = consistency_report[consistency_report["status"] == "mismatch"] if not consistency_report.empty else pd.DataFrame()
    lines = [
        "# TAMU Validation Catalog Summary",
        "",
        "## Candidate buckets",
        "",
    ]
    for bucket in CATALOG_BUCKETS:
        lines.append(f"- {bucket}: {int(counts.get(bucket, 0))}")
    lines.extend(
        [
            "",
            "## Plot generation",
            "",
            f"- Velocity plot rows: {len(plot_index)}",
            f"- Successful velocity plot bundles: {int((plot_index.get('status', pd.Series(dtype=str)) == 'plotted').sum()) if not plot_index.empty else 0}",
            "",
            "## Validation source consistency",
            "",
            f"- Repeated-source mismatch rows: {len(mismatches)}",
        ]
    )
    return "\n".join(lines) + "\n"


def export_tamu_validation_artifacts(
    outdir: str | Path,
    *,
    inventory_root: str | Path | None = None,
    inventory_csv: str | Path | None = None,
    source_tables: list[str | Path] | None = None,
    export_profiles: list[str] | None = None,
    config_path: str | Path | None = None,
) -> TamuValidationExportResult:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    export_profiles = export_profiles or ["fluid_normalized", "physor_wide"]
    source_tables = source_tables or []

    inventory_result: TamuInventoryResult | None = None
    if inventory_csv:
        case_inventory = pd.read_csv(inventory_csv)
    elif inventory_root:
        inventory_result = build_tamu_inventory(inventory_root, out / "inventory", config_path=config_path)
        case_inventory = pd.read_csv(inventory_result.case_inventory_csv)
    else:
        case_inventory = pd.DataFrame()

    inventory_candidates = _make_inventory_candidates(case_inventory)
    inventory_candidates_csv = out / "inventory_validation_candidates.csv" if not inventory_candidates.empty else None
    if inventory_candidates_csv is not None:
        inventory_candidates.to_csv(inventory_candidates_csv, index=False)

    normalized_cases_raw, source_index, office_workbook_rows = _collect_validation_source_rows(
        source_tables,
        inventory_root=inventory_root,
    )
    normalized_cases, consistency_report = build_validation_source_consistency_audit(
        normalized_cases_raw,
        canonical_source_profiles=CANONICAL_SOURCE_PROFILES,
    )
    normalized_cases_csv = out / "validation_cases.csv" if "fluid_normalized" in export_profiles and not normalized_cases.empty else None
    if normalized_cases_csv is not None:
        normalized_cases.to_csv(normalized_cases_csv, index=False)

    source_index_csv = out / "validation_source_index.csv" if not source_index.empty else None
    if source_index_csv is not None:
        source_index.to_csv(source_index_csv, index=False)

    office_workbook_rows_csv = out / "office_workbook_case_rows.csv" if not office_workbook_rows.empty else None
    if office_workbook_rows_csv is not None:
        office_workbook_rows.to_csv(office_workbook_rows_csv, index=False)

    office_workbook_promotion = _build_office_workbook_promotion_decisions(office_workbook_rows, consistency_report)
    office_workbook_promotion_csv = out / "office_workbook_promotion_decisions.csv" if not office_workbook_promotion.empty else None
    if office_workbook_promotion_csv is not None:
        office_workbook_promotion.to_csv(office_workbook_promotion_csv, index=False)

    policy_yaml = out / "validation_policy.yaml" if normalized_cases_csv is not None else None
    if policy_yaml is not None:
        policy_yaml.write_text(_build_policy_yaml(normalized_cases), encoding="utf-8")

    physor_wide_csv = out / "validation_data.csv" if "physor_wide" in export_profiles and not normalized_cases.empty else None
    if physor_wide_csv is not None:
        build_physor_wide_table(normalized_cases).to_csv(physor_wide_csv, index=False)

    nearest_fit = build_nearest_fit_table(case_inventory, normalized_cases)
    nearest_fit_csv = out / "nearest_fit_suggestions.csv" if not nearest_fit.empty else None
    if nearest_fit_csv is not None:
        nearest_fit.to_csv(nearest_fit_csv, index=False)

    consistency_report_csv = out / "validation_source_consistency_report.csv" if not consistency_report.empty else None
    if consistency_report_csv is not None:
        consistency_report.to_csv(consistency_report_csv, index=False)
    discrepancies_only = consistency_report[consistency_report["status"] == "mismatch"].copy() if not consistency_report.empty else pd.DataFrame()
    discrepancies_only_csv = out / "validation_source_discrepancies_only.csv" if not discrepancies_only.empty else None
    if discrepancies_only_csv is not None:
        discrepancies_only.to_csv(discrepancies_only_csv, index=False)
    consistency_summary_md = out / "validation_source_consistency_summary.md" if consistency_report_csv is not None else None
    if consistency_summary_md is not None:
        consistency_summary_md.write_text(_render_consistency_summary(consistency_report), encoding="utf-8")

    summary = {
        "outdir": str(out),
        "inventory_root": str(inventory_root) if inventory_root else None,
        "inventory_csv": str(inventory_csv) if inventory_csv else None,
        "source_tables": [str(Path(path)) for path in source_tables],
        "profiles": export_profiles,
        "n_inventory_candidates": int(len(inventory_candidates)),
        "n_normalized_cases": int(len(normalized_cases)),
        "n_nearest_fit_rows": int(len(nearest_fit)),
        "n_consistency_rows": int(len(consistency_report)),
        "n_consistency_mismatches": int(len(discrepancies_only)),
        "n_office_workbook_rows": int(len(office_workbook_rows)),
        "n_office_workbook_blocked": int((office_workbook_promotion.get("promotion_status", pd.Series(dtype=str)) == "blocked_by_mismatch").sum()) if not office_workbook_promotion.empty else 0,
        "inventory_generated": inventory_result is not None,
    }
    summary_json = out / "validation_export_summary.json"
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_provenance(out, config_path=config_path, extra={"command": "tamu-validation-export", "result": summary})
    return TamuValidationExportResult(
        outdir=str(out),
        inventory_candidates_csv=str(inventory_candidates_csv) if inventory_candidates_csv else None,
        normalized_cases_csv=str(normalized_cases_csv) if normalized_cases_csv else None,
        policy_yaml=str(policy_yaml) if policy_yaml else None,
        physor_wide_csv=str(physor_wide_csv) if physor_wide_csv else None,
        nearest_fit_csv=str(nearest_fit_csv) if nearest_fit_csv else None,
        source_index_csv=str(source_index_csv) if source_index_csv else None,
        office_workbook_rows_csv=str(office_workbook_rows_csv) if office_workbook_rows_csv else None,
        office_workbook_promotion_csv=str(office_workbook_promotion_csv) if office_workbook_promotion_csv else None,
        summary_json=str(summary_json),
        n_inventory_candidates=int(len(inventory_candidates)),
        n_normalized_cases=int(len(normalized_cases)),
        n_nearest_fit_rows=int(len(nearest_fit)),
        n_office_workbook_rows=int(len(office_workbook_rows)),
        n_office_workbook_blocked=int((office_workbook_promotion.get("promotion_status", pd.Series(dtype=str)) == "blocked_by_mismatch").sum()) if not office_workbook_promotion.empty else 0,
    )


def build_tamu_validation_catalog(
    outdir: str | Path,
    *,
    inventory_root: str | Path | None = None,
    inventory_csv: str | Path | None = None,
    source_tables: list[str | Path] | None = None,
    config_path: str | Path | None = None,
) -> TamuValidationCatalogResult:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    source_tables = source_tables or []

    inventory_result: TamuInventoryResult | None = None
    if inventory_csv:
        case_inventory = pd.read_csv(inventory_csv)
        root_path = None
    elif inventory_root:
        root_path = Path(inventory_root)
        inventory_result = build_tamu_inventory(root_path, out / "inventory", config_path=config_path)
        case_inventory = pd.read_csv(inventory_result.case_inventory_csv)
    else:
        raise ValueError("Provide --inventory-root or --inventory-csv to build the TAMU validation catalog.")

    if root_path is None:
        raise ValueError("Catalog generation currently requires --inventory-root so file-level provenance can be resolved.")

    catalog = _build_validation_catalog(root_path, case_inventory)
    validation_catalog_csv = out / "validation_catalog.csv"
    catalog.to_csv(validation_catalog_csv, index=False)

    bucket_paths = {
        "steady_sensor_candidates": out / "steady_sensor_candidates.csv",
        "transient_sensor_candidates": out / "transient_sensor_candidates.csv",
        "steady_velocity_profile_candidates": out / "steady_velocity_profile_candidates.csv",
        "unknown_or_not_yet_interpretable": out / "unknown_or_not_yet_interpretable.csv",
    }
    for bucket, path in bucket_paths.items():
        catalog[catalog["candidate_bucket"] == bucket].copy().to_csv(path, index=False)

    source_provenance_index_csv = out / "source_provenance_index.csv"
    catalog[
        [
            "candidate_bucket",
            "candidate_case_name",
            "recognized_case_name",
            "recognition_basis",
            "top_level_folder",
            "source_file_path",
            "source_bundle_paths",
            "measurement_family",
            "confidence",
            "provenance_notes",
        ]
    ].to_csv(source_provenance_index_csv, index=False)

    normalized_cases, source_index, office_workbook_rows = _collect_validation_source_rows(
        source_tables,
        inventory_root=root_path,
    )
    _, consistency_report = build_validation_source_consistency_audit(
        normalized_cases,
        canonical_source_profiles=CANONICAL_SOURCE_PROFILES,
    )
    consistency_report_csv = out / "validation_source_consistency_report.csv" if not consistency_report.empty else None
    if consistency_report_csv is not None:
        consistency_report.to_csv(consistency_report_csv, index=False)
    discrepancies_only = consistency_report[consistency_report["status"] == "mismatch"].copy() if not consistency_report.empty else pd.DataFrame()
    discrepancies_only_csv = out / "validation_source_discrepancies_only.csv" if not discrepancies_only.empty else None
    if discrepancies_only_csv is not None:
        discrepancies_only.to_csv(discrepancies_only_csv, index=False)
    consistency_summary_md = out / "validation_source_consistency_summary.md" if consistency_report_csv is not None else None
    if consistency_summary_md is not None:
        consistency_summary_md.write_text(_render_consistency_summary(consistency_report), encoding="utf-8")

    office_workbook_rows_csv = out / "office_workbook_case_rows.csv" if not office_workbook_rows.empty else None
    if office_workbook_rows_csv is not None:
        office_workbook_rows.to_csv(office_workbook_rows_csv, index=False)

    office_workbook_promotion = _build_office_workbook_promotion_decisions(office_workbook_rows, consistency_report)
    office_workbook_promotion_csv = out / "office_workbook_promotion_decisions.csv" if not office_workbook_promotion.empty else None
    if office_workbook_promotion_csv is not None:
        office_workbook_promotion.to_csv(office_workbook_promotion_csv, index=False)

    source_index_csv = out / "validation_source_index.csv" if not source_index.empty else None
    if source_index_csv is not None:
        source_index.to_csv(source_index_csv, index=False)

    plot_index = _write_velocity_profile_outputs(catalog, out)
    velocity_plot_index_csv = out / "velocity_profile_plot_index.csv" if not plot_index.empty else None
    if velocity_plot_index_csv is not None:
        plot_index.to_csv(velocity_plot_index_csv, index=False)

    summary_md = out / "validation_catalog_summary.md"
    summary_md.write_text(_render_validation_catalog_summary(catalog, plot_index, consistency_report), encoding="utf-8")

    summary_payload = {
        "outdir": str(out),
        "inventory_root": str(root_path),
        "inventory_generated": inventory_result is not None,
        "source_tables": [str(Path(path)) for path in source_tables],
        "n_catalog_rows": int(len(catalog)),
        "n_velocity_plot_rows": int(len(plot_index)),
        "n_consistency_rows": int(len(consistency_report)),
        "n_consistency_mismatches": int(len(discrepancies_only)),
        "n_office_workbook_rows": int(len(office_workbook_rows)),
        "n_office_workbook_blocked": int((office_workbook_promotion.get("promotion_status", pd.Series(dtype=str)) == "blocked_by_mismatch").sum()) if not office_workbook_promotion.empty else 0,
    }
    summary_json = out / "validation_catalog_summary.json"
    summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    write_provenance(out, config_path=config_path, extra={"command": "tamu-validation-catalog", "result": summary_payload})
    return TamuValidationCatalogResult(
        outdir=str(out),
        validation_catalog_csv=str(validation_catalog_csv),
        steady_sensor_csv=str(bucket_paths["steady_sensor_candidates"]),
        transient_sensor_csv=str(bucket_paths["transient_sensor_candidates"]),
        steady_velocity_csv=str(bucket_paths["steady_velocity_profile_candidates"]),
        unknown_csv=str(bucket_paths["unknown_or_not_yet_interpretable"]),
        source_provenance_index_csv=str(source_provenance_index_csv),
        velocity_plot_index_csv=str(velocity_plot_index_csv) if velocity_plot_index_csv else None,
        consistency_report_csv=str(consistency_report_csv) if consistency_report_csv else None,
        consistency_summary_md=str(consistency_summary_md) if consistency_summary_md else None,
        discrepancies_only_csv=str(discrepancies_only_csv) if discrepancies_only_csv else None,
        office_workbook_rows_csv=str(office_workbook_rows_csv) if office_workbook_rows_csv else None,
        office_workbook_promotion_csv=str(office_workbook_promotion_csv) if office_workbook_promotion_csv else None,
        summary_md=str(summary_md),
        summary_json=str(summary_json),
        n_catalog_rows=int(len(catalog)),
        n_velocity_plot_rows=int(len(plot_index)),
        n_consistency_rows=int(len(consistency_report)),
        n_consistency_mismatches=int(len(discrepancies_only)),
        n_office_workbook_rows=int(len(office_workbook_rows)),
        n_office_workbook_blocked=int((office_workbook_promotion.get("promotion_status", pd.Series(dtype=str)) == "blocked_by_mismatch").sum()) if not office_workbook_promotion.empty else 0,
    )


__all__ = [
    "TamuInventoryResult",
    "TamuValidationExportResult",
    "TamuValidationCatalogResult",
    "build_tamu_inventory",
    "export_tamu_validation_artifacts",
    "build_tamu_validation_catalog",
    "normalize_wide_validation_sources",
    "build_physor_wide_table",
    "build_validation_source_consistency_audit",
]
