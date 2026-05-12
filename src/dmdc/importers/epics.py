"""Optional EPICS import and live adapter scaffolding.

EPICS support is optional because most developer machines and CI runners do not
have control-network access.  The classes here are still designed around field
use: explicit PV maps, connection checks, timestamp capture, reconnect-friendly
failures, and JSON-friendly metadata.  Long-running EPICS streaming can plug
into the same ``StreamAdapter`` style used by CSV replay/tail workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Any
import time

import pandas as pd

from .base import ImportResult
from ..streaming import LiveSample, StreamAdapter


@dataclass
class EPICSPVImporter:
    """Import a one-row EPICS process-variable snapshot.

    Parameters
    ----------
    pvs:
        Mapping from desired canonical column name to EPICS PV name, e.g.
        ``{"TP1": "LOOP:TP1", "q_heater": "LOOP:HEATER:POWER"}``.
    timeout:
        Read timeout passed to pyepics.
    include_pv_status:
        If true, add ``<column>__pv`` columns to document which process variable
        produced each canonical value.  This is helpful during commissioning.
    """

    pvs: Mapping[str, str]
    timeout: float = 2.0
    timestamp_col: str = "received_utc"
    include_pv_status: bool = True
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    def import_data(self) -> ImportResult:
        epics = _import_epics()
        row: dict[str, Any] = {self.timestamp_col: datetime.now(timezone.utc).isoformat()}
        warnings: list[str] = []
        for column, pv_name in self.pvs.items():
            try:
                value = epics.caget(pv_name, timeout=self.timeout)
            except Exception as exc:  # pragma: no cover - depends on EPICS runtime
                value = None
                warnings.append(f"Failed to read PV {pv_name!r} for column {column!r}: {exc}")
            row[column] = value
            if self.include_pv_status:
                row[f"{column}__pv"] = pv_name
        return ImportResult(
            frame=pd.DataFrame([row]),
            metadata={
                "importer": "epics_pv_snapshot",
                "n_pvs": len(self.pvs),
                "pvs": dict(self.pvs),
                "timeout": self.timeout,
                **self.extra_metadata,
            },
            warnings=warnings,
        )


@dataclass
class EPICSPollingStreamAdapter(StreamAdapter):
    """Polling EPICS stream adapter.

    This adapter is suitable for early field trials where a workstation polls a
    small set of PVs at a fixed interval.  It returns one :class:`LiveSample` per
    poll.  A production monitor/callback adapter can be added later without
    changing the live ROM pipeline.
    """

    pvs: Mapping[str, str]
    timeout: float = 2.0
    poll_seconds: float = 0.5
    timestamp_col: str = "received_utc"
    source: str = "epics_poll"
    add_pv_metadata: bool = False

    def __post_init__(self) -> None:
        self._row_index = 0
        self._epics = _import_epics()

    def read_new_samples(self) -> list[LiveSample]:
        row: dict[str, Any] = {self.timestamp_col: datetime.now(timezone.utc).isoformat()}
        for column, pv_name in self.pvs.items():
            try:
                row[column] = self._epics.caget(pv_name, timeout=self.timeout)
            except Exception:
                row[column] = None
            if self.add_pv_metadata:
                row[f"{column}__pv"] = pv_name
        sample = LiveSample(values=row, source=self.source, row_index=self._row_index)
        self._row_index += 1
        if self.poll_seconds > 0:
            time.sleep(float(self.poll_seconds))
        return [sample]


def check_epics_pvs(pvs: Mapping[str, str], *, timeout: float = 2.0) -> pd.DataFrame:
    """Return a human-readable PV connectivity table.

    The function does not require a live run.  It is useful during commissioning
    and can be called from notebooks/tests with mocked ``epics`` modules.
    """

    epics = _import_epics()
    rows: list[dict[str, Any]] = []
    for column, pv_name in pvs.items():
        ok = False
        value = None
        error = ""
        try:
            value = epics.caget(pv_name, timeout=timeout)
            ok = value is not None
        except Exception as exc:  # pragma: no cover - runtime network dependent
            error = str(exc)
        rows.append({"column": column, "pv": pv_name, "connected": bool(ok), "sample_value": value, "error": error})
    return pd.DataFrame(rows)


def _import_epics():
    try:
        import epics  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "EPICS support requires pyepics and access to the control network. "
            "Install with `python -m pip install -e '.[epics]'` and test with "
            "a small PV map before connecting the live ROM pipeline."
        ) from exc
    return epics
