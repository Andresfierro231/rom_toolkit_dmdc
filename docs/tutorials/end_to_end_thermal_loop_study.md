# End-to-End Thermal Loop ROM Study

This tutorial is the recommended “start here” path for SAM or experimental loop data.  It uses a small synthetic thermal-loop dataset with the same kind of columns you will commonly have in a natural-circulation molten-salt loop study:

- fluid temperatures: `TP1`--`TP6`
- wall temperatures: `TW1`--`TW3`
- flow: `massFlowRate`
- operating conditions / inputs: `q_heater`, `T_amb`, `h_amb`
- independent cases: `case_id`
- physical time: `time`

The synthetic cases are inspired by the simple natural-circulation loop/SAM studies we discussed: Hitec-like salt, Salt Tests 1--4 as training cases, a held-out hotter case for unseen validation, heater powers in the few-hundred-W range, airflow fixed at 37 L/min, and centerline temperature sensors around a loop.  The data are for tutorial/software validation only; they are not a replacement for your actual SAM or TAMU/ACU-VCU data.

## 1. Create the example dataset

```bash
python -m dmdc.cli make-thermal-loop-example \
  --outdir examples/end_to_end_thermal_loop_study
```

This writes:

```text
examples/end_to_end_thermal_loop_study/
├── thermal_loop_synthetic.csv
├── loop_geometry.toml
├── thermal_loop_study.toml
└── README.md
```

## 2. Inspect data quality

```bash
python -m dmdc.cli inspect-data \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --expected-final-time 850 \
  --outdir outputs/thermal_loop/inspection
```

Important outputs:

```text
case_quality_dashboard.csv
warnings.txt
dt_summary_by_case.csv
state_variance.csv
input_variance.csv
provenance.json
```

## 3. Validate POD-DMDc on an unseen case

```bash
python -m dmdc.cli validate \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --train-cases salt_test_1 salt_test_2 salt_test_3 salt_test_4 \
  --test-cases salt_test_5_unseen_hot \
  --pod-rank 0.999 \
  --dmdc-rank full \
  --forecast-horizons 1 5 10 25 \
  --outdir outputs/thermal_loop/validation \
  --plots
```

The validation folder reports training error, held-out error, forecast-horizon error, operating-condition extrapolation warnings, and bootstrap uncertainty summaries wherever enough case-level data are available.


## 3b. Fit an adaptive/variable-time-step DMDc model

The synthetic tutorial data intentionally uses a nonuniform/adaptive-like time
grid. To learn a physical-time generator directly from the changing time steps,
run:

```bash
python -m dmdc.cli adaptive-fit \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/thermal_loop/adaptive_fit \
  --plots
```

This fits

\[
    \frac{dx}{dt} \approx A_c x + B_c u
\]

using the actual \(\Delta t_k\) for each transition.

## 4. Compare models and include regularized DMDc

```bash
python -m dmdc.cli compare \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --train-cases salt_test_1 salt_test_2 salt_test_3 salt_test_4 \
  --test-cases salt_test_5_unseen_hot \
  --models persistence mean adaptive_dmdc dmdc ridge_dmdc pod_dmdc pod_ml_ridge \
  --outdir outputs/thermal_loop/compare \
  --plots \
  --report
```

New high-value files:

```text
model_comparison.csv
operating_condition_summary.csv
uncertainty_summary.csv
best_model_recommendation.txt
report/report.tex
provenance.json
```

The held-out hot case is intentionally outside the training heater-power range, so the operating-condition summary should mark the validation as extrapolation.

## 5. Run a rank/delay/model sweep

```bash
python -m dmdc.cli sweep \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --train-cases salt_test_1 salt_test_2 salt_test_3 salt_test_4 \
  --test-cases salt_test_5_unseen_hot \
  --models persistence adaptive_dmdc dmdc ridge_dmdc pod_dmdc \
  --pod-ranks 2 4 6 0.999 \
  --dmdc-ranks full \
  --n-delays 1 2 4 \
  --outdir outputs/thermal_loop/sweep \
  --plots \
  --report
```

The sweep writes a transparent best-model recommendation.  The recommendation is not magic; it ranks by held-out error while filtering obviously failed/unstable candidates.

## 6. Continuous-time interpretation

You only have discrete time series, so the model is first fit as a discrete map:

\[
    x_{k+1} = A_d x_k + B_d u_k.
\]

If the sample interval is approximately uniform, the repo can derive an approximate continuous-time generator from a discrete map. If the time grid is adaptive/nonuniform, prefer `dmdc adaptive-fit`:

\[
    A_c = \frac{1}{\Delta t}\log(A_d).
\]

Run this on one case at a time:

```bash
python -m dmdc.cli continuous \
  --data examples/end_to_end_thermal_loop_study/thermal_loop_synthetic.csv \
  --time-col time \
  --case-col case_id \
  --case-id salt_test_1 \
  --state-cols TP1 TP2 TP3 TP4 TP5 TP6 TW1 TW2 TW3 massFlowRate \
  --input-cols q_heater T_amb h_amb \
  --outdir outputs/thermal_loop/continuous
```

Use continuous-time eigenvalues for time constants and oscillation frequencies, but keep validation in discrete time unless you explicitly simulate the continuous ODE.

## 7. Kalman filter / state estimation idea

For sparse sensing, fit POD-DMDc in reduced coordinates and use selected sensors:

\[
    a_{k+1}=A_r a_k+B_r u_k+w_k,
\]

\[
    y_k=C\Phi_r a_k+v_k.
\]

The Kalman filter estimates modal coefficients \(a_k\) from noisy sparse sensor measurements \(y_k\), then reconstructs the full loop state:

\[
    \hat{x}_k = \bar{x}+\Phi_r\hat{a}_k.
\]

See `docs/math/12_kalman_filtering.md` and `examples/kalman_state_estimation/example_kalman_pod_state_estimation.py`.
