#!/usr/bin/env python3
"""Delegate root workflow wrapper scripts to the generic starter tools in .agents."""

from __future__ import annotations

from pathlib import Path
import runpy


def run_agent_tool(wrapper_file: str) -> None:
    wrapper = Path(wrapper_file).resolve()
    repo_root = wrapper.parents[2]
    rel = wrapper.relative_to(repo_root / "tools")
    target = repo_root / ".agents" / "tools" / rel
    if not target.exists():
        raise SystemExit(f"Missing delegated tool: {target}")
    runpy.run_path(str(target), run_name="__main__")
