# Mathematical Guide to the ROM Repository

This page is the entry point for the math behind the repository. The goal is to make the code easy to audit: every major workflow has a short mathematical description, the matrices it builds, the assumptions it makes, and the files/modules that implement it.

## Reading order

1. [Data matrices, cases, and notation](math/00_data_matrices_and_notation.md)
2. [DMD and DMDc](math/01_dmd_and_dmdc.md)
3. [Delay embeddings and loop memory](math/02_delay_embeddings.md)
4. [POD/SVD reduced bases](math/03_pod_and_svd.md)
5. [POD-DMDc reduced-order modeling](math/04_pod_dmdc.md)
6. [Optional POD-ML modal dynamics](math/05_pod_ml.md)
7. [QR/Q-DEIM sensor selection and POD sparse sensing](math/06_sparse_sensing.md)
8. [Validation, unseen-case error, residuals, and metrics](math/07_validation_and_metrics.md)
9. [Stability diagnostics](math/08_stability.md)
10. [Rank, delay, and model sweeps](math/09_sweeps.md)
11. [Irregular time steps and resampling](math/10_irregular_time_and_resampling.md)

## Core philosophy

The repo is intentionally built around transparent numerical linear algebra:

- **SVD/POD** constructs reduced bases.
- **DMD/DMDc** learns linear discrete-time dynamics.
- **Adaptive DMDc** learns a continuous generator from nonuniform physical time steps.
- **Delay embedding** adds finite memory for transport-dominated systems.
- **QR/Q-DEIM** identifies informative state/sensor locations.
- **ML is optional** and acts only on POD modal coefficients; it does not replace POD or DMDc.

For thermal-hydraulic loop data, this means you can start with physically interpretable ROMs and then add optional nonlinear reduced-coordinate models only when the linear ROMs are not adequate.

## Additional research-readiness math notes

- [Regularized and continuous-time DMDc](math/11_regularized_and_continuous_dmdc.md)
- [Kalman filtering and POD-space state estimation](math/12_kalman_filtering.md)
- [Adaptive / variable-time-step DMDc](math/13_adaptive_variable_dt_dmdc.md)

- [14 — Bias Correction and Conservative Online Adaptation](math/14_bias_correction_and_online_adaptation.md)
