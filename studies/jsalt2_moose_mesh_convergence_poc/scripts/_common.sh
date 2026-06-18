#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STUDY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$STUDY_DIR/../.." && pwd)"
CONFIG="${CONFIG:-$STUDY_DIR/study_config.toml}"

if [[ ! -f "$CONFIG" ]]; then
  echo "Could not find study config: $CONFIG" >&2
  exit 1
fi

cd "$REPO_ROOT"
export PYTHONPATH="${PYTHONPATH:-src}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-${USER:-codex}}"

run_dmdc() {
  if command -v dmdc >/dev/null 2>&1; then
    dmdc "$@"
    return
  fi
  if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    "$REPO_ROOT/.venv/bin/python" -m dmdc.cli "$@"
    return
  fi
  python -m dmdc.cli "$@"
}
