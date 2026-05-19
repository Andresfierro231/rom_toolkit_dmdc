# Codex Research Workflow Starter Kit

Drop these files into the root of a research/code repository to give Codex a reproducible analysis workflow.

## What this kit does

- Gives Codex durable repo rules through `AGENTS.md`.
- Provides reusable skills under `.agents/skills/`.
- Adds small Python tools for provenance, campaign scaffolding, runtime rows, manifests, checkpoints, journal entries, tables, and figure manifests.
- Creates a standard `analysis/` structure for report-ready work.

## First command after copying into a repo

```bash
python tools/studies/init_campaign.py \
  --name workflow_adaptation_smoke_test \
  --question "Tailor the Codex research workflow to this repository."
```

Then give Codex this prompt:

```text
Use docs/workflows/codex_repo_adaptation_prompt.md and tailor this workflow to the current repository.
```

## Optional dependency

The tools work best with PyYAML:

```bash
python -m pip install -r requirements-codex-tools.txt
```
