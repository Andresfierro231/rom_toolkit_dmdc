# Executive Summary

Generated: `2026-06-05T10:40:13-05:00`

## Brief Summary

The current `ethan_runs` workspace is much stronger than the current `tamu_box_loop_data` mirror for quantitative validation reporting. Ethan currently has `13` analyzable CFD rows: `1` actively running continuation (`val_salt_test_2_coarse_mesh_laminar`), `2` completed Kirst salt rows that should still be treated as not fully converged, and `10` terminated rows that still need convergence audit before they can be treated as clean validation claims. Under that stricter interpretation, Ethan now has `1` comparison candidate and `12` rows that still belong in convergence-audit-required status. The strongest current Ethan manuscript path is still Salt 2, with Salt 3 and much of Salt 4 now useful for steady-state interpretation even where the coded convergence monitor never fired. Salt 1 remains the weakest salt family because both current rows sit on a materially larger heat-balance residual floor.

The refreshed `tamu_box_loop_data` inventory shows `53` case-like subfolders under `23` top-level items, with `0` metadata parse failures after tolerant repair. The validation-export side is still structurally limited: all `43` candidate rows remain `metadata_only`, and none are auto-ready for validation export. The highest-value TAMU subfolders are the collaborator-confirmed `2024_05_04` salt anchors plus a smaller set of advisory water-side nearest-fit candidates. The largest current family is still `2025_06_19` with `17` case-like subfolders.

## First Four To Analyze First

1. `val_salt_test_2_coarse_mesh_laminar`
2. `viscosity_screening_salt_test_4_jin_coarse_mesh`
3. `2024_05_04/3`
4. `2025_03_19/4`

These four were chosen because they maximize immediate paper value:
- Salt 2 native continuation is the strongest live Ethan validation case and should be anchored to its latest written step.
- Salt 4 Jin is still one of the strongest practically useful salt rows even without a clean convergence claim.
- `2024_05_04/3` is the refreshed TAMU-confirmed Salt 2 anchor subfolder.
- `2025_03_19/4` is the best current water-side TAMU nearest-fit anchor across multiple Water targets, even though it is still advisory-only.

## Next Priority Order

5. `viscosity_screening_salt_test_3_jin_coarse_mesh`
6. `2024_05_04/2`
7. `2024_05_04/4`
8. `2024_05_04/6`
9. `viscosity_screening_salt_test_1_kirst_coarse_mesh`
10. `2025_06_19/16`
11. `2025_05_20/4`
12. `2024_05_04/1`
13. `viscosity_screening_salt_test_4_kirst_coarse_mesh`
14. `viscosity_screening_salt_test_3_kirst_coarse_mesh`
15. `viscosity_screening_salt_test_2_kirst_coarse_mesh`
16. `viscosity_screening_salt_test_2_jin_coarse_mesh`
17. `viscosity_screening_salt_test_1_jin_coarse_mesh`
18. Water laminar group as a diagnostic-only ladder: `water_test_4`, `water_test_3`, `water_test_2`, `water_test_1`

## Main Takeaways

- Ethan:
  - `val_salt_test_2_coarse_mesh_laminar` is still the best active representative, should be anchored to its latest written continuation step, and was confirmed `RUNNING` on job `3202708` at report time.
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh` and `viscosity_screening_salt_test_1_kirst_coarse_mesh` remain useful completed staged rows, but should not be treated as fully converged.
  - Salt 3 Jin and Salt 4 Jin/Kirst are still useful diagnostic/manuscript-sensitivity rows despite terminated status because their temperature and mass-flow errors are materially better than Salt 1.
  - All four water laminar rows remain `needs_convergence_audit`.

- TAMU:
  - The current mirror is structurally healthy and richer than before, but still mostly metadata-driven for validation onboarding.
  - `2024_05_04/2`, `/3`, `/4`, and `/6` are now the most defensible salt-side TAMU subfolders because the refreshed nearest-fit table recognizes them as collaborator-confirmed known-case mappings.
  - `2025_03_19/4` is the best current water-side metadata anchor, but its mapping is still advisory rather than confirmed.
  - `2025_06_19` is the most important exploratory family because it is the largest recent acquisition and includes a representative mid-power case with both transient and fiber-optic workspaces.
