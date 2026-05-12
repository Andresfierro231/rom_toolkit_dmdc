# TODO: testing and roadmap

## Immediate additions completed in this revision

- Modular campaign runner with dry-run and selected steps.
- Local model registry and deployment stages.
- Archive schema validation and human-readable context CSVs.
- Resource summary helper for local/HPC planning.
- `.gitignore` for generated outputs, raw data, registry artifacts, and archives.

## High-priority next steps

1. Presentation-grade operator dashboard with loop schematic and sensors colored by residual.
2. Large-data benchmark command with peak memory, summary time, write MB/sec, and dashboard load time.
3. Model registry integration into best-model recommendations and sweep outputs.
4. More complete archive schema validators and migration helpers.
5. SAM-specific importer/folder scanner.

## Large-data tests still needed

- 1M / 10M / 100M row import and archive tests.
- Thousands of folder chunks.
- Parquet compression and partitioning tests.
- Summary generation timing and peak memory.
- Dashboard archive-mode timing.
- Interrupted archive-run recovery.

## Later phases

- Field-ready EPICS adapter.
- Field-ready LabVIEW/DAQ folder-drop adapter.
- HPC/batch workflows with completed site-specific Slurm scripts.
- Guarded RLS online adaptation, disabled by default.
- Advisory/control mode, documented as future only.

## Added follow-up items after operator dashboard and archive benchmark layer

### Presentation dashboard hardening
- Test operator schematic with real residuals and actual loop geometry.
- Add a richer loop schematic if/when a 2D drawing of the loop is available.
- Add screenshot/export helper for meetings.
- Validate dashboard load time with large archive summaries.

### Large-data benchmark roadmap
- Run `dmdc benchmark-archive` at 1M, 10M, and 100M rows on the target workstation.
- Record archive write MB/sec, summary rows/sec, peak memory, and dashboard load time.
- Compare CSV vs Parquet+zstd once `pyarrow` is installed.
- Stress test many small partitions and interrupted archive writes.

### Field adapter roadmap
- EPICS: test PV connectivity and timestamp behavior on the real control network.
- EPICS: add monitor/callback adapter after PV names and update rates are known.
- LabVIEW/DAQ: test partial-file and folder-drop behavior once real logger files exist.
- LabVIEW/DAQ: add vendor-specific metadata parsing when file headers/sidecars are known.

### HPC/batch roadmap
- Fill in `scripts/slurm/*.template` with site-specific account/module details.
- Add cluster-specific docs after account, partition, modules, and scratch paths are known.
- Add batch sweeps and archive summarization jobs after local workflows are validated.

### Future advisory/control mode
- Keep current repo read-only/advisory.
- Document advisory recommendations only after live monitoring and validation are trusted.
- Do not connect to hardware actuation in this repo without independent safety systems.


## Test hardening added in latest pass

The test suite now includes additional coverage for:

- source-tree CLI subprocess robustness via `tests/conftest.py`;
- central campaign dry-run workflows;
- importer edge cases such as corrupt CSV chunks, LabVIEW/DAQ folder mapping, and partial/empty files;
- archive schema validation, including relative manifest paths and missing archived files;
- operator dashboard residual color/status logic;
- bias-correction guardrails for low trust and critical alerts;
- model registry deployment identity and HPC/local planning scaffolds;
- mathematical consistency checks for DMDc, POD, adaptive DMDc, Kalman filtering, and regularized DMDc;
- archive benchmark metrics fields;
- opt-in large benchmark smoke tests marked with `@pytest.mark.large`.

Run normal tests with:

```bash
pytest
```

Run opt-in large benchmark tests with:

```bash
pytest -m large
```

---

## Pre-GitHub / first alpha release checklist

Before turning this into a real GitHub repository or sharing it as an internal alpha, complete this release-readiness checklist.

```text
[ ] Fresh install works from a clean virtual environment.
[ ] Full default test suite passes with `pytest`.
[ ] Optional extras install: `.[ml,dashboard,excel,parquet]`.
[ ] `dmdc --help` works.
[ ] `dmdc guide` works.
[ ] `dmdc campaign --config configs/templates/one_command_local_workflow.toml --dry-run` works.
[ ] No private, raw, generated, or large files are staged for commit.
[ ] `find . -type f -size +20M` has been reviewed.
[ ] `du -sh *` has been reviewed.
[ ] README top section clearly explains purpose, installation, first commands, outputs, and limitations.
[ ] LICENSE is present.
[ ] CITATION.cff is present.
[ ] Version is set for the first alpha release.
[ ] GitHub Actions workflow exists and passes after push.
[ ] Known limitations are documented in README and `docs/known_limitations.md`.
[ ] One end-to-end demo works using the thermal-loop example.
[ ] Operator dashboard opens in presentation/operator view.
[ ] Optional dashboard screenshots are added only if they are non-sensitive.
[ ] First tag is created, for example `v0.1.0-alpha`.
```

Suggested alpha release description:

> A research-grade ROM and live monitoring toolkit for DMD/DMDc/POD workflows, with live replay, dashboarding, archive support, and model registry scaffolding. Not yet field-validated on live hardware.

Recommended clean-install check:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest

dmdc --help
dmdc guide
```

Recommended optional-extras check:

```bash
python -m pip install -e ".[ml,dashboard,excel,parquet]"
dmdc live-dashboard --help
```

Recommended file-safety check before first commit:

```bash
find . -type f -size +20M
find . -type f | grep -E "(outputs|live_archive|models/registry|data/raw|data/private|data/processed)"
du -sh *
```

Do not commit raw data, generated outputs, live archives, model registry artifacts, private configs, or large binary files unless they are tiny intentional examples.
