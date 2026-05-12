# Loop Geometry and Physical Plots

DMDc and POD only see matrix columns.  A column called `TP4` has no built-in spatial meaning unless you provide metadata.  Optional loop geometry adds a physical coordinate to each sensor:

```toml
[positions_m]
TP1 = 0.0
TP2 = 0.7
TP3 = 1.4
TP4 = 2.3
TP5 = 3.2
TP6 = 4.0
massFlowRate = 4.1
```

The helper class is:

```python
from dmdc.loop_geometry import LoopGeometry

geometry = LoopGeometry.load("loop_geometry.toml")
```

Useful plots:

```python
from dmdc.loop_geometry import (
    plot_pod_modes_vs_geometry,
    plot_error_vs_geometry,
    plot_selected_sensors_on_geometry,
)
```

These plots help answer physical questions:

- Which POD modes are heater/cooler dominated?
- Where along the loop does prediction error grow?
- Are QR/POD-selected sensors spatially clustered or well distributed?

For real SAM data, use actual centerline distances or sensor positions wherever possible.
