#!/usr/bin/env bash
set -euo pipefail

# Local campaign helper.
# Usage:
#   bash scripts/workflows/run_campaign_local.sh studies/my_loop/study_config.toml import inspect compare
# If no steps are supplied, the steps from [campaign].steps in the config are used.

CONFIG=${1:-configs/templates/central_campaign_config.toml}
shift || true
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-${USER:-codex}}"

if [ "$#" -gt 0 ]; then
  if command -v dmdc >/dev/null 2>&1; then
    dmdc campaign --config "$CONFIG" --steps "$@"
  elif [ -x ".venv/bin/python" ]; then
    .venv/bin/python -m dmdc.cli campaign --config "$CONFIG" --steps "$@"
  else
    python -m dmdc.cli campaign --config "$CONFIG" --steps "$@"
  fi
else
  if command -v dmdc >/dev/null 2>&1; then
    dmdc campaign --config "$CONFIG"
  elif [ -x ".venv/bin/python" ]; then
    .venv/bin/python -m dmdc.cli campaign --config "$CONFIG"
  else
    python -m dmdc.cli campaign --config "$CONFIG"
  fi
fi
