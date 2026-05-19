# Checkpoint — 2026-05-18_workflow_adaptation_smoke_test

Generated: 2026-05-18T12:05:38-05:00

## Research question

Tailor the Codex research workflow to this repository.

## Repository state

- Branch: `main`
- Commit: `007e798`
- Dirty working tree: `True`

## Files inspected / inputs

- README.md
- WORKFLOWS.md
- COMMANDS.md
- pyproject.toml
- `docs/workflows/README.md`
- `docs/workflows/campaign_workflows.md`
- `docs/navigation/workflow_map.md`
- `configs/templates/central_campaign_config.toml`
- `configs/templates/central_study_config.toml`
- `configs/templates/one_command_local_workflow.toml`
- `examples/real_data_onboarding/README.md`
- `examples/real_data_onboarding/study_config.toml`
- `scripts/workflows/run_campaign_local.sh`
- `src/dmdc/cli.py`
- `src/dmdc/campaign.py`
- `outputs/campaigns/local_rom_campaign/campaign_plan.md`
- `outputs/campaigns/local_rom_campaign/campaign_step_index.csv`

## Validation or reference data

- `data/example_timeseries.csv`
- `data/example_multicase_timeseries.csv`
- `examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv`

## Commands recorded

- python -m pip install -r requirements-codex-tools.txt
- python -m py_compile $(find tools -name "*.py")
- `python tools/studies/init_campaign.py --name workflow_adaptation_smoke_test --question "Tailor the Codex research workflow to this repository."`
- `.venv/bin/python -m dmdc.cli campaign --config configs/templates/one_command_local_workflow.toml --dry-run --steps inspect compare`
- `python tools/provenance/collect_git_state.py --format yaml`

## Scripts used

- `tools/studies/init_campaign.py`
- `tools/provenance/collect_git_state.py`
- `tools/reporting/make_checkpoint.py`
- `src/dmdc/campaign.py`
- `scripts/workflows/run_campaign_local.sh`

## Outputs generated

### Reports

- `analysis/reports/2026-05-18_workflow_adaptation_smoke_test/CHECKPOINT.md`
- `analysis/reports/2026-05-18_workflow_adaptation_smoke_test/CHANGELOG.md`
- `analysis/reports/2026-05-18_workflow_adaptation_smoke_test/EXECUTIVE_SUMMARY.md`
- `analysis/reports/2026-05-18_workflow_adaptation_smoke_test/TECHNICAL_REPORT.md`

### Figures

- None recorded.

### Tables

- None recorded.

## Key numerical results

Not yet summarized. Add metrics here or update `MANIFEST.yaml.metrics`.

## Interpretation

Not yet written. Distinguish observed results from interpretation.

## Limitations

- The `.agents` directory is mounted read-only inside the sandbox, so syncing repo-specific skill metadata required elevated writes outside the sandbox.
- `The root `tools/` entrypoints are thin wrappers around `.agents/tools/`; if the `.agents` starter content is removed, those wrappers will need to be repointed or the generic scripts copied into root `tools/`.`
- `The `dmdc campaign --dry-run` smoke test emitted a Matplotlib config-directory warning because the default `~/.config/matplotlib` path is not writable in this environment.`
- `python -m pip install -r requirements-codex-tools.txt` targeted the user site-packages path, not the repo `.venv`.

## Missing information

Add missing files, failed runs, or incomplete provenance here.

## Next actions

- `Copy `examples/real_data_onboarding/` or a template config into `studies/<study>/` and run `dmdc campaign --config studies/<study>/study_config.toml --dry-run`.`
- Set `MPLCONFIGDIR` to a writable path when running plotting or dashboard-related commands in restricted environments.
- `Decide whether to keep the starter workflow delegated through `.agents/` or promote the generic helper scripts fully into root `tools/`.`

## Exact files future agents should inspect first

- `analysis/reports/2026-05-18_workflow_adaptation_smoke_test/MANIFEST.yaml`
- This checkpoint file
- Campaign config listed in the manifest
- Figure/table manifests under the report directory, if present
