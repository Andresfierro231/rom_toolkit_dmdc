#!/usr/bin/env bash
#SBATCH -J dmdc_tamu_inv
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -o analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/logs/%x_%j.out
#SBATCH -e analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/logs/%x_%j.err

set -euo pipefail

REPO_ROOT="/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis"
cd "$REPO_ROOT"
mkdir -p analysis/campaigns/2026-05-25_overnight_tamu_jsalt2_queue/logs
export PYTHONPATH="${PYTHONPATH:-src}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-${USER:-codex}}"

.venv/bin/python -m dmdc.cli tamu-inventory \
  --root "../tamu_loop_data_25_mayo/Loop Operational Data" \
  --outdir "outputs/tamu_inventory_overnight_20260525"
