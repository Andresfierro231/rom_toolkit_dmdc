#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _agents_bridge import run_agent_tool


if __name__ == "__main__":
    run_agent_tool(__file__)
