# Workflow Documentation

This folder explains how to run the repo as a set of modular workflows instead of isolated commands.

Start with:

```text
../../WORKFLOWS.md
campaign_workflows.md
../navigation/workflow_map.md
../navigation/command_index.md
```

The main rule is simple:

```bash
dmdc campaign --config study_config.toml --steps import inspect compare
```

Change the `--steps` list depending on what you need.  The central config can contain many sections, but only the selected commands read the relevant sections.
