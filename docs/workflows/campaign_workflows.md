# Modular campaign workflows

A campaign is a repeatable study driven by one central config file. It is meant
for the real workflow where you do **not** run every analysis step every time.

Typical dry-run:

```bash
dmdc campaign --config configs/templates/central_campaign_config.toml --dry-run
```

Run selected steps only:

```bash
dmdc campaign --config studies/simple_loop/study_config.toml --steps inspect compare dashboard
```

The campaign runner writes:

- `campaign_plan.md` — commands and output folders for each step.
- `campaign_step_index.csv` — machine-readable step status.
- `next_steps.md` — plain-English suggestions after each step.
- `resource_summary.json` — local/HPC resource snapshot.

Local workstation execution is the default. Setting `[execution].mode = "hpc"`
currently writes a plan only. Edit `scripts/slurm/*.sbatch.template` with your
account, partition, and environment before using HPC submission manually.
