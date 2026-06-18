# Overnight follow-up — 2026-06-01

This queue prepares the next defensible overnight runs after the repaired
JSALT2 autonomous/no-h campaign completed locally on 2026-05-26.

## Jobs prepared

| Order | Job name | Script | Purpose | Expected main outputs |
| --- | --- | --- | --- | --- |
| 1 | `dmdc_swno_r` | `jobs/jsalt2_sweep_no_h_repaired.sbatch` | Re-run the no-`h` JSALT2 sweep from the repaired autonomous campaign import. | `outputs/overnight_sweeps/jsalt2_no_h_repaired_20260601/` |
| 2 | `dmdc_swph_r` | `jobs/jsalt2_sweep_with_h_pair.sbatch` | Run a matching with-`h` sweep pair for comparison against the repaired no-`h` sweep. | `outputs/overnight_sweeps/jsalt2_with_h_pair_20260601/` |
| 3 | `dmdc_pytestr` | `jobs/full_pytest_regression.sbatch` | Run the full pytest suite as an overnight guardrail on the current dirty tree. | Slurm logs under `analysis/campaigns/2026-06-01_overnight_jsalt2_followup/logs/` |

## Notes

- The repaired no-`h` input is `outputs/campaigns/jsalt2_moose_mesh_convergence_autonomous_no_h/run_20260526T133003Z_5943a549/workflow_outputs/import/jsalt2_moose_mesh_convergence_autonomous_no_h.parquet`.
- The comparison with-`h` input remains `outputs/campaigns/jsalt2_moose_mesh_convergence_poc/run_20260525T230237Z_0842b2f6/workflow_outputs/import/jsalt2_moose_mesh_convergence_poc.parquet`.
- The scripts use absolute Slurm log paths so the repo-visible `logs/` directory should capture stdout and stderr.
