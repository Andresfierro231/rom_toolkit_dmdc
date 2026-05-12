# HPC / batch workflow plan

This repo is currently workstation-friendly, but the offline workflows should eventually support HPC/batch execution for large SAM sweeps.

Planned additions:

```text
scripts/slurm/run_sweep.sbatch
scripts/slurm/archive_summarize.sbatch
configs/templates/hpc_rank_delay_sweep.toml
configs/templates/hpc_archive_summary.toml
```

Use cases:

- rank/delay/model sweeps over thousands of SAM cases;
- archive summaries over partitioned long-running live data;
- generating reports and dashboards from HPC outputs without loading raw TB-scale data.

The design should remain config-first: local workstation and HPC jobs should use the same TOML files where possible.
