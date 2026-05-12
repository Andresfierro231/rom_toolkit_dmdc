# HPC / batch workflow plan

Local workstation execution is the default. HPC support is planned as an opt-in
layer for large sweeps, archive summaries, and report generation.

Templates are provided under:

```text
scripts/slurm/run_campaign.sbatch.template
scripts/slurm/run_archive_summarize.sbatch.template
```

They are intentionally incomplete because account, partition, module, and
filesystem details are site-specific. Fill in the `FIXME` lines before use.

Future HPC work:

- campaign submission wrappers
- array jobs for rank/delay sweeps
- archive summary jobs for large partitioned archives
- resource-aware local vs HPC execution planner
- TACC-specific examples with placeholders
