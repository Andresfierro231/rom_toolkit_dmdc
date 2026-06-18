# Ethan Modeling Assumptions Import Note

Date: `2026-06-10`

This note mirrors the analysis-side provenance for the consolidated Ethan CFD
methods support package prepared for manuscript use.

## Imported support package

- Analysis checkpoint:
  [CHECKPOINT.md](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/CHECKPOINT.md:1)
- Consolidated dossier:
  [ETHAN_MODELING_ASSUMPTIONS_DOSSIER.md](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ETHAN_MODELING_ASSUMPTIONS_DOSSIER.md:1)
- Compact case matrix:
  [ethan_case_assumption_matrix.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ethan_case_assumption_matrix.csv:1)

## Coverage statement

This package documents the paper-relevant Ethan CFD evidence set currently
indexed in the June 4 metadata package and linked validation notes. It does not
yet claim a complete normalized methods registry for every historical directory
under `ethan_runs/`.

Current compact matrix coverage:

- `13` indexed case rows
- salt validation and viscosity-screening cases in the June 4 package
- water/salt comparison rows already represented in the case metadata index

## Paper-safe claims supported by this package

- Runtime family: `OpenFOAM 13`
- Driver declaration in inspected control files: `application foamRun`
- Solver path declared in inspected control files: `solver fluid`
- Main solved fields evidenced in the current representative control files:
  `p_rgh`, `U`, and `h`
- Current indexed representative cases are laminar in the metadata package
- Wall-loss treatment is patchwise and combines layered external wall treatment
  with fixed-loss surrogate boundaries
- Fluid-property closures and key coefficients are documented in the per-case
  metadata index and raw `case_config.yaml` files
- Common runtime settings such as `nprocs`, `walltime`, `scale_to_meters`,
  `ncc_couples`, and convergence controls are documented for the modern-runs
  source inventory

## Remaining gap before a final manuscript appendix

- If the paper needs a claim about the entire historical `ethan_runs` tree,
  someone still needs to extend the same extraction process to every run family
  not represented in the June 4 index.
- If the paper needs equation-level derivations or solver discretization detail,
  that should live in a separate numerical-methods appendix rather than this
  provenance note.
