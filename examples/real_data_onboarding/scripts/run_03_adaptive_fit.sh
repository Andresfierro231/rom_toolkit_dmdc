#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[3/10] Fitting adaptive/variable-dt DMDc..."
dmdc adaptive-fit --config "$CONFIG"
