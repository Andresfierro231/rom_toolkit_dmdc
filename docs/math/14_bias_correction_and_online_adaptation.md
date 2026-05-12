# Math Guide — Bias Correction and Conservative Online Adaptation

This guide explains the math behind Live Phase 6.1.

The goal is to help a beginner understand the difference between:

```text
state estimation
forecasting
residual monitoring
bias correction
online retraining
```

Phase 6.1 implements only **bias correction**.

---

## 1. The fixed ROM forecast

Assume an offline ROM has already been trained and validated.

A discrete POD-DMDc model might evolve modal coefficients as

```math
a_{k+1} = A_r a_k + B_r u_k.
```

The full state is reconstructed by

```math
x_k \approx \bar{x} + \Phi_r a_k.
```

During live operation, the model produces a forecast:

```math
\hat{x}_{\text{ROM}}(t+h \mid t),
```

meaning:

```text
the model prediction for time t+h, made at time t.
```

---

## 2. Forecast residual

When the real measurement at time `t+h` arrives, the repo can compare it against the old forecast.

For state `i`, define

```math
r_i(t,h) = x_{i,\text{measured}}(t+h) - \hat{x}_{i,\text{ROM}}(t+h \mid t).
```

If

```text
r_i > 0
```

then the model predicted too low.

If

```text
r_i < 0
```

then the model predicted too high.

---

## 3. Bias correction idea

If residuals are consistently nonzero, the model may have a systematic offset.

A bias-corrected forecast is

```math
\hat{x}_{i,\text{corrected}}(t+h \mid t)
=
\hat{x}_{i,\text{ROM}}(t+h \mid t)
+
c_i(t).
```

For horizon-dependent bias,

```math
\hat{x}_{i,\text{corrected}}(t+h \mid t)
=
\hat{x}_{i,\text{ROM}}(t+h \mid t)
+
c_i(h,t).
```

So the model dynamics remain unchanged. Only the displayed/recorded forecast gets a bounded offset.

---

## 4. Exponential smoothing update

The repo updates bias using

```math
c_{k+1} = c_k + \alpha(r_k - c_k).
```

This is equivalent to

```math
c_{k+1} = (1-\alpha)c_k + \alpha r_k.
```

where:

```text
c_k      current bias
r_k      newest residual
alpha    learning rate
```

If `alpha = 0.01`, the update is slow. The bias changes only a little with each residual.

---

## 5. Why this is safer than retraining

DMDc learns matrices:

```math
x_{k+1} \approx A x_k + B u_k.
```

Changing `A` and `B` online can change stability, eigenvalues, and physical interpretation.

Bias correction does not change `A` or `B`.

It only adds:

```math
+ c.
```

That means the validated model remains the source of dynamics, and the bias history is easy to inspect and roll back.

---

## 6. Bounded update

The raw smoothing step is

```math
\Delta c = \alpha(r_k - c_k).
```

The repo bounds this step:

```math
|\Delta c| \leq \Delta c_{\max}.
```

It also bounds total bias:

```math
|c| \leq c_{\max}.
```

This prevents one bad sensor spike from creating a huge correction.

---

## 7. Trust-gated update

Let `T_k` be the model trust score from Phase 4.

The update is allowed only if

```math
T_k \geq T_{\min}.
```

If trust is low, the system records the skipped update and keeps the old bias.

This avoids learning during questionable operating periods.

---

## 8. Operating-envelope gate

If the live loop is outside the training envelope, then residuals may represent extrapolation, not a correctable bias.

For example:

```text
Training q_heater range: 0–120 W
Live q_heater: 160 W
```

In that case, the repo can skip bias updates and record:

```text
outside_training_or_operating_envelope
```

---

## 9. What gets reported

Every residual event produces an audit row:

```text
old_bias
new_bias
delta_bias
raw_residual
residual_used
trust_score
accepted
rejection_reason
```

This is the most important scientific feature of Phase 6.1: adaptation is not hidden.

---

## 10. What Phase 6.1 does not do

It does not:

```text
recompute POD modes
change DMDc matrices
change Kalman filter matrices
perform recursive least squares
actuate hardware
control the loop
replace safety systems
```

Later phases may add guarded recursive least squares, but it should remain experimental and opt-in.
