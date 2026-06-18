# Codex Research Workflow Starter Kit

This repository keeps the agent-facing workflow assets under `.agents/` and
exposes the reusable command-line entrypoints through root `tools/` wrappers.

## Canonical organization

| Path | Role | Notes |
|---|---|---|
| `.agents/skills/` | Codex skill instructions | Skill discovery should treat this as canonical. |
| `.agents/tools/` | Canonical research/provenance/reporting utilities | Root `tools/` delegates here one-to-one. |
| `.agents/docs/workflows/` | Agent-specific workflow contracts and prompts | These support repo adaptation and reporting norms. |
| `tools/` | Human-facing wrapper entrypoints | Do not duplicate logic here; keep them as thin delegates. |
| `analysis/` | Generated provenance records and report artifacts | Campaign YAMLs, manifests, checkpoints, figures, and tables live here. |

## Main rule

Do not replace the repository's active modeling workflow with custom agent
scripts. The active workflow stays in the repo's own runtime surface:

- `src/dmdc/`
- `configs/templates/`
- `examples/real_data_onboarding/`
- `scripts/workflows/`

The `.agents/` layer is for durable instructions, provenance tools, and report
artifacts around that workflow.

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
