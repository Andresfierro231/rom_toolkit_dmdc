"""Configuration helpers for repeatable DMD/DMDc workflows.

The CLI is convenient for one-off experiments, but research workflows quickly become hard to
reproduce when every command line contains dozens of flags. This module provides a small,
dependency-light configuration layer around the same CLI/API options.

Supported formats
-----------------
- JSON: always supported.
- TOML: supported on Python 3.11+ through the standard-library ``tomllib`` module.
- YAML/YML: supported only if ``PyYAML`` is installed by the user.

The design intentionally avoids a large workflow framework. A config file is just a dictionary
with optional sections such as ``data``, ``model``, ``preprocessing``, ``output``, ``fit``,
``sensor_selection``, and ``cases``.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json
import re


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a workflow configuration from JSON, TOML, or YAML.

    Parameters
    ----------
    path:
        Path to a ``.json``, ``.toml``, ``.yaml``, or ``.yml`` file.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    elif suffix == ".toml":
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError as exc:  # pragma: no cover - Python < 3.11 fallback
            raise RuntimeError("TOML configs require Python 3.11+ or a TOML parser.") from exc
        with path.open("rb") as f:
            data = tomllib.load(f)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "YAML configs require PyYAML. Install it or use JSON/TOML instead."
            ) from exc
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported config type {suffix!r}. Use .json, .toml, .yaml, or .yml.")

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("The top level of the config file must be a mapping/dictionary.")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries without mutating either one."""

    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def flatten_fit_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten a structured config into keyword arguments understood by ``cmd_fit``.

    The returned keys intentionally mirror the argparse field names used in ``cli.py``.
    """

    fit = config.get("fit", {})
    if fit is None:
        fit = {}
    if not isinstance(fit, dict):
        raise ValueError("The 'fit' section must be a mapping if provided.")

    data = config.get("data", {}) or {}
    model = config.get("model", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    output = config.get("output", {}) or {}

    if not isinstance(data, dict) or not isinstance(model, dict) or not isinstance(preprocessing, dict) or not isinstance(output, dict):
        raise ValueError("Sections 'data', 'model', 'preprocessing', and 'output' must be mappings.")

    flat = {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "rank": model.get("rank", config.get("rank", "full")),
        "center": bool(preprocessing.get("center", config.get("center", False))),
        "scale": bool(preprocessing.get("scale", config.get("scale", False))),
        "n_delays": int(model.get("n_delays", config.get("n_delays", 1))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": output.get("outdir", config.get("outdir", "outputs/dmdc_fit")),
    }
    flat.update(fit)
    return flat


def flatten_sensor_selection_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``select-sensors`` command."""

    section = config.get("sensor_selection", {}) or {}
    if not isinstance(section, dict):
        raise ValueError("The 'sensor_selection' section must be a mapping if provided.")

    data = config.get("data", {}) or {}
    model = config.get("model", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    output = config.get("output", {}) or {}

    flat = {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "rank": model.get("rank", config.get("rank", "full")),
        "n_sensors": section.get("n_sensors", config.get("n_sensors")),
        "center": bool(preprocessing.get("center", config.get("center", False))),
        "scale": bool(preprocessing.get("scale", config.get("scale", False))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": section.get("outdir", output.get("sensor_outdir", "outputs/sensor_selection")),
    }
    flat.update(section)
    return flat


def flatten_pod_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``pod`` command."""

    data = config.get("data", {}) or {}
    pod = config.get("pod", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(data, dict) or not isinstance(pod, dict) or not isinstance(preprocessing, dict) or not isinstance(output, dict):
        raise ValueError("Sections 'data', 'pod', 'preprocessing', and 'output' must be mappings.")
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "rank": pod.get("rank", config.get("rank", "full")),
        "energy_threshold": pod.get("energy_threshold", config.get("energy_threshold")),
        "center": bool(pod.get("center", preprocessing.get("center", config.get("center", True)))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", config.get("scale", False)))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": pod.get("outdir", output.get("pod_outdir", output.get("outdir", "outputs/pod"))),
    }


def flatten_inspect_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``inspect-data`` command."""

    data = config.get("data", {}) or {}
    output = config.get("output", {}) or {}
    inspect = config.get("inspection", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols", [])),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "outdir": inspect.get("outdir", output.get("inspection_outdir", output.get("outdir", "outputs/data_inspection"))),
    }


def flatten_resample_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``resample`` command."""

    data = config.get("data", {}) or {}
    resampling = config.get("resampling", {}) or {}
    output = config.get("output", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "columns": data.get("state_cols", []) + data.get("input_cols", []),
        "dt": resampling.get("dt", config.get("dt")),
        "method": resampling.get("method", "linear"),
        "out": resampling.get("out", output.get("resampled_data", config.get("out"))),
    }


def apply_config_defaults(args: Any, values: dict[str, Any]) -> Any:
    """Fill missing argparse attributes from a flattened config dictionary.

    CLI values win over config values. This lets users keep stable defaults in a config file and
    override one or two options interactively at the command line.
    """

    parser_defaults = {
        "state_cols": [],
        "input_cols": [],
        "time_col": None,
        "case_col": None,
        "case_id": None,
        "rank": "full",
        "center": False,
        "scale": False,
        "outdir": None,
        "plots": False,
        "n_delays": 1,
        "n_sensors": None,
        "energy_threshold": None,
        "dt": None,
        "out": None,
        "columns": None,
        "pod_rank": "0.999",
        "dmdc_rank": "full",
        "train_cases": None,
        "test_cases": None,
        "train_fraction": 0.7,
        "split_strategy": "by_case_fraction",
        "forecast_horizons": [1, 5, 10],
        "models": ["persistence", "mean", "dmdc", "pod_dmdc"],
        "report": False,
        "model_type": "ridge",
        "model_registry_name": None,
        "model_stage": "production",
        "model_version": None,
        "model_registry_root": "models/registry",
        "recursive_rollout": True,
        "pod_ranks": [0.999],
        "dmdc_ranks": ["full"],
        "n_delays_list": [1],
        "alpha": 1e-8,
        "stream_type": "csv_replay",
        "path": None,
        "chunk_size": 1,
        "poll_seconds": 0.0,
        "max_samples": None,
        "max_polls": None,
        "buffer_seconds": None,
        "buffer_max_samples": None,
        "start_at_end": False,
        "save_every_batch": False,
        "residual_abs_threshold": 5.0,
        "innovation_abs_threshold": 5.0,
        "innovation_norm_threshold": None,
        "covariance_trace_threshold": None,
        "forecast_match_tolerance_seconds": None,
        "max_abs_forecast_value": None,
        "run_dir": None,
        "archive_root": None,
        "mode": "auto",
        "window_label": "60s",
        "refresh_seconds": 2.0,
        "host": None,
        "port": None,
        "theme": None,
        "write_summary_only": False,
        "archive_root": None,
        "archive_format": "parquet",
        "archive_compression": "zstd",
        "archive_write_csv_mirrors": False,
        "archive_strict_format": False,
        "archive_flush_rows": 10000,
        "archive_flush_seconds": 30.0,
        "archive_enabled": False,
        "summary_outdir": None,
        "windows_seconds": None,
        "max_files_per_kind": None,
        "quicklook_outdir": None,
        "summaries_dir": None,
        "window_label": "60s",
        "source": None,
        "source_type": "auto",
        "output_format": "parquet",
        "sheet": None,
        "pattern": "*.csv",
        "column_map": None,
        "rename_col": [],
        "case_from_filename": False,
        "max_files": None,
        "epics_pvs": None,
        "strict_parquet": False,
        "view": "operator",
    }
    for key, value in values.items():
        if value is None or not hasattr(args, key):
            continue
        current = getattr(args, key)
        default = parser_defaults.get(key, None)
        if current is None or current == default:
            setattr(args, key, value)
    return args


def flatten_pod_dmdc_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``pod-dmdc`` command."""

    data = config.get("data", {}) or {}
    pod = config.get("pod", {}) or {}
    model = config.get("model", {}) or {}
    output = config.get("output", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "pod_rank": pod.get("rank", config.get("pod_rank", 0.999)),
        "dmdc_rank": model.get("dmdc_rank", model.get("rank", config.get("dmdc_rank", "full"))),
        "center": bool(pod.get("center", preprocessing.get("center", True))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", False))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": output.get("outdir", config.get("outdir", "outputs/pod_dmdc")),
    }


def flatten_validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``validate`` command."""

    data = config.get("data", {}) or {}
    pod = config.get("pod", {}) or {}
    model = config.get("model", {}) or {}
    output = config.get("output", {}) or {}
    split = config.get("split", {}) or {}
    validation = config.get("validation", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "train_cases": split.get("train_cases", config.get("train_cases")),
        "test_cases": split.get("test_cases", config.get("test_cases")),
        "train_fraction": split.get("train_fraction", config.get("train_fraction", 0.7)),
        "split_strategy": split.get("strategy", config.get("split_strategy", "by_case_fraction")),
        "pod_rank": pod.get("rank", config.get("pod_rank", 0.999)),
        "dmdc_rank": model.get("dmdc_rank", model.get("rank", config.get("dmdc_rank", "full"))),
        "center": bool(pod.get("center", preprocessing.get("center", True))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", False))),
        "forecast_horizons": validation.get("forecast_horizons", config.get("forecast_horizons", [1, 5, 10])),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": validation.get("outdir", output.get("validation_outdir", output.get("outdir", "outputs/validation"))),
    }



def flatten_pod_ml_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``pod-ml`` command."""

    data = config.get("data", {}) or {}
    pod = config.get("pod", {}) or {}
    ml = config.get("ml", {}) or {}
    output = config.get("output", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "pod_rank": pod.get("rank", config.get("pod_rank", 0.999)),
        "model_type": ml.get("model_type", config.get("model_type", "ridge")),
        "recursive_rollout": bool(ml.get("recursive_rollout", config.get("recursive_rollout", True))),
        "center": bool(pod.get("center", preprocessing.get("center", True))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", False))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": ml.get("outdir", output.get("pod_ml_outdir", output.get("outdir", config.get("outdir", "outputs/pod_ml")))),
    }


def flatten_sweep_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``sweep`` command."""

    data = config.get("data", {}) or {}
    split = config.get("split", {}) or {}
    sweep = config.get("sweep", {}) or {}
    pod = config.get("pod", {}) or {}
    model = config.get("model", {}) or {}
    output = config.get("output", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "train_cases": split.get("train_cases", config.get("train_cases")),
        "test_cases": split.get("test_cases", config.get("test_cases")),
        "train_fraction": split.get("train_fraction", config.get("train_fraction", 0.7)),
        "models": sweep.get("models", config.get("models", ["pod_dmdc"])),
        "pod_ranks": sweep.get("pod_ranks", [pod.get("rank", config.get("pod_rank", 0.999))]),
        "dmdc_ranks": sweep.get("dmdc_ranks", [model.get("dmdc_rank", model.get("rank", config.get("dmdc_rank", "full")))]),
        "n_delays_list": sweep.get("n_delays", sweep.get("n_delays_list", [model.get("n_delays", config.get("n_delays", 1))])),
        "center": bool(pod.get("center", preprocessing.get("center", config.get("center", True)))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", config.get("scale", False)))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "report": bool((config.get("report", {}) or {}).get("enabled", config.get("report", False))),
        "outdir": sweep.get("outdir", output.get("sweep_outdir", output.get("outdir", "outputs/sweep"))),
    }


def flatten_pod_sensors_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the ``pod-sensors`` command."""

    data = config.get("data", {}) or {}
    pod = config.get("pod", {}) or {}
    sensor_selection = config.get("sensor_selection", {}) or {}
    output = config.get("output", {}) or {}
    preprocessing = config.get("preprocessing", {}) or {}
    return {
        "data": data.get("path", config.get("data_path")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "rank": pod.get("rank", config.get("rank", 0.999)),
        "n_sensors": sensor_selection.get("n_sensors", config.get("n_sensors")),
        "center": bool(pod.get("center", preprocessing.get("center", config.get("center", True)))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", config.get("scale", False)))),
        "plots": bool(output.get("plots", config.get("plots", False))),
        "outdir": sensor_selection.get("outdir", output.get("pod_sensors_outdir", output.get("outdir", "outputs/pod_sensors"))),
    }


def require_sweep_fields(args: Any) -> None:
    """Validate required sweep settings."""
    missing: list[str] = []
    for key in ("data", "state_cols", "case_col"):
        if not getattr(args, key, None):
            missing.append(key)
    if missing:
        raise ValueError(f"Missing required sweep setting(s): {', '.join(missing)}.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/sweep"


def require_pod_sensors_fields(args: Any) -> None:
    """Validate required POD sparse-sensor settings."""
    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        raise ValueError(f"Missing required pod-sensors setting(s): {', '.join(missing)}.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/pod_sensors"


def require_pod_ml_fields(args: Any) -> None:
    """Validate required POD-ML settings."""
    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        raise ValueError(f"Missing required pod-ml setting(s): {', '.join(missing)}.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/pod_ml"


def require_pod_dmdc_fields(args: Any) -> None:
    """Validate required POD-DMDc settings."""
    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        raise ValueError(f"Missing required pod-dmdc setting(s): {', '.join(missing)}.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/pod_dmdc"


def require_validate_fields(args: Any) -> None:
    """Validate required validation settings."""
    missing: list[str] = []
    for key in ("data", "state_cols", "case_col"):
        if not getattr(args, key, None):
            missing.append(key)
    if missing:
        raise ValueError(f"Missing required validate setting(s): {', '.join(missing)}.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/validation"


def flatten_live_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for ``live-replay`` and ``live-run`` commands.

    The streaming section describes how rows arrive; the data section describes
    how those rows map to the ROM state/input schema.  This mirrors the rest of
    the repo so a user can point the live layer at the same columns used for
    offline training and validation.
    """

    data = config.get("data", {}) or {}
    stream = config.get("stream", {}) or {}
    live = config.get("live", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(data, dict) or not isinstance(stream, dict) or not isinstance(live, dict) or not isinstance(output, dict):
        raise ValueError("Sections 'data', 'stream', 'live', and 'output' must be mappings when provided.")
    return {
        "stream_type": stream.get("type", stream.get("stream_type", config.get("stream_type", "csv_replay"))),
        "path": stream.get("path", data.get("path", config.get("path", config.get("data_path")))),
        "state_cols": data.get("state_cols", config.get("state_cols")),
        "input_cols": data.get("input_cols", config.get("input_cols", [])),
        "time_col": data.get("time_col", config.get("time_col")),
        "case_col": data.get("case_col", config.get("case_col")),
        "case_id": data.get("case_id", config.get("case_id")),
        "chunk_size": int(stream.get("chunk_size", config.get("chunk_size", 1))),
        "poll_seconds": float(stream.get("poll_seconds", config.get("poll_seconds", 0.0))),
        "max_samples": live.get("max_samples", stream.get("max_samples", config.get("max_samples"))),
        "max_polls": live.get("max_polls", stream.get("max_polls", config.get("max_polls"))),
        "buffer_seconds": live.get("buffer_seconds", config.get("buffer_seconds")),
        "buffer_max_samples": live.get("buffer_max_samples", config.get("buffer_max_samples")),
        "start_at_end": bool(stream.get("start_at_end", config.get("start_at_end", False))),
        "save_every_batch": bool(live.get("save_every_batch", config.get("save_every_batch", False))),
        "outdir": live.get("outdir", output.get("live_outdir", output.get("outdir", config.get("outdir", "outputs/live_ingestion")))),
    }


def require_live_fields(args: Any) -> None:
    """Validate required fields for live replay/tail ingestion."""

    missing: list[str] = []
    if not getattr(args, "path", None):
        missing.append("stream.path or data.path")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        raise ValueError("Missing required live setting(s): " + ", ".join(missing))
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/live_ingestion"


def flatten_live_prediction_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for live replay/tail prediction commands.

    This extends ``flatten_live_config`` with saved-model and forecast settings.
    The same TOML file can therefore be used for Phase-1 ingestion-only testing
    and Phase-2 online forecasting by adding ``[model]`` and ``[forecast]``
    sections.
    """

    out = flatten_live_config(config)
    model = config.get("model", {}) or {}
    forecast = config.get("forecast", {}) or {}
    live = config.get("live", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(model, dict) or not isinstance(forecast, dict):
        raise ValueError("Sections 'model' and 'forecast' must be mappings when provided.")
    horizons = forecast.get(
        "horizons_seconds",
        live.get("forecast_horizons_seconds", config.get("forecast_horizons_seconds", [5.0, 10.0, 30.0, 60.0])),
    )
    model_path = model.get("path", config.get("model_path"))
    registry_name = model.get("registry_name", config.get("model_registry_name"))
    registry_stage = model.get("stage", config.get("model_stage", "production"))
    registry_version = model.get("version", config.get("model_version"))
    registry_root = model.get("registry_root", config.get("model_registry_root", "models/registry"))
    if model_path is None and registry_name:
        from .model_registry import resolve_model
        model_path = resolve_model(name=registry_name, stage=registry_stage, version=registry_version, registry_root=registry_root)["model_path"]
    out.update(
        {
            "model_path": model_path,
            "model_registry_name": registry_name,
            "model_stage": registry_stage,
            "model_version": registry_version,
            "model_registry_root": registry_root,
            "forecast_horizons_seconds": horizons,
            "discrete_dt_seconds": forecast.get("discrete_dt_seconds", config.get("discrete_dt_seconds")),
            "outdir": live.get(
                "outdir",
                output.get("live_prediction_outdir", output.get("outdir", config.get("outdir", "outputs/live_prediction"))),
            ),
        }
    )
    return out


def require_live_prediction_fields(args: Any) -> None:
    """Validate required fields for live replay/tail prediction."""

    require_live_fields(args)
    missing: list[str] = []
    if not getattr(args, "model_path", None):
        missing.append("model.path or --model")
    if missing:
        raise ValueError("Missing required live prediction setting(s): " + ", ".join(missing))
    if not getattr(args, "forecast_horizons_seconds", None):
        args.forecast_horizons_seconds = [5.0, 10.0, 30.0, 60.0]


def flatten_live_estimation_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for live POD-Kalman estimation commands.

    Live Phase-3 extends the Phase-2 prediction config with an ``[estimator]``
    section.  The stream only needs to contain ``measurement_cols`` plus any
    input columns, while ``state_cols`` describes the full model state.
    """

    out = flatten_live_prediction_config(config)
    data = config.get("data", {}) or {}
    estimator = config.get("estimator", {}) or {}
    if not isinstance(data, dict) or not isinstance(estimator, dict):
        raise ValueError("Sections 'data' and 'estimator' must be mappings when provided.")
    measurement_cols = estimator.get(
        "measurement_cols",
        data.get("measurement_cols", config.get("measurement_cols", data.get("state_cols", config.get("state_cols")))),
    )
    out.update(
        {
            "measurement_cols": measurement_cols,
            "process_noise": estimator.get("process_noise", config.get("process_noise", 1.0e-6)),
            "measurement_noise": estimator.get("measurement_noise", config.get("measurement_noise", 1.0e-3)),
            "initial_covariance": estimator.get("initial_covariance", config.get("initial_covariance", 1.0)),
        }
    )
    return out




def _parse_operating_ranges(ranges: Any) -> dict[str, tuple[float, float]] | None:
    """Normalize operating-envelope ranges from TOML/JSON config."""

    if not ranges:
        return None
    if not isinstance(ranges, dict):
        raise ValueError("monitor.operating_ranges must be a mapping such as {q_heater = [0, 100]}.")
    out: dict[str, tuple[float, float]] = {}
    for key, value in ranges.items():
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError(f"Operating range for {key!r} must be [min, max].")
        out[str(key)] = (float(value[0]), float(value[1]))
    return out


def flatten_live_monitoring_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for live monitoring/alerts commands.

    Live Phase-4 extends the Phase-3 estimator config with a ``[monitor]``
    section.  The monitor emits residual, innovation, operating-envelope,
    covariance, and trust-score outputs; it still never retrains the ROM online.
    """

    out = flatten_live_estimation_config(config)
    monitor = config.get("monitor", {}) or {}
    live = config.get("live", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(monitor, dict):
        raise ValueError("The 'monitor' section must be a mapping when provided.")
    out.update(
        {
            "residual_abs_threshold": monitor.get("residual_abs_threshold", config.get("residual_abs_threshold", 5.0)),
            "innovation_abs_threshold": monitor.get("innovation_abs_threshold", config.get("innovation_abs_threshold", 5.0)),
            "innovation_norm_threshold": monitor.get("innovation_norm_threshold", config.get("innovation_norm_threshold")),
            "covariance_trace_threshold": monitor.get("covariance_trace_threshold", config.get("covariance_trace_threshold")),
            "forecast_match_tolerance_seconds": monitor.get("forecast_match_tolerance_seconds", config.get("forecast_match_tolerance_seconds")),
            "max_abs_forecast_value": monitor.get("max_abs_forecast_value", config.get("max_abs_forecast_value")),
            "operating_ranges": _parse_operating_ranges(monitor.get("operating_ranges", config.get("operating_ranges"))),
            "trust_warning_penalty": monitor.get("trust_warning_penalty", config.get("trust_warning_penalty", 0.10)),
            "trust_critical_penalty": monitor.get("trust_critical_penalty", config.get("trust_critical_penalty", 0.25)),
            "outdir": live.get(
                "outdir",
                output.get("live_monitoring_outdir", output.get("outdir", config.get("outdir", "outputs/live_monitoring"))),
            ),
        }
    )
    return out


def require_live_monitoring_fields(args: Any) -> None:
    """Validate required fields for live monitoring."""

    require_live_estimation_fields(args)
    if not getattr(args, "forecast_horizons_seconds", None):
        # Residual monitoring is most useful with forecasts, but Kalman innovation
        # and operating-envelope alerts still work without horizons.  Provide a
        # small default so beginner configs produce useful forecast residuals.
        args.forecast_horizons_seconds = [5.0, 10.0, 30.0]



def flatten_live_adaptation_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for Live Phase-6.1 bias-correction commands.

    Live Phase-6.1 extends monitoring with a ``[live_adaptation]`` section.
    The adapter is conservative: it learns additive forecast bias only and never
    overwrites the saved ROM or raw forecasts.
    """

    out = flatten_live_monitoring_config(config)
    adaptation = config.get("live_adaptation", config.get("adaptation", {})) or {}
    bias = adaptation.get("bias", {}) if isinstance(adaptation, dict) else {}
    live = config.get("live", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(adaptation, dict) or not isinstance(bias, dict):
        raise ValueError("Sections 'live_adaptation' and 'live_adaptation.bias' must be mappings when provided.")
    out.update(
        {
            "adaptation_enabled": bool(adaptation.get("enabled", config.get("adaptation_enabled", True))),
            "adaptation_method": adaptation.get("method", config.get("adaptation_method", "horizon_state_bias")),
            "bias_learning_rate": bias.get("learning_rate", config.get("bias_learning_rate", 0.01)),
            "max_abs_bias": bias.get("max_abs_bias", config.get("max_abs_bias", 10.0)),
            "max_update_step": bias.get("max_update_step", config.get("max_update_step", 0.25)),
            "update_only_when_trust_above": bias.get("update_only_when_trust_above", config.get("update_only_when_trust_above", 0.70)),
            "skip_when_outside_training_envelope": bool(bias.get("skip_when_outside_training_envelope", config.get("skip_when_outside_training_envelope", True))),
            "skip_on_alert_severity": bias.get("skip_on_alert_severity", config.get("skip_on_alert_severity", ["critical"])),
            "clip_residual_abs": bias.get("clip_residual_abs", config.get("clip_residual_abs", 20.0)),
            "apply_bias_to_forecasts": bool(bias.get("apply_bias_to_forecasts", config.get("apply_bias_to_forecasts", True))),
            "outdir": live.get(
                "outdir",
                output.get("live_adaptation_outdir", output.get("outdir", config.get("outdir", "outputs/live_adaptation"))),
            ),
        }
    )
    return out


def require_live_adaptation_fields(args: Any) -> None:
    """Validate required fields for live bias-correction adaptation."""

    require_live_monitoring_fields(args)
    if not getattr(args, "adaptation_method", None):
        args.adaptation_method = "horizon_state_bias"

def flatten_live_dashboard_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for the optional Streamlit live dashboard.

    The dashboard is intentionally read-only.  It points at an existing live-run
    output directory and renders the CSV artifacts produced by Live Phases 1--4.
    """

    dashboard = config.get("dashboard", {}) or {}
    output = config.get("output", {}) or {}
    live = config.get("live", {}) or {}
    if not isinstance(dashboard, dict) or not isinstance(output, dict) or not isinstance(live, dict):
        raise ValueError("Sections 'dashboard', 'output', and 'live' must be mappings when provided.")
    run_dir = dashboard.get(
        "run_dir",
        live.get("outdir", output.get("live_monitoring_outdir", output.get("outdir", config.get("run_dir", "outputs/live_monitoring")))),
    )
    archive_section = config.get("live_archive", config.get("archive", {})) or {}
    archive_root = dashboard.get(
        "archive_root",
        archive_section.get("root", config.get("archive_root")) if isinstance(archive_section, dict) else config.get("archive_root"),
    )
    return {
        "run_dir": run_dir,
        "archive_root": archive_root,
        "mode": dashboard.get("mode", config.get("mode", "auto")),
        "window_label": dashboard.get("window_label", config.get("window_label", "60s")),
        "refresh_seconds": dashboard.get("refresh_seconds", config.get("refresh_seconds", 2.0)),
        "host": dashboard.get("host", config.get("host")),
        "port": dashboard.get("port", config.get("port")),
        "theme": dashboard.get("theme", config.get("theme")),
        "view": dashboard.get("view", config.get("view", "operator")),
        "write_summary_only": bool(dashboard.get("write_summary_only", config.get("write_summary_only", False))),
        "geometry": dashboard.get("geometry", config.get("geometry")),
        "residual_warning_threshold": dashboard.get("residual_warning_threshold", config.get("residual_warning_threshold", 2.0)),
        "residual_critical_threshold": dashboard.get("residual_critical_threshold", config.get("residual_critical_threshold", 5.0)),
    }

def require_live_dashboard_fields(args: Any) -> None:
    """Validate required fields for the Streamlit live dashboard."""

    if not getattr(args, "mode", None):
        args.mode = "auto"
    if not getattr(args, "window_label", None):
        args.window_label = "60s"
    if not getattr(args, "run_dir", None):
        args.run_dir = "outputs/live_monitoring"

def require_live_estimation_fields(args: Any) -> None:
    """Validate required fields for live POD-Kalman estimation."""

    require_live_prediction_fields(args)
    if not getattr(args, "measurement_cols", None):
        # If measurement columns are omitted, default to all state columns.  This
        # is convenient for a fully observed live stream, while still allowing
        # sparse sensing through an explicit measurement_cols list.
        args.measurement_cols = list(getattr(args, "state_cols", []) or [])
    if not getattr(args, "measurement_cols", None):
        raise ValueError("Missing required live estimation setting(s): measurement_cols or state_cols")


def require_fit_fields(args: Any) -> None:
    """Validate that the minimum required fit fields are available."""

    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required fit setting(s): {joined}. Provide them by CLI or config.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/dmdc_fit"


def require_sensor_fields(args: Any) -> None:
    """Validate that the minimum required sensor-selection fields are available."""

    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required sensor-selection setting(s): {joined}. Provide them by CLI or config.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/sensor_selection"


def require_pod_fields(args: Any) -> None:
    """Validate that the minimum required POD fields are available."""

    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "state_cols", None):
        missing.append("state_cols")
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required POD setting(s): {joined}. Provide them by CLI or config.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/pod"


def require_inspect_fields(args: Any) -> None:
    """Validate required data inspection fields."""

    if not getattr(args, "data", None):
        raise ValueError("Missing required inspect-data setting: data.")
    if not getattr(args, "outdir", None):
        args.outdir = "outputs/data_inspection"


def require_resample_fields(args: Any) -> None:
    """Validate required resampling fields."""

    missing: list[str] = []
    if not getattr(args, "data", None):
        missing.append("data")
    if not getattr(args, "time_col", None):
        missing.append("time_col")
    if getattr(args, "dt", None) is None:
        missing.append("dt")
    if not getattr(args, "out", None):
        missing.append("out")
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required resample setting(s): {joined}.")


def flatten_archive_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for ``archive-run`` / Live Phase-6.2 storage.

    The ``[live_archive]`` section is intentionally separate from ``[output]``:
    ``output.outdir`` is the live run folder, while ``live_archive.root`` is the
    long-term archive root that may contain many runs over many months.
    """

    archive = config.get("live_archive", config.get("archive", {})) or {}
    output = config.get("output", {}) or {}
    live = config.get("live", {}) or {}
    if not isinstance(archive, dict):
        raise ValueError("The 'live_archive' section must be a mapping when provided.")
    return {
        "run_dir": archive.get("run_dir", live.get("outdir", output.get("outdir", config.get("run_dir", "outputs/live_adaptation")))),
        "archive_root": archive.get("root", config.get("archive_root", "live_archive")),
        "archive_format": archive.get("format", config.get("archive_format", "parquet")),
        "archive_compression": archive.get("compression", config.get("archive_compression", "zstd")),
        "archive_write_csv_mirrors": bool(archive.get("write_csv_mirrors", config.get("archive_write_csv_mirrors", False))),
        "archive_strict_format": bool(archive.get("strict_format", config.get("archive_strict_format", False))),
        "archive_enabled": bool(archive.get("enabled", config.get("archive_enabled", False))),
        "archive_flush_rows": int(archive.get("flush_rows", config.get("archive_flush_rows", 10000))),
        "archive_flush_seconds": float(archive.get("flush_seconds", config.get("archive_flush_seconds", 30.0))),
    }


def flatten_archive_summary_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for ``archive-summarize`` / Live Phase-6.3 summaries."""

    archive = config.get("live_archive", config.get("archive", {})) or {}
    summaries = config.get("summaries", {}) or {}
    data = config.get("data", {}) or {}
    if not isinstance(archive, dict) or not isinstance(summaries, dict):
        raise ValueError("Sections 'live_archive' and 'summaries' must be mappings when provided.")
    return {
        "archive_root": archive.get("root", config.get("archive_root", "live_archive")),
        "summary_outdir": summaries.get("outdir", config.get("summary_outdir")),
        "windows_seconds": summaries.get("windows_seconds", config.get("windows_seconds", [60.0, 300.0, 3600.0])),
        "max_files_per_kind": summaries.get("max_files_per_kind", config.get("max_files_per_kind")),
        "state_cols": data.get("state_cols", config.get("state_cols")),
    }


def flatten_archive_quicklook_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for ``archive-quicklook``."""

    archive = config.get("live_archive", config.get("archive", {})) or {}
    quicklooks = config.get("quicklooks", {}) or {}
    summaries = config.get("summaries", {}) or {}
    if not isinstance(archive, dict) or not isinstance(quicklooks, dict):
        raise ValueError("Sections 'live_archive' and 'quicklooks' must be mappings when provided.")
    return {
        "archive_root": archive.get("root", config.get("archive_root", "live_archive")),
        "summaries_dir": summaries.get("outdir", quicklooks.get("summaries_dir", config.get("summaries_dir"))),
        "quicklook_outdir": quicklooks.get("outdir", config.get("quicklook_outdir")),
        "window_label": quicklooks.get("window_label", config.get("window_label", "60s")),
    }


def require_archive_fields(args: Any) -> None:
    """Validate required archive settings."""

    if not getattr(args, "run_dir", None):
        raise ValueError("Missing required archive setting: run_dir or live.outdir.")
    if not getattr(args, "archive_root", None):
        args.archive_root = "live_archive"


def require_archive_summary_fields(args: Any) -> None:
    """Validate required summary settings."""

    if not getattr(args, "archive_root", None):
        args.archive_root = "live_archive"
    if not getattr(args, "windows_seconds", None):
        args.windows_seconds = [60.0, 300.0, 3600.0]


def require_archive_quicklook_fields(args: Any) -> None:
    """Validate required quicklook settings."""

    if not getattr(args, "archive_root", None):
        args.archive_root = "live_archive"
    if not getattr(args, "window_label", None):
        args.window_label = "60s"

def expand_case_runs(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a workflow config into per-case fit runs.

    Each case inherits the base config and may override any data/model/preprocessing/output field.
    If a case has no explicit output directory, a stable folder is generated from
    ``output.root / case.name``.
    """

    base = flatten_fit_config(config)
    cases = config.get("cases")
    output = config.get("output", {}) or {}
    output_root = output.get("root", config.get("output_root", "outputs/workflow"))

    if not cases:
        run = dict(base)
        run["name"] = config.get("name", "fit")
        if run.get("outdir") in {None, "outputs/dmdc_fit"}:
            run["outdir"] = str(Path(output_root) / safe_name(run["name"]))
        return [run]

    if not isinstance(cases, list):
        raise ValueError("The 'cases' section must be a list of case mappings.")

    runs: list[dict[str, Any]] = []
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Case entry {idx} must be a mapping.")
        merged_structured = deep_merge(config, {"data": {}, "model": {}, "preprocessing": {}, "output": {}})
        # Allow both structured per-case sections and flat per-case keys.
        merged_structured = deep_merge(merged_structured, case)
        run = flatten_fit_config(merged_structured)
        run.update({k: v for k, v in case.items() if k in run or k in {"name"}})
        name = str(case.get("name") or case.get("case_id") or run.get("case_id") or f"case_{idx:03d}")
        run["name"] = name
        if not run.get("outdir") or run.get("outdir") == base.get("outdir"):
            run["outdir"] = str(Path(output_root) / safe_name(name))
        runs.append(run)
    return runs


def safe_name(value: object) -> str:
    """Convert an arbitrary case/workflow name into a filesystem-friendly folder name."""

    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9_.=-]+", "_", text)
    text = text.strip("._")
    return text or "unnamed"


def flatten_import_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten config keys for ``dmdc import-data``.

    Importer config follows the same central-study pattern as modeling/live
    commands: ``[importer]`` describes the source adapter, ``[data]`` describes
    canonical column names, and ``[output]`` describes where the tidy table goes.
    """

    importer = config.get("importer", {}) or {}
    data = config.get("data", {}) or {}
    output = config.get("output", {}) or {}
    if not isinstance(importer, dict) or not isinstance(data, dict) or not isinstance(output, dict):
        raise ValueError("Sections 'importer', 'data', and 'output' must be mappings when provided.")
    return {
        "source": importer.get("source", importer.get("path", data.get("path", config.get("source")))),
        "source_type": importer.get("type", config.get("source_type", "auto")),
        "out": importer.get("out", output.get("imported_data", output.get("data", config.get("out", "data/imported_data.parquet")))),
        "output_format": importer.get("output_format", output.get("format", config.get("output_format", "parquet"))),
        "sheet": importer.get("sheet", config.get("sheet")),
        "pattern": importer.get("pattern", config.get("pattern", "*.csv")),
        "column_map": importer.get("column_map", config.get("column_map")),
        "rename_col": importer.get("rename_col", config.get("rename_col", [])),
        "add_source_file_col": bool(importer.get("add_source_file_col", config.get("add_source_file_col", True))),
        "case_from_filename": bool(importer.get("case_from_filename", config.get("case_from_filename", False))),
        "max_files": importer.get("max_files", config.get("max_files")),
        "epics_pvs": importer.get("epics_pvs", config.get("epics_pvs")),
        "strict_parquet": bool(importer.get("strict_parquet", config.get("strict_parquet", False))),
        "skip_unstable_files": bool(importer.get("skip_unstable_files", config.get("skip_unstable_files", False))),
        "settle_seconds": float(importer.get("settle_seconds", config.get("settle_seconds", 0.0))),
    }


def require_import_fields(args: Any) -> None:
    """Validate required import-data settings."""

    if not getattr(args, "out", None):
        args.out = "data/imported_data.parquet"
    source_type = str(getattr(args, "source_type", "auto")).lower().replace("-", "_")
    if source_type not in {"epics", "epics_pv"} and not getattr(args, "source", None):
        raise ValueError("Missing import source. Provide --source or importer.source in config.")
    if source_type in {"epics", "epics_pv"} and not getattr(args, "epics_pvs", None):
        raise ValueError("EPICS import requires importer.epics_pvs mapping in config.")
