## jsalt2_surface_winner_comparison

Held-out rollout RMSE of the selected JSALT2 winner under the narrow delay-1 compare surface and the broader tuned sweep surface. The project policy now treats the broader tuned sweep as authoritative, which shifts the selected winner from POD-DMDc to delay-4 DMDc on the current split.

## jsalt2_case_rmse_comparison

Per-case held-out rollout RMSE for the selected JSALT2 winners under each selection surface. The broader tuned sweep improves error on every held-out case in the current split for both the with-h and no-h variants.

## jsalt2_stability_tradeoff

Held-out JSALT2 rollout RMSE versus spectral radius for the broader tuned sweep candidates. Adaptive DMDc achieves the lowest raw RMSE but is flagged as potentially unstable, while the selected delay-4 DMDc winner stays near the stability boundary with zero unstable eigenvalues.

## tamu_candidate_cleanup

Candidate-count comparison between the prior TAMU validation export and the filtered export. The filtered workflow preserves the retained candidate set while removing example/demo rows, pseudo-root rows, and metadata-only Jadyn rows from collaborator-facing tables.

## tamu_catalog_buckets

Bucket counts from the current TAMU raw-source validation catalog. The repository already separates reusable sources into steady-sensor, transient-sensor, and steady velocity-profile candidates, with a smaller residual unknown bucket for future triage.
