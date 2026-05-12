# HPC / Batch Workflow Planning

The default way to run this repo is still a local workstation. HPC is useful for
large offline sweeps, large archive summaries, and batch reports, but it should
not be required for day-to-day live operation.

## Local/HPC planning command

```bash
dmdc hpc-plan \
  --config configs/templates/central_campaign_config.toml \
  --outdir outputs/hpc_plan
```

This writes:

```text
outputs/hpc_plan/
├── hpc_command_plan.md
├── run_local_campaign.sh
├── run_campaign.sbatch.FIXME
├── run_archive_summarize.sbatch.FIXME
├── resource_summary.json
└── hpc_plan_summary.json
```

The Slurm files intentionally contain `FIXME` placeholders. Fill in account,
partition, module loads, walltime, and environment activation for your cluster.

## Config convention

```toml
[execution]
mode = "local"  # local is the default; hpc is planned/explicit
steps = ["import", "inspect", "compare", "archive"]
```

Future work:

- array jobs for rank/delay sweeps,
- archive summarization by date partitions,
- automatic resource estimates from input file sizes,
- TACC-specific templates with account placeholders.
