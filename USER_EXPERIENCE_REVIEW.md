# Final User Experience Review

This repo has been organized around a few user-facing principles.

## 1. One central config, many modular commands

Use one TOML file as the study contract.  Run only the pieces needed with:

```bash
dmdc campaign --config study_config.toml --steps import inspect compare
```

The campaign runner writes `campaign_plan.md`, `campaign_step_index.csv`, and `next_steps.md` so users always know where outputs went and what to inspect next.

## 2. Command discovery is explicit

Use:

```bash
dmdc guide
```

or read:

```text
COMMANDS.md
WORKFLOWS.md
docs/navigation/workflow_map.md
```

## 3. Local workstation first

The default execution mode is local.  HPC/Slurm files are generated as planning templates with `FIXME` fields and should not be treated as ready-to-submit scripts.

## 4. Nonuniform/adaptive time is expected

Real loop and SAM data often have nonuniform time steps.  The docs and workflows recommend inspection first, then `adaptive_dmdc` or explicit resampling only when truly needed.

## 5. Live mode is advisory

The live pipeline reads, estimates, forecasts, monitors, archives, reports, and visualizes.  It does not control hardware and does not replace safety systems.

## 6. Archives are summary-first

For long runs, users should inspect summaries, quicklooks, manifest, and context tables before opening raw partitions.

## Suggested final smoke test for a new user

```bash
dmdc guide
dmdc campaign --config configs/templates/one_command_local_workflow.toml --dry-run
dmdc resources
dmdc benchmark-archive --n-rows 1000 --n-states 4 --format csv --no-quicklooks
```
