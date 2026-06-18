#!/usr/bin/env python3
"""Delegate to the reusable Box upload helper under .agents/tools/."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools._agents_bridge import run_agent_tool


if __name__ == "__main__":
    run_agent_tool(__file__)
