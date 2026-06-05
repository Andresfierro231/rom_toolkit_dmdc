# Ethan Representative 8 Postprocess Audit

## Brief Summary

We do have solid infrastructure today for the representative 8 to report TP/TW/m_dot comparison errors, RMSE, net heat-balance terms, ambient-loss proxies, and salt-side latest-time hydraulic branch losses. We do not yet have a robust published path for derived internal/external effective HTCs, fully populated axial thermal profiles, or a thermal-resistance circuit decomposition.

The selected 8 are the existing study-level representatives already formalized in Ethan's eight-case package: Salt 1 Kirst, Salt 2 native continuation, Salt 3 Jin, Salt 4 Jin, and Water 1-4 direct laminar validation rows. For the current working interpretation, the Kirst representative should be treated as not fully converged even if an older coded-convergence flag was set, and Salt 2 should be anchored to the latest written continuation step for postprocessing.

## Selected 8

- `Salt 1`: `viscosity_screening_salt_test_1_kirst_coarse_mesh`; treated here as `not converged`; steady-state class `not_steady_enough`; all-temp RMSE `17.55620984679648` K; mdot abs error `30.809515537974686`%.
- `Salt 2`: `val_salt_test_2_coarse_mesh_laminar`; steady-state class `essentially_steady`; all-temp RMSE `5.195921279377687` K; mdot abs error `18.951017976190467`%.
- `Salt 3`: `viscosity_screening_salt_test_3_jin_coarse_mesh`; steady-state class `essentially_steady`; all-temp RMSE `5.612608549444536` K; mdot abs error `14.711376500000014`%.
- `Salt 4`: `viscosity_screening_salt_test_4_jin_coarse_mesh`; steady-state class `borderline_but_usable`; all-temp RMSE `6.061627553731621` K; mdot abs error `15.496810024875622`%.
- `Water 1`: `val_water_test_1_coarse_mesh_laminar`; steady-state class `borderline_but_usable`; all-temp RMSE `1.4286990033767857` K; mdot abs error `21.60989997891566`%.
- `Water 2`: `val_water_test_2_coarse_mesh_laminar`; steady-state class `borderline_but_usable`; all-temp RMSE `1.6620440471672377` K; mdot abs error `21.657708990000003`%.
- `Water 3`: `val_water_test_3_coarse_mesh_laminar`; steady-state class `borderline_but_usable`; all-temp RMSE `1.815082567549664` K; mdot abs error `25.560936558333335`%.
- `Water 4`: `val_water_test_4_coarse_mesh_laminar`; steady-state class `borderline_but_usable`; all-temp RMSE `2.3761628765606178` K; mdot abs error `28.00657187086093`%.

## What We Can Report Now

- Validation scorecards: TP RMSE, TW RMSE, all-temperature RMSE, max TP/TW error location, mdot absolute error, and external-loss absolute error are already published per run.
- Heat-balance outputs: total wall heat, ambient-loss proxy, cooling-branch removal, and section net-Q terms are already published per run.
- Salt hydraulics: latest-time section `|Δp_rgh|` is already published for the representative salt runs and is good enough for branch-loss ranking.
- External heat-transfer coefficients: prescribed BC values such as heater/cooler/test-section `h` are already recorded in case metadata.

## What Is Not Ready Yet

- Internal HTC and `Nu(x)`: the current representative salt rows have zero populated `areaAverage_Nu` entries in the axial package.
- Axial `T_w(x)` or `T_bulk(x)`: the current representative salt rows also have zero populated `areaAverage_T_k` entries in the axial package.
- Thermal circuit / resistance network: there is no current published table that turns the CFD into section-by-section thermal resistances or a closed thermal-circuit model.
- Water-side hydraulics/axial packages: the current reusable section-transport and axial packages are salt-focused, not full 8-run generalized products.

## Output Files

- `representative_8_postprocess_summary.csv`: merged run-level table for the chosen 8.
- `representative_salt_hydraulics.csv`: latest-time salt section pressure-drop table for the 4 representative salt rows.
- `capability_matrix.csv`: what is available now versus still missing.
- `MANIFEST.json`: provenance and file list for this package.

