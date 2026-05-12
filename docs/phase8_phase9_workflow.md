# Phase 8--9 Workflow Guide

This guide connects sweep-based model selection with sparse POD sensing.

## Recommended order

```text
1. inspect-data
2. resample if needed
3. pod
4. pod-dmdc
5. validate
6. compare
7. sweep
8. pod-sensors
9. report
```

## Why sweep before sparse sensing?

Sparse sensing depends on a POD basis. The POD rank should not be arbitrary. Use `dmdc sweep` or POD reconstruction diagnostics to choose a sensible rank before using `dmdc pod-sensors`.

## Example

```bash
dmdc sweep --config configs/example_rank_delay_sweep.toml
dmdc pod-sensors --config configs/example_pod_sensors.toml
dmdc report --run outputs/example_rank_delay_sweep
```

## Thermal-hydraulic interpretation

For loop data, delay sweeps can reveal whether transport memory matters. POD sparse sensing can then suggest which temperature or flow measurement locations span the dominant low-dimensional thermal response.

A good final report should include:

- sweep results
- best held-out model
- stability status
- selected sensors
- reconstruction error versus number of sensors
- warnings and limitations
