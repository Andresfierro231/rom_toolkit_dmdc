#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CONFIG:-study_config.toml}"

if [[ ! -f "$CONFIG" ]]; then
  echo "Could not find $CONFIG. Run scripts from examples/real_data_onboarding or set CONFIG=/path/to/study_config.toml." >&2
  exit 1
fi

if grep -q "TODO_" "$CONFIG"; then
  echo "WARNING: $CONFIG still contains TODO placeholders. Edit it before running on real data." >&2
fi

export PYTHONPATH="${PYTHONPATH:-src}"
