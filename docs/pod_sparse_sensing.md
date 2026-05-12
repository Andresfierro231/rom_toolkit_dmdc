# POD Sparse Sensing

`dmdc pod-sensors` selects a small set of state variables/sensors using QR/Q-DEIM on a fitted POD basis, then reconstructs the full state using only those selected measurements.

## Main idea

POD gives

```math
x \approx \bar{x} + \Phi_r a.
```

If only selected sensors are measured,

```math
y = Cx,
```

then the modal coefficients are estimated by

```math
a \approx (C\Phi_r)^\dagger (y - C\bar{x}).
```

The full state is reconstructed as

```math
\hat{x} = \bar{x} + \Phi_r a.
```

If scaling was used during POD, the implementation applies the same scaling before solving the sparse least-squares problem.

## Command

```bash
dmdc pod-sensors --config configs/example_pod_sensors.toml
```

## Outputs

```text
selected_sensors.csv
selected_sensors.txt
sparse_sensor_measurements.csv
sparse_sensor_coefficients.csv
sparse_sensor_reconstruction.csv
sparse_sensor_reconstruction_error.csv
reconstruction_error_vs_sensors.csv
reconstruction_error_vs_sensors.pdf
pod_sensor_summary.json
```

## Recommended use

Use this workflow when you want to identify thermocouple/sensor locations that are informative for reconstructing the dominant POD subspace. Do not interpret the result as causal importance. A sensor can be valuable for reconstruction without being the physical cause of a downstream response.

## Practical decision rule

Inspect `reconstruction_error_vs_sensors.csv`. Choose the smallest number of sensors after which the error curve flattens. Then validate on held-out cases.
