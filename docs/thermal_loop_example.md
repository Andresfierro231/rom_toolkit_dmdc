# Thermal Loop Example Dataset

The repo includes a generator for a small synthetic thermal-loop dataset:

```bash
dmdc make-thermal-loop-example --outdir examples/end_to_end_thermal_loop_study
```

The generated dataset is inspired by the simple natural-circulation SAM loop studies we discussed together:

- Hitec-like molten salt behavior,
- training cases resembling Salt Tests 1--4,
- a held-out hotter case for unseen validation,
- centerline thermocouples `TP1`--`TP6`,
- wall temperatures `TW1`--`TW3`,
- `massFlowRate`,
- operating conditions `q_heater`, `T_amb`, and `h_amb`,
- fixed airflow metadata of 37 L/min.

It is a tutorial/software dataset only.  Replace it with real SAM, Pronghorn, TAMU, ACU-VCU, or experiment CSVs for research conclusions.

## Why include a synthetic loop example?

A ROM repo is easier to learn when the example columns look like the real application.  This example lets you test:

- data inspection,
- failed/short-case detection,
- POD-DMDc validation,
- model comparison,
- rank/delay sweeps,
- operating-condition extrapolation warnings,
- LaTeX reporting,
- sparse sensing and geometry-aware plots.

## Files created

```text
thermal_loop_synthetic.csv
loop_geometry.toml
thermal_loop_study.toml
README.md
```

The `loop_geometry.toml` file maps sensor names to approximate one-dimensional loop positions.  Geometry is optional, but it enables plots of modes, selected sensors, and errors versus loop position.
