"""Shared pytest configuration for source-tree subprocess tests.

Several CLI smoke tests spawn ``python -m dmdc.cli``.  Those subprocesses do not
see pytest's ``pythonpath = src`` setting from ``pyproject.toml``, so we set a
repository-local ``PYTHONPATH`` here.  This keeps tests robust both before and
after an editable install.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
existing = os.environ.get("PYTHONPATH", "")
parts = [str(SRC)] + ([existing] if existing else [])
os.environ["PYTHONPATH"] = os.pathsep.join(parts)
