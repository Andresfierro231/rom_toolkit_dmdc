# Live Dashboard Cheat Sheet

Install:

```bash
python -m pip install -e '.[dashboard]'
```

Create live monitoring outputs:

```bash
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml
```

Launch dashboard:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring
```

Launch from config:

```bash
dmdc live-dashboard --config configs/templates/live_dashboard.toml
```

Write summary only:

```bash
dmdc live-dashboard --run-dir outputs/live_monitoring --write-summary-only
```

Best files to look for in a live folder:

```text
live_state_estimates.csv       full estimated state
live_forecasts.csv             long-form forecasts
live_forecast_residuals.csv    matched forecast errors
live_alerts.csv                warning/critical alert log
live_trust_score.csv           operator-facing trust score
```

Best demo sequence:

```bash
# 1. Fit/prepare a POD-DMDc model offline.
# 2. Replay with monitoring.
dmdc live-replay-monitor --config configs/templates/live_replay_monitor.toml --save-every-batch

# 3. Open dashboard.
dmdc live-dashboard --run-dir outputs/live_monitoring
```
