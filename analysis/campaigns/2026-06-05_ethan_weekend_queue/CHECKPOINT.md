# Checkpoint — 2026-06-05_ethan_weekend_queue

Generated: `2026-06-05`

## Date and campaign/task name

- Date: `2026-06-05`
- Task: submit weekend Ethan continuation and lightweight follow-on jobs, then write a durable handoff with next-week TODOs.

## Research question

Which Ethan jobs are worth keeping alive over the weekend, which lightweight static jobs are worth queuing in parallel, and what exact follow-up should happen next week once those jobs move?

## Repository state

- Branch: `main`
- Commit before this checkpoint: `93d9e59391f1ce8de3472d55f1e316723e976998`
- Dirty working tree before commit: `True`

## Source files inspected

Repo-side:
- `README.md`
- `WORKFLOWS.md`
- `COMMANDS.md`
- `docs/navigation/workflow_map.md`
- `docs/workflows/README.md`
- `tools/ethan_zero_advance_transport.py`
- `analysis/reports/2026-06-05_ethan_representative8_postprocess/representative_8_postprocess_summary.csv`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/TECHNICAL_REPORT.md`
- `analysis/reports/2026-06-05_ethan_zero_advance_transport_phase1_2/representative8_postprocess_readiness.csv`

Sibling Ethan workspace:
- `../ethan_runs/journals/2026-06/2026-06-02_ethan_runs.md`
- `../ethan_runs/reports/2026-06-04_ethan_runtime_and_hypothesis_matrix/README.md`
- `../ethan_runs/reports/2026-06-05_ethan_convergence_and_salt1_campaign/README.md`
- `../ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_openfoam13_template.sbatch`
- `../ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `../ethan_runs/jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `../ethan_runs/jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/run_continuation_openfoam13.sbatch`
- `../ethan_runs/staging/render_jobs/viscosity_screening_salt_test_1_kirst_coarse_mesh_render.sbatch`
- `../ethan_runs/staging/render_jobs/val_salt_test_2_coarse_mesh_laminar_render.sbatch`
- live continuation logs under the four active case-stage `logs/log.foamRun_continuation` files

## Commands run

- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short`
- `squeue -u andresfierro231`
- `sacct -j 3202708,3210231,3210760,3210761 --format=JobID,JobName%30,State,Elapsed,NodeList%20`
- multiple `sed -n` reads against repo docs, current report artifacts, Ethan runtime notes, and staged sbatch wrappers
- `find ../ethan_runs/jadyn_runs -maxdepth 4 -type f \( -name 'run_continuation_openfoam13*.sbatch' -o -name '*.sbatch' \) | sort`
- `find ../ethan_runs/staging -maxdepth 3 -type f -name '*.sbatch' | sort`
- `tail -40` on the four active continuation logs
- `sbatch --parsable --dependency=afterany:3202708 --export=ALL,RCWALLBC_LIBDIR=/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data ../ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_openfoam13_template.sbatch`
- `sbatch --parsable --dependency=afterany:3210761 ../ethan_runs/jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `sbatch --parsable --dependency=afterany:3210760 ../ethan_runs/jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/run_continuation_openfoam13.sbatch`
- `sbatch --parsable --dependency=afterany:3210231 ../ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `sbatch --parsable analysis/campaigns/2026-06-05_ethan_weekend_queue/render_salt3_jin.sbatch`
- `sbatch --parsable analysis/campaigns/2026-06-05_ethan_weekend_queue/render_water1_laminar.sbatch`
- `sbatch --parsable --dependency=afterany:3211197:3211199:3211200 analysis/campaigns/2026-06-05_ethan_weekend_queue/refresh_zero_advance_pilot3.sbatch`
- `squeue -j 3211196,3211197,3211198,3211199,3211200,3211201,3211208`
- `scontrol show job <jobid> | tr ' ' '
' | grep '^Dependency='` for the dependent jobs

## Inputs used

- Repo root: `/scratch/09748/andresfierro231/projects_scratch/dmdc-analysis`
- Sibling CFD workspace: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`
- OpenFOAM env bootstrap: `../ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh`
- RC wall BC shared library dir for Salt 2 template submission: `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data`

## Outputs generated

- `analysis/campaigns/2026-06-05_ethan_weekend_queue/README.md`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/campaign_plan.md`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/campaign_step_index.csv`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/submitted_jobs.csv`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/CHECKPOINT.md`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/render_salt3_jin.sbatch`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/render_water1_laminar.sbatch`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/refresh_zero_advance_pilot3.sbatch`

## Key numerical results

Measured current live runtime state at inspection time:
- `3202708` Salt 2 continuation: `RUNNING`; latest inspected solver time `4073.754285714 s`
- `3210231` Salt 4 Jin continuation: `RUNNING`; latest inspected solver time `2246.871287129 s`
- `3210761` Salt 1 Jin continuation: `RUNNING`; latest inspected solver time `3440.225 s`
- `3210760` Salt 1 Kirst continuation: `RUNNING`; latest inspected solver time `3395.006289308 s`

Measured queue results from this turn:
- Follow-on continuation jobs submitted: `4`
- Lightweight static render jobs submitted: `2`
- Lightweight dependent analysis refresh jobs submitted: `1`
- Total weekend jobs submitted in this turn: `7`

Current report-side measured status carried into this queueing decision:
- Ethan current-state report now treats Kirst rows as `not fully converged`
- Ethan current-state report now counts `1` comparison candidate and `12` convergence-audit-required rows
- Latest successful zero-advance single-case Salt 2 pass used processor time `4066`
- Latest pilot-3 zero-advance pass produced `success=yes` for Water 1 and `partial` for Salt 2 / Salt 3 because latest reconstructed salt `T` files can still alternate between readable and malformed states

