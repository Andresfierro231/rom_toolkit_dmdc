"""High-level data import workflow used by the CLI.

The goal of ``dmdc import-data`` is to bridge messy current-data sources into
the rest of the ROM pipeline.  It reads CSV/Excel/folder/EPICS-like sources,
renames columns if requested, writes a canonical CSV/Parquet file, and produces
sidecar summaries so users immediately know what was imported.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .importers import (
    EPICSPVImporter,
    FolderTableImporter,
    LabVIEWDAQFolderImporter,
    TabularFileImporter,
    load_column_mapping,
    parse_rename_pairs,
)
from .utils import write_json


def run_import_workflow(
    *,
    source: str | Path | None,
    source_type: str = "auto",
    out: str | Path,
    output_format: str = "parquet",
    sheet: str | int | None = None,
    pattern: str = "*.csv",
    column_map: str | Path | None = None,
    rename_col: list[str] | None = None,
    add_source_file_col: bool = True,
    case_from_filename: bool = False,
    max_files: int | None = None,
    epics_pvs: dict[str, str] | None = None,
    strict_parquet: bool = False,
    skip_unstable_files: bool = False,
    settle_seconds: float = 0.0,
) -> dict[str, Any]:
    """Run one configured import job and return a JSON-friendly summary."""

    mapping = load_column_mapping(column_map)
    mapping.update(parse_rename_pairs(rename_col))
    key = source_type.strip().lower().replace("-", "_")
    source_path = Path(source) if source is not None else None
    if key == "auto":
        if source_path is None:
            key = "epics" if epics_pvs else "csv"
        elif source_path.is_dir():
            key = "folder"
        elif source_path.suffix.lower() in {".xlsx", ".xls"}:
            key = "excel"
        else:
            key = "csv"

    if key in {"csv", "excel", "parquet", "tabular"}:
        if source_path is None:
            raise ValueError("A source path is required for csv/excel/parquet import.")
        importer = TabularFileImporter(
            source_path,
            sheet=sheet,
            column_mapping=mapping,
            add_source_file_col=False,
        )
    elif key in {"folder", "folder_table"}:
        if source_path is None:
            raise ValueError("A source folder is required for folder import.")
        importer = FolderTableImporter(
            source_path,
            pattern=pattern,
            sheet=sheet,
            column_mapping=mapping,
            add_source_file_col=add_source_file_col,
            case_from_filename=case_from_filename,
            max_files=max_files,
            skip_unstable_files=skip_unstable_files,
            settle_seconds=settle_seconds,
        )
    elif key in {"labview", "labview_daq", "daq"}:
        if source_path is None:
            raise ValueError("A source folder is required for LabVIEW/DAQ folder import.")
        importer = LabVIEWDAQFolderImporter(
            root=source_path,
            pattern=pattern,
            sheet=sheet,
            column_mapping=mapping,
            add_source_file_col=add_source_file_col,
            case_from_filename=case_from_filename,
            max_files=max_files,
            skip_unstable_files=skip_unstable_files,
            settle_seconds=settle_seconds,
        )
    elif key in {"epics", "epics_pv"}:
        if not epics_pvs:
            raise ValueError("EPICS import requires a [importer.epics_pvs] mapping in config.")
        importer = EPICSPVImporter(epics_pvs)
    else:
        raise ValueError(
            f"Unsupported import source_type {source_type!r}. Use auto, csv, excel, parquet, folder, labview_daq, or epics."
        )

    result = importer.import_data()
    out_path = result.save(out, fmt=output_format, strict_parquet=strict_parquet)
    sidecar_dir = out_path.parent
    result.metadata.update(
        {
            "canonical_output": str(out_path),
            "output_format_requested": output_format,
            "output_format_actual": out_path.suffix.lstrip("."),
            "column_mapping_used": mapping,
        }
    )
    result.write_sidecars(sidecar_dir)
    write_json(result.metadata, sidecar_dir / "import_metadata.json")
    return {**result.metadata, "warnings": result.warnings}
