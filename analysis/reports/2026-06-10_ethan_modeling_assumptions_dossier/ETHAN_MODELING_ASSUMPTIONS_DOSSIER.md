# Ethan Modeling Assumptions Dossier

Date: `2026-06-10`

## Short answer

Yes, much of the Ethan CFD modeling documentation already exists, but it was
not previously assembled into one paper-ready source.

For precision: this dossier covers the paper-relevant Ethan CFD evidence set
that is already indexed in the June 4 metadata package and linked validation
notes. It should not be read as a claim that every historical directory under
`ethan_runs/` has already been normalized into the same level of methods
documentation.

The main existing sources are:

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- raw case files such as:
  - `case_config.yaml`
  - `system/controlDict`
  - `system/fvSolution`
- imported manuscript-side support notes under:
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/imported_ethan_support/`

The main gap was the lack of one consolidated paper-support document that says,
in one place:

- what solver/runtime is being used,
- what fields are actually solved,
- what the wall-loss and property assumptions are,
- which assumptions vary by case,
- and where those facts come from.

This dossier is that consolidated source.

## Coverage

This dossier is strongest for the currently indexed representative and
validation-linked cases that appear in:

- `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`

The compact assumption matrix created for this checkpoint contains `13`
paper-facing case rows plus the header row, covering the current set of indexed
salt and water comparison cases.

What this means in practice:

- for the paper-relevant representative cases, the core modeling assumptions
  now exist in one consolidated support package;
- for the entire historical `ethan_runs/` tree, a full all-runs normalized
  methods registry still does not exist as one finished manuscript appendix.

## What already existed

### 1. Per-case structured assumptions

The strongest existing source is the June 4 case metadata index:

- `.../ethan_case_metadata_index.csv`
- `.../ethan_case_metadata_index.json`
- `.../README.md`

It already records, per case:

- case identity and provenance
- fluid and turbulence model labels
- heater power, cooling power, and initial temperature
- MPI rank count and walltime
- geometry and mesh metadata
- external wall-loss coefficients and ambient temperatures
- parsed insulation thickness
- radiation-like boundary-condition summary
- viscosity, conductivity, heat-capacity, and density model summaries
- convergence-monitor settings
- runtime state and validation metrics
- a long-form `assumption_note`

### 2. Raw solver-side setup files

Representative case files confirm the metadata index is tied to the actual run
setup:

- `case_config.yaml` documents:
  - operating point
  - boundary-condition parameters
  - mesh settings
  - convergence settings
  - fluid-property coefficients
  - `nprocs`
  - `walltime`
- `system/controlDict` documents:
  - OpenFOAM version banner
  - `application foamRun`
  - `solver fluid`
  - adaptive time-step controls
  - linked runtime library `libRCWallBC.so`
- `system/fvSolution` documents:
  - solution of `p_rgh`
  - solution of `U`
  - solution of `h`
  - PIMPLE settings
  - residual controls
  - pressure reference point

### 3. Scientific interpretation packages

Additional report-package READMEs already explain:

- direct validation metrics and how they are constructed
- the ambient-loss proxy definition
- section-transport and pressure-drop interpretation
- axial/transient limitations
- representative-case selection logic

These are useful for the paper, but they are downstream interpretation layers,
not the primary setup dossier.

## What did not yet exist

Before this pass, there was no single document that combined:

- solver/runtime identity,
- solved fields,
- closure and boundary assumptions,
- per-case input values,
- and case-by-case setup differences

into one artifact designed for manuscript support.

That is why the new compact matrix was generated:

- `analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ethan_case_assumption_matrix.csv`

## Solver and runtime statement

From the inspected representative Salt 2 continuation case:

- runtime family: `OpenFOAM 13`
- application entrypoint: `foamRun`
- solver selector in `controlDict`: `fluid`
- linked runtime library: `libRCWallBC.so`
- time stepping:
  - `adjustTimeStep yes`
  - `deltaT 0.01`
  - `maxCo 1`
  - `maxDeltaT 1.0`
- output control:
  - `writeControl adjustableRunTime`
  - `writeInterval 1`
  - `purgeWrite 5`

The inspected `fvSolution` shows the main solved field families explicitly:

- `p_rgh`
- `U`
- `h`
- `rho.*` as diagonal solves

The generic regular-expression blocks also mention turbulence quantities such as
`k`, `omega`, `epsilon`, `gammaInt`, and `ReThetat`, but the currently indexed
manuscript cases in the matrix are labeled `laminar`. For the present paper
evidence set, the safe statement is that the active representative cases are
laminar OpenFOAM thermal-loop runs using the `fluid` solver path with
pressure-like field `p_rgh`, velocity `U`, and enthalpy `h` in the main solve
stack.

## Common setup across the modern-runs evidence set

The June 1 source inventory identifies several assumptions that are shared
across the readable modern-runs batch:

- `nprocs = 64`
- `walltime = 120:00:00`
- `scale_to_meters = 0.001`
- `ncc_couples = 10`
- convergence enabled
- convergence check interval `100`
- minimum iterations `500`
- QoI relative tolerance `1e-4`
- QoI window `100`

These values are consistent with the per-case metadata matrix for the currently
indexed evidence rows.

## Boundary-condition and loss-model assumptions

The consistent wall-loss interpretation across the current evidence set is:

- patchwise `rcExternalTemperature` layered walls
- `externalTemperature` fixed-loss surrogates on some regions
- radiation-like exchange encoded through `Tsur` and emissivity terms in the
  3D wall model
- parsed emissivity entries documented as `0.95` in the metadata summaries

For paper use, the safe wording is:

`The current 3D Ethan cases use patchwise external thermal boundary conditions
with layered wall-loss treatment and radiation-like exchange embedded in the
wall BC configuration, rather than a single uniform whole-loop loss coefficient.`

## Property-model assumptions

### Salt-family cases

The current salt cases share:

- conductivity as a polynomial model
- heat capacity effectively constant at `Cp = 1423.47 J/kg-K`
- density represented by a coefficient array whose leading active terms are
  summarized as `[2293.6, -0.7497]`

The main salt-family difference is viscosity branch:

- Jin:
  - `expInvT`
  - coefficients `[0.001149, -810.896, 780600]`
- Kirst:
  - `expInvT`
  - coefficients `[6.757e-05, 2247.11]`

### Water-family cases

The current water validation rows in the indexed evidence set are also labeled
`laminar`, but their property models differ from the salt cases:

- viscosity: polynomial
- conductivity: polynomial
- heat capacity: polynomial coefficient array
- density: polynomial coefficient array

The compact case matrix preserves the per-case parameter summaries for these
water rows.

## Case-varying inputs that matter scientifically

The main case-varying inputs documented in the current index are:

- `heater_power_W`
- `cooling_power_W`
- `T_init_K`
- `cooler_h_W_m2K`
- parsed outer insulation thickness
- Jin versus Kirst viscosity branch
- run status and whether coded convergence was reached

Examples already visible in the current matrix:

- the native Salt 2 continuation carries thicker parsed outer insulation
  (`1.65 in`) than the staged Jin/Kirst Salt 2 screening rows (`1.40 in`)
- the water validation rows carry much larger cooler-side `h` values than the
  current salt cases

## What the paper can now cite safely

The paper can now cite this dossier and the compact matrix for claims about:

- OpenFOAM-based runtime family and solver path
- main solved fields `p_rgh`, `U`, and `h`
- laminar designation of the current representative evidence set
- patchwise wall-loss and radiation-like boundary treatment
- per-case heater duty, cooler duty, initial temperature, and wall coefficients
- Jin versus Kirst property-branch differences
- common convergence-monitor settings across the modern-runs batch

## What is still not fully documented

Two things are still weaker than a final paper appendix should ideally be:

1. Governing-equation exposition in paper language.
   The raw OpenFOAM setup is documented, but the manuscript still does not have
   a self-contained appendix that restates the governing equations and closures
   in academic prose.

2. `libRCWallBC.so` implementation semantics.
   Its use is clearly documented in the runtime setup and metadata summaries,
   but this dossier does not yet audit the boundary-condition implementation
   source code itself.

## Recommended paper use

For an academic paper, the cleanest path is:

1. Treat this dossier as the analysis-side source note.
2. Use `ethan_case_assumption_matrix.csv` as the source for a manuscript table
   or appendix table.
3. Add a short manuscript appendix section that restates:
   - runtime family,
   - solved fields,
   - convergence monitor,
   - wall-loss treatment,
   - salt and water property models,
   - case-varying setup differences.

## Primary support artifacts

- [ethan_case_assumption_matrix.csv](/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis/analysis/reports/2026-06-10_ethan_modeling_assumptions_dossier/ethan_case_assumption_matrix.csv)
- [/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/README.md)
- [/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv)
- [/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml)
- [/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/controlDict](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/controlDict)
- [/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/fvSolution](/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/system/fvSolution)
