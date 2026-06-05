# Weekend Queue Plan

Date: `2026-06-05`

## Intent

Keep the already-justified Ethan salt continuation lanes alive over the weekend, add two low-cost static render jobs for representative cases, and leave a queued transport-refresh job behind the targeted Salt 1 and Salt 4 follow-on chunks.

## Submission policy used

- Keep `val_salt_test_2_coarse_mesh_laminar` as the primary continuation lane.
- Continue the explicitly recommended Salt 1 Jin and Salt 1 Kirst runtime tests.
- Continue Salt 4 Jin because it is still one of the strongest practically useful manuscript lanes.
- Do not submit a blanket continuation campaign for Salt 3, Salt 4 Kirst, or all water rows.
- Prefer follow-on chunks from existing staged wrappers over inventing new solver workflows.

## Files in this campaign directory

- `submitted_jobs.csv`
- `campaign_step_index.csv`
- `CHECKPOINT.md`
- `render_salt3_jin.sbatch`
- `render_water1_laminar.sbatch`
- `refresh_zero_advance_pilot3.sbatch`
