#!/usr/bin/env bash
#SBATCH -J dmdc_swph_r
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

.venv/bin/python -m dmdc.cli sweep \
  --data outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet \
  --state-cols TP1 TP2 TP3 TP6 massFlowRate \
  --input-cols h \
  --time-col time \
  --case-col case_id \
  --train-fraction 0.75 \
  --models persistence mean adaptive_dmdc dmdc ridge_dmdc pod_dmdc \
  --pod-ranks 2 3 4 0.999 \
  --dmdc-ranks full 2 3 4 \
  --n-delays 1 2 4 \
  --center \
  --plots \
  --report \
  --outdir outputs/overnight_sweeps/jsalt2_with_h_pair_20260601
