#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[8/10] Replaying data as live stream with bounded bias correction..."
dmdc live-replay-adapt --config "$CONFIG"
