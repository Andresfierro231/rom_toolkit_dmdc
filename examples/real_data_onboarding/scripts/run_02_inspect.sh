#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[2/10] Inspecting canonical data, dt behavior, missing values, and case quality..."
dmdc inspect-data --config "$CONFIG"
