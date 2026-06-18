#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[5/6] Comparing DMDc, ridge DMDc, POD-DMDc, and baselines..."
run_dmdc compare --config "$CONFIG"
