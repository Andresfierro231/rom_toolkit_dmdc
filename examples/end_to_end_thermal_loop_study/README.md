# End-to-End Thermal Loop ROM Tutorial

This folder contains a small synthetic TAMU/SAM-like natural-circulation loop dataset.
It is for software testing and tutorial use only; it is not validated experimental data.

## Files

- `thermal_loop_synthetic.csv`: multi-case time series with TP1--TP6, TW1--TW3, massFlowRate, and inputs.
- `loop_geometry.toml`: optional one-dimensional sensor positions around the loop.
- `thermal_loop_study.toml`: config for a POD-DMDc validation study.

## Suggested commands

```bash
python -m dmdc.cli inspect-data --config thermal_loop_study.toml
python -m dmdc.cli validate --config thermal_loop_study.toml
python -m dmdc.cli compare   --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv   --time-col time --case-col case_id   --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate   --input-cols q_heater T_amb h_amb   --train-cases salt_test_1 salt_test_2 salt_test_3 salt_test_4   --test-cases salt_test_5_unseen_hot   --models persistence mean adaptive_dmdc dmdc ridge_dmdc pod_dmdc   --outdir examples/end_to_end_thermal_loop_study/outputs/compare --plots --report
```

The synthetic time grid is intentionally nonuniform/adaptive-like, and the held-out case has a heater power above the training range on purpose.  The operating-condition summary should flag that as extrapolation.
