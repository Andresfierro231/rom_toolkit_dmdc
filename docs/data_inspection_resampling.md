# Data Inspection, Adaptive Time Steps, and Resampling

Before fitting DMD, DMDc, POD, or POD-DMDc models, inspect the time-series table.

```bash
dmdc inspect-data \
  --data data/example_multicase_timeseries.csv \
  --time-col time \
  --case-col case_id \
  --state-cols x1 x2 \
  --input-cols u1 \
  --outdir outputs/inspection
```

This writes:

```text
inspection_summary.json
columns_summary.csv
missing_values.csv
dt_summary_by_case.csv
case_lengths.csv
state_variance.csv
input_variance.csv
large_time_gaps.csv
warnings.txt
inspection_report.tex
```

The warning system is intentionally friendly. It explains what was detected, why
it matters, and what to try next.

## Nonuniform time is expected

Most real SAM and experimental datasets will not have a perfectly uniform time
step. That is fine. Use the inspection output to decide:

| Case | Recommended action |
|---|---|
| You want physical-time dynamics with changing dt | `dmdc adaptive-fit` |
| You want fixed-step discrete DMDc | `dmdc resample`, then `dmdc fit` or `dmdc pod-dmdc` |
| You only need sample-to-sample prediction | `dmdc fit`, with sample-index interpretation |

## Adaptive fit

```bash
dmdc adaptive-fit \
  --data data/example_multicase_timeseries.csv \
  --time-col time \
  --case-col case_id \
  --state-cols x1 x2 \
  --input-cols u1 \
  --outdir outputs/adaptive_fit \
  --plots
```

## Resampling

DMD/DMDc learns a discrete map between samples. If you intentionally want a
fixed time grid, resampling is explicit and opt-in:

```bash
dmdc resample \
  --data data/example_multicase_timeseries.csv \
  --time-col time \
  --case-col case_id \
  --columns x1 x2 u1 \
  --dt 0.1 \
  --out outputs/resampled_data.csv
```

The current implementation supports linear interpolation. It never silently
resamples during fitting.
