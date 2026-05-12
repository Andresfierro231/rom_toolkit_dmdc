#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[5/10] Comparing baselines, adaptive DMDc, regularized DMDc, and POD-DMDc..."
dmdc compare --config "$CONFIG"
