#!/usr/bin/env bash
#SBATCH -J dmdc_pytestr
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-01_overnight_jsalt2_followup/logs/%x_%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-01_overnight_jsalt2_followup/logs/%x_%j.err

set -euo pipefail

REPO_ROOT="/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis"
cd "$REPO_ROOT"
mkdir -p analysis/campaigns/2026-06-01_overnight_jsalt2_followup/logs
export PYTHONPATH="${PYTHONPATH:-src}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-${USER:-codex}}"

.venv/bin/python -m pytest -q
