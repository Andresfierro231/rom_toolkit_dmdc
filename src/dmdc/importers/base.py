"""Importer interfaces for getting external data into the ROM toolkit.

The rest of the repo works best with tidy tables: one row per sample, named
columns for time/state/input signals, and an optional case identifier.  Real
systems rarely start that clean.  This module defines a small importer contract
so new data sources can be added without touching DMDc/POD/live-monitoring code.

Every importer returns an :class:`ImportResult` containing a pandas DataFrame,
metadata, and human-readable warnings.  A command such as ``dmdc import-data``
can then write the frame to CSV/Parquet and immediately inspect it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
import json

import pandas as pd


@dataclass
class ImportResult:
    """Container returned by all data importers."""

    frame: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def save(self, out: str | Path, *, fmt: str = "parquet", strict_parquet: bool = False) -> Path:
        """Save the imported frame to CSV or Parquet.

        Parquet is preferred for large data and long-term archives.  If Parquet
        dependencies are unavailable and ``strict_parquet`` is false, this helper
        falls back to CSV while recording the actual file extension.
        """

        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        fmt_key = fmt.lower().strip()
        if fmt_key in {"parquet", "pq"}:
            path = out if out.suffix.lower() in {".parquet", ".pq"} else out.with_suffix(".parquet")
            try:
                self.frame.to_parquet(path, index=False)
                return path
            except Exception as exc:
                if strict_parquet:
                    raise RuntimeError(
                        "Could not write Parquet. Install pyarrow or use --format csv."
                    ) from exc
                self.warnings.append(
                    "Parquet write failed; falling back to CSV. Install pyarrow for serious large-data use."
                )
                path = out.with_suffix(".csv")
                self.frame.to_csv(path, index=False)
                return path
        if fmt_key == "csv":
            path = out if out.suffix.lower() == ".csv" else out.with_suffix(".csv")
            self.frame.to_csv(path, index=False)
            return path
        raise ValueError(f"Unsupported import output format {fmt!r}. Use csv or parquet.")

    def write_sidecars(self, outdir: str | Path) -> None:
        """Write metadata/warnings sidecars next to imported data."""

        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "import_summary.json").write_text(
            json.dumps({**self.metadata, "warnings": self.warnings}, indent=2, default=str),
            encoding="utf-8",
        )
        if self.warnings:
            (outdir / "import_warnings.txt").write_text("\n".join(self.warnings) + "\n", encoding="utf-8")
        else:
            (outdir / "import_warnings.txt").write_text("No importer warnings.\n", encoding="utf-8")
        cols = pd.DataFrame(
            {
                "column": list(self.frame.columns),
                "dtype": [str(self.frame[c].dtype) for c in self.frame.columns],
                "n_missing": [int(self.frame[c].isna().sum()) for c in self.frame.columns],
                "n_unique": [int(self.frame[c].nunique(dropna=True)) for c in self.frame.columns],
            }
        )
        cols.to_csv(outdir / "import_columns_summary.csv", index=False)


class DataImporter(Protocol):
    """Minimal protocol for importers.

    New adapters should keep this interface: ingest external data and return a
    tidy DataFrame with metadata.  This makes EPICS, LabVIEW, DAQ, folder-drop,
    HDF5, or database importers plug-compatible.
    """

    def import_data(self) -> ImportResult:
        """Load external data and return a standardized import result."""


def apply_column_mapping(frame: pd.DataFrame, mapping: dict[str, str] | None) -> pd.DataFrame:
    """Rename columns using an external mapping dictionary.

    ``mapping`` should map original names to desired canonical repo names, for
    example ``{"HeaterPower_W": "q_heater", "TC01": "TP1"}``.
    Missing source columns are ignored so the same mapping file can be reused
    across experiments with slightly different sensors.
    """

    if not mapping:
        return frame
    actual = {old: new for old, new in mapping.items() if old in frame.columns}
    return frame.rename(columns=actual)


def parse_rename_pairs(pairs: list[str] | None) -> dict[str, str]:
    """Parse CLI rename pairs of the form ``old=new`` or ``old:new``."""

    mapping: dict[str, str] = {}
    for pair in pairs or []:
        if "=" in pair:
            old, new = pair.split("=", 1)
        elif ":" in pair:
            old, new = pair.split(":", 1)
        else:
            raise ValueError(f"Rename pair {pair!r} must look like old=new or old:new.")
        mapping[old.strip()] = new.strip()
    return mapping


def load_column_mapping(path: str | Path | None) -> dict[str, str]:
    """Load a JSON/TOML column-mapping file if supplied."""

    if path is None:
        return {}
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Column mapping file not found: {path}")
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".toml":
        try:
            import tomllib
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("TOML mapping files require Python 3.11+.") from exc
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Column mapping files must be .json or .toml.")
    if "columns" in payload and isinstance(payload["columns"], dict):
        payload = payload["columns"]
    if not isinstance(payload, dict):
        raise ValueError("Column mapping must be a mapping/dictionary.")
    return {str(k): str(v) for k, v in payload.items()}
