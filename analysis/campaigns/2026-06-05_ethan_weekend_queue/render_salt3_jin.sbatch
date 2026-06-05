#!/bin/bash
#SBATCH -J render_salt3_jin
#SBATCH -p NuclearEnergy
#SBATCH -A ASC23046
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -o /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-05_ethan_weekend_queue/render_salt3_jin-%j.out
#SBATCH -e /scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/campaigns/2026-06-05_ethan_weekend_queue/render_salt3_jin-%j.err

set -euo pipefail
module load gcc/11.2.0 impi/19.0.9 paraview_osmesa/5.13.3
unset TACC_PARAVIEW_BIN
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
/usr/bin/python tools/extract/prepare_render_input.py --source-id viscosity_screening_salt_test_3_jin_coarse_mesh --format auto
/usr/bin/python tools/extract/render_field_figures.py --source-id viscosity_screening_salt_test_3_jin_coarse_mesh --backend paraview
