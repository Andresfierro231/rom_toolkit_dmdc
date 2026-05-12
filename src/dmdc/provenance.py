"""Reproducibility and provenance helpers for ROM output folders.

Every analysis folder should be self-describing: what command created it, which
version of the package was used, which Python version was used, and what files
or configs were involved.  These helpers are intentionally small and dependency
light so that all CLI commands can call them without creating a heavy workflow
framework.
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
import json
import os
import platform
import subprocess
import sys
from typing import Any


def package_version() -> str:
    """Return the installed package version, falling back to a local dev label."""

    try:
        return metadata.version("dmdc-analysis")
    except metadata.PackageNotFoundError:
        return "0.1.0+local"


def git_commit(repo_root: str | Path | None = None) -> str | None:
    """Return the current git commit hash if the folder is inside a git repo."""

    root = Path(repo_root or Path.cwd())
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        return None
    commit = completed.stdout.strip()
    return commit or None


def collect_provenance(
    *,
    command: list[str] | None = None,
    config_path: str | Path | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect reproducibility metadata for an output folder."""

    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "package": "dmdc-analysis",
        "package_version": package_version(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "working_directory": str(Path.cwd()),
        "command": command if command is not None else sys.argv,
        "config_path": None if config_path is None else str(config_path),
        "git_commit": git_commit(),
        "environment": {
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
        },
        "extra": extra or {},
    }


def write_provenance(
    outdir: str | Path,
    *,
    command: list[str] | None = None,
    config_path: str | Path | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``provenance.json`` to an output directory and return its path."""

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "provenance.json"
    path.write_text(json.dumps(collect_provenance(command=command, config_path=config_path, extra=extra), indent=2), encoding="utf-8")
    return path
