# Live workflows index

Use this folder when the repo is connected to a live or replayed loop data stream.

## Recommended live path

1. `streaming_phase1.md` — replay/tail rows and maintain a rolling buffer.
2. `forecasting_phase2.md` — load a saved ROM and forecast ahead.
3. `state_estimation_phase3.md` — POD-Kalman state estimation from sparse sensors.
4. `monitoring_phase4.md` — residual alerts, trust score, and operating-envelope checks.
5. `dashboard_phase5.md` — interactive Streamlit dashboard.
6. `adaptation_phase6.md` — bounded bias correction and audit records.
7. `archive_phase6_2.md` — partitioned long-term archive storage.
8. `summaries_quicklooks_phase6_3.md` — compact summaries and quicklook plots.
9. `dashboard_archive_phase6_4.md` — dashboard archive mode.
10. `operator_report.md` — meeting-ready Markdown/HTML status reports.

## Quick demo

```bash
dmdc live-replay-adapt --config configs/templates/live_replay_adapt.toml
dmdc live-dashboard --run-dir outputs/live_adaptation_replay --view operator
dmdc live-operator-report --run-dir outputs/live_adaptation_replay
```

The live system is read-only/advisory. It does not control hardware.
