# Stability diagnostics

For a discrete-time DMD/DMDc model,

\[
x_{k+1} = A x_k + B u_k,
\]

the eigenvalues of \(A\) determine the autonomous amplification behavior.  If the
spectral radius

\[
\rho(A)=\max_i |\lambda_i(A)|
\]

is greater than one, long rollouts can diverge even when one-step prediction
error is small.

The repository now saves:

- `stability_summary.json`
- `eigenvalues.csv`
- `stability_warnings.txt`
- `eigenvalues_complex_plane.pdf` when plots are enabled

The tool does **not** silently stabilize or clip eigenvalues.  If a model is
unstable, the warning suggests actions such as reducing rank, using POD-DMDc,
scaling variables, adding regularization later, or comparing forecast-horizon
error instead of only one-step error.
