#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[3/6] Inspecting the canonical JSALT2 table..."
run_dmdc inspect-data --config "$CONFIG"
