# Kalman Filtering and POD-Space State Estimation

## Motivation

In a loop experiment, you may not measure every useful state.  You may only have a few thermocouples, while the ROM state includes many fluid and wall temperatures.  POD gives a reduced representation:

\[
x_k \approx \bar{x}+\Phi_r a_k.
\]

Here:

- \(x_k\) is the full state,
- \(\bar{x}\) is the training mean,
- \(\Phi_r\) contains POD modes,
- \(a_k\) contains modal coefficients.

A POD-DMDc model advances the coefficients:

\[
a_{k+1}=A_r a_k+B_r u_k+w_k.
\]

The term \(w_k\) is process noise: it represents model error, unresolved dynamics, and disturbances.

## Sparse measurements

Suppose only selected sensors are measured.  Let \(C\) select those rows of the full state.  Then

\[
y_k = Cx_k + v_k.
\]

Substitute the POD approximation:

\[
y_k \approx C\bar{x}+C\Phi_r a_k+v_k.
\]

After subtracting the selected mean:

\[
y_k-C\bar{x} \approx H a_k+v_k,
\]

where

\[
H=C\Phi_r.
\]

## Kalman filter prediction step

Given an estimate \(\hat{a}_{k-1}\), predict:

\[
\hat{a}_{k|k-1}=A_r\hat{a}_{k-1}+B_r u_{k-1}.
\]

The uncertainty covariance propagates as

\[
P_{k|k-1}=A_rP_{k-1}A_r^T+Q.
\]

## Kalman filter update step

Compute the innovation:

\[
r_k=y_k-H\hat{a}_{k|k-1}.
\]

Compute the innovation covariance:

\[
S_k=HP_{k|k-1}H^T+R.
\]

Compute the Kalman gain:

\[
K_k=P_{k|k-1}H^TS_k^{-1}.
\]

Update the modal coefficients:

\[
\hat{a}_k=\hat{a}_{k|k-1}+K_kr_k.
\]

Update covariance:

\[
P_k=(I-K_kH)P_{k|k-1}.
\]

## Full-state reconstruction

After filtering,

\[
\hat{x}_k=\bar{x}+\Phi_r\hat{a}_k.
\]

This turns a few noisy sensors into a full-state estimate, provided the POD basis and dynamics are representative.

## Choosing Q and R

- \(Q\): process noise covariance. Increase it when the ROM dynamics are imperfect.
- \(R\): measurement noise covariance. Increase it when sensors are noisy.

A beginner-friendly starting point is diagonal matrices:

\[
Q=qI,\qquad R=rI.
\]

Then tune \(q\) and \(r\) by comparing estimates against withheld measurements.

## Live POD-Kalman implementation in this repo

The live Phase-3 commands use a saved `PODDMDcPipeline`. The estimator works in POD coordinates because this is usually much smaller than the full state dimension.

Let the saved POD-DMDc model be

\[
a_{k+1} = A_r a_k + B_r u_k + w_k.
\]

Let the POD reconstruction be

\[
x_k = \bar{x} + D_s \Phi_r a_k,
\]

where \(D_s\) is the POD scaling matrix. If scaling was not used, \(D_s=I\).

If the live stream measures only selected full-state rows, then

\[
y_k = Cx_k + v_k.
\]

Substituting the POD reconstruction gives

\[
y_k = C\bar{x} + C D_s \Phi_r a_k + v_k.
\]

The live estimator defines

\[
H = C D_s \Phi_r,
\]

so the measurement model is

\[
y_k = C\bar{x} + H a_k + v_k.
\]

The Kalman update is then applied to \(a_k\), not directly to \(x_k\). After each update, the full state is reconstructed by

\[
\hat{x}_k = \bar{x} + D_s \Phi_r \hat{a}_k.
\]

This is why the live stream can contain only a subset of columns such as `TP1`, `TP3`, and `massFlowRate`, while the output `live_state_estimates.csv` can contain the full state used by the ROM.

### What Phase 3 does not do yet

Phase 3 logs the Kalman innovation

\[
\nu_k = y_k - \hat{y}_{k|k-1},
\]

but it does not yet turn large innovations into alerts. Alert thresholds, trust scores, and residual monitoring belong in Live Phase 4.
