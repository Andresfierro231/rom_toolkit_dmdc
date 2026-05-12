#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[4/10] Fitting POD-DMDc..."
dmdc pod-dmdc --config "$CONFIG"
