# Checkpoint — 2026-06-10_ethan_modeling_assumptions_dossier

## Date and campaign/task name

- Date: `2026-06-10`
- Task: determine whether Ethan CFD modeling assumptions are already documented
  well enough for paper use and create a consolidated paper-support dossier if
  not.

## Research question

Do the current `ethan_runs` workspaces already document, in a durable and
 paper-usable way:

- the solver stack and runtime,
- what fields are actually being solved,
- boundary-condition and property assumptions,
- per-case setup inputs,
- and the provenance needed to cite those claims in an academic paper?

## Repository state

- Analysis repo branch: `main`
- Analysis repo commit: `1808fa8abeaf035a26174334b803f9e725e5352b`
- Analysis repo dirty working tree: `True`

## Source files inspected

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/AGENTS.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-02_openfoam13_runtime_source.json`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/registry/case_registry.csv`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/controlDict`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/fvSolution`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/2026-06-04_ethan_cfd_dossier.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/2026-06-04_ethan_direct_validation_README.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/2026-06-04_ethan_section_transport_package_README.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/scientific_numerical_analysis.md`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/09_ethan_numerical_setup.tex`

## Commands run

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/AGENTS.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/README.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/2026-06-04_ethan_cfd_dossier.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/README.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md
head -5 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/2026-06-04_ethan_direct_validation_README.md
sed -n '1,240p' /scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/2026-06-04_ethan_section_transport_package_README.md
sed -n '1,260p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_transient_axial_package/scientific_writeup_notes.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/imports/2026-06-02_openfoam13_runtime_source.json
head -5 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/registry/case_registry.csv
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/modern_runs/2026-06-01_source_inventory/README.md
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/controlDict
sed -n '1,220p' /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/fvSolution
python3.11 - <<'PY'
... csv extraction of a compact per-case assumptions matrix ...
PY
```

## Inputs used

- Existing Ethan report packages and manuscript-imported support notes
- Raw case configuration and OpenFOAM control files for the Salt 2 continuation
- The June 4 expanded case metadata index as the main structured source

## Outputs generated

- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/CHECKPOINT.md`
- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ETHAN_MODELING_ASSUMPTIONS_DOSSIER.md`
- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ethan_case_assumption_matrix.csv`
- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/MANUSCRIPT_IMPORT_NOTE.md`

## Key numerical results

- Rows extracted into the compact case-assumption matrix: `13`
- Common readable modern-runs setup values called out in the source inventory:
  - `nprocs = 64`
  - `walltime = 120:00:00`
  - `scale_to_meters = 0.001`
  - `ncc_couples = 10`
  - convergence `check_interval = 100`
  - convergence `min_iterations = 500`
  - convergence QoI `rtol = 1e-4`
  - convergence QoI window `100`

## Plots/tables generated

- `ethan_case_assumption_matrix.csv`: compact per-case matrix for paper support

## Interpretation

Yes, substantial Ethan modeling documentation already exists. The strongest
existing source is the June 4 case metadata index, which already captures
per-case setup inputs, property-model summaries, wall-loss treatment,
radiation-like treatment, convergence settings, runtime status, and linked
validation metrics.

However, that material was fragmented across:

- the metadata-index report,
- report-package READMEs,
- raw `case_config.yaml`,
- raw OpenFOAM `controlDict` and `fvSolution`,
- manuscript notes and imported support notes.

So the answer is:

- documentation exists, but
- not yet as one consolidated paper-ready dossier.

This checkpoint closes that gap by creating a single dossier plus a compact
per-case assumptions matrix inside `dmdc-analysis`.

Coverage clarification:

- this package is strong for the currently indexed paper-relevant Ethan cases;
- it is not yet a claim that every historical run family under `ethan_runs/`
  has already been normalized into the same methods-ready registry.

## Limitations

- The dossier is built from existing case metadata and representative solver
  files; it does not audit the full OpenFOAM source code or every auxiliary
  boundary-condition implementation.
- The explicit ``what is solved'' statement is grounded in representative
  `controlDict` and `fvSolution` files and the manuscript numerical-setup note,
  not yet in a dedicated solver-code appendix.
- The matrix covers the 13 currently indexed Ethan rows, which is the current
  structured manuscript evidence set, not every conceivable inaccessible or
  unindexed external case.

## Bugs or anomalies

- None encountered during this documentation pass.

## Follow-up tasks

1. Mirror the new dossier into the manuscript workspace as a paper note or
   appendix source. A manuscript-facing import note now exists in this report
   directory but has not yet been copied into the paper repo.
2. If the paper needs direct equation-level language, add a short appendix that
   translates the OpenFOAM setup into manuscript math and cites the governing
   fields `p_rgh`, `U`, and `h`.
3. If broader water or turbulence campaigns are to be discussed, extend the
   case-assumption matrix beyond the current indexed evidence set.

## Exact files future agents should inspect first

- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ETHAN_MODELING_ASSUMPTIONS_DOSSIER.md`
- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ethan_case_assumption_matrix.csv`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/controlDict`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/fvSolution`

## Missing information

- No dedicated manuscript appendix yet restates the governing equations and
  closure assumptions in purely paper-facing language.
- No single current note fully documents the implementation details of
  `libRCWallBC.so`; only its use and parsed boundary settings are currently
  documented here.
