#!/usr/bin/env bash
# Runs the non-interactive replay workflow. The dashboard step is intentionally
# omitted because it opens a Streamlit server.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

bash "$SCRIPT_DIR/run_01_import.sh"
bash "$SCRIPT_DIR/run_02_inspect.sh"
bash "$SCRIPT_DIR/run_03_adaptive_fit.sh"
bash "$SCRIPT_DIR/run_04_pod_dmdc.sh"
bash "$SCRIPT_DIR/run_05_compare_models.sh"
bash "$SCRIPT_DIR/run_06_validate_unseen_cases.sh"
bash "$SCRIPT_DIR/run_07_live_replay_monitor.sh"
bash "$SCRIPT_DIR/run_08_live_replay_adapt.sh"
bash "$SCRIPT_DIR/run_10_operator_report.sh"
