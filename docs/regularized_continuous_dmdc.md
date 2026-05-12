# Regularized and Continuous-Time DMDc

Use `ridge_dmdc` in comparison/sweep workflows when ordinary DMDc is noisy or ill-conditioned:

```bash
dmdc compare --models persistence mean dmdc ridge_dmdc pod_dmdc ...
```

Ridge DMDc solves a regularized least-squares problem.  See `docs/math/11_regularized_and_continuous_dmdc.md` for the derivation.

Continuous-time conversion is available through:

```bash
dmdc continuous \
  --data data.csv \
  --time-col time \
  --case-col case_id \
  --case-id run_001 \
  --state-cols TP1 TP2 massFlowRate \
  --input-cols q_heater \
  --outdir outputs/continuous
```

This first fits a discrete map and then computes:

\[
A_c = \frac{1}{\Delta t}\log(A_d).
\]

Use it for interpretation of growth rates, decay rates, and frequencies.  Validate predictions in discrete time unless you add a dedicated continuous ODE integrator.
