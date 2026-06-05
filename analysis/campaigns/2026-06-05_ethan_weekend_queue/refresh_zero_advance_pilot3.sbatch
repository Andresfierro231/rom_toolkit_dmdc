#!/bin/bash
#SBATCH -J zeroadv_pilot3
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -t 01:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-05_ethan_weekend_queue/zeroadv_pilot3-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-05_ethan_weekend_queue/zeroadv_pilot3-%j.err

set -euo pipefail
cd /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis
/usr/bin/python3.11 tools/ethan_zero_advance_transport.py
