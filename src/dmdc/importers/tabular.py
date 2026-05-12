"""CSV, Excel, folder, and LabVIEW/DAQ-style tabular importers.

These importers are intentionally boring and dependable.  They normalize common
file formats into a single tidy DataFrame.  High-throughput live logging should
use the live archive writer, but these importers are the right bridge for
existing CSV/XLSX exports, DAQ folder drops, and SAM/experimental batches.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from .base import ImportResult, apply_column_mapping


SUPPORTED_TABLE_SUFFIXES = {".csv", ".parquet", ".pq", ".xlsx", ".xls"}


def read_tabular_file(path: str | Path, *, sheet: str | int | None = None) -> pd.DataFrame:
    """Read one CSV/Parquet/Excel file into a DataFrame."""

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".xlsx", ".xls"}:
        # pandas/openpyxl is optional in many environments.  Let pandas raise a
        # useful dependency error, then wrap it with context for the user.
        try:
            return pd.read_excel(path, sheet_name=0 if sheet is None else sheet)
        except ImportError as exc:
            raise RuntimeError(
                "Excel import requires openpyxl/xlrd. Install with `python -m pip install openpyxl`."
            ) from exc
    raise ValueError(f"Unsupported tabular file type {suffix!r}. Supported: {sorted(SUPPORTED_TABLE_SUFFIXES)}")


def is_probably_stable_file(path: str | Path, *, settle_seconds: float = 0.0, min_size_bytes: int = 1) -> bool:
    """Return whether a DAQ/LabVIEW chunk file appears ready to read.

    Field loggers often write files in place.  A future folder watcher may call
    this before ingesting a chunk.  The default is permissive for offline imports;
    production configs can increase ``settle_seconds`` to avoid partial files.
    """

    import time

    path = Path(path)
    if not path.exists() or not path.is_file():
        return False
    try:
        size1 = path.stat().st_size
        if size1 < min_size_bytes:
            return False
        if settle_seconds <= 0:
            return True
        time.sleep(float(settle_seconds))
        size2 = path.stat().st_size
        return size1 == size2 and size2 >= min_size_bytes
    except OSError:
        return False


@dataclass
class TabularFileImporter:
    """Importer for a single CSV, Parquet, or Excel file."""

    path: str | Path
    sheet: str | int | None = None
    column_mapping: dict[str, str] | None = None
    add_source_file_col: bool = False

    def import_data(self) -> ImportResult:
        path = Path(self.path)
        frame = read_tabular_file(path, sheet=self.sheet)
        frame = apply_column_mapping(frame, self.column_mapping)
        if self.add_source_file_col:
            frame["source_file"] = path.name
        return ImportResult(
            frame=frame,
            metadata={
                "importer": "tabular_file",
                "source_path": str(path),
                "sheet": self.sheet,
                "n_rows": int(len(frame)),
                "n_columns": int(frame.shape[1]),
            },
            warnings=[],
        )


@dataclass
class FolderTableImporter:
    """Importer for a folder containing many CSV/Excel/Parquet chunks.

    This is the first general-purpose adapter for LabVIEW/DAQ folder-drop
    workflows.  A DAQ process can write one file per interval or per experiment;
    this importer stacks them with optional source-file and case columns.
    """

    root: str | Path
    pattern: str = "*.csv"
    sheet: str | int | None = None
    column_mapping: dict[str, str] | None = None
    add_source_file_col: bool = True
    case_from_filename: bool = False
    max_files: int | None = None
    skip_unstable_files: bool = False
    settle_seconds: float = 0.0

    def import_data(self) -> ImportResult:
        root = Path(self.root)
        files = sorted(p for p in root.glob(self.pattern) if p.is_file())
        if self.skip_unstable_files:
            stable_files = []
            for candidate in files:
                if is_probably_stable_file(candidate, settle_seconds=self.settle_seconds):
                    stable_files.append(candidate)
            files = stable_files
        if self.max_files is not None:
            files = files[: int(self.max_files)]
        if not files:
            raise FileNotFoundError(f"No files matched {self.pattern!r} under {root}")
        frames: list[pd.DataFrame] = []
        warnings: list[str] = []
        for path in files:
            try:
                frame = read_tabular_file(path, sheet=self.sheet)
            except Exception as exc:
                warnings.append(f"Skipped {path}: {exc}")
                continue
            frame = apply_column_mapping(frame, self.column_mapping)
            if self.add_source_file_col:
                frame["source_file"] = path.name
            if self.case_from_filename and "case_id" not in frame.columns:
                frame["case_id"] = path.stem
            frames.append(frame)
        if not frames:
            raise ValueError(f"No readable files matched {self.pattern!r} under {root}")
        out = pd.concat(frames, ignore_index=True, sort=False)
        return ImportResult(
            frame=out,
            metadata={
                "importer": "folder_table",
                "root": str(root),
                "pattern": self.pattern,
                "n_files_found": len(files),
                "n_files_imported": len(frames),
                "skip_unstable_files": bool(self.skip_unstable_files),
                "settle_seconds": float(self.settle_seconds),
                "n_rows": int(len(out)),
                "n_columns": int(out.shape[1]),
            },
            warnings=warnings,
        )


@dataclass
class LabVIEWDAQFolderImporter(FolderTableImporter):
    """Alias/semantic wrapper for LabVIEW or DAQ folder-drop exports.

    LabVIEW and many DAQ systems commonly write rolling CSV/XLSX chunks to a
    folder.  This class deliberately reuses :class:`FolderTableImporter` so the
    same code path can be tested heavily while leaving room for vendor-specific
    parsing later.
    """

    def import_data(self) -> ImportResult:
        result = super().import_data()
        result.metadata["importer"] = "labview_daq_folder"
        result.warnings.append(
            "LabVIEW/DAQ importer currently assumes ordinary tabular chunk files. "
            "For field use, enable skip_unstable_files/settle_seconds in a vendor-specific workflow, "
            "and add a parser for any logger metadata headers or sidecar files."
        )
        return result
