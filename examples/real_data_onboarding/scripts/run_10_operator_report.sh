#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[10/10] Generating live operator report..."
dmdc live-operator-report --config "$CONFIG"
