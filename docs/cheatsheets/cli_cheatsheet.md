# CLI Cheat Sheet

```bash
# Inspect data quality and failed/short cases
dmdc inspect-data --data data.csv --time-col time --case-col case_id --state-cols TP1 TP2 --input-cols q_heater --outdir outputs/inspect

# Fit POD-DMDc on multi-case data
dmdc pod-dmdc --data data.csv --case-col case_id --time-col time --state-cols TP1 TP2 --input-cols q_heater --pod-rank 0.999 --outdir outputs/pod_dmdc --plots

# Validate on unseen cases
dmdc validate --data data.csv --case-col case_id --time-col time --state-cols TP1 TP2 --input-cols q_heater --train-cases c1 c2 --test-cases c3 --outdir outputs/validate --plots

# Compare against baselines and regularized DMDc
dmdc compare --data data.csv --case-col case_id --time-col time --state-cols TP1 TP2 --input-cols q_heater --train-cases c1 c2 --test-cases c3 --models persistence mean dmdc ridge_dmdc pod_dmdc --outdir outputs/compare --plots --report

# Sweep rank and delays
dmdc sweep --config configs/templates/rank_delay_sweep.toml

# Generate LaTeX report
dmdc report --run outputs/compare
```
