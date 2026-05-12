"""Optional thermal-loop geometry metadata and physical plots.

The core ROM algorithms only see columns in a matrix.  Loop geometry metadata
adds physical meaning: TP2 may be upstream of TP3, wall thermocouples may sit at
known positions, and selected POD sensors can be displayed along the loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
import json
import numpy as np
import pandas as pd


@dataclass
class LoopGeometry:
    """Map state/sensor names to one-dimensional loop positions."""

    positions_m: dict[str, float]
    description: str = ""

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, float], description: str = "") -> "LoopGeometry":
        return cls({str(k): float(v) for k, v in mapping.items()}, description=description)

    @classmethod
    def load(cls, path: str | Path) -> "LoopGeometry":
        """Load geometry from JSON or TOML.

        JSON format::
            {"description": "...", "positions_m": {"TP1": 0.0, "TP2": 0.5}}

        TOML format::
            description = "..."
            [positions_m]
            TP1 = 0.0
            TP2 = 0.5
        """

        path = Path(path)
        if path.suffix.lower() == ".json":
            obj = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".toml":
            import tomllib

            obj = tomllib.loads(path.read_text(encoding="utf-8"))
        else:
            raise ValueError("Loop geometry must be JSON or TOML.")
        return cls.from_mapping(obj.get("positions_m", {}), description=obj.get("description", ""))

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"state": list(self.positions_m), "position_m": list(self.positions_m.values())}).sort_values("position_m")

    def ordered_states(self, state_names: Sequence[str]) -> list[str]:
        return sorted([s for s in state_names if s in self.positions_m], key=lambda s: self.positions_m[s])


def plot_pod_modes_vs_geometry(modes: np.ndarray, state_names: Sequence[str], geometry: LoopGeometry, path: str | Path, *, n_modes: int = 4) -> None:
    """Plot POD mode amplitudes versus loop position for physically located states."""

    import matplotlib.pyplot as plt

    states = geometry.ordered_states(state_names)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    if not states:
        ax.text(0.5, 0.5, "No geometry positions matched state names", ha="center")
    else:
        idx = [list(state_names).index(s) for s in states]
        x = [geometry.positions_m[s] for s in states]
        for j in range(min(n_modes, modes.shape[1])):
            ax.plot(x, modes[idx, j], marker="o", label=f"mode {j+1}")
        ax.set_xlabel("Loop position [m]")
        ax.set_ylabel("POD mode amplitude")
        ax.set_title("POD modes versus loop position")
        ax.legend()
        ax.grid(True)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_error_vs_geometry(error_by_state: pd.DataFrame, geometry: LoopGeometry, path: str | Path) -> None:
    """Plot state-wise error versus loop position."""

    import matplotlib.pyplot as plt

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    if error_by_state.empty:
        ax.text(0.5, 0.5, "No error-by-state rows", ha="center")
    else:
        state_col = "column" if "column" in error_by_state.columns else "state"
        metric_col = "rmse" if "rmse" in error_by_state.columns else error_by_state.select_dtypes("number").columns[-1]
        rows = []
        for _, row in error_by_state.iterrows():
            state = str(row[state_col])
            if state in geometry.positions_m:
                rows.append((geometry.positions_m[state], state, float(row[metric_col])))
        rows.sort()
        if rows:
            ax.plot([r[0] for r in rows], [r[2] for r in rows], marker="o")
            for x, state, y in rows:
                ax.annotate(state, (x, y), fontsize="x-small")
            ax.set_xlabel("Loop position [m]")
            ax.set_ylabel(metric_col)
            ax.set_title("Error versus loop position")
            ax.grid(True)
        else:
            ax.text(0.5, 0.5, "No error states matched geometry", ha="center")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_selected_sensors_on_geometry(selected_sensors: Sequence[str], geometry: LoopGeometry, path: str | Path) -> None:
    """Plot selected sensors as markers along a one-dimensional loop coordinate."""

    import matplotlib.pyplot as plt

    frame = geometry.to_frame()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 1.8))
    if frame.empty:
        ax.text(0.5, 0.5, "No geometry positions available", ha="center")
    else:
        ax.hlines(0.0, frame["position_m"].min(), frame["position_m"].max(), linewidth=1.0)
        for _, row in frame.iterrows():
            state = str(row["state"])
            x = float(row["position_m"])
            selected = state in selected_sensors
            ax.plot([x], [0], marker="o", markersize=8 if selected else 4)
            ax.annotate(state + (" *" if selected else ""), (x, 0), xytext=(0, 10 if selected else -15), textcoords="offset points", ha="center", fontsize="x-small")
        ax.set_xlabel("Loop position [m]")
        ax.set_yticks([])
        ax.set_title("Selected sensors along loop geometry")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
