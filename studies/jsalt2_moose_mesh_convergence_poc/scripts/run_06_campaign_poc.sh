#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[6/6] Running the focused JSALT2 POC campaign..."
run_dmdc campaign --config "$CONFIG" --steps import inspect pod_dmdc compare
