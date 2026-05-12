# Test Hardening Pass

This pass adds tests that focus on the parts of the repo most likely to fail when the toolkit is used on real data or deployed as a live monitoring workflow.

## What was added

The new hardening tests cover:

- **CLI/source-tree robustness**: subprocess-based `python -m dmdc.cli ...` calls work before an editable install by setting `PYTHONPATH=src` in `tests/conftest.py`.
- **Central config/campaign workflows**: dry-run campaigns with selected steps write a plan, step index, and next-step prompts.
- **Importer edge cases**: folder imports skip corrupt chunks, LabVIEW/DAQ-style imports infer case IDs from filenames, column maps are applied, and empty/partial files are detected.
- **Archive schema validation**: relative manifest paths are validated relative to the archive root, and missing archived files are reported as schema failures.
- **Operator dashboard logic**: residual magnitudes map to green/yellow/red/gray statuses, including missing residuals and partial geometry files.
- **Bias-correction safeguards**: low-trust periods and critical alerts block bias updates; update steps and absolute bias are clipped.
- **Model registry and deployment**: registering, promoting, resolving, and writing model identity metadata are covered.
- **Local/HPC planning scaffolds**: the local-first plan and Slurm `FIXME` placeholders are checked.
- **Mathematical consistency**: DMDc recovers known `A, B`; POD error decreases with rank; adaptive DMDc recovers a nonuniform-time continuous slope; Kalman filtering reduces measurement noise; regularized DMDc shrinks ill-conditioned operators.
- **Archive benchmark metrics**: benchmark outputs include write throughput, summary rate, peak memory, and timing fields.

## How to run

Normal unit/smoke tests:

```bash
pytest
```

Hardening tests only:

```bash
pytest tests/test_hardening_*.py
```

Opt-in larger benchmark plumbing test:

```bash
pytest -m large
```

The default pytest configuration excludes tests marked `large` so routine CI stays fast.
