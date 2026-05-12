# Field-Ready EPICS and LabVIEW/DAQ Adapters

The repo now has a modular importer/streaming framework. The goal is that EPICS,
LabVIEW, DAQ folder-drop, CSV tail, MQTT, or future adapters all produce the same
kind of rows for the live ROM pipeline.

## Adapter contract

Offline importers implement:

```python
def import_data() -> ImportResult
```

Live stream adapters implement:

```python
def read_new_samples() -> list[LiveSample]
```

That separation keeps DMDc/POD/Kalman/monitoring code independent of the data
source.

## EPICS

Optional dependency:

```bash
python -m pip install -e '.[epics]'
```

Current support:

- one-shot EPICS PV snapshot importer,
- PV connectivity table helper,
- polling EPICS stream adapter scaffold.

Example PV map:

```toml
[epics.pvs]
TP1 = "LOOP:TP1"
TP2 = "LOOP:TP2"
massFlowRate = "LOOP:MDOT"
q_heater = "LOOP:HEATER:POWER"
```

Remaining field work once real PVs are available:

- monitor/callback adapter instead of polling,
- reconnect logic for transient PV failures,
- timestamp alignment with control-system timestamps,
- alarm/status/severity metadata,
- PV unit metadata.

## LabVIEW / DAQ folder drop

The LabVIEW/DAQ importer currently stacks ordinary tabular chunks. It includes
options for partial-file protection through `skip_unstable_files` and
`settle_seconds` in the lower-level importer.

Remaining field work once actual files are available:

- parse metadata headers or sidecar files,
- detect locked/partially written files robustly,
- enforce chunk ordering,
- handle duplicate rows across chunk boundaries,
- preserve DAQ sample-clock timestamps.

See also:

- `docs/importers/README.md`
- `docs/live/streaming_phase1.md`
- `docs/live/archive_phase6_2.md`
