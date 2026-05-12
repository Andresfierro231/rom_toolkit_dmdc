# DMDc/ROM Command Guide

## Minimal workflows

- **First real-data pass:** `dmdc campaign --config studies/my_loop/study_config.toml --steps import inspect compare`
- **Live replay demo:** `dmdc campaign --config studies/my_loop/study_config.toml --steps live_replay_adapt dashboard operator_report`
- **Long archive pass:** `dmdc campaign --config studies/my_loop/study_config.toml --steps archive_run archive_summarize archive_schema dashboard`
- **HPC planning only:** `dmdc hpc-plan --config studies/my_loop/study_config.toml`

## One-command campaign workflow

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc campaign --config studies/my_loop/study_config.toml --steps import inspect compare dashboard` | Run selected workflow steps from one central config file. | campaign_plan.md, campaign_step_index.csv, next_steps.md, plus step outputs | `WORKFLOWS.md; docs/workflows/campaign_workflows.md` |
| `dmdc campaign --config studies/my_loop/study_config.toml --dry-run` | Preview folder locations and commands before running anything expensive. | A dry-run campaign plan and step index | `WORKFLOWS.md` |

## Connect current data

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc import-data --config studies/my_loop/study_config.toml` | Import CSV/Excel/folder/LabVIEW/EPICS-style data into a canonical table. | Canonical CSV/Parquet table | `docs/importers/README.md` |
| `dmdc inspect-data --config studies/my_loop/study_config.toml` | Inspect columns, missing values, case quality, and nonuniform/adaptive time steps. | inspection_summary.json, warnings.txt, case_quality_dashboard.csv | `docs/start_here_connect_your_data.md; docs/data_inspection_resampling.md` |

## Offline ROM analysis

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc compare --config studies/my_loop/study_config.toml` | Compare baselines, adaptive DMDc, DMDc, ridge DMDc, POD-DMDc, and optional POD-ML. | model_comparison.csv, stability dashboard, recommendation inputs | `docs/analysis_menu.md; docs/stability.md` |
| `dmdc sweep --config studies/my_loop/study_config.toml` | Sweep ranks/delays/models and evaluate on held-out cases. | sweep_results.csv, best_models.csv, plots, optional report | `docs/sweeps.md` |
| `dmdc report --run outputs/compare` | Create a LaTeX report from a run folder. | report.tex and optional report.pdf | `docs/dashboards_reports.md` |

## Model deployment

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc model-register --model outputs/best/model.pkl --name simple_loop_v1 --stage candidate` | Copy a validated model into the local registry with metadata. | models/registry/... and registry_index.csv | `docs/model_registry/README.md` |
| `dmdc model-promote --name simple_loop_v1 --version <VERSION> --stage production` | Promote a registered model for live use. | Deployment pointer used by live configs/dashboard | `docs/model_registry/README.md` |

## Live digital twin workflow

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc live-replay-adapt --config studies/my_loop/study_config.toml` | Replay historical data as if live, estimate state, forecast, monitor, and apply bounded bias correction. | live_forecasts.csv, alerts, trust score, bias logs | `docs/live/README.md; docs/live/adaptation_phase6.md` |
| `dmdc live-dashboard --config studies/my_loop/study_config.toml` | Open the operator dashboard for a run or archive. | Interactive Streamlit dashboard | `docs/live/dashboard_phase5.md; docs/dashboard/operator_presentation_mode.md` |
| `dmdc live-operator-report --config studies/my_loop/study_config.toml` | Generate a compact operator-facing HTML/Markdown report. | live_operator_report.html and summary JSON | `docs/live/operator_report.md` |

## Archive and long-term operations

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc archive-run --config studies/my_loop/study_config.toml` | Move live run outputs into a manifest-indexed archive. | live_archive/manifest.csv and partitioned data folders | `docs/live/archive_phase6_2.md` |
| `dmdc archive-summarize --config studies/my_loop/study_config.toml` | Create compact summary tables for long archives. | state/residual/trust/bias summary CSVs | `docs/live/summaries_quicklooks_phase6_3.md` |
| `dmdc validate-archive-schema --config studies/my_loop/study_config.toml` | Check archive structure and write human-readable context tables. | archive_schema_validation.md, archive_context_index.csv | `docs/archive/schema_validation.md` |

## Performance and execution planning

| Command | Purpose | Typical output | Docs |
|---|---|---|---|
| `dmdc benchmark-archive --n-rows 1000000 --n-states 32` | Measure archive write speed, summary speed, peak memory, and quicklook generation time. | benchmark_metrics.csv and benchmark_summary.json | `docs/benchmarks/archive_benchmarking.md` |
| `dmdc hpc-plan --config studies/my_loop/study_config.toml` | Write local runner scripts and FIXME Slurm templates. | run_local_campaign.sh and sbatch templates | `docs/hpc/batch_workflows.md` |
| `dmdc resources` | Print local CPU/memory/Slurm resource summary used by campaign planning. | JSON resource summary | `docs/hpc/README.md` |

## Recommended entrypoints

- Start with `WORKFLOWS.md` for one-command workflows.
- Use `examples/real_data_onboarding/` when connecting messy SAM/experimental data.
- Use `docs/navigation/choose_your_path.md` when you know the task but not the command.
