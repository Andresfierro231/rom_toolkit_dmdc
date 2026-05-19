---
name: repo-archaeology
description: Use when asked to understand, modify, adapt, or extend this repository. Inspect the dmdc CLI workflow, config templates, example studies, outputs, and conventions before editing.
---

# Repo archaeology skill

## Goal

Build a grounded understanding of the current repository before editing.

## Required steps

1. Record current working directory, git branch, commit, and git status.
2. Inspect `README.md`, `WORKFLOWS.md`, `COMMANDS.md`, `docs/workflows/`, and `docs/navigation/`.
3. Inspect `configs/templates/`, `examples/real_data_onboarding/`, `scripts/workflows/run_campaign_local.sh`, and `src/dmdc/campaign.py`.
4. Identify the sources of truth for study configs, campaign plans, dry-run outputs, validation outputs, reports, dashboards, and archive summaries.
5. Distinguish active workflow paths from planning-only artifacts such as Slurm templates.
6. Summarize active workflow, legacy or secondary wrappers, extension points, risks, and ambiguities before editing.

## Output

A. Repository understanding
B. Existing workflow map
C. Relevant files inspected
D. Risks and ambiguities
E. Recommended modification plan
