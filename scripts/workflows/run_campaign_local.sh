#!/usr/bin/env bash
set -euo pipefail

# Local campaign helper.
# Usage:
#   bash scripts/workflows/run_campaign_local.sh studies/my_loop/study_config.toml import inspect compare
# If no steps are supplied, the steps from [campaign].steps in the config are used.

CONFIG=${1:-configs/templates/central_campaign_config.toml}
shift || true

if [ "$#" -gt 0 ]; then
  dmdc campaign --config "$CONFIG" --steps "$@"
else
  dmdc campaign --config "$CONFIG"
fi
