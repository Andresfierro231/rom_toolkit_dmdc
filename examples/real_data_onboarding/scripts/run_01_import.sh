#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[1/10] Importing raw data into canonical table..."
run_dmdc import-data --config "$CONFIG"
