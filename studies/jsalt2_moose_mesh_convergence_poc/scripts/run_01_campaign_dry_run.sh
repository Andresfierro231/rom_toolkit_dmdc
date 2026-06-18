#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[1/6] Dry-running the JSALT2 POC campaign..."
run_dmdc campaign --config "$CONFIG" --dry-run
