#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

echo "[7/10] Replaying data as live stream with monitoring/trust scoring..."
dmdc live-replay-monitor --config "$CONFIG"
