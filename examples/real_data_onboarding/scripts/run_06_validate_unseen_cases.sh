#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[6/10] Validating on held-out/unseen cases..."
dmdc validate --config "$CONFIG"
