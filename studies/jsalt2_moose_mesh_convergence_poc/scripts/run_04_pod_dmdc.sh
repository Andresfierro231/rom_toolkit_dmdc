#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[4/6] Fitting POD-DMDc for the JSALT2 proof-of-concept..."
run_dmdc pod-dmdc --config "$CONFIG"
