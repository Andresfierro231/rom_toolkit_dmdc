---
name: run-campaign
description: Use for reproducible dmdc campaign planning, model comparisons, validation studies, dry-run workflows, runtime tracking, and campaign reporting.
---

# Run campaign skill

## Goal

Create or execute a reproducible campaign with traceable inputs, outputs, metrics, and reports.

## Required artifacts

Each campaign should produce or update:

- `analysis/campaigns/<campaign_id>.yaml`
- `analysis/reports/<campaign_id>/MANIFEST.yaml`
- `analysis/reports/<campaign_id>/CHECKPOINT.md`
- `outputs/campaigns/<campaign_name>/campaign_plan.md` when `dmdc campaign` is used
- `outputs/campaigns/<campaign_name>/campaign_step_index.csv` when `dmdc campaign` is used
- `analysis/runtime_rows/<run_id>.json` and `analysis/runtimes_master.csv` when timed runs are performed

## Required behavior

- Prefer `dmdc campaign --dry-run` before expensive runs.
- Never claim a run succeeded unless output files or command results prove it.
- If only a plan was created, say only a plan was created.
- Preserve failure logs and summarize failure signatures.
- Use existing `dmdc` CLI commands and central TOML configs instead of replacing them with one-off scripts.
- Treat HPC mode and Slurm templates as planning-only unless the user explicitly provides a real execution environment.

## Output

A. Campaign purpose
B. Files inspected
C. Commands run or prepared
D. Outputs created
E. Validation metrics
F. Known failures
G. Report-ready conclusions
H. Next actions
