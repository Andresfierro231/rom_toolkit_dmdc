"""Friendly warnings for ROM workflows.

The package tries to fail loudly for impossible inputs and warn clearly for inputs that are
technically usable but likely to produce misleading ROMs.  A warning is represented as a small
structured object so it can be printed, saved to JSON, and later included in reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FriendlyWarning:
    """Actionable warning emitted by data inspection or modeling workflows."""

    code: str
    message: str
    why_it_matters: str = ""
    suggested_actions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def format(self) -> str:
        """Return a readable multi-line warning message."""

        lines = [f"[{self.code}] {self.message}"]
        if self.why_it_matters:
            lines.append("")
            lines.append("Why this matters:")
            lines.append(self.why_it_matters)
        if self.suggested_actions:
            lines.append("")
            lines.append("Suggested actions:")
            lines.extend(f"- {action}" for action in self.suggested_actions)
        return "\n".join(lines)


def write_warnings(warnings: Iterable[FriendlyWarning], path: str | Path) -> None:
    """Save warnings to a plain-text file that is easy to read in output folders."""

    warnings = list(warnings)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not warnings:
        Path(path).write_text("No warnings emitted.\n", encoding="utf-8")
        return
    Path(path).write_text("\n\n".join(w.format() for w in warnings) + "\n", encoding="utf-8")


def warnings_to_dicts(warnings: Iterable[FriendlyWarning]) -> list[dict[str, object]]:
    """Convert warnings into JSON-serializable dictionaries."""

    return [w.to_dict() for w in warnings]
