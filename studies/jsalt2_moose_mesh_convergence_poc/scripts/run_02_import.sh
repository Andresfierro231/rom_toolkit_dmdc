#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[2/6] Importing JSALT2 trajectory CSVs into the canonical table..."
run_dmdc import-data --config "$CONFIG"
