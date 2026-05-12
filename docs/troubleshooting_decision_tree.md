# Troubleshooting Decision Tree

## Rollout diverges

1. Check `stability_dashboard.csv`.
2. If spectral radius is above 1, reduce rank or try `ridge_dmdc`.
3. Scale variables if pressure/temperature/flow have very different magnitudes.
4. Compare one-step error with forecast-horizon error.
5. Try POD-DMDc before full-state DMDc.
6. Use delay embedding only if it improves held-out rollout error.

## Test error is much larger than training error

1. Open `operating_condition_summary.csv`.
2. Check whether test heater power, ambient temperature, or boundary conditions are outside the training range.
3. Reduce POD rank if overfitting is suspected.
4. Add missing input columns if the held-out case differs by an unmodeled operating condition.
5. Use rank/delay sweeps and choose by held-out error, not training error.

## POD uses too many modes

1. Check `cumulative_energy.pdf`.
2. Use `rank = 0.999` or a smaller integer rank.
3. Consider centering states before POD.
4. Remove constant or near-constant states.

## Data inspection reports irregular time steps

1. Look at `dt_summary_by_case.csv` and `large_time_gaps.csv`.
2. Use `dmdc resample` only if interpolation is physically defensible.
3. Otherwise fit separate models to consistently sampled segments.

## Sparse sensor reconstruction is poor

1. Increase `n_sensors`.
2. Check whether selected sensors cover the loop spatially.
3. Use `loop_geometry.toml` plots to see sensor placement.
4. Validate reconstructed states against withheld sensors.
