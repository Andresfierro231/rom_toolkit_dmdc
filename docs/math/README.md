# Math documentation index

Start with `docs/math_index.md`, then use these focused notes:

- `00_data_matrices_and_notation.md` — snapshot matrices and notation.
- `01_dmd_and_dmdc.md` — DMD/DMDc least-squares model.
- `02_delay_embeddings.md` — memory/transport delay embedding.
- `03_pod_and_svd.md` — POD basis from SVD.
- `04_pod_dmdc.md` — DMDc in POD coordinates.
- `05_pod_ml.md` — optional ML for modal coefficients.
- `06_sparse_sensing.md` — QR/Q-DEIM sparse measurement reconstruction.
- `07_validation_and_metrics.md` — unseen-case validation and errors.
- `08_stability.md` — eigenvalues, spectral radius, rollout divergence.
- `11_regularized_and_continuous_dmdc.md` — ridge DMDc and continuous-time interpretation.
- `12_kalman_filtering.md` — POD-Kalman state estimation.
- `14_bias_correction_and_online_adaptation.md` — bounded online bias correction.

The key philosophy: SVD/POD/DMDc remain the interpretable core; ML and adaptation are optional layers around that core.
