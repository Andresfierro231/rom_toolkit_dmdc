# Failed/Short Cases and Time-Window Selection

## Case quality

Large SAM sweeps can include failed or partial cases.  `inspect-data` now writes:

```text
case_quality_dashboard.csv
```

This dashboard identifies:

- too-short cases,
- missing required columns,
- NaNs in required columns,
- nonmonotonic or duplicate time,
- missing expected final time.

Example:

```bash
dmdc inspect-data \
  --data runs.csv \
  --time-col time \
  --case-col case_id \
  --state-cols TP1 TP2 TP3 massFlowRate \
  --input-cols q_heater \
  --expected-final-time 850 \
  --outdir outputs/inspection
```

## Time-window selection

The module `dmdc.time_windows` provides explicit helpers for steady-state and transient filtering:

```python
from dmdc.time_windows import filter_time_window, split_transient_steady_windows

steady = filter_time_window(df, time_col="time", t_min=300.0)
windows = split_transient_steady_windows(df, time_col="time", steady_start=300.0, case_col="case_id")
```

This is useful when you want to exclude startup, train only on transients, or validate late-time behavior.
