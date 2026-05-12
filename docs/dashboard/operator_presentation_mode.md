# Operator Presentation Mode

The live dashboard has two audiences:

1. **Technical users** who want raw tables, diagnostics, and debug views.
2. **Operators/reviewers** who want immediate situational awareness.

The operator view is meant for the second group. It emphasizes a clear status
banner, trust score, current alert counts, model identity from the registry, and
a loop schematic whose sensors are colored by the latest matched forecast residual.

## Launch

```bash
dmdc live-dashboard \
  --run-dir outputs/live_adaptation_replay \
  --view operator \
  --geometry configs/templates/simple_loop_geometry.toml \
  --residual-warning-threshold 2.0 \
  --residual-critical-threshold 5.0
```

Archive mode is still summary-first:

```bash
dmdc live-dashboard \
  --archive-root live_archive \
  --mode archive \
  --view operator \
  --window-label 60s
```

## Sensor colors

The schematic uses the most recent residual available for each sensor:

| Color | Meaning |
|---|---|
| Green | residual below warning threshold |
| Amber | residual above warning threshold |
| Red | residual above critical threshold |
| Gray | no matched residual yet |

The plot is intentionally advisory. It is not a safety system and it does not
send control commands.

## Geometry file

A geometry file is optional. Without it, states are displayed evenly along a line.
For a real loop, define physical positions:

```toml
description = "Simple thermal loop display geometry"

[positions_m]
TP1 = 0.0
TP2 = 0.4
TP3 = 0.9
TP4 = 1.5
TP5 = 2.1
TP6 = 2.8
massFlowRate = 3.2
```

The same geometry convention is also used by POD/error-vs-position plots.

See also:

- `docs/live/dashboard_phase5.md`
- `docs/live/monitoring_phase4.md`
- `docs/model_registry/README.md`