## Plots/tables generated

Already-existing referenced analysis artifacts that govern the queueing decision:
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/TECHNICAL_REPORT.md`
- `analysis/reports/2026-06-05_ethan_representative8_postprocess/representative_8_postprocess_summary.csv`
- `analysis/reports/2026-06-05_ethan_zero_advance_transport_phase1_2/representative8_postprocess_readiness.csv`
- `../ethan_runs/reports/2026-06-04_ethan_runtime_and_hypothesis_matrix/README.md`
- `../ethan_runs/reports/2026-06-05_ethan_convergence_and_salt1_campaign/README.md`

New queue-tracking tables from this turn:
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/submitted_jobs.csv`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/campaign_step_index.csv`

## Interpretation

- The active continuation lanes are numerically healthy enough to justify one more chained chunk each.
- The strongest justifications remain Salt 2 first, then the targeted Salt 1 Jin/Kirst runtime tests, then Salt 4 Jin as a manuscript sensitivity lane.
- I did not submit a blanket continuation campaign for Salt 3, Salt 4 Kirst, or all water cases because the current Ethan runtime note still explicitly warns against that.
- The two static render jobs are low-cost and paper-useful; they add weekend value without consuming another 64-rank CFD node.
- The zero-advance refresh was queued only as a lightweight dependent follow-up and not forced directly onto the live-running salt cases, because latest readable-state stability still alternates on the active salt reconstructions.

## Limitations

- No new solver-side case-stage directories were created this turn; I only queued existing staged wrappers plus repo-local lightweight wrappers.
- I did not submit Salt 3 or water continuations because the latest runtime policy still argues against a blanket continuation queue.
- The active Salt 2 continuation keeps advancing, so any report-level `latest_runtime_write` reference is a moving target rather than a fixed final state.
- The queued render wrappers for Salt 3 Jin and Water 1 are new wrappers inferred from the existing render-job pattern; they passed `bash -n`, but they have not executed yet.

## Bugs or anomalies

- Repo-local `apply_patch` remained blocked by sandbox namespace exhaustion, so file writes used a shell/Python fallback.
- The pilot-3 zero-advance package still shows a moving Salt 2 failure mode: one latest write can be readable and the next latest write can fail with malformed reconstructed `T` tokens.
- Cluster `sacct` on this system rejected `Dependency` as a requested field, so dependency provenance was captured via `scontrol show job` instead.

## Follow-up tasks

1. Monday morning: check `squeue -u andresfierro231` and `sacct` for `3202708`, `3210231`, `3210760`, `3210761`, `3211196`, `3211197`, `3211199`, `3211200`, `3211198`, `3211201`, and `3211208`.
2. If the two render jobs finish, review generated field figures for Salt 3 Jin and Water 1 before deciding whether to stage more static figure jobs.
3. If the Salt 1 follow-on chunks finish cleanly, compare new net-heat residual behavior against the Salt 1 hypothesis in `../ethan_runs/reports/2026-06-05_ethan_convergence_and_salt1_campaign/README.md`.
4. When `3211208` runs, inspect whether the pilot zero-advance package still shows `partial` for Salt 2 and Salt 3 or whether newer latest writes are readable.
5. If Salt 2 still alternates between readable and malformed latest reconstructed `T` files, modify `tools/ethan_zero_advance_transport.py` to use the latest readable reconstructed time rather than the absolute latest write.
6. Refresh `analysis/reports/2026-06-05_ethan_tamu_current_state_report/` and `analysis/reports/2026-06-05_ethan_representative8_postprocess/` after the first meaningful new continuation checkpoints land.
7. Revisit whether Salt 4 Kirst deserves runtime only after the Salt 4 Jin follow-on finishes and the updated residual/QoI tail is known.
8. Keep water continuations off the queue unless the next week’s review changes the runtime priority policy.

## Exact files future agents should inspect first

- `analysis/campaigns/2026-06-05_ethan_weekend_queue/submitted_jobs.csv`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/CHECKPOINT.md`
- `analysis/campaigns/2026-06-05_ethan_weekend_queue/campaign_plan.md`
- `analysis/reports/2026-06-05_ethan_tamu_current_state_report/TECHNICAL_REPORT.md`
- `analysis/reports/2026-06-05_ethan_representative8_postprocess/representative_8_postprocess_summary.csv`
- `analysis/reports/2026-06-05_ethan_zero_advance_transport_phase1_2/representative8_postprocess_readiness.csv`
- `tools/ethan_zero_advance_transport.py`
- `../ethan_runs/reports/2026-06-04_ethan_runtime_and_hypothesis_matrix/README.md`
- `../ethan_runs/reports/2026-06-05_ethan_convergence_and_salt1_campaign/README.md`
- `../ethan_runs/jadyn_runs/salt2/2026-06-01_continuation_candidate/run_continuation_openfoam13_template.sbatch`
- `../ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `../ethan_runs/jadyn_runs/salt1/2026-06-04_jin_continuation_candidate/run_continuation_openfoam13.sbatch`
- `../ethan_runs/jadyn_runs/salt1/2026-06-05_targeted_campaign/kirst_continuation_candidate/run_continuation_openfoam13.sbatch`

## Missing information

- None of the newly submitted weekend jobs has started or finished yet, so no new CFD or render outputs exist from this queue at checkpoint time.
