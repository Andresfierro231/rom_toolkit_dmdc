#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[9/10] Opening executive/operator dashboard..."
dmdc live-dashboard --config "$CONFIG" --view operator
