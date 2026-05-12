# Regularized and Continuous-Time DMDc

## Ridge/Tikhonov DMDc

Ordinary DMDc solves

\[
X' \approx G\Omega, \qquad G=[A\;B], \qquad \Omega=\begin{bmatrix}X\\U\end{bmatrix}.
\]

When \(\Omega\) is noisy or ill-conditioned, the least-squares solution can overreact to tiny singular directions.  Ridge DMDc solves

\[
\min_G \|X' - G\Omega\|_F^2 + \alpha\|G\|_F^2.
\]

If

\[
\Omega = W\Sigma V^T,
\]

then the ridge solution in the retained SVD subspace is

\[
G = X' V_r \operatorname{diag}\left(\frac{\sigma_i}{\sigma_i^2+\alpha}\right) W_r^T.
\]

The parameter \(\alpha\) damps directions associated with small singular values.  Larger \(\alpha\) is more conservative but can underfit.

## Continuous-time interpretation

A DMDc model fit from sampled data is a discrete map:

\[
x_{k+1}=A_d x_k+B_d u_k.
\]

If the sample spacing \(\Delta t\) is approximately uniform, we can derive a continuous generator

\[
A_c = \frac{1}{\Delta t}\log(A_d).
\]

This gives eigenvalues with physical units.  If \(\lambda_c = \sigma+i\omega\), then \(\sigma\) is a growth/decay rate and \(\omega\) is an angular frequency.

For inputs, the exact relation is

\[
B_d = \int_0^{\Delta t} e^{A_c\tau}\,d\tau\,B_c.
\]

The repo estimates \(B_c\) by solving this linear relation approximately.  This is useful for interpretation, but the safest predictive validation still compares sampled discrete rollouts against held-out data.

## Important warning

Continuous-time conversion does **not** fix irregular data.  If \(\Delta t\) varies strongly, first inspect/resample data or fit models on consistently sampled segments.
