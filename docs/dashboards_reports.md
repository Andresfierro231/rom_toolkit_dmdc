# Dashboards and LaTeX reports

Phase 6 adds portable model-comparison dashboards and LaTeX report generation.

## Compare models

```bash
dmdc compare \
  --data data/example_multicase_timeseries.csv \
  --case-col case_id \
  --time-col time \
  --state-cols x1 x2 \
  --input-cols u1 \
  --train-cases run_001 run_002 \
  --test-cases run_003 \
  --models persistence mean dmdc pod_dmdc \
  --outdir outputs/model_comparison \
  --plots \
  --report
```

This writes:

- `model_comparison.csv/md/tex`
- `error_by_case.csv/md/tex`
- `error_by_state.csv/md/tex`
- `stability_dashboard.csv/md/tex`
- `model_comparison.pdf`
- `eigenvalues_complex_plane.pdf`
- `report/report.tex`

## Generate a report later

```bash
dmdc report --run outputs/model_comparison
```

If `pdflatex` is installed, you may also use:

```bash
dmdc report --run outputs/model_comparison --compile-pdf
```

The report is intentionally tolerant of missing optional artifacts. It includes
whatever tables and figures are present in the run directory.
