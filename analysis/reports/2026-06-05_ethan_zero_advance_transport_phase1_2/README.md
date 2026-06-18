# Ethan Zero-Advance Transport Phase 1/2

This package tests whether the missing transport layer can be extracted from the latest written OpenFOAM state without advancing the solver.

## Case status

- `Salt 2` (`val_salt_test_2_coarse_mesh_laminar`): latest processor time `8203`, wall rows `49`, bulk rows `4`, joined rows `49`, success `partial`.
- `Salt 3` (`viscosity_screening_salt_test_3_jin_coarse_mesh`): latest processor time `2514`, wall rows `49`, bulk rows `4`, joined rows `49`, success `partial`.
- `Water 1` (`val_water_test_1_coarse_mesh_laminar`): latest processor time `5274`, wall rows `49`, bulk rows `4`, joined rows `49`, success `yes`.

## Notes

- Kirst should be treated as not fully converged for decision purposes even where an older coded-convergence flag exists.
- Salt 2 uses the actual latest written processor time, not the older probe-history horizon.
- The current extractor derives internal HTC and internal Nusselt from sampled `T_w`, sampled mass-flux-weighted `T_bulk`, and sampled `wallHeatFlux`.
- The pre-existing OpenFOAM `Nu` field in the Ethan cases is reference-temperature-based and is not used as the final internal-Nusselt definition here.

