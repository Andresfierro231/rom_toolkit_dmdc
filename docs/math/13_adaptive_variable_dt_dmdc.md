# Adaptive / Variable-Time-Step DMDc

## Why this exists

Standard discrete DMDc learns

\[
x_{k+1} \approx A_d x_k + B_d u_k.
\]

This is cleanest when every transition has the same duration \(\Delta t\). Real
SAM outputs and experimental logs often do not satisfy that assumption. If one
transition is 0.01 s and another is 0.5 s, a single discrete operator \(A_d\)
no longer represents one fixed physical time interval.

## Continuous-generator approach

The adaptive model learns a continuous-time approximation:

\[
\frac{dx}{dt} \approx A_c x + B_c u.
\]

For each observed transition,

\[
\Delta t_k = t_{k+1} - t_k,
\]

and

\[
\dot{x}_k \approx \frac{x_{k+1}-x_k}{\Delta t_k}.
\]

Then the least-squares problem is

\[
\dot{X} \approx A_c X + B_c U.
\]

Define

\[
\Omega = \begin{bmatrix} X \\ U \end{bmatrix}.
\]

The fitted generator is

\[
[A_c \; B_c] \approx \dot{X}\Omega^\dagger.
\]

The repo uses the same SVD/rank-truncation philosophy as DMDc, with optional
ridge regularization:

\[
\min_G \|\dot{X} - G\Omega\|_F^2 + \alpha \|G\|_F^2,
\]

where \(G = [A_c\;B_c]\).

## Rollout with changing time steps

During prediction, each step uses its own \(\Delta t_k\). Assuming the input is
held constant over the interval, the model integrates

\[
\dot{x} = A_c x + B_c u_k
\]

from \(t_k\) to \(t_{k+1}\). This is implemented with a matrix exponential of an
augmented system:

\[
\exp\left(
\Delta t_k
\begin{bmatrix}
A_c & B_c \\
0 & 0
\end{bmatrix}
\right).
\]

This gives an exact step for the learned linear continuous-time model under
zero-order-hold inputs.

## When to use this

Use `adaptive-fit` or `adaptive_dmdc` in `compare`/`sweep` when:

- time steps are nonuniform,
- time steps come from an adaptive integrator,
- you care about physical time constants, growth rates, and frequencies,
- resampling would hide important solver/experimental behavior.

Use ordinary `fit`/`pod-dmdc` when:

- data is already fixed-step,
- you intentionally resampled to a fixed grid,
- you only care about sample-to-sample prediction.

## Caveats

Finite-difference slopes can amplify noise. For noisy experimental data:

- use regularization (`alpha`),
- inspect residuals,
- consider smoothing before fitting,
- compare against fixed-step/resampled DMDc as a baseline.
