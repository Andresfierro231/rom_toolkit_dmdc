# Time Handling Cheat Sheet

## My time steps are nonuniform

This is expected for most real SAM/experimental data.

Run:

```bash
dmdc inspect-data --config my_study.toml
```

Then choose:

| Situation | Use |
|---|---|
| Changing/adaptive `dt`, physical-time interpretation matters | `dmdc adaptive-fit` or model `adaptive_dmdc` |
| Fixed-step map desired and interpolation is acceptable | `dmdc resample`, then `dmdc fit` / `dmdc pod-dmdc` |
| You only care about sample index | `dmdc fit`, but interpret `A` as sample-to-sample |

## Recommended compare list

```toml
[compare]
models = ["persistence", "mean", "adaptive_dmdc", "ridge_dmdc", "pod_dmdc"]
```

## Important warning

Do not silently resample. Always save the resampled CSV and keep the original
inspection output.
