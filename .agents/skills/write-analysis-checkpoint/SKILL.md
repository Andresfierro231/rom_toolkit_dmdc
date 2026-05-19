---
name: write-analysis-checkpoint
description: Use when asked to summarize recent dmdc analysis, record a campaign dry-run, preserve context, or prepare future agents for continuation.
---

# Write analysis checkpoint skill

## Goal

Write a durable checkpoint that future agents can use without guessing.

## Required sections

1. Date and campaign/task name
2. Research question
3. Repository state
4. Source files inspected
5. Commands run
6. Inputs used
7. Outputs generated
8. Key numerical results
9. Plots/tables generated
10. Interpretation
11. Limitations
12. Bugs or anomalies
13. Follow-up tasks
14. Exact files future agents should inspect first

## Rules

- Include file paths.
- Include `outputs/campaigns/<campaign_name>/campaign_plan.md` and `campaign_step_index.csv` when they exist.
- Include `outputs/.../report/report.tex` paths when reports are generated.
- Include git branch and commit if available.
- Distinguish measured results from interpretation.
- Do not invent missing values.
- If information is missing, add a `Missing information` section.
