"""Command-line interface for DMDc analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from .data import load_timeseries, load_trajectories
from .config import (
    apply_config_defaults,
    expand_case_runs,
    flatten_fit_config,
    flatten_sensor_selection_config,
    flatten_pod_config,
    flatten_inspect_config,
    flatten_resample_config,
    flatten_pod_dmdc_config,
    flatten_pod_ml_config,
    flatten_validate_config,
    flatten_sweep_config,
    flatten_pod_sensors_config,
    flatten_live_config,
    flatten_live_prediction_config,
    flatten_live_estimation_config,
    flatten_live_monitoring_config,
    flatten_live_adaptation_config,
    flatten_live_dashboard_config,
    flatten_archive_config,
    flatten_archive_summary_config,
    flatten_archive_quicklook_config,
    flatten_import_config,
    load_config,
    require_fit_fields,
    require_sensor_fields,
    require_pod_fields,
    require_inspect_fields,
    require_resample_fields,
    require_pod_dmdc_fields,
    require_pod_ml_fields,
    require_validate_fields,
    require_sweep_fields,
    require_pod_sensors_fields,
    require_live_fields,
    require_live_prediction_fields,
    require_live_estimation_fields,
    require_live_monitoring_fields,
    require_live_adaptation_fields,
    require_live_dashboard_fields,
    require_archive_fields,
    require_archive_summary_fields,
    require_archive_quicklook_fields,
    require_import_fields,
)
from .delayed import make_delay_embedding, make_delay_embeddings_for_trajectories
from .diagnostics import evaluate_model, evaluate_trajectories, save_diagnostics
from .model import DMDcModel
from .sensor_selection import qr_sensor_ranking, reconstruction_error_vs_sensors
from .pod_sensors import run_pod_sensor_workflow
from .sweeps import run_rank_delay_sweep, parse_sweep_values
from .pod import PODBasis, save_reconstruction_error_vs_rank
from .reduced import PODDMDcPipeline
from .ml import PODDynamicsRegressor
from .splits import make_split, split_by_case_ids, split_by_fraction
from .validation import run_pod_dmdc_validation, evaluate_pod_dmdc_on_datasets
from .resampling import inspect_table, read_table, resample_all_cases
from .plotting import (
    plot_eigenvalues,
    plot_singular_values,
    plot_true_vs_predicted,
    plot_reconstruction_error_vs_sensors,
    plot_pod_singular_values,
    plot_pod_cumulative_energy,
    plot_pod_reconstruction_error_vs_rank,
    plot_pod_coefficients,
)
from .utils import ensure_dir, write_json
from .stability import analyze_transition_matrix, save_stability_outputs, plot_eigenvalues_table
from .baselines import fit_baseline_or_rom
from .dashboards import save_dashboard, plot_model_comparison
from .reports import generate_latex_report
from .metrics import rmse, relative_frobenius_error, error_by_column
from .provenance import write_provenance
from .case_quality import summarize_case_quality
from .operating_conditions import summarize_operating_conditions, operating_condition_warnings
from .uncertainty import uncertainty_table_from_case_metrics
from .recommendations import recommend_best_model, write_recommendation
from .loop_geometry import LoopGeometry, plot_error_vs_geometry, plot_selected_sensors_on_geometry, plot_pod_modes_vs_geometry
from .regularized import RegularizedDMDcModel
from .continuous import ContinuousDMDcModel, discrete_to_continuous
from .adaptive import AdaptiveDMDcModel
from .thermal_loop_example import write_thermal_loop_example
from .time_windows import filter_time_window
from .live import LiveIngestionConfig, run_live_ingestion
from .live_forecast import LivePredictionConfig, run_live_prediction
from .live_estimation import LiveEstimationConfig, run_live_estimation
from .live_monitoring import LiveMonitoringConfig, run_live_monitoring
from .live_adaptation import LiveAdaptationConfig, run_live_adaptation
from .live_dashboard import launch_streamlit_dashboard, write_dashboard_summary, write_archive_dashboard_summary
from .live_archive import LiveArchiveConfig, archive_live_run, read_archive_manifest
from .live_summaries import LiveSummaryConfig, summarize_live_archive
from .live_quicklooks import QuicklookConfig, make_archive_quicklooks
from .archive_search import ArchiveSearchConfig, search_archive
from .import_workflow import run_import_workflow
from .live_operator_report import generate_live_operator_report
from .model_registry import register_model, promote_model, resolve_model, read_registry_index, write_model_identity
from .archive_schema import validate_archive_schema, build_archive_context_index
from .campaign import run_campaign
from .resources import get_resource_summary, write_resource_summary
from .archive_benchmark import ArchiveBenchmarkConfig, run_archive_benchmark
from .hpc_workflows import write_hpc_workflow_plan
from .command_catalog import render_command_guide, write_command_guide


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DMDc/POD reduced-order modeling toolkit for time-series data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Start with: dmdc guide. Minimal reproducible workflow: dmdc campaign --config studies/my_loop/study_config.toml --steps import inspect compare. Live replay workflow: dmdc campaign --config studies/my_loop/study_config.toml --steps live_replay_adapt dashboard operator_report.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    guide = sub.add_parser(
        "guide",
        help="Print the streamlined workflow and command guide.",
        description="Shows the smallest set of commands needed for common workflows and points to the connected docs.",
    )
    guide.add_argument("--markdown", action="store_true", help="Render the guide as Markdown instead of plain text.")
    guide.add_argument("--out", default=None, help="Optional path to write the guide, e.g. outputs/command_guide.md.")

    import_data = sub.add_parser(
        "import-data",
        help="Import CSV/Excel/folder/EPICS data into a tidy CSV/Parquet table for ROM workflows.",
        description=(
            "Bridge current or archived data into the repo. Supports CSV, Excel, Parquet, "
            "folders of chunks, LabVIEW/DAQ folder drops, and optional EPICS PV snapshots. "
            "Recommended first step for messy real data: import-data -> inspect-data -> compare/sweep."
        ),
    )
    import_data.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [importer], [data], and [output] sections.")
    import_data.add_argument("--source", default=None, help="Input file/folder path. Not required for EPICS config with importer.epics_pvs.")
    import_data.add_argument("--source-type", default="auto", choices=["auto", "csv", "excel", "parquet", "folder", "labview_daq", "epics"], help="Importer adapter to use.")
    import_data.add_argument("--out", default=None, help="Canonical imported output path, e.g. data/simple_loop.parquet.")
    import_data.add_argument("--format", dest="output_format", default="parquet", choices=["parquet", "csv"], help="Output file format for the tidy imported table.")
    import_data.add_argument("--sheet", default=None, help="Excel sheet name/index for xlsx/xls imports.")
    import_data.add_argument("--pattern", default="*.csv", help="Glob pattern for folder/LabVIEW/DAQ imports.")
    import_data.add_argument("--column-map", default=None, help="JSON/TOML mapping from source names to canonical names.")
    import_data.add_argument("--rename-col", nargs="*", default=[], help="Inline rename pairs like TC01=TP1 Heater_W=q_heater.")
    import_data.add_argument("--case-from-filename", action="store_true", help="For folder imports, create case_id from each file stem when case_id is absent.")
    import_data.add_argument("--max-files", type=int, default=None, help="Only import the first N matching files. Useful for testing huge folders.")
    import_data.add_argument("--strict-parquet", action="store_true", help="Fail instead of falling back to CSV when Parquet support is unavailable.")
    import_data.add_argument("--skip-unstable-files", action="store_true", help="For folder/LabVIEW imports, skip files that still appear to be growing or empty.")
    import_data.add_argument("--settle-seconds", type=float, default=0.0, help="For folder/LabVIEW imports, wait this long and require file size to remain stable before reading.")

    fit = sub.add_parser("fit", help="Fit a DMDc model from time-series data.")
    fit.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    fit.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    fit.add_argument("--state-cols", nargs="+", default=None, help="State column names.")
    fit.add_argument("--input-cols", nargs="*", default=[], help="Input/control column names.")
    fit.add_argument("--time-col", default=None, help="Optional time column name.")
    fit.add_argument("--case-col", default=None, help="Optional case/group column.")
    fit.add_argument("--case-id", default=None, help="Optional case id to filter.")
    fit.add_argument("--rank", default="full", help="Rank: full, auto, integer, or energy fraction like 0.999.")
    fit.add_argument("--center", action="store_true", help="Center variables before fitting.")
    fit.add_argument("--scale", action="store_true", help="Scale variables before fitting.")
    fit.add_argument("--outdir", default=None, help="Output directory.")
    fit.add_argument("--plots", action="store_true", help="Save diagnostic plots.")
    fit.add_argument("--n-delays", type=int, default=1, help="Number of delay-coordinate state blocks. Use >1 for delay-DMD/DMDc.")

    pred = sub.add_parser("predict", help="Predict/roll out using a saved DMDc model.")
    pred.add_argument("--model", required=True, help="Path to saved model.pkl.")
    pred.add_argument("--data", required=True, help="Path to new CSV/Parquet/NPZ data with initial state and inputs.")
    pred.add_argument("--state-cols", nargs="+", required=True, help="State column names.")
    pred.add_argument("--input-cols", nargs="*", default=[], help="Input/control column names.")
    pred.add_argument("--time-col", default=None, help="Optional time column name.")
    pred.add_argument("--outdir", default="outputs/dmdc_predict", help="Output directory.")

    sel = sub.add_parser("select-sensors", help="Rank/select state variables using SVD modes and pivoted QR.")
    sel.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    sel.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    sel.add_argument("--state-cols", nargs="+", default=None, help="State column names to rank.")
    sel.add_argument("--time-col", default=None, help="Optional time column name.")
    sel.add_argument("--case-col", default=None, help="Optional case/group column. If supplied, all cases are stacked for SVD only; no transitions are formed.")
    sel.add_argument("--rank", default="full", help="SVD rank: full, auto, integer, or energy fraction like 0.999.")
    sel.add_argument("--n-sensors", type=int, default=None, help="Number of selected sensors/states. Defaults to rank used.")
    sel.add_argument("--center", action="store_true", help="Center state columns before SVD.")
    sel.add_argument("--scale", action="store_true", help="Scale state columns before SVD.")
    sel.add_argument("--outdir", default=None, help="Output directory.")
    sel.add_argument("--plots", action="store_true", help="Save singular-value and reconstruction-error plots.")

    pod = sub.add_parser("pod", help="Fit a POD/SVD reduced basis and save modal coefficients.")
    pod.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    pod.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    pod.add_argument("--state-cols", nargs="+", default=None, help="State column names used for POD snapshots.")
    pod.add_argument("--time-col", default=None, help="Optional time column name.")
    pod.add_argument("--case-col", default=None, help="Optional case/group column. All selected cases are stacked as POD snapshots.")
    pod.add_argument("--case-id", default=None, help="Optional single case id to filter before fitting POD.")
    pod.add_argument("--rank", default="full", help="POD rank: full, auto, integer, or energy fraction like 0.999.")
    pod.add_argument("--energy-threshold", type=float, default=None, help="Explicit cumulative energy threshold for POD rank selection.")
    pod.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    pod.add_argument("--scale", action="store_true", help="Scale states before POD.")
    pod.add_argument("--outdir", default=None, help="Output directory.")
    pod.add_argument("--plots", action="store_true", help="Save POD plots.")

    pod_sensors = sub.add_parser("pod-sensors", help="Select POD/Q-DEIM sensors and reconstruct the full state from sparse measurements.")
    pod_sensors.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    pod_sensors.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    pod_sensors.add_argument("--state-cols", nargs="+", default=None, help="Full-state columns used to fit POD and select sensors.")
    pod_sensors.add_argument("--time-col", default=None, help="Optional time column name.")
    pod_sensors.add_argument("--case-col", default=None, help="Optional case/group column. All selected cases are stacked for POD snapshots.")
    pod_sensors.add_argument("--case-id", default=None, help="Optional single case id to filter before fitting POD sensors.")
    pod_sensors.add_argument("--rank", default="0.999", help="POD rank: full, integer, or energy fraction like 0.999.")
    pod_sensors.add_argument("--n-sensors", type=int, default=None, help="Number of sparse sensors to select. Defaults to POD rank used.")
    pod_sensors.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    pod_sensors.add_argument("--scale", action="store_true", help="Scale states before POD.")
    pod_sensors.add_argument("--outdir", default=None, help="Output directory.")
    pod_sensors.add_argument("--plots", action="store_true", help="Save sparse-sensing reconstruction plots.")

    inspect = sub.add_parser("inspect-data", help="Inspect a CSV/Parquet time-series table before ROM fitting.")
    inspect.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file.")
    inspect.add_argument("--data", default=None, help="Path to CSV or Parquet data.")
    inspect.add_argument("--state-cols", nargs="*", default=[], help="State column names to inspect.")
    inspect.add_argument("--input-cols", nargs="*", default=[], help="Input/control column names to inspect.")
    inspect.add_argument("--time-col", default=None, help="Optional time column name.")
    inspect.add_argument("--case-col", default=None, help="Optional case/group column.")
    inspect.add_argument("--outdir", default=None, help="Output directory.")
    inspect.add_argument("--min-samples", type=int, default=3, help="Minimum samples required for a case to be considered usable.")
    inspect.add_argument("--expected-final-time", type=float, default=None, help="Optional expected final time for success/failed-case detection.")

    resample = sub.add_parser("resample", help="Resample a CSV/Parquet table to a uniform time step.")
    resample.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file.")
    resample.add_argument("--data", default=None, help="Path to CSV or Parquet data.")
    resample.add_argument("--time-col", default=None, help="Time column name.")
    resample.add_argument("--case-col", default=None, help="Optional case/group column.")
    resample.add_argument("--columns", nargs="*", default=None, help="Numeric columns to interpolate. Defaults to numeric non-time columns.")
    resample.add_argument("--dt", type=float, default=None, help="Target uniform time step.")
    resample.add_argument("--method", default="linear", help="Interpolation method. Currently only linear is supported.")
    resample.add_argument("--out", default=None, help="Output CSV path for resampled data.")

    pod_dmdc = sub.add_parser("pod-dmdc", help="Fit POD-DMDc: POD projection followed by DMD/DMDc in modal space.")
    pod_dmdc.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    pod_dmdc.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    pod_dmdc.add_argument("--state-cols", nargs="+", default=None, help="Full-state columns used to fit POD.")
    pod_dmdc.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns for DMDc. Omit for POD-DMD.")
    pod_dmdc.add_argument("--time-col", default=None, help="Optional time column name.")
    pod_dmdc.add_argument("--case-col", default=None, help="Optional case/group column for multi-trajectory fitting.")
    pod_dmdc.add_argument("--case-id", default=None, help="Optional single case id to filter.")
    pod_dmdc.add_argument("--pod-rank", default="0.999", help="POD rank: full, integer, or energy fraction such as 0.999.")
    pod_dmdc.add_argument("--dmdc-rank", default="full", help="Reduced DMDc rank: full, auto, integer, or energy fraction.")
    pod_dmdc.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    pod_dmdc.add_argument("--scale", action="store_true", help="Scale states before POD.")
    pod_dmdc.add_argument("--outdir", default=None, help="Output directory.")
    pod_dmdc.add_argument("--plots", action="store_true", help="Save POD-DMDc plots.")

    pod_ml = sub.add_parser("pod-ml", help="Fit optional ML dynamics in POD modal-coefficient space.")
    pod_ml.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file. CLI values override config values.")
    pod_ml.add_argument("--data", default=None, help="Path to CSV, Parquet, or NPZ data.")
    pod_ml.add_argument("--state-cols", nargs="+", default=None, help="Full-state columns used to fit POD.")
    pod_ml.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns. Omit for autonomous POD-ML dynamics.")
    pod_ml.add_argument("--time-col", default=None, help="Optional time column name.")
    pod_ml.add_argument("--case-col", default=None, help="Optional case/group column for multi-trajectory fitting.")
    pod_ml.add_argument("--case-id", default=None, help="Optional single case id to filter.")
    pod_ml.add_argument("--pod-rank", default="0.999", help="POD rank: full, integer, or energy fraction such as 0.999.")
    pod_ml.add_argument("--model-type", default="ridge", choices=["ridge", "random_forest", "gradient_boosting", "mlp"], help="Optional scikit-learn regressor used on POD coefficients.")
    pod_ml.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    pod_ml.add_argument("--scale", action="store_true", help="Scale states before POD.")
    pod_ml.add_argument("--recursive-rollout", action="store_true", default=True, help="Recursively feed predicted modal coefficients during rollouts.")
    pod_ml.add_argument("--outdir", default=None, help="Output directory.")
    pod_ml.add_argument("--plots", action="store_true", help="Save POD-ML plots.")

    validate = sub.add_parser("validate", help="Train on some cases and evaluate POD-DMDc on unseen cases.")
    validate.add_argument("--config", default=None, help="Optional JSON/TOML/YAML validation config.")
    validate.add_argument("--data", default=None, help="Path to CSV or Parquet data containing multiple cases.")
    validate.add_argument("--state-cols", nargs="+", default=None, help="State column names.")
    validate.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    validate.add_argument("--time-col", default=None, help="Optional time column name.")
    validate.add_argument("--case-col", default=None, help="Required case/group column.")
    validate.add_argument("--train-cases", nargs="*", default=None, help="Explicit train case ids.")
    validate.add_argument("--test-cases", nargs="*", default=None, help="Explicit held-out test case ids.")
    validate.add_argument("--train-fraction", type=float, default=0.7, help="Deterministic case fraction for training if explicit cases are not supplied.")
    validate.add_argument("--split-strategy", default="by_case_fraction", help="Split strategy: explicit_case_lists or by_case_fraction.")
    validate.add_argument("--pod-rank", default="0.999", help="POD rank: full, integer, or energy fraction.")
    validate.add_argument("--dmdc-rank", default="full", help="Reduced DMDc rank.")
    validate.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    validate.add_argument("--scale", action="store_true", help="Scale states before POD.")
    validate.add_argument("--forecast-horizons", nargs="*", type=int, default=[1, 5, 10], help="Forecast horizons in steps.")
    validate.add_argument("--outdir", default=None, help="Output directory.")
    validate.add_argument("--plots", action="store_true", help="Save validation plots.")



    compare = sub.add_parser("compare", help="Compare baselines, DMDc, adaptive DMDc, POD-DMDc, and optional POD-ML on held-out cases.")
    compare.add_argument("--config", default=None, help="Optional JSON/TOML/YAML config file.")
    compare.add_argument("--data", default=None, help="Path to CSV or Parquet data containing multiple cases.")
    compare.add_argument("--state-cols", nargs="+", default=None, help="State columns.")
    compare.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    compare.add_argument("--time-col", default=None, help="Optional time column.")
    compare.add_argument("--case-col", default=None, help="Case/group column.")
    compare.add_argument("--train-cases", nargs="*", default=None, help="Case ids used for training.")
    compare.add_argument("--test-cases", nargs="*", default=None, help="Case ids used for testing.")
    compare.add_argument("--train-fraction", type=float, default=0.7, help="Fallback train fraction when explicit cases are omitted.")
    compare.add_argument("--models", nargs="+", default=["persistence", "mean", "dmdc", "pod_dmdc"], help="Models to compare. Supports persistence, mean, dmdc, ridge_dmdc, adaptive_dmdc, pod_dmdc, and pod_ml_*.")
    compare.add_argument("--pod-rank", default="0.999", help="POD rank for POD-DMDc.")
    compare.add_argument("--dmdc-rank", default="full", help="DMDc rank for DMDc/POD-DMDc.")
    compare.add_argument("--center", action="store_true", default=False, help="Center states before POD for POD-DMDc.")
    compare.add_argument("--scale", action="store_true", help="Scale states before POD for POD-DMDc.")
    compare.add_argument("--outdir", default=None, help="Output directory.")
    compare.add_argument("--plots", action="store_true", help="Save comparison/stability plots.")
    compare.add_argument("--report", action="store_true", help="Generate a LaTeX report after comparison.")

    sweep = sub.add_parser("sweep", help="Run model/rank/delay sweeps with held-out validation, including adaptive_dmdc for nonuniform time data.")
    sweep.add_argument("--config", default=None, help="Optional JSON/TOML/YAML sweep config file.")
    sweep.add_argument("--data", default=None, help="Path to CSV or Parquet data containing multiple cases.")
    sweep.add_argument("--state-cols", nargs="+", default=None, help="State columns.")
    sweep.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    sweep.add_argument("--time-col", default=None, help="Optional time column.")
    sweep.add_argument("--case-col", default=None, help="Case/group column.")
    sweep.add_argument("--train-cases", nargs="*", default=None, help="Explicit training case ids.")
    sweep.add_argument("--test-cases", nargs="*", default=None, help="Explicit held-out test case ids.")
    sweep.add_argument("--train-fraction", type=float, default=0.7, help="Fallback train fraction when explicit cases are omitted.")
    sweep.add_argument("--models", nargs="+", default=["persistence", "mean", "dmdc", "pod_dmdc"], help="Models to sweep, e.g. adaptive_dmdc dmdc ridge_dmdc pod_dmdc pod_ml_ridge.")
    sweep.add_argument("--pod-ranks", nargs="*", default=None, help="POD-rank candidates, e.g. 2 4 0.999 full.")
    sweep.add_argument("--dmdc-ranks", nargs="*", default=None, help="DMDc-rank candidates, e.g. full 2 4.")
    sweep.add_argument("--n-delays", dest="n_delays_list", nargs="*", default=None, help="Delay-block candidates, e.g. 1 2 4.")
    sweep.add_argument("--center", action="store_true", default=False, help="Center states before POD. Config defaults may set this true.")
    sweep.add_argument("--scale", action="store_true", help="Scale states before POD.")
    sweep.add_argument("--outdir", default=None, help="Output directory.")
    sweep.add_argument("--plots", action="store_true", help="Save sweep plots.")
    sweep.add_argument("--report", action="store_true", help="Generate a LaTeX report after the sweep.")

    continuous = sub.add_parser("continuous", help="Fit a discrete DMDc model and save an approximate continuous-time generator A_c=logm(A_d)/dt.")
    continuous.add_argument("--data", required=True, help="Path to CSV/Parquet/NPZ data.")
    continuous.add_argument("--state-cols", nargs="+", required=True, help="State columns.")
    continuous.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    continuous.add_argument("--time-col", default=None, help="Optional time column used to infer dt when --dt is omitted.")
    continuous.add_argument("--case-col", default=None, help="Optional case/group column for filtering one case.")
    continuous.add_argument("--case-id", default=None, help="Optional case id to filter before fitting continuous-time model.")
    continuous.add_argument("--dt", type=float, default=None, help="Uniform sample time step. If omitted, median dt from --time-col is used.")
    continuous.add_argument("--rank", default="full", help="Discrete DMDc rank used before continuous conversion.")
    continuous.add_argument("--outdir", default="outputs/continuous_dmdc", help="Output directory.")

    adaptive = sub.add_parser("adaptive-fit", help="Fit variable-time-step/adaptive DMDc using dx/dt = A_c x + B_c u and actual dt values.")
    adaptive.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config file. Uses data/model/output sections like fit.")
    adaptive.add_argument("--data", default=None, help="Path to CSV/Parquet/NPZ data.")
    adaptive.add_argument("--state-cols", nargs="+", default=None, help="State columns.")
    adaptive.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    adaptive.add_argument("--time-col", default=None, help="Physical time column. Required for adaptive fitting.")
    adaptive.add_argument("--case-col", default=None, help="Optional case/group column for multi-case fitting.")
    adaptive.add_argument("--case-id", default=None, help="Optional single case id to filter.")
    adaptive.add_argument("--rank", default="full", help="SVD rank: full, auto, integer, or energy fraction such as 0.999.")
    adaptive.add_argument("--alpha", type=float, default=1e-8, help="Ridge regularization used when fitting the continuous generator.")
    adaptive.add_argument("--outdir", default=None, help="Output directory.")
    adaptive.add_argument("--plots", action="store_true", help="Save true-vs-rollout plot for the first/only case.")

    thermal = sub.add_parser("make-thermal-loop-example", help="Create a synthetic TAMU/SAM-like thermal-loop dataset, geometry file, configs, and tutorial outputs.")
    thermal.add_argument("--outdir", default="examples/end_to_end_thermal_loop_study", help="Directory where the tutorial assets are written.")
    thermal.add_argument("--n-time", type=int, default=160, help="Number of time samples per case.")
    thermal.add_argument("--seed", type=int, default=7, help="Random seed used for reproducible synthetic noise.")

    recommend = sub.add_parser("recommend", help="Recommend the best model from a comparison or sweep dashboard.")
    recommend.add_argument("--table", required=True, help="Path to model_comparison.csv or sweep_results.csv.")
    recommend.add_argument("--outdir", default="outputs/recommendation", help="Output directory for recommendation files.")
    recommend.add_argument("--allow-unstable", action="store_true", help="Allow candidates marked potentially unstable.")

    report = sub.add_parser("report", help="Generate a LaTeX report from an existing run directory.")
    report.add_argument("--run", required=True, help="Run/output directory to summarize.")
    report.add_argument("--out", default=None, help="Optional output report.tex path.")
    report.add_argument("--compile-pdf", action="store_true", help="Attempt to compile with pdflatex if available.")

    live_replay = sub.add_parser(
        "live-replay",
        help="Replay an existing CSV as a live stream and write raw/clean buffer logs. This is the safest first test of online workflows.",
    )
    live_replay.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live-stream config file.")
    live_replay.add_argument("--data", dest="path", default=None, help="CSV file to replay as if rows were arriving live.")
    live_replay.add_argument("--state-cols", nargs="+", default=None, help="State columns expected by the online ROM layer.")
    live_replay.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    live_replay.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_replay.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_replay.add_argument("--case-id", default=None, help="Optional case id to replay from a multi-case CSV.")
    live_replay.add_argument("--chunk-size", type=int, default=1, help="Rows emitted per adapter poll.")
    live_replay.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to replay.")
    live_replay.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_replay.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_replay.add_argument("--outdir", default=None, help="Output folder for stream logs and summaries.")
    live_replay.add_argument("--save-every-batch", action="store_true", help="Write logs after each batch as well as at the end.")

    live_run = sub.add_parser(
        "live-run",
        help="Tail a CSV file being appended by a live logger and write raw/clean buffer logs. Use --max-polls or Ctrl-C for open-ended runs.",
    )
    live_run.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live-stream config file.")
    live_run.add_argument("--data", dest="path", default=None, help="CSV file to tail as rows are appended.")
    live_run.add_argument("--state-cols", nargs="+", default=None, help="State columns expected by the online ROM layer.")
    live_run.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns.")
    live_run.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_run.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_run.add_argument("--case-id", default=None, help="Optional case id to keep from a multi-case CSV.")
    live_run.add_argument("--poll-seconds", type=float, default=1.0, help="Seconds between CSV-tail polls.")
    live_run.add_argument("--max-samples", type=int, default=None, help="Maximum new samples to ingest before exiting.")
    live_run.add_argument("--max-polls", type=int, default=None, help="Maximum polls before exiting. Useful for testing tail mode.")
    live_run.add_argument("--start-at-end", action="store_true", help="Ignore rows already present at startup and only ingest newly appended rows.")
    live_run.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_run.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_run.add_argument("--outdir", default=None, help="Output folder for stream logs and summaries.")
    live_run.add_argument("--save-every-batch", action="store_true", help="Write logs after each batch as well as at the end.")

    live_replay_predict = sub.add_parser(
        "live-replay-predict",
        help="Replay a CSV stream and produce forecasts from a saved offline ROM. Phase-2 live workflow; no Kalman filtering or residual alerts yet.",
    )
    live_replay_predict.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live prediction config file.")
    live_replay_predict.add_argument("--data", dest="path", default=None, help="CSV file to replay as live data.")
    live_replay_predict.add_argument("--model", dest="model_path", default=None, help="Saved model path, e.g. adaptive_model.pkl, model.pkl, pod_dmdc_model.pkl.")
    live_replay_predict.add_argument("--state-cols", nargs="+", default=None, help="State columns expected by the saved model.")
    live_replay_predict.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_replay_predict.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_replay_predict.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_replay_predict.add_argument("--case-id", default=None, help="Optional case id to replay from a multi-case CSV.")
    live_replay_predict.add_argument("--chunk-size", type=int, default=1, help="Rows emitted per adapter poll.")
    live_replay_predict.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to replay.")
    live_replay_predict.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_replay_predict.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_replay_predict.add_argument("--forecast-horizons-seconds", nargs="+", type=float, default=None, help="Physical forecast horizons, e.g. 5 10 30 60.")
    live_replay_predict.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete models. Adaptive models use horizons directly.")
    live_replay_predict.add_argument("--outdir", default=None, help="Output folder for live forecasts and logs.")
    live_replay_predict.add_argument("--save-every-batch", action="store_true", help="Write logs/forecasts after each batch as well as at the end.")

    live_run_predict = sub.add_parser(
        "live-run-predict",
        help="Tail a live CSV logger and produce forecasts from a saved offline ROM. Use --max-polls while testing; Ctrl-C for open-ended runs.",
    )
    live_run_predict.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live prediction config file.")
    live_run_predict.add_argument("--data", dest="path", default=None, help="CSV file to tail as rows are appended.")
    live_run_predict.add_argument("--model", dest="model_path", default=None, help="Saved model path, e.g. adaptive_model.pkl, model.pkl, pod_dmdc_model.pkl.")
    live_run_predict.add_argument("--state-cols", nargs="+", default=None, help="State columns expected by the saved model.")
    live_run_predict.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_run_predict.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_run_predict.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_run_predict.add_argument("--case-id", default=None, help="Optional case id to keep from a multi-case CSV.")
    live_run_predict.add_argument("--poll-seconds", type=float, default=1.0, help="Seconds between CSV-tail polls.")
    live_run_predict.add_argument("--max-samples", type=int, default=None, help="Maximum new samples to ingest before exiting.")
    live_run_predict.add_argument("--max-polls", type=int, default=None, help="Maximum polls before exiting. Useful for testing tail mode.")
    live_run_predict.add_argument("--start-at-end", action="store_true", help="Ignore rows already present at startup and only ingest newly appended rows.")
    live_run_predict.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_run_predict.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_run_predict.add_argument("--forecast-horizons-seconds", nargs="+", type=float, default=None, help="Physical forecast horizons, e.g. 5 10 30 60.")
    live_run_predict.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete models. Adaptive models use horizons directly.")
    live_run_predict.add_argument("--outdir", default=None, help="Output folder for live forecasts and logs.")
    live_run_predict.add_argument("--save-every-batch", action="store_true", help="Write logs/forecasts after each batch as well as at the end.")


    live_replay_estimate = sub.add_parser(
        "live-replay-estimate",
        help="Replay a CSV stream and estimate the full state with a POD-Kalman filter from a saved POD-DMDc model. Phase-3 live workflow; no residual alerts or online retraining yet.",
    )
    live_replay_estimate.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live estimation config file.")
    live_replay_estimate.add_argument("--data", dest="path", default=None, help="CSV file to replay as live data.")
    live_replay_estimate.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_replay_estimate.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_replay_estimate.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_replay_estimate.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_replay_estimate.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_replay_estimate.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_replay_estimate.add_argument("--case-id", default=None, help="Optional case id to replay from a multi-case CSV.")
    live_replay_estimate.add_argument("--chunk-size", type=int, default=1, help="Rows emitted per adapter poll.")
    live_replay_estimate.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to replay.")
    live_replay_estimate.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_replay_estimate.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_replay_estimate.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_replay_estimate.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_replay_estimate.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_replay_estimate.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Optional physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_replay_estimate.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_replay_estimate.add_argument("--outdir", default=None, help="Output folder for estimates, innovations, and optional forecasts.")
    live_replay_estimate.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")

    live_run_estimate = sub.add_parser(
        "live-run-estimate",
        help="Tail a live CSV logger and estimate the full state with POD-Kalman filtering. Use --max-polls while testing; Ctrl-C for open-ended runs.",
    )
    live_run_estimate.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live estimation config file.")
    live_run_estimate.add_argument("--data", dest="path", default=None, help="CSV file to tail as rows are appended.")
    live_run_estimate.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_run_estimate.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_run_estimate.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_run_estimate.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_run_estimate.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_run_estimate.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_run_estimate.add_argument("--case-id", default=None, help="Optional case id to keep from a multi-case CSV.")
    live_run_estimate.add_argument("--poll-seconds", type=float, default=1.0, help="Seconds between CSV-tail polls.")
    live_run_estimate.add_argument("--max-samples", type=int, default=None, help="Maximum new samples to ingest before exiting.")
    live_run_estimate.add_argument("--max-polls", type=int, default=None, help="Maximum polls before exiting. Useful for testing tail mode.")
    live_run_estimate.add_argument("--start-at-end", action="store_true", help="Ignore rows already present at startup and only ingest newly appended rows.")
    live_run_estimate.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_run_estimate.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_run_estimate.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_run_estimate.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_run_estimate.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_run_estimate.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Optional physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_run_estimate.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_run_estimate.add_argument("--outdir", default=None, help="Output folder for estimates, innovations, and optional forecasts.")
    live_run_estimate.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")


    live_replay_monitor = sub.add_parser(
        "live-replay-monitor",
        help="Replay a CSV stream, run POD-Kalman estimation/forecasts, and emit Phase-4 residual alerts plus trust scores.",
    )
    live_replay_monitor.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live monitoring config file.")
    live_replay_monitor.add_argument("--data", dest="path", default=None, help="CSV file to replay as live data.")
    live_replay_monitor.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_replay_monitor.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_replay_monitor.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_replay_monitor.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_replay_monitor.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_replay_monitor.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_replay_monitor.add_argument("--case-id", default=None, help="Optional case id to replay from a multi-case CSV.")
    live_replay_monitor.add_argument("--chunk-size", type=int, default=1, help="Rows emitted per adapter poll.")
    live_replay_monitor.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to replay.")
    live_replay_monitor.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_replay_monitor.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_replay_monitor.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_replay_monitor.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_replay_monitor.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_replay_monitor.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_replay_monitor.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_replay_monitor.add_argument("--residual-abs-threshold", type=float, default=5.0, help="Alert threshold for |measured - forecast| in state units.")
    live_replay_monitor.add_argument("--innovation-abs-threshold", type=float, default=5.0, help="Alert threshold for absolute Kalman innovation in measurement units.")
    live_replay_monitor.add_argument("--innovation-norm-threshold", type=float, default=None, help="Optional threshold for total Kalman innovation norm.")
    live_replay_monitor.add_argument("--covariance-trace-threshold", type=float, default=None, help="Optional threshold for modal covariance trace.")
    live_replay_monitor.add_argument("--forecast-match-tolerance-seconds", type=float, default=None, help="Tolerance for matching forecast target times to measurements.")
    live_replay_monitor.add_argument("--max-abs-forecast-value", type=float, default=None, help="Optional sanity bound for estimated/forecast state magnitude.")
    live_replay_monitor.add_argument("--outdir", default=None, help="Output folder for estimates, forecasts, alerts, and trust scores.")
    live_replay_monitor.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")
    live_replay_monitor.set_defaults(operating_ranges=None)

    live_run_monitor = sub.add_parser(
        "live-run-monitor",
        help="Tail a live CSV logger, run POD-Kalman estimation/forecasts, and emit Phase-4 residual alerts plus trust scores.",
    )
    live_run_monitor.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live monitoring config file.")
    live_run_monitor.add_argument("--data", dest="path", default=None, help="CSV file to tail as rows are appended.")
    live_run_monitor.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_run_monitor.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_run_monitor.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_run_monitor.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_run_monitor.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_run_monitor.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_run_monitor.add_argument("--case-id", default=None, help="Optional case id to keep from a multi-case CSV.")
    live_run_monitor.add_argument("--poll-seconds", type=float, default=1.0, help="Seconds between CSV-tail polls.")
    live_run_monitor.add_argument("--max-samples", type=int, default=None, help="Maximum new samples to ingest before exiting.")
    live_run_monitor.add_argument("--max-polls", type=int, default=None, help="Maximum polls before exiting. Useful for testing tail mode.")
    live_run_monitor.add_argument("--start-at-end", action="store_true", help="Ignore rows already present at startup and only ingest newly appended rows.")
    live_run_monitor.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_run_monitor.add_argument("--buffer-max-samples", type=float, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_run_monitor.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_run_monitor.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_run_monitor.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_run_monitor.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_run_monitor.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_run_monitor.add_argument("--residual-abs-threshold", type=float, default=5.0, help="Alert threshold for |measured - forecast| in state units.")
    live_run_monitor.add_argument("--innovation-abs-threshold", type=float, default=5.0, help="Alert threshold for absolute Kalman innovation in measurement units.")
    live_run_monitor.add_argument("--innovation-norm-threshold", type=float, default=None, help="Optional threshold for total Kalman innovation norm.")
    live_run_monitor.add_argument("--covariance-trace-threshold", type=float, default=None, help="Optional threshold for modal covariance trace.")
    live_run_monitor.add_argument("--forecast-match-tolerance-seconds", type=float, default=None, help="Tolerance for matching forecast target times to measurements.")
    live_run_monitor.add_argument("--max-abs-forecast-value", type=float, default=None, help="Optional sanity bound for estimated/forecast state magnitude.")
    live_run_monitor.add_argument("--outdir", default=None, help="Output folder for estimates, forecasts, alerts, and trust scores.")
    live_run_monitor.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")
    live_run_monitor.set_defaults(operating_ranges=None)

    live_replay_adapt = sub.add_parser(
        "live-replay-adapt",
        help="Replay a CSV stream, monitor it, and apply Live Phase-6.1 bounded bias correction with full audit logs.",
    )
    live_replay_adapt.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live adaptation config file.")
    live_replay_adapt.add_argument("--data", dest="path", default=None, help="CSV file to replay as live data.")
    live_replay_adapt.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_replay_adapt.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_replay_adapt.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_replay_adapt.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_replay_adapt.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_replay_adapt.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_replay_adapt.add_argument("--case-id", default=None, help="Optional case id to replay from a multi-case CSV.")
    live_replay_adapt.add_argument("--chunk-size", type=int, default=1, help="Rows emitted per adapter poll.")
    live_replay_adapt.add_argument("--max-samples", type=int, default=None, help="Maximum number of samples to replay.")
    live_replay_adapt.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_replay_adapt.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_replay_adapt.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_replay_adapt.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_replay_adapt.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_replay_adapt.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_replay_adapt.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_replay_adapt.add_argument("--residual-abs-threshold", type=float, default=5.0, help="Alert threshold for |measured - forecast| in state units.")
    live_replay_adapt.add_argument("--innovation-abs-threshold", type=float, default=5.0, help="Alert threshold for absolute Kalman innovation in measurement units.")
    live_replay_adapt.add_argument("--innovation-norm-threshold", type=float, default=None, help="Optional threshold for total Kalman innovation norm.")
    live_replay_adapt.add_argument("--covariance-trace-threshold", type=float, default=None, help="Optional threshold for modal covariance trace.")
    live_replay_adapt.add_argument("--forecast-match-tolerance-seconds", type=float, default=None, help="Tolerance for matching forecast target times to measurements.")
    live_replay_adapt.add_argument("--adaptation-method", default="horizon_state_bias", choices=["state_bias", "horizon_state_bias"], help="Bias mode: one bias per state or per state/horizon.")
    live_replay_adapt.add_argument("--bias-learning-rate", type=float, default=0.01, help="Exponential-smoothing rate for bias updates.")
    live_replay_adapt.add_argument("--max-abs-bias", type=float, default=10.0, help="Hard bound on the magnitude of any learned bias.")
    live_replay_adapt.add_argument("--max-update-step", type=float, default=0.25, help="Maximum change allowed for one bias update.")
    live_replay_adapt.add_argument("--update-only-when-trust-above", type=float, default=0.70, help="Skip bias updates when trust score is below this value.")
    live_replay_adapt.add_argument("--clip-residual-abs", type=float, default=20.0, help="Clip residuals before updating bias. Set negative in config is not supported; use config null to disable.")
    live_replay_adapt.add_argument("--disable-bias-correction", dest="adaptation_enabled", action="store_false", help="Run monitoring but do not update/apply bias.")
    live_replay_adapt.add_argument("--outdir", default=None, help="Output folder for estimates, forecasts, alerts, trust, and bias records.")
    live_replay_adapt.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")
    live_replay_adapt.set_defaults(operating_ranges=None, adaptation_enabled=True, skip_when_outside_training_envelope=True, skip_on_alert_severity=["critical"], apply_bias_to_forecasts=True)

    live_run_adapt = sub.add_parser(
        "live-run-adapt",
        help="Tail a live CSV logger, monitor it, and apply Live Phase-6.1 bounded bias correction with full audit logs.",
    )
    live_run_adapt.add_argument("--config", default=None, help="Optional TOML/JSON/YAML live adaptation config file.")
    live_run_adapt.add_argument("--data", dest="path", default=None, help="CSV file to tail as rows are appended.")
    live_run_adapt.add_argument("--model", dest="model_path", default=None, help="Saved POD-DMDc model path, usually pod_dmdc_model.pkl.")
    live_run_adapt.add_argument("--state-cols", nargs="*", default=None, help="Full model state names. If omitted, inferred from the saved POD-DMDc model when possible.")
    live_run_adapt.add_argument("--measurement-cols", nargs="+", default=None, help="Measured sensor columns present in the stream. May be a subset of state-cols.")
    live_run_adapt.add_argument("--input-cols", nargs="*", default=[], help="Optional input/control columns expected by the saved model.")
    live_run_adapt.add_argument("--time-col", default=None, help="Physical time column. Nonuniform/adaptive time is expected.")
    live_run_adapt.add_argument("--case-col", default=None, help="Optional case/group column.")
    live_run_adapt.add_argument("--case-id", default=None, help="Optional case id to keep from a multi-case CSV.")
    live_run_adapt.add_argument("--poll-seconds", type=float, default=1.0, help="Seconds between CSV-tail polls.")
    live_run_adapt.add_argument("--max-samples", type=int, default=None, help="Maximum new samples to ingest before exiting.")
    live_run_adapt.add_argument("--max-polls", type=int, default=None, help="Maximum polls before exiting. Useful for testing tail mode.")
    live_run_adapt.add_argument("--start-at-end", action="store_true", help="Ignore rows already present at startup and only ingest newly appended rows.")
    live_run_adapt.add_argument("--buffer-seconds", type=float, default=None, help="Rolling physical-time buffer length in seconds.")
    live_run_adapt.add_argument("--buffer-max-samples", type=int, default=None, help="Maximum number of clean samples kept in memory/logged clean buffer.")
    live_run_adapt.add_argument("--process-noise", type=float, default=1.0e-6, help="POD modal process-noise scalar Q = q I.")
    live_run_adapt.add_argument("--measurement-noise", type=float, default=1.0e-3, help="Measurement-noise scalar R = r I in sensor units.")
    live_run_adapt.add_argument("--initial-covariance", type=float, default=1.0, help="Initial POD modal covariance scalar P0 = p I.")
    live_run_adapt.add_argument("--forecast-horizons-seconds", nargs="*", type=float, default=None, help="Physical forecast horizons from the filtered state, e.g. 5 10 30.")
    live_run_adapt.add_argument("--discrete-dt-seconds", type=float, default=None, help="Seconds per sample step for discrete POD-DMDc forecasts.")
    live_run_adapt.add_argument("--residual-abs-threshold", type=float, default=5.0, help="Alert threshold for |measured - forecast| in state units.")
    live_run_adapt.add_argument("--innovation-abs-threshold", type=float, default=5.0, help="Alert threshold for absolute Kalman innovation in measurement units.")
    live_run_adapt.add_argument("--innovation-norm-threshold", type=float, default=None, help="Optional threshold for total Kalman innovation norm.")
    live_run_adapt.add_argument("--covariance-trace-threshold", type=float, default=None, help="Optional threshold for modal covariance trace.")
    live_run_adapt.add_argument("--forecast-match-tolerance-seconds", type=float, default=None, help="Tolerance for matching forecast target times to measurements.")
    live_run_adapt.add_argument("--adaptation-method", default="horizon_state_bias", choices=["state_bias", "horizon_state_bias"], help="Bias mode: one bias per state or per state/horizon.")
    live_run_adapt.add_argument("--bias-learning-rate", type=float, default=0.01, help="Exponential-smoothing rate for bias updates.")
    live_run_adapt.add_argument("--max-abs-bias", type=float, default=10.0, help="Hard bound on the magnitude of any learned bias.")
    live_run_adapt.add_argument("--max-update-step", type=float, default=0.25, help="Maximum change allowed for one bias update.")
    live_run_adapt.add_argument("--update-only-when-trust-above", type=float, default=0.70, help="Skip bias updates when trust score is below this value.")
    live_run_adapt.add_argument("--clip-residual-abs", type=float, default=20.0, help="Clip residuals before updating bias.")
    live_run_adapt.add_argument("--disable-bias-correction", dest="adaptation_enabled", action="store_false", help="Run monitoring but do not update/apply bias.")
    live_run_adapt.add_argument("--outdir", default=None, help="Output folder for estimates, forecasts, alerts, trust, and bias records.")
    live_run_adapt.add_argument("--save-every-batch", action="store_true", help="Write logs/estimates after each batch as well as at the end.")
    live_run_adapt.set_defaults(operating_ranges=None, adaptation_enabled=True, skip_when_outside_training_envelope=True, skip_on_alert_severity=["critical"], apply_bias_to_forecasts=True)

    live_dashboard = sub.add_parser(
        "live-dashboard",
        help="Launch a polished Streamlit dashboard for live monitoring outputs, or write a dashboard summary JSON.",
    )
    live_dashboard.add_argument("--config", default=None, help="Optional TOML/JSON/YAML dashboard config file.")
    live_dashboard.add_argument("--run-dir", default=None, help="Existing live output directory, for example outputs/live_monitoring.")
    live_dashboard.add_argument("--archive-root", default=None, help="Long-term live archive root. If provided, dashboard opens summary-first archive mode.")
    live_dashboard.add_argument("--mode", default="auto", choices=["auto", "run", "archive"], help="Dashboard source mode. auto uses archive mode when --archive-root is supplied.")
    live_dashboard.add_argument("--window-label", default="60s", help="Archive summary window label to display, e.g. 60s, 300s, or 3600s.")
    live_dashboard.add_argument("--refresh-seconds", type=float, default=2.0, help="Suggested dashboard refresh interval shown in the UI.")
    live_dashboard.add_argument("--host", default=None, help="Optional Streamlit server address, for example 0.0.0.0.")
    live_dashboard.add_argument("--port", type=int, default=None, help="Optional Streamlit server port.")
    live_dashboard.add_argument("--theme", default=None, help="Optional dashboard theme label stored/passed to the app.")
    live_dashboard.add_argument("--view", default="operator", choices=["operator", "technical"], help="Dashboard view. operator shows presentation-friendly KPIs first; technical emphasizes detailed tabs.")
    live_dashboard.add_argument("--geometry", default=None, help="Optional loop geometry JSON/TOML file for presentation-grade operator schematic.")
    live_dashboard.add_argument("--residual-warning-threshold", type=float, default=2.0, help="Residual magnitude where schematic sensors turn amber/warning.")
    live_dashboard.add_argument("--residual-critical-threshold", type=float, default=5.0, help="Residual magnitude where schematic sensors turn red/critical.")
    live_dashboard.add_argument(
        "--write-summary-only",
        action="store_true",
        help="Do not launch Streamlit; just write live_dashboard_summary.json. Useful for CI and report automation.",
    )

    live_report = sub.add_parser(
        "live-operator-report",
        help="Generate a compact Markdown/HTML operator report from a live run folder or archive.",
        description="Creates a meeting-friendly summary of status, trust, alerts, residuals, and bias correction. It is advisory only and does not control hardware.",
    )
    live_report.add_argument("--run-dir", default=None, help="Live output directory, e.g. outputs/live_adaptation_replay.")
    live_report.add_argument("--archive-root", default=None, help="Long-term archive root. If supplied, creates an archive-level operator report.")
    live_report.add_argument("--outdir", default="outputs/live_operator_report", help="Output directory for live_operator_report.md/html/json.")
    live_report.add_argument("--window-label", default="60s", help="Archive summary window label for archive reports.")

    archive_run = sub.add_parser(
        "archive-run",
        help="Archive one live run directory into partitioned CSV/Parquet storage with a manifest (Live Phase-6.2).",
    )
    archive_run.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [live_archive] settings.")
    archive_run.add_argument("--run-dir", default=None, help="Live output directory to archive, e.g. outputs/live_adaptation_replay.")
    archive_run.add_argument("--archive-root", default=None, help="Long-term archive root directory.")
    archive_run.add_argument("--format", dest="archive_format", default="parquet", choices=["parquet", "csv"], help="Preferred archive file format. Parquet falls back to CSV unless strict format is enabled.")
    archive_run.add_argument("--compression", dest="archive_compression", default="zstd", help="Parquet compression codec, e.g. zstd or snappy.")
    archive_run.add_argument("--write-csv-mirrors", dest="archive_write_csv_mirrors", action="store_true", help="Also write CSV copies next to Parquet files. Avoid for very large archives.")
    archive_run.add_argument("--strict-format", dest="archive_strict_format", action="store_true", help="Fail instead of falling back to CSV if Parquet support is unavailable.")
    archive_run.add_argument("--flush-rows", dest="archive_flush_rows", type=int, default=10000, help="Planned row flush size recorded in metadata for incremental writers.")
    archive_run.add_argument("--flush-seconds", dest="archive_flush_seconds", type=float, default=30.0, help="Planned time flush interval recorded in metadata for incremental writers.")

    archive_index = sub.add_parser(
        "archive-index",
        help="Print or export the manifest index for a live archive.",
    )
    archive_index.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [live_archive] root.")
    archive_index.add_argument("--archive-root", default=None, help="Archive root directory.")
    archive_index.add_argument("--out", default=None, help="Optional CSV path to write a copy of the manifest.")

    archive_summarize = sub.add_parser(
        "archive-summarize",
        help="Create compact windowed summaries from a live archive (Live Phase-6.3).",
    )
    archive_summarize.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [summaries] settings.")
    archive_summarize.add_argument("--archive-root", default=None, help="Archive root directory.")
    archive_summarize.add_argument("--summary-outdir", default=None, help="Output directory for summary CSVs. Defaults to archive/summaries.")
    archive_summarize.add_argument("--windows-seconds", nargs="*", type=float, default=None, help="Summary windows in seconds, e.g. 60 300 3600.")
    archive_summarize.add_argument("--max-files-per-kind", type=int, default=None, help="Only read the most recent N files per data kind. Useful for huge archives.")
    archive_summarize.add_argument("--state-cols", nargs="*", default=None, help="Optional state columns to summarize from cleaned_stream.")

    archive_search = sub.add_parser(
        "archive-search",
        help="Search a live archive for alerts, low trust, large residuals, or rows involving a state.",
    )
    archive_search.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [live_archive] root.")
    archive_search.add_argument("--archive-root", default=None, help="Archive root directory.")
    archive_search.add_argument("--outdir", default="outputs/archive_search", help="Output directory for search results.")
    archive_search.add_argument("--data-kind", default=None, help="Optional manifest data kind to search, e.g. residuals or alerts.")
    archive_search.add_argument("--alert-code", default=None, help="Filter alerts by code, e.g. FORECAST_RESIDUAL_HIGH.")
    archive_search.add_argument("--severity", default=None, help="Filter alerts by severity, e.g. warning or critical.")
    archive_search.add_argument("--state", default=None, help="Filter long tables by state name, or wide cleaned_stream by column name.")
    archive_search.add_argument("--residual-above", type=float, default=None, help="Find residual rows with absolute residual above this threshold.")
    archive_search.add_argument("--trust-below", type=float, default=None, help="Find trust-score rows at or below this threshold.")
    archive_search.add_argument("--max-files-per-kind", type=int, default=None, help="Only scan the most recent N files per data kind.")

    archive_quicklook = sub.add_parser(
        "archive-quicklook",
        help="Generate small quicklook PNG plots from archive summaries.",
    )
    archive_quicklook.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [quicklooks] settings.")
    archive_quicklook.add_argument("--archive-root", default=None, help="Archive root directory.")
    archive_quicklook.add_argument("--summaries-dir", default=None, help="Directory containing summary CSVs. Defaults to archive/summaries.")
    archive_quicklook.add_argument("--quicklook-outdir", default=None, help="Output directory for quicklook plots. Defaults to archive/quicklooks.")
    archive_quicklook.add_argument("--window-label", default="60s", help="Summary window label to plot, such as 60s, 300s, or 3600s.")


    model_register = sub.add_parser("model-register", help="Register a trained model artifact under a local model registry for live deployment.")
    model_register.add_argument("--model", required=True, help="Path to a saved model artifact, e.g. pod_dmdc_model.pkl.")
    model_register.add_argument("--name", required=True, help="Human-readable registry name, e.g. simple_loop_pod_dmdc_v1.")
    model_register.add_argument("--stage", default="candidate", help="Deployment stage to point at this version: candidate, staging, production, etc.")
    model_register.add_argument("--version", default=None, help="Optional immutable version string. Defaults to timestamp + short UUID.")
    model_register.add_argument("--registry-root", default="models/registry", help="Registry root directory.")
    model_register.add_argument("--model-type", default=None, help="Optional model type label for humans/dashboards.")
    model_register.add_argument("--metrics", default=None, help="Optional metrics/validation file copied into the registry version folder.")
    model_register.add_argument("--notes", default=None, help="Optional short note stored in metadata.")

    model_list = sub.add_parser("model-list", help="List registered model versions and deployment stages.")
    model_list.add_argument("--registry-root", default="models/registry", help="Registry root directory.")
    model_list.add_argument("--out", default=None, help="Optional CSV output path for a copy of the registry index.")

    model_promote = sub.add_parser("model-promote", help="Promote a registered model version to a stage such as production.")
    model_promote.add_argument("--name", required=True, help="Registered model name.")
    model_promote.add_argument("--version", required=True, help="Immutable version to promote.")
    model_promote.add_argument("--stage", default="production", help="Deployment stage to update.")
    model_promote.add_argument("--registry-root", default="models/registry", help="Registry root directory.")

    model_resolve = sub.add_parser("model-resolve", help="Resolve a registry name/stage to the concrete model artifact path.")
    model_resolve.add_argument("--name", required=True, help="Registered model name.")
    model_resolve.add_argument("--stage", default="production", help="Deployment stage to resolve.")
    model_resolve.add_argument("--version", default=None, help="Optional immutable version to resolve instead of stage.")
    model_resolve.add_argument("--registry-root", default="models/registry", help="Registry root directory.")

    archive_schema = sub.add_parser("validate-archive-schema", help="Validate live archive manifest/schema and write human-readable context index tables.")
    archive_schema.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [live_archive] root.")
    archive_schema.add_argument("--archive-root", default=None, help="Live archive root directory.")
    archive_schema.add_argument("--outdir", default=None, help="Output directory for schema validation report. Defaults to archive/schema_validation.")

    archive_context = sub.add_parser("archive-context", help="Write human-readable archive context/index CSV files from manifest metadata.")
    archive_context.add_argument("--config", default=None, help="Optional TOML/JSON/YAML config with [live_archive] root.")
    archive_context.add_argument("--archive-root", default=None, help="Live archive root directory.")
    archive_context.add_argument("--outdir", default=None, help="Output directory for context CSVs. Defaults to archive/context.")

    benchmark_archive = sub.add_parser(
        "benchmark-archive",
        help="Generate synthetic live data and benchmark archive writing/summaries/quicklooks.",
        description="Local-workstation benchmark for large-data archive planning. Increase n-rows for stress tests; use small values in CI.",
    )
    benchmark_archive.add_argument("--n-rows", type=int, default=100000, help="Synthetic cleaned-stream rows to generate.")
    benchmark_archive.add_argument("--n-states", type=int, default=12, help="Number of synthetic state columns.")
    benchmark_archive.add_argument("--n-inputs", type=int, default=3, help="Number of synthetic input columns.")
    benchmark_archive.add_argument("--chunk-files", type=int, default=1, help="Reserved for future multi-file benchmark; recorded in metrics.")
    benchmark_archive.add_argument("--outdir", default="outputs/archive_benchmark", help="Benchmark output directory.")
    benchmark_archive.add_argument("--archive-root", default=None, help="Archive root. Defaults to outdir/live_archive.")
    benchmark_archive.add_argument("--format", dest="archive_format", default="csv", choices=["csv", "parquet"], help="Archive format to test. Use parquet with pyarrow installed for serious tests.")
    benchmark_archive.add_argument("--windows-seconds", nargs="*", type=float, default=[60.0, 300.0, 3600.0], help="Summary windows to benchmark.")
    benchmark_archive.add_argument("--no-quicklooks", action="store_true", help="Skip quicklook plotting during benchmark.")

    hpc_plan = sub.add_parser(
        "hpc-plan",
        help="Write local runner and incomplete Slurm templates for a central campaign config.",
        description="Creates command plans and FIXME sbatch files. Local execution remains the default; fill in cluster account details before using Slurm.",
    )
    hpc_plan.add_argument("--config", required=True, help="Central campaign/study config.")
    hpc_plan.add_argument("--outdir", default="outputs/hpc_plan", help="Plan output directory.")
    hpc_plan.add_argument("--steps", nargs="*", default=None, help="Optional steps to include, e.g. import inspect compare archive.")

    resources = sub.add_parser("resources", help="Print local/HPC resource summary used by campaign workflows.")
    resources.add_argument("--out", default=None, help="Optional JSON output path for the resource summary.")

    campaign = sub.add_parser("campaign", help="Run or dry-run a modular campaign from one central config file.")
    campaign.add_argument("--config", required=True, help="Central TOML/JSON/YAML campaign config.")
    campaign.add_argument("--steps", nargs="*", default=None, help="Optional subset/order of steps, e.g. import inspect compare dashboard.")
    campaign.add_argument("--dry-run", action="store_true", help="Write the plan and commands without executing steps.")

    workflow = sub.add_parser("workflow", help="Run one or more configured fit jobs from a config file.")
    workflow.add_argument("--config", required=True, help="JSON/TOML/YAML workflow config file.")

    return parser


def parse_rank(value: str):
    if value in {"full", "auto"}:
        return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid rank value: {value}") from exc


def cmd_guide(args: argparse.Namespace) -> None:
    """Print or write the streamlined command guide."""
    if getattr(args, "out", None):
        out = write_command_guide(args.out, markdown=bool(getattr(args, "markdown", False)) if Path(args.out).suffix.lower() not in {".md", ".markdown"} else True)
        print(f"Wrote command guide to {out}")
        return
    print(render_command_guide(markdown=bool(getattr(args, "markdown", False))))


def cmd_fit(args: argparse.Namespace) -> None:
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_fit_config(cfg))
    require_fit_fields(args)
    outdir = ensure_dir(args.outdir)
    model = DMDcModel(rank=parse_rank(args.rank), center=args.center, scale=args.scale)

    # Multi-trajectory mode: if a case column is supplied without a case-id filter, fit all
    # independent cases together. This avoids the common mistake of sorting the full table and
    # accidentally learning transitions from the final point of one run to the first point of another.
    if args.case_col is not None and args.case_id is None:
        datasets = load_trajectories(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
        )
        X_list = [ds.X for ds in datasets]
        U_list = [ds.U for ds in datasets]
        state_names = datasets[0].state_cols
        if args.n_delays > 1:
            X_list, U_list, state_names = make_delay_embeddings_for_trajectories(
                X_list, U_list, n_delays=args.n_delays, state_names=state_names
            )
        model.fit_trajectories(
            X_list,
            U_list,
            state_names=state_names,
            input_names=datasets[0].input_cols,
            dt=datasets[0].dt,
        )
        model.save(outdir / "model.pkl")
        write_json(model.to_dict(), outdir / "model_summary.json")

        diagnostics = evaluate_trajectories(
            model,
            X_list,
            U_list,
            [ds.case_id for ds in datasets],
        )
        diagnostics["n_delays"] = args.n_delays
        save_diagnostics(diagnostics, outdir / "diagnostics.json")

        all_pred_frames = []
        for ds, X_fit, U_fit in zip(datasets, X_list, U_list, strict=True):
            U0 = U_fit[:-1] if U_fit is not None and U_fit.shape[0] == X_fit.shape[0] else U_fit
            rollout = model.simulate(X_fit[0], U0 if U0 is not None and U0.shape[1] else None, n_steps=X_fit.shape[0] - 1)
            pred_df = pd.DataFrame(rollout, columns=[f"pred_{c}" for c in state_names])
            pred_df.insert(0, args.case_col, ds.case_id)
            if ds.time is not None:
                aligned_time = ds.time[args.n_delays - 1 :]
                pred_df.insert(1, args.time_col, aligned_time)
            all_pred_frames.append(pred_df)
        pd.concat(all_pred_frames, ignore_index=True).to_csv(outdir / "rollout_predictions.csv", index=False)

        if args.plots:
            plot_singular_values(model, outdir / "singular_values.pdf")
            plot_eigenvalues(model, outdir / "eigenvalues.pdf")
            # Plot the first case as a readable representative plot. Full predictions for all cases
            # are written to CSV, and per-case metrics are in diagnostics.json.
            ds0 = datasets[0]
            X0_fit = X_list[0]
            U0_fit = U_list[0]
            U0 = U0_fit[:-1] if U0_fit is not None and U0_fit.shape[0] == X0_fit.shape[0] else U0_fit
            rollout0 = model.simulate(X0_fit[0], U0 if U0 is not None and U0.shape[1] else None, n_steps=X0_fit.shape[0] - 1)
            plot_true_vs_predicted(
                X0_fit,
                rollout0,
                time=ds0.time[args.n_delays - 1 :] if ds0.time is not None else None,
                state_names=state_names,
                path=outdir / "true_vs_rollout_first_case.pdf",
            )
    else:
        dataset = load_timeseries(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
            case_id=args.case_id,
        )
        X_fit = dataset.X
        U_fit = dataset.U
        state_names = dataset.state_cols
        if args.n_delays > 1:
            X_fit, U_fit, state_names = make_delay_embedding(
                dataset.X, dataset.U, n_delays=args.n_delays, state_names=dataset.state_cols
            )
        model.fit(
            X_fit,
            U_fit,
            state_names=state_names,
            input_names=dataset.input_cols,
            dt=dataset.dt,
        )
        model.save(outdir / "model.pkl")
        write_json(model.to_dict(), outdir / "model_summary.json")

        diagnostics = evaluate_model(model, X_fit, U_fit)
        diagnostics["n_delays"] = args.n_delays
        save_diagnostics(diagnostics, outdir / "diagnostics.json")

        U0 = U_fit[:-1] if U_fit is not None and U_fit.shape[0] == X_fit.shape[0] else U_fit
        rollout = model.simulate(X_fit[0], U0 if U0 is not None and U0.shape[1] else None, n_steps=X_fit.shape[0] - 1)
        pred_df = pd.DataFrame(rollout, columns=[f"pred_{c}" for c in state_names])
        if dataset.time is not None:
            pred_df.insert(0, args.time_col, dataset.time[args.n_delays - 1 :])
        pred_df.to_csv(outdir / "rollout_predictions.csv", index=False)

        if args.plots:
            plot_singular_values(model, outdir / "singular_values.pdf")
            plot_eigenvalues(model, outdir / "eigenvalues.pdf")
            plot_true_vs_predicted(
                X_fit,
                rollout,
                time=dataset.time[args.n_delays - 1 :] if dataset.time is not None else None,
                state_names=state_names,
                path=outdir / "true_vs_rollout.pdf",
            )
    print(f"Saved DMDc outputs to {outdir}")


def cmd_predict(args: argparse.Namespace) -> None:
    outdir = ensure_dir(args.outdir)
    model = DMDcModel.load(args.model)
    dataset = load_timeseries(
        args.data,
        state_cols=args.state_cols,
        input_cols=args.input_cols,
        time_col=args.time_col,
    )
    U0 = dataset.U[:-1] if dataset.U.shape[0] == dataset.X.shape[0] else dataset.U
    rollout = model.simulate(dataset.X[0], U0 if U0.shape[1] else None, n_steps=dataset.X.shape[0] - 1)
    pred_df = pd.DataFrame(rollout, columns=[f"pred_{c}" for c in dataset.state_cols])
    if dataset.time is not None:
        pred_df.insert(0, args.time_col, dataset.time)
    pred_df.to_csv(outdir / "predictions.csv", index=False)

    diagnostics = evaluate_model(model, dataset.X, dataset.U)
    save_diagnostics(diagnostics, outdir / "prediction_diagnostics.json")
    print(f"Saved predictions to {outdir}")


def cmd_select_sensors(args: argparse.Namespace) -> None:
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_sensor_selection_config(cfg))
    require_sensor_fields(args)
    outdir = ensure_dir(args.outdir)
    if args.case_col:
        datasets = load_trajectories(
            args.data,
            state_cols=args.state_cols,
            input_cols=[],
            time_col=args.time_col,
            case_col=args.case_col,
        )
        X = np.vstack([ds.X for ds in datasets])
    else:
        dataset = load_timeseries(
            args.data,
            state_cols=args.state_cols,
            input_cols=[],
            time_col=args.time_col,
        )
        X = dataset.X

    result = qr_sensor_ranking(
        X,
        args.state_cols,
        rank=parse_rank(args.rank),
        n_sensors=args.n_sensors,
        center=args.center,
        scale=args.scale,
    )
    result.save(outdir)
    errors = reconstruction_error_vs_sensors(
        X,
        result.selected_indices,
        rank=parse_rank(args.rank),
        center=args.center,
        scale=args.scale,
    )
    errors.to_csv(outdir / "reconstruction_error_vs_sensors.csv", index=False)
    if args.plots:
        # Reuse a temporary model-like object is unnecessary; write CSV plus reconstruction plot.
        plot_reconstruction_error_vs_sensors(errors, outdir / "reconstruction_error_vs_sensors.pdf")
    print(f"Saved sensor-selection outputs to {outdir}")
    print("Selected states: " + ", ".join(result.selected_state_names))



def _stack_pod_snapshots(args: argparse.Namespace):
    """Load POD snapshots, stacking cases if requested."""
    if args.case_col is not None and args.case_id is None:
        datasets = load_trajectories(
            args.data,
            state_cols=args.state_cols,
            input_cols=[],
            time_col=args.time_col,
            case_col=args.case_col,
        )
        X = np.vstack([ds.X for ds in datasets])
        time = None
        case_ids = []
        for ds in datasets:
            case_ids.extend([ds.case_id] * ds.X.shape[0])
        return X, datasets[0].state_cols, time, np.asarray(case_ids, dtype=object)
    dataset = load_timeseries(
        args.data,
        state_cols=args.state_cols,
        input_cols=[],
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
    )
    return dataset.X, dataset.state_cols, dataset.time, None


def cmd_pod(args: argparse.Namespace) -> None:
    """Fit and save a POD basis."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_pod_config(cfg))
    require_pod_fields(args)
    outdir = ensure_dir(args.outdir)
    X, state_names, time, case_ids = _stack_pod_snapshots(args)
    pod = PODBasis(
        rank=parse_rank(str(args.rank)),
        energy_threshold=args.energy_threshold,
        center=bool(args.center),
        scale=bool(args.scale),
    ).fit(X, state_names=state_names)
    summary = pod.save_outputs(X, outdir, time=time)
    if case_ids is not None:
        coeffs = pod.transform(X)
        recon = pod.inverse_transform(coeffs)
        coeff_df = pd.DataFrame(coeffs, columns=[f"a{i+1}" for i in range(coeffs.shape[1])])
        coeff_df.insert(0, args.case_col, case_ids)
        coeff_df.to_csv(outdir / "pod_coefficients.csv", index=False)
        recon_df = pd.DataFrame(recon, columns=[f"recon_{c}" for c in state_names])
        recon_df.insert(0, args.case_col, case_ids)
        recon_df.to_csv(outdir / "pod_reconstruction.csv", index=False)
    err_curve = save_reconstruction_error_vs_rank(
        X,
        outdir / "reconstruction_error_vs_rank.csv",
        center=bool(args.center),
        scale=bool(args.scale),
        state_names=state_names,
    )
    if args.plots:
        plot_pod_singular_values(pod.singular_values_, outdir / "singular_values.pdf")
        plot_pod_cumulative_energy(pod.cumulative_energy_, outdir / "cumulative_energy.pdf")
        plot_pod_reconstruction_error_vs_rank(err_curve, outdir / "reconstruction_error_vs_rank.pdf")
        plot_pod_coefficients(pod.transform(X), outdir / "coefficient_timeseries.pdf", time=time)
    print(f"Saved POD outputs to {outdir}")
    print(f"POD rank used: {summary['rank_used']}")


def cmd_pod_sensors(args: argparse.Namespace) -> None:
    """Fit POD, select QR/Q-DEIM sensors, and reconstruct from sparse measurements."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_pod_sensors_config(cfg))
    require_pod_sensors_fields(args)
    outdir = ensure_dir(args.outdir)
    X, state_names, time, case_ids = _stack_pod_snapshots(args)
    summary = run_pod_sensor_workflow(
        X,
        state_names=state_names,
        rank=parse_rank(str(args.rank)),
        n_sensors=args.n_sensors,
        center=bool(args.center),
        scale=bool(args.scale),
        outdir=outdir,
        time=time,
    )
    if case_ids is not None:
        # Keep a lightweight map from stacked snapshot row to case id.  This is
        # useful when all cases were stacked for POD but the sparse-sensor
        # reconstruction table intentionally stays numerical and compact.
        pd.DataFrame({args.case_col: case_ids}).to_csv(outdir / "snapshot_case_ids.csv", index=False)
    if args.plots:
        err = pd.read_csv(outdir / "reconstruction_error_vs_sensors.csv")
        plot_reconstruction_error_vs_sensors(err, outdir / "reconstruction_error_vs_sensors.pdf")
    print(f"Saved POD sparse-sensing outputs to {outdir}")
    print("Selected states: " + ", ".join(summary["selected_state_names"]))


def cmd_import_data(args: argparse.Namespace) -> None:
    """Run the configured importer and write a canonical table plus sidecars."""

    if args.config:
        cfg = load_config(args.config)
        args = apply_config_defaults(args, flatten_import_config(cfg))
    require_import_fields(args)
    summary = run_import_workflow(
        source=args.source,
        source_type=args.source_type,
        out=args.out,
        output_format=args.output_format,
        sheet=args.sheet,
        pattern=args.pattern,
        column_map=args.column_map,
        rename_col=args.rename_col,
        case_from_filename=bool(args.case_from_filename),
        max_files=args.max_files,
        epics_pvs=getattr(args, "epics_pvs", None),
        strict_parquet=bool(args.strict_parquet),
        skip_unstable_files=bool(getattr(args, "skip_unstable_files", False)),
        settle_seconds=float(getattr(args, "settle_seconds", 0.0)),
    )
    print(f"Imported {summary.get('n_rows', 'unknown')} rows to {summary.get('canonical_output')}")
    print("Next: run `dmdc inspect-data --data <canonical_output> ...` or point your central config [data].path at it.")


def cmd_inspect_data(args: argparse.Namespace) -> None:
    """Inspect input data and save warnings/diagnostics."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_inspect_config(cfg))
    require_inspect_fields(args)
    outdir = ensure_dir(args.outdir)
    frame = read_table(args.data)
    result = inspect_table(
        frame,
        time_col=args.time_col,
        case_col=args.case_col,
        state_cols=args.state_cols,
        input_cols=args.input_cols,
    )
    result.save(outdir)
    quality = summarize_case_quality(
        frame,
        case_col=args.case_col,
        time_col=args.time_col,
        required_cols=list(args.state_cols or []) + list(args.input_cols or []),
        min_samples=int(getattr(args, "min_samples", 3)),
        expected_final_time=getattr(args, "expected_final_time", None),
    )
    quality.to_csv(outdir / "case_quality_dashboard.csv", index=False)
    write_provenance(outdir, config_path=getattr(args, "config", None), extra={"command": "inspect-data"})
    print(f"Saved data inspection outputs to {outdir}")
    if result.warnings:
        print(f"Emitted {len(result.warnings)} warning(s); see warnings.txt")
    bad = quality[quality["usable_for_rom"] == False]  # noqa: E712
    if not bad.empty:
        print(f"Detected {len(bad)} case(s) marked not usable; see case_quality_dashboard.csv")


def cmd_resample(args: argparse.Namespace) -> None:
    """Resample input data to a uniform dt and save a CSV."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_resample_config(cfg))
    require_resample_fields(args)
    frame = read_table(args.data)
    resampled = resample_all_cases(
        frame,
        time_col=args.time_col,
        case_col=args.case_col,
        dt=float(args.dt),
        method=args.method,
        columns=args.columns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    resampled.to_csv(out, index=False)
    print(f"Saved resampled data to {out}")

def cmd_pod_dmdc(args: argparse.Namespace) -> None:
    """Fit POD-DMDc and save reduced/full-state outputs."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_pod_dmdc_config(cfg))
    require_pod_dmdc_fields(args)
    outdir = ensure_dir(args.outdir)
    pod_rank = parse_rank(str(args.pod_rank))
    dmdc_rank = parse_rank(str(args.dmdc_rank))

    if args.case_col is not None and args.case_id is None:
        datasets = load_trajectories(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
        )
        pipeline = PODDMDcPipeline(pod_rank=pod_rank, dmdc_rank=dmdc_rank, center=bool(args.center), scale=bool(args.scale)).fit_trajectories(
            [ds.X for ds in datasets],
            [ds.U for ds in datasets],
            state_names=datasets[0].state_cols,
            input_names=datasets[0].input_cols,
        )
        pipeline.save(outdir / "pod_dmdc_model.pkl")
        write_json(pipeline.to_dict(), outdir / "pod_dmdc_summary.json")
        all_pred = []
        all_coeff = []
        for ds in datasets:
            U = ds.U if ds.U.shape[1] else None
            U_future = None if U is None else (U[:-1] if U.shape[0] == ds.X.shape[0] else U)
            pred = pipeline.rollout(ds.X[0], U_future=U_future, n_steps=ds.X.shape[0] - 1)
            coeff = pipeline.transform(ds.X)
            pred_df = pd.DataFrame(pred, columns=[f"pred_{c}" for c in ds.state_cols])
            coeff_df = pd.DataFrame(coeff, columns=[f"a{i+1}" for i in range(coeff.shape[1])])
            pred_df.insert(0, args.case_col, ds.case_id)
            coeff_df.insert(0, args.case_col, ds.case_id)
            if ds.time is not None:
                pred_df.insert(1, args.time_col, ds.time)
                coeff_df.insert(1, args.time_col, ds.time)
            all_pred.append(pred_df)
            all_coeff.append(coeff_df)
        pd.concat(all_pred, ignore_index=True).to_csv(outdir / "reconstructed_rollout_predictions.csv", index=False)
        pd.concat(all_coeff, ignore_index=True).to_csv(outdir / "modal_coefficients.csv", index=False)
        from .validation import evaluate_pod_dmdc_on_datasets
        diag = evaluate_pod_dmdc_on_datasets(pipeline, datasets, split_name="fit", forecast_horizons=[1,5,10])
        write_json(diag["summary"], outdir / "diagnostics.json")
        diag["case_metrics"].to_csv(outdir / "error_by_case.csv", index=False)
        diag["state_metrics"].to_csv(outdir / "error_by_state.csv", index=False)
        if args.plots:
            plot_pod_singular_values(pipeline.pod_.singular_values_, outdir / "singular_values.pdf")
            plot_pod_cumulative_energy(pipeline.pod_.cumulative_energy_, outdir / "cumulative_energy.pdf")
            # Reduced A eigenvalues use the existing DMDc plotter on the reduced model.
            plot_eigenvalues(pipeline.model_, outdir / "eigenvalues_reduced_A.pdf")
            ds0 = datasets[0]
            U0 = ds0.U if ds0.U.shape[1] else None
            U0f = None if U0 is None else (U0[:-1] if U0.shape[0] == ds0.X.shape[0] else U0)
            pred0 = pipeline.rollout(ds0.X[0], U_future=U0f, n_steps=ds0.X.shape[0] - 1)
            plot_true_vs_predicted(ds0.X, pred0, time=ds0.time, state_names=ds0.state_cols, path=outdir / "true_vs_reconstructed_first_case.pdf")
    else:
        dataset = load_timeseries(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
            case_id=args.case_id,
        )
        pipeline = PODDMDcPipeline(pod_rank=pod_rank, dmdc_rank=dmdc_rank, center=bool(args.center), scale=bool(args.scale)).fit(
            dataset.X, dataset.U, state_names=dataset.state_cols, input_names=dataset.input_cols
        )
        pipeline.save_outputs(dataset.X, dataset.U, outdir, time=dataset.time, state_names=dataset.state_cols)
        if args.plots:
            plot_pod_singular_values(pipeline.pod_.singular_values_, outdir / "singular_values.pdf")
            plot_pod_cumulative_energy(pipeline.pod_.cumulative_energy_, outdir / "cumulative_energy.pdf")
            plot_eigenvalues(pipeline.model_, outdir / "eigenvalues_reduced_A.pdf")
            U = dataset.U if dataset.U.shape[1] else None
            U_future = None if U is None else (U[:-1] if U.shape[0] == dataset.X.shape[0] else U)
            pred = pipeline.rollout(dataset.X[0], U_future=U_future, n_steps=dataset.X.shape[0] - 1)
            plot_true_vs_predicted(dataset.X, pred, time=dataset.time, state_names=dataset.state_cols, path=outdir / "true_vs_reconstructed.pdf")
    print(f"Saved POD-DMDc outputs to {outdir}")


def cmd_pod_ml(args: argparse.Namespace) -> None:
    """Fit optional POD-ML reduced dynamics."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_pod_ml_config(cfg))
    require_pod_ml_fields(args)
    outdir = ensure_dir(args.outdir)
    pod_rank = parse_rank(str(args.pod_rank))

    if args.case_col is not None and args.case_id is None:
        datasets = load_trajectories(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
        )
        model = PODDynamicsRegressor(
            pod_rank=pod_rank,
            model_type=args.model_type,
            center=bool(args.center),
            scale=bool(args.scale),
            recursive_rollout=bool(args.recursive_rollout),
        ).fit_trajectories(
            [ds.X for ds in datasets],
            [ds.U for ds in datasets],
            state_names=datasets[0].state_cols,
            input_names=datasets[0].input_cols,
        )
        model.save(outdir / "pod_ml_model.pkl")
        write_json(model.to_dict(), outdir / "pod_ml_summary.json")
        all_pred = []
        all_coeff = []
        case_rows = []
        state_rows = []
        for ds in datasets:
            U = ds.U if ds.U.shape[1] else None
            U_future = None if U is None else (U[:-1] if U.shape[0] == ds.X.shape[0] else U)
            pred = model.rollout(ds.X[0], U_future=U_future, n_steps=ds.X.shape[0] - 1)
            coeff = model.transform(ds.X)
            pred_df = pd.DataFrame(pred, columns=[f"pred_{c}" for c in ds.state_cols])
            coeff_df = pd.DataFrame(coeff, columns=[f"a{i+1}" for i in range(coeff.shape[1])])
            pred_df.insert(0, args.case_col, ds.case_id)
            coeff_df.insert(0, args.case_col, ds.case_id)
            if ds.time is not None:
                pred_df.insert(1, args.time_col, ds.time)
                coeff_df.insert(1, args.time_col, ds.time)
            all_pred.append(pred_df)
            all_coeff.append(coeff_df)
            case_rows.append({"case_id": ds.case_id, "rmse": rmse(ds.X, pred), "relative_frobenius_error": relative_frobenius_error(ds.X, pred)})
            for row in error_by_column(ds.X, pred, ds.state_cols):
                row.update({"case_id": ds.case_id})
                state_rows.append(row)
        pd.concat(all_pred, ignore_index=True).to_csv(outdir / "reconstructed_predictions.csv", index=False)
        pd.concat(all_coeff, ignore_index=True).to_csv(outdir / "modal_coefficients.csv", index=False)
        pd.DataFrame(case_rows).to_csv(outdir / "error_by_case.csv", index=False)
        pd.DataFrame(state_rows).to_csv(outdir / "error_by_state.csv", index=False)
        write_json({"rollout_rmse": float(pd.DataFrame(case_rows)["rmse"].mean()), "model_type": args.model_type}, outdir / "diagnostics.json")
        if args.plots:
            plot_pod_singular_values(model.pod_.singular_values_, outdir / "singular_values.pdf")
            plot_pod_cumulative_energy(model.pod_.cumulative_energy_, outdir / "cumulative_energy.pdf")
            ds0 = datasets[0]
            U0 = ds0.U if ds0.U.shape[1] else None
            U0f = None if U0 is None else (U0[:-1] if U0.shape[0] == ds0.X.shape[0] else U0)
            pred0 = model.rollout(ds0.X[0], U_future=U0f, n_steps=ds0.X.shape[0] - 1)
            plot_true_vs_predicted(ds0.X, pred0, time=ds0.time, state_names=ds0.state_cols, path=outdir / "true_vs_reconstructed_first_case.pdf")
            plot_pod_coefficients(model.transform(ds0.X), outdir / "modal_coefficients_first_case.pdf", time=ds0.time)
    else:
        dataset = load_timeseries(
            args.data,
            state_cols=args.state_cols,
            input_cols=args.input_cols,
            time_col=args.time_col,
            case_col=args.case_col,
            case_id=args.case_id,
        )
        model = PODDynamicsRegressor(
            pod_rank=pod_rank,
            model_type=args.model_type,
            center=bool(args.center),
            scale=bool(args.scale),
            recursive_rollout=bool(args.recursive_rollout),
        ).fit(dataset.X, dataset.U, state_names=dataset.state_cols, input_names=dataset.input_cols)
        model.save_outputs(dataset.X, dataset.U, outdir, time=dataset.time, state_names=dataset.state_cols)
        if args.plots:
            plot_pod_singular_values(model.pod_.singular_values_, outdir / "singular_values.pdf")
            plot_pod_cumulative_energy(model.pod_.cumulative_energy_, outdir / "cumulative_energy.pdf")
            U = dataset.U if dataset.U.shape[1] else None
            U_future = None if U is None else (U[:-1] if U.shape[0] == dataset.X.shape[0] else U)
            pred = model.rollout(dataset.X[0], U_future=U_future, n_steps=dataset.X.shape[0] - 1)
            plot_true_vs_predicted(dataset.X, pred, time=dataset.time, state_names=dataset.state_cols, path=outdir / "true_vs_reconstructed.pdf")
            plot_pod_coefficients(model.transform(dataset.X), outdir / "modal_coefficients.pdf", time=dataset.time)
    print(f"Saved POD-ML outputs to {outdir}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate POD-DMDc on held-out cases."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_validate_config(cfg))
    require_validate_fields(args)
    datasets = load_trajectories(
        args.data,
        state_cols=args.state_cols,
        input_cols=args.input_cols,
        time_col=args.time_col,
        case_col=args.case_col,
    )
    if args.train_cases and args.test_cases:
        split = split_by_case_ids(datasets, train_cases=args.train_cases, test_cases=args.test_cases)
    else:
        split = split_by_fraction(datasets, train_fraction=float(args.train_fraction))
    outdir = ensure_dir(args.outdir)
    summary = run_pod_dmdc_validation(
        split.train,
        split.test,
        pod_rank=parse_rank(str(args.pod_rank)),
        dmdc_rank=parse_rank(str(args.dmdc_rank)),
        center=bool(args.center),
        scale=bool(args.scale),
        forecast_horizons=args.forecast_horizons,
        outdir=outdir,
        plots=bool(args.plots),
    )
    train_frame = pd.concat([ds.frame for ds in split.train], ignore_index=True)
    test_frame = pd.concat([ds.frame for ds in split.test], ignore_index=True)
    op_summary = summarize_operating_conditions(train_frame, test_frame, condition_cols=args.input_cols or [])
    warnings = []
    if not op_summary.empty:
        save_dashboard(op_summary, outdir, "operating_condition_summary", caption="Train/test operating-condition ranges")
        warnings.extend(operating_condition_warnings(op_summary))
    case_path = outdir / "error_by_case.csv"
    if case_path.exists():
        case_df = pd.read_csv(case_path)
        unc = uncertainty_table_from_case_metrics(case_df, value_col="rmse")
        if not unc.empty:
            save_dashboard(unc, outdir, "uncertainty_summary", caption="Bootstrap uncertainty from case-level errors")
    if warnings:
        with (outdir / "warnings.txt").open("a", encoding="utf-8") as f:
            f.write("\n\n" + "\n".join(warnings) + "\n")
    write_provenance(outdir, config_path=getattr(args, "config", None), extra={"command": "validate"})
    print(f"Saved validation outputs to {outdir}")
    print(f"Train RMSE: {summary['train_rollout_rmse']:.6g}; Test RMSE: {summary['test_rollout_rmse']:.6g}")



def _u_future_for_dataset(ds):
    U = ds.U if ds.U.shape[1] else None
    if U is None:
        return None
    return U[:-1] if U.shape[0] == ds.X.shape[0] else U


def _rollout_any_model(model, ds):
    u_future = _u_future_for_dataset(ds)
    n_steps = ds.X.shape[0] - 1
    # AdaptiveDMDcModel should use the actual future time grid when available.
    if hasattr(model, "rollout"):
        try:
            if ds.time is not None and model.__class__.__name__ == "AdaptiveDMDcModel":
                return model.rollout(ds.X[0], U_future=u_future, time_future=ds.time)
        except TypeError:
            pass
        return model.rollout(ds.X[0], U_future=u_future, n_steps=n_steps)
    if hasattr(model, "simulate"):
        return model.simulate(ds.X[0], U_future=u_future, n_steps=n_steps)
    raise TypeError(f"Model object {type(model)!r} cannot roll out.")


def _evaluate_any_model(model, datasets, split_name: str):
    rows_case = []
    rows_state = []
    all_true = []
    all_pred = []
    residual_frames = []
    for ds in datasets:
        pred = _rollout_any_model(model, ds)
        all_true.append(ds.X)
        all_pred.append(pred)
        rows_case.append({
            "split": split_name,
            "case_id": ds.case_id,
            "n_snapshots": int(ds.X.shape[0]),
            "rmse": rmse(ds.X, pred),
            "relative_frobenius_error": relative_frobenius_error(ds.X, pred),
        })
        for row in error_by_column(ds.X, pred, ds.state_cols):
            row.update({"split": split_name, "case_id": ds.case_id})
            rows_state.append(row)
        residual = pd.DataFrame(ds.X - pred, columns=[f"residual_{c}" for c in ds.state_cols])
        residual.insert(0, "split", split_name)
        residual.insert(1, "case_id", ds.case_id)
        if ds.time is not None:
            residual.insert(2, "time", ds.time)
        residual_frames.append(residual)
    X = np.vstack(all_true)
    P = np.vstack(all_pred)
    return {
        "summary": {"split": split_name, "rmse": rmse(X, P), "relative_frobenius_error": relative_frobenius_error(X, P), "n_cases": len(datasets)},
        "case_metrics": pd.DataFrame(rows_case),
        "state_metrics": pd.DataFrame(rows_state),
        "residuals": pd.concat(residual_frames, ignore_index=True) if residual_frames else pd.DataFrame(),
    }


def _transition_matrix_for_model(model):
    if hasattr(model, "A_") and getattr(model, "A_") is not None:
        return getattr(model, "A_")
    if hasattr(model, "A_c_") and getattr(model, "A_c_") is not None:
        return getattr(model, "A_c_")
    if hasattr(model, "model_") and getattr(model, "model_") is not None:
        inner = getattr(model, "model_")
        if hasattr(inner, "A_"):
            return getattr(inner, "A_")
    return None


def _flatten_compare_config(cfg: dict) -> dict:
    data = cfg.get("data", {}) or {}
    split = cfg.get("split", {}) or {}
    compare = cfg.get("compare", {}) or {}
    model = cfg.get("model", {}) or {}
    pod = cfg.get("pod", {}) or {}
    output = cfg.get("output", {}) or {}
    preprocessing = cfg.get("preprocessing", {}) or {}
    report = cfg.get("report", {}) or {}
    return {
        "data": data.get("path", cfg.get("data")),
        "state_cols": data.get("state_cols", cfg.get("state_cols")),
        "input_cols": data.get("input_cols", cfg.get("input_cols", [])),
        "time_col": data.get("time_col", cfg.get("time_col")),
        "case_col": data.get("case_col", cfg.get("case_col")),
        "train_cases": split.get("train_cases", cfg.get("train_cases")),
        "test_cases": split.get("test_cases", cfg.get("test_cases")),
        "train_fraction": split.get("train_fraction", cfg.get("train_fraction", 0.7)),
        "models": compare.get("models", cfg.get("models", ["persistence", "mean", "dmdc", "pod_dmdc"])),
        "pod_rank": pod.get("rank", cfg.get("pod_rank", 0.999)),
        "dmdc_rank": model.get("dmdc_rank", model.get("rank", cfg.get("dmdc_rank", "full"))),
        "center": bool(pod.get("center", preprocessing.get("center", cfg.get("center", True)))),
        "scale": bool(pod.get("scale", preprocessing.get("scale", cfg.get("scale", False)))),
        "outdir": compare.get("outdir", output.get("comparison_outdir", output.get("outdir", "outputs/model_comparison"))),
        "plots": bool(output.get("plots", cfg.get("plots", False))),
        "report": bool(report.get("enabled", cfg.get("report", False))),
    }


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare ROMs and baseline models on train/test cases."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, _flatten_compare_config(cfg))
    missing = [k for k in ("data", "state_cols", "case_col") if not getattr(args, k, None)]
    if missing:
        raise ValueError(f"Missing required compare setting(s): {', '.join(missing)}")
    outdir = ensure_dir(args.outdir or "outputs/model_comparison")
    datasets = load_trajectories(args.data, state_cols=args.state_cols, input_cols=args.input_cols, time_col=args.time_col, case_col=args.case_col)
    if args.train_cases and args.test_cases:
        split = split_by_case_ids(datasets, train_cases=args.train_cases, test_cases=args.test_cases)
    else:
        split = split_by_fraction(datasets, train_fraction=float(args.train_fraction))
    rows = []
    all_case_rows = []
    all_state_rows = []
    stability_rows = []
    warnings = []
    for name in args.models:
        model = fit_baseline_or_rom(
            name,
            [ds.X for ds in split.train],
            [ds.U for ds in split.train],
            train_time=[ds.time for ds in split.train],
            state_names=split.train[0].state_cols,
            input_names=split.train[0].input_cols,
            dmdc_rank=parse_rank(str(args.dmdc_rank)),
            pod_rank=parse_rank(str(args.pod_rank)),
            center=bool(args.center),
            scale=bool(args.scale),
        )
        train_eval = _evaluate_any_model(model, split.train, "train")
        test_eval = _evaluate_any_model(model, split.test, "test")
        A = _transition_matrix_for_model(model)
        spectral_radius = None
        n_unstable = None
        status = "not_applicable"
        if A is not None:
            stab = analyze_transition_matrix(A)
            spectral_radius = stab["summary"]["spectral_radius"]
            n_unstable = stab["summary"]["n_unstable_eigenvalues"]
            status = stab["summary"]["status"]
            stability_row = {"model_name": name, **stab["summary"]}
            stability_rows.append(stability_row)
            warnings.extend([f"{name}: {w}" for w in stab.get("warnings", [])])
            if args.plots and name == args.models[-1]:
                # Save one representative eigenvalue plot, normally POD-DMDc if requested.
                stab["eigenvalue_table"].to_csv(outdir / "eigenvalues.csv", index=False)
                plot_eigenvalues_table(stab["eigenvalue_table"], outdir / "eigenvalues_complex_plane.pdf")
        train_rmse = train_eval["summary"]["rmse"]
        test_rmse = test_eval["summary"]["rmse"]
        rows.append({
            "model_name": name,
            "train_rollout_rmse": train_rmse,
            "test_rollout_rmse": test_rmse,
            "generalization_gap": test_rmse - train_rmse,
            "generalization_ratio": test_rmse / train_rmse if train_rmse > 0 else np.inf,
            "spectral_radius": spectral_radius,
            "n_unstable_eigenvalues": n_unstable,
            "stability_status": status,
            "pod_rank": args.pod_rank if name.startswith("pod_") else "",
            "dmdc_rank": args.dmdc_rank if name in {"dmd", "dmdc", "pod_dmdc"} else "",
            "n_states": len(args.state_cols),
            "n_inputs": len(args.input_cols or []),
        })
        cm = pd.concat([train_eval["case_metrics"], test_eval["case_metrics"]], ignore_index=True)
        cm.insert(0, "model_name", name)
        sm = pd.concat([train_eval["state_metrics"], test_eval["state_metrics"]], ignore_index=True)
        sm.insert(0, "model_name", name)
        all_case_rows.append(cm)
        all_state_rows.append(sm)
    comp = pd.DataFrame(rows).sort_values("test_rollout_rmse").reset_index(drop=True)
    save_dashboard(comp, outdir, "model_comparison", caption="Model comparison on held-out data")
    recommendation = recommend_best_model(comp)
    write_json(recommendation, outdir / "best_model_recommendation.json")
    write_recommendation(recommendation, outdir / "best_model_recommendation.txt")
    # Operating-condition range checks tell the user whether held-out cases are
    # interpolation or extrapolation in known inputs/boundary conditions.
    train_frame = pd.concat([ds.frame for ds in split.train], ignore_index=True)
    test_frame = pd.concat([ds.frame for ds in split.test], ignore_index=True)
    op_summary = summarize_operating_conditions(train_frame, test_frame, condition_cols=args.input_cols or [])
    if not op_summary.empty:
        save_dashboard(op_summary, outdir, "operating_condition_summary", caption="Train/test operating-condition ranges")
        warnings.extend(operating_condition_warnings(op_summary))
    if all_case_rows:
        case_df = pd.concat(all_case_rows, ignore_index=True)
        save_dashboard(case_df, outdir, "error_by_case", caption="Error by case and model")
        unc = uncertainty_table_from_case_metrics(case_df, value_col="rmse")
        if not unc.empty:
            save_dashboard(unc, outdir, "uncertainty_summary", caption="Bootstrap uncertainty from case-level errors")
    if all_state_rows:
        state_df = pd.concat(all_state_rows, ignore_index=True)
        save_dashboard(state_df, outdir, "error_by_state", caption="Error by state and model")
    if stability_rows:
        stability_df = pd.DataFrame(stability_rows)
        save_dashboard(stability_df, outdir, "stability_dashboard", caption="Stability diagnostics by model")
        write_json(stability_rows[-1], outdir / "stability_summary.json")
    write_json({"n_models": len(rows), "best_model": str(comp.iloc[0]["model_name"]) if not comp.empty else None}, outdir / "comparison_summary.json")
    if warnings:
        (outdir / "stability_warnings.txt").write_text("\n\n".join(warnings), encoding="utf-8")
    else:
        (outdir / "stability_warnings.txt").write_text("No stability warnings emitted.\n", encoding="utf-8")
    if args.plots:
        plot_model_comparison(comp, outdir / "model_comparison.pdf")
    write_provenance(outdir, config_path=getattr(args, "config", None), extra={"command": "compare", "models": args.models})
    if getattr(args, "report", False):
        generate_latex_report(outdir, compile_pdf=False)
    print(f"Saved model comparison outputs to {outdir}")
    if not comp.empty:
        print(f"Best held-out model by test RMSE: {comp.iloc[0]['model_name']}")


def cmd_sweep(args: argparse.Namespace) -> None:
    """Run a rank/delay/model sweep with held-out case validation."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_sweep_config(cfg))
    require_sweep_fields(args)
    datasets = load_trajectories(
        args.data,
        state_cols=args.state_cols,
        input_cols=args.input_cols,
        time_col=args.time_col,
        case_col=args.case_col,
    )
    if args.train_cases and args.test_cases:
        split = split_by_case_ids(datasets, train_cases=args.train_cases, test_cases=args.test_cases)
    else:
        split = split_by_fraction(datasets, train_fraction=float(args.train_fraction))
    pod_ranks = parse_sweep_values(args.pod_ranks, default=[0.999])
    dmdc_ranks = parse_sweep_values(args.dmdc_ranks, default=["full"])
    n_delays = [int(v) for v in parse_sweep_values(args.n_delays_list, default=[1])]
    outdir = ensure_dir(args.outdir)
    results = run_rank_delay_sweep(
        split.train,
        split.test,
        models=args.models,
        pod_ranks=pod_ranks,
        dmdc_ranks=dmdc_ranks,
        n_delays=n_delays,
        center=bool(args.center),
        scale=bool(args.scale),
        outdir=outdir,
        plots=bool(args.plots),
    )
    recommendation = recommend_best_model(results)
    write_json(recommendation, outdir / "best_model_recommendation.json")
    write_recommendation(recommendation, outdir / "best_model_recommendation.txt")
    write_provenance(outdir, config_path=getattr(args, "config", None), extra={"command": "sweep", "models": args.models})
    if getattr(args, "report", False):
        generate_latex_report(outdir, compile_pdf=False)
    print(f"Saved sweep outputs to {outdir}")
    if not results.empty:
        successful = results[results["status"] == "ok"]
        if not successful.empty:
            print(f"Best sweep candidate: {successful.iloc[0]['run_name']}")


def cmd_adaptive_fit(args: argparse.Namespace) -> None:
    """Fit variable-time-step/adaptive DMDc from physical time data."""
    if getattr(args, "config", None):
        cfg = load_config(args.config)
        # Reuse the familiar fit sections plus optional [adaptive] settings.
        defaults = flatten_fit_config(cfg)
        adaptive = cfg.get("adaptive", {}) or {}
        defaults.update({"alpha": adaptive.get("alpha", cfg.get("alpha", getattr(args, "alpha", 1e-8)))})
        apply_config_defaults(args, defaults)
    if not getattr(args, "data", None) or not getattr(args, "state_cols", None) or not getattr(args, "time_col", None):
        raise ValueError("adaptive-fit requires --data, --state-cols, and --time-col.")
    outdir = ensure_dir(args.outdir or "outputs/adaptive_dmdc")
    model = AdaptiveDMDcModel(rank=parse_rank(str(args.rank)), alpha=float(args.alpha))
    if args.case_col is not None and args.case_id is None:
        datasets = load_trajectories(args.data, state_cols=args.state_cols, input_cols=args.input_cols, time_col=args.time_col, case_col=args.case_col)
        if any(ds.time is None for ds in datasets):
            raise ValueError("All datasets must include time for adaptive-fit.")
        model.fit_trajectories(
            [ds.X for ds in datasets],
            [ds.U for ds in datasets],
            [ds.time for ds in datasets],
            state_names=datasets[0].state_cols,
            input_names=datasets[0].input_cols,
        )
        all_pred = []
        for ds in datasets:
            pred = model.rollout(ds.X[0], U_future=_u_future_for_dataset(ds), time_future=ds.time)
            pdf = pd.DataFrame(pred, columns=[f"pred_{c}" for c in ds.state_cols])
            pdf.insert(0, args.case_col, ds.case_id)
            pdf.insert(1, args.time_col, ds.time)
            all_pred.append(pdf)
        pd.concat(all_pred, ignore_index=True).to_csv(outdir / "adaptive_rollout_predictions.csv", index=False)
        if args.plots and datasets:
            pred0 = model.rollout(datasets[0].X[0], U_future=_u_future_for_dataset(datasets[0]), time_future=datasets[0].time)
            plot_true_vs_predicted(datasets[0].X, pred0, time=datasets[0].time, state_names=datasets[0].state_cols, path=outdir / "true_vs_adaptive_rollout_first_case.pdf")
    else:
        ds = load_timeseries(args.data, state_cols=args.state_cols, input_cols=args.input_cols, time_col=args.time_col, case_col=args.case_col, case_id=args.case_id)
        if ds.time is None:
            raise ValueError("adaptive-fit requires a time column.")
        model.fit(ds.X, ds.U, time=ds.time, state_names=ds.state_cols, input_names=ds.input_cols)
        pred = model.rollout(ds.X[0], U_future=_u_future_for_dataset(ds), time_future=ds.time)
        pdf = pd.DataFrame(pred, columns=[f"pred_{c}" for c in ds.state_cols])
        pdf.insert(0, args.time_col, ds.time)
        pdf.to_csv(outdir / "adaptive_rollout_predictions.csv", index=False)
        if args.plots:
            plot_true_vs_predicted(ds.X, pred, time=ds.time, state_names=ds.state_cols, path=outdir / "true_vs_adaptive_rollout.pdf")
    model.save(outdir / "adaptive_model.pkl")
    write_json(model.to_dict(), outdir / "adaptive_dmdc_summary.json")
    write_provenance(outdir, config_path=getattr(args, "config", None), extra={"command": "adaptive-fit", "time_handling": "variable_dt_continuous_generator"})
    print(f"Saved adaptive variable-dt DMDc outputs to {outdir}")


def cmd_continuous(args: argparse.Namespace) -> None:
    """Fit DMDc and save continuous-time matrices derived from the discrete map."""
    ds = load_timeseries(args.data, state_cols=args.state_cols, input_cols=args.input_cols, time_col=args.time_col, case_col=args.case_col, case_id=args.case_id)
    dt = args.dt if args.dt is not None else ds.dt
    if dt is None:
        raise ValueError("Provide --dt or --time-col so the continuous-time conversion has a sample interval.")
    outdir = ensure_dir(args.outdir)
    model = ContinuousDMDcModel(dt=float(dt), rank=parse_rank(str(args.rank))).fit(ds.X, ds.U, state_names=ds.state_cols, input_names=ds.input_cols)
    write_json(model.to_dict(), outdir / "continuous_dmdc_summary.json")
    pd.DataFrame(model.A_c_, index=ds.state_cols, columns=ds.state_cols).to_csv(outdir / "A_continuous.csv")
    if model.B_c_ is not None and model.B_c_.size:
        pd.DataFrame(model.B_c_, index=ds.state_cols, columns=ds.input_cols).to_csv(outdir / "B_continuous.csv")
    write_provenance(outdir, extra={"command": "continuous", "dt": float(dt)})
    print(f"Saved continuous-time DMDc outputs to {outdir}")
    print("Note: continuous matrices are derived from a discrete map and assume an approximately uniform dt.")


def cmd_make_thermal_loop_example(args: argparse.Namespace) -> None:
    """Create a synthetic thermal-loop tutorial dataset and configs."""
    paths = write_thermal_loop_example(args.outdir, n_time=int(args.n_time), seed=int(args.seed))
    write_provenance(args.outdir, extra={"command": "make-thermal-loop-example", "created_files": paths})
    print(f"Created thermal-loop tutorial assets in {args.outdir}")
    for name, path in paths.items():
        print(f"  {name}: {path}")


def cmd_recommend(args: argparse.Namespace) -> None:
    """Recommend a best model from an existing dashboard CSV."""
    table = pd.read_csv(args.table)
    outdir = ensure_dir(args.outdir)
    rec = recommend_best_model(table, require_stable=not bool(args.allow_unstable))
    write_json(rec, outdir / "best_model_recommendation.json")
    write_recommendation(rec, outdir / "best_model_recommendation.txt")
    write_provenance(outdir, extra={"command": "recommend", "source_table": args.table})
    print(f"Saved recommendation to {outdir}")
    print(rec.get("reason"))


def cmd_report(args: argparse.Namespace) -> None:
    report_path = generate_latex_report(args.run, output_tex=args.out, compile_pdf=bool(args.compile_pdf))
    print(f"Saved LaTeX report to {report_path}")


def _cmd_live_ingestion(args: argparse.Namespace, *, stream_type_override: str | None = None) -> None:
    """Shared implementation for live-replay and live-run."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_live_config(cfg))
    if stream_type_override is not None:
        args.stream_type = stream_type_override
    elif not getattr(args, "stream_type", None):
        args.stream_type = "csv_replay"
    require_live_fields(args)
    cfg = LiveIngestionConfig(
        stream_type=args.stream_type,
        path=args.path,
        state_cols=list(args.state_cols),
        input_cols=list(args.input_cols or []),
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
        outdir=args.outdir,
        chunk_size=int(getattr(args, "chunk_size", 1) or 1),
        poll_seconds=float(getattr(args, "poll_seconds", 0.0) or 0.0),
        max_samples=getattr(args, "max_samples", None),
        max_polls=getattr(args, "max_polls", None),
        buffer_seconds=getattr(args, "buffer_seconds", None),
        buffer_max_samples=getattr(args, "buffer_max_samples", None),
        start_at_end=bool(getattr(args, "start_at_end", False)),
        save_every_batch=bool(getattr(args, "save_every_batch", False)),
    )
    result = run_live_ingestion(cfg, config_path=config_path)
    print(f"Saved live ingestion logs to {result.outdir}")
    print(f"Batches: {result.n_batches}; samples seen: {result.n_samples_seen}; clean buffered: {result.n_clean_samples_buffered}; warnings: {result.n_warnings}")


def cmd_live_replay(args: argparse.Namespace) -> None:
    _cmd_live_ingestion(args, stream_type_override="csv_replay")


def cmd_live_run(args: argparse.Namespace) -> None:
    _cmd_live_ingestion(args, stream_type_override="csv_tail")



def _write_model_identity_if_available(args: argparse.Namespace, outdir: str | Path) -> None:
    """Persist model registry identity in live run folders for dashboards/reports."""
    try:
        if getattr(args, "model_registry_name", None):
            identity = resolve_model(name=args.model_registry_name, stage=getattr(args, "model_stage", "production"), version=getattr(args, "model_version", None), registry_root=getattr(args, "model_registry_root", "models/registry"))
        elif getattr(args, "model_path", None):
            identity = resolve_model(path=args.model_path)
        else:
            return
        write_model_identity(outdir, identity)
    except Exception as exc:
        Path(outdir).mkdir(parents=True, exist_ok=True)
        (Path(outdir) / "model_identity_warning.txt").write_text(f"Could not write model identity metadata: {exc}\n", encoding="utf-8")


def _cmd_live_prediction(args: argparse.Namespace, *, stream_type_override: str | None = None) -> None:
    """Shared implementation for live-replay-predict and live-run-predict."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_live_prediction_config(cfg))
    if stream_type_override is not None:
        args.stream_type = stream_type_override
    elif not getattr(args, "stream_type", None):
        args.stream_type = "csv_replay"
    require_live_prediction_fields(args)
    cfg = LivePredictionConfig(
        stream_type=args.stream_type,
        path=args.path,
        state_cols=list(args.state_cols),
        input_cols=list(args.input_cols or []),
        model_path=args.model_path,
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
        outdir=args.outdir,
        chunk_size=int(getattr(args, "chunk_size", 1) or 1),
        poll_seconds=float(getattr(args, "poll_seconds", 0.0) or 0.0),
        max_samples=getattr(args, "max_samples", None),
        max_polls=getattr(args, "max_polls", None),
        buffer_seconds=getattr(args, "buffer_seconds", None),
        buffer_max_samples=getattr(args, "buffer_max_samples", None),
        start_at_end=bool(getattr(args, "start_at_end", False)),
        save_every_batch=bool(getattr(args, "save_every_batch", False)),
        forecast_horizons_seconds=list(getattr(args, "forecast_horizons_seconds", None) or [5.0, 10.0, 30.0, 60.0]),
        discrete_dt_seconds=getattr(args, "discrete_dt_seconds", None),
    )
    result = run_live_prediction(cfg, config_path=config_path)
    _write_model_identity_if_available(args, result.outdir)
    print(f"Saved live prediction logs to {result.outdir}")
    print(
        f"Batches: {result.n_batches}; samples seen: {result.n_samples_seen}; "
        f"forecast origins: {result.n_forecast_origins}; forecast rows: {result.n_forecast_rows}; "
        f"warnings: {result.n_warnings}; model: {result.model_type}"
    )


def cmd_live_replay_predict(args: argparse.Namespace) -> None:
    _cmd_live_prediction(args, stream_type_override="csv_replay")


def cmd_live_run_predict(args: argparse.Namespace) -> None:
    _cmd_live_prediction(args, stream_type_override="csv_tail")



def _cmd_live_estimation(args: argparse.Namespace, *, stream_type_override: str | None = None) -> None:
    """Shared implementation for live-replay-estimate and live-run-estimate."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_live_estimation_config(cfg))
    if stream_type_override is not None:
        args.stream_type = stream_type_override
    elif not getattr(args, "stream_type", None):
        args.stream_type = "csv_replay"
    require_live_estimation_fields(args)
    cfg = LiveEstimationConfig(
        stream_type=args.stream_type,
        path=args.path,
        model_path=args.model_path,
        state_cols=list(args.state_cols) if getattr(args, "state_cols", None) else None,
        measurement_cols=list(args.measurement_cols),
        input_cols=list(args.input_cols or []),
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
        outdir=args.outdir,
        chunk_size=int(getattr(args, "chunk_size", 1) or 1),
        poll_seconds=float(getattr(args, "poll_seconds", 0.0) or 0.0),
        max_samples=getattr(args, "max_samples", None),
        max_polls=getattr(args, "max_polls", None),
        buffer_seconds=getattr(args, "buffer_seconds", None),
        buffer_max_samples=getattr(args, "buffer_max_samples", None),
        start_at_end=bool(getattr(args, "start_at_end", False)),
        save_every_batch=bool(getattr(args, "save_every_batch", False)),
        process_noise=float(getattr(args, "process_noise", 1.0e-6)),
        measurement_noise=float(getattr(args, "measurement_noise", 1.0e-3)),
        initial_covariance=float(getattr(args, "initial_covariance", 1.0)),
        forecast_horizons_seconds=list(getattr(args, "forecast_horizons_seconds", None) or []),
        discrete_dt_seconds=getattr(args, "discrete_dt_seconds", None),
    )
    result = run_live_estimation(cfg, config_path=config_path)
    _write_model_identity_if_available(args, result.outdir)
    print(f"Saved live state-estimation logs to {result.outdir}")
    print(
        f"Batches: {result.n_batches}; samples seen: {result.n_samples_seen}; "
        f"estimate updates: {result.n_estimate_updates}; forecast rows: {result.n_forecast_rows}; "
        f"warnings: {result.n_warnings}; estimator: {result.estimator_type}"
    )


def cmd_live_replay_estimate(args: argparse.Namespace) -> None:
    _cmd_live_estimation(args, stream_type_override="csv_replay")


def cmd_live_run_estimate(args: argparse.Namespace) -> None:
    _cmd_live_estimation(args, stream_type_override="csv_tail")



def _cmd_live_monitoring(args: argparse.Namespace, *, stream_type_override: str | None = None) -> None:
    """Shared implementation for live-replay-monitor and live-run-monitor."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_live_monitoring_config(cfg))
    if stream_type_override is not None:
        args.stream_type = stream_type_override
    elif not getattr(args, "stream_type", None):
        args.stream_type = "csv_replay"
    require_live_monitoring_fields(args)
    cfg = LiveMonitoringConfig(
        stream_type=args.stream_type,
        path=args.path,
        model_path=args.model_path,
        state_cols=list(args.state_cols) if getattr(args, "state_cols", None) else None,
        measurement_cols=list(args.measurement_cols),
        input_cols=list(args.input_cols or []),
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
        outdir=args.outdir,
        chunk_size=int(getattr(args, "chunk_size", 1) or 1),
        poll_seconds=float(getattr(args, "poll_seconds", 0.0) or 0.0),
        max_samples=getattr(args, "max_samples", None),
        max_polls=getattr(args, "max_polls", None),
        buffer_seconds=getattr(args, "buffer_seconds", None),
        buffer_max_samples=getattr(args, "buffer_max_samples", None),
        start_at_end=bool(getattr(args, "start_at_end", False)),
        save_every_batch=bool(getattr(args, "save_every_batch", False)),
        process_noise=float(getattr(args, "process_noise", 1.0e-6)),
        measurement_noise=float(getattr(args, "measurement_noise", 1.0e-3)),
        initial_covariance=float(getattr(args, "initial_covariance", 1.0)),
        forecast_horizons_seconds=list(getattr(args, "forecast_horizons_seconds", None) or [5.0, 10.0, 30.0]),
        discrete_dt_seconds=getattr(args, "discrete_dt_seconds", None),
        residual_abs_threshold=float(getattr(args, "residual_abs_threshold", 5.0)),
        innovation_abs_threshold=float(getattr(args, "innovation_abs_threshold", 5.0)),
        innovation_norm_threshold=getattr(args, "innovation_norm_threshold", None),
        covariance_trace_threshold=getattr(args, "covariance_trace_threshold", None),
        forecast_match_tolerance_seconds=getattr(args, "forecast_match_tolerance_seconds", None),
        max_abs_forecast_value=getattr(args, "max_abs_forecast_value", None),
        operating_ranges=getattr(args, "operating_ranges", None),
    )
    result = run_live_monitoring(cfg, config_path=config_path)
    _write_model_identity_if_available(args, result.outdir)
    print(f"Saved live monitoring outputs to {result.outdir}")
    print(
        f"estimate updates: {result.n_estimate_updates}; forecast rows: {result.n_forecast_rows}; "
        f"forecast residuals: {result.n_forecast_residuals}; alerts: {result.n_alerts}; "
        f"final trust score: {result.final_trust_score:.3f}"
    )


def cmd_live_replay_monitor(args: argparse.Namespace) -> None:
    _cmd_live_monitoring(args, stream_type_override="csv_replay")


def cmd_live_run_monitor(args: argparse.Namespace) -> None:
    _cmd_live_monitoring(args, stream_type_override="csv_tail")


def _cmd_live_adaptation(args: argparse.Namespace, *, stream_type_override: str | None = None) -> None:
    """Shared implementation for live-replay-adapt and live-run-adapt."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_live_adaptation_config(cfg))
    if stream_type_override is not None:
        args.stream_type = stream_type_override
    elif not getattr(args, "stream_type", None):
        args.stream_type = "csv_replay"
    require_live_adaptation_fields(args)
    cfg = LiveAdaptationConfig(
        stream_type=args.stream_type,
        path=args.path,
        model_path=args.model_path,
        state_cols=list(args.state_cols) if getattr(args, "state_cols", None) else None,
        measurement_cols=list(args.measurement_cols),
        input_cols=list(args.input_cols or []),
        time_col=args.time_col,
        case_col=args.case_col,
        case_id=args.case_id,
        outdir=args.outdir,
        chunk_size=int(getattr(args, "chunk_size", 1) or 1),
        poll_seconds=float(getattr(args, "poll_seconds", 0.0) or 0.0),
        max_samples=getattr(args, "max_samples", None),
        max_polls=getattr(args, "max_polls", None),
        buffer_seconds=getattr(args, "buffer_seconds", None),
        buffer_max_samples=getattr(args, "buffer_max_samples", None),
        start_at_end=bool(getattr(args, "start_at_end", False)),
        save_every_batch=bool(getattr(args, "save_every_batch", False)),
        process_noise=float(getattr(args, "process_noise", 1.0e-6)),
        measurement_noise=float(getattr(args, "measurement_noise", 1.0e-3)),
        initial_covariance=float(getattr(args, "initial_covariance", 1.0)),
        forecast_horizons_seconds=list(getattr(args, "forecast_horizons_seconds", None) or [5.0, 10.0, 30.0]),
        discrete_dt_seconds=getattr(args, "discrete_dt_seconds", None),
        residual_abs_threshold=float(getattr(args, "residual_abs_threshold", 5.0)),
        innovation_abs_threshold=float(getattr(args, "innovation_abs_threshold", 5.0)),
        innovation_norm_threshold=getattr(args, "innovation_norm_threshold", None),
        covariance_trace_threshold=getattr(args, "covariance_trace_threshold", None),
        forecast_match_tolerance_seconds=getattr(args, "forecast_match_tolerance_seconds", None),
        max_abs_forecast_value=getattr(args, "max_abs_forecast_value", None),
        operating_ranges=getattr(args, "operating_ranges", None),
        adaptation_enabled=bool(getattr(args, "adaptation_enabled", True)),
        adaptation_method=getattr(args, "adaptation_method", "horizon_state_bias"),
        bias_learning_rate=float(getattr(args, "bias_learning_rate", 0.01)),
        max_abs_bias=float(getattr(args, "max_abs_bias", 10.0)),
        max_update_step=float(getattr(args, "max_update_step", 0.25)),
        update_only_when_trust_above=float(getattr(args, "update_only_when_trust_above", 0.70)),
        skip_when_outside_training_envelope=bool(getattr(args, "skip_when_outside_training_envelope", True)),
        skip_on_alert_severity=list(getattr(args, "skip_on_alert_severity", ["critical"]) or []),
        clip_residual_abs=getattr(args, "clip_residual_abs", 20.0),
        apply_bias_to_forecasts=bool(getattr(args, "apply_bias_to_forecasts", True)),
    )
    result = run_live_adaptation(cfg, config_path=config_path)
    _write_model_identity_if_available(args, result.outdir)
    print(f"Saved live adaptation outputs to {result.outdir}")
    print(
        f"estimate updates: {result.n_estimate_updates}; forecast rows: {result.n_forecast_rows}; "
        f"residuals: {result.n_forecast_residuals}; bias events: {result.n_bias_update_events}; "
        f"accepted: {result.n_bias_updates_accepted}; skipped: {result.n_bias_updates_skipped}; "
        f"method: {result.adaptation_method}"
    )

    # Live Phase-6.2/6.3 integration: if the same config enables a long-term
    # archive, copy the run outputs into partitioned storage, then optionally
    # create compact summaries and quicklook plots.  This is intentionally done
    # after the live pass so the core monitoring/adaptation logic remains simple
    # and so archive failures do not silently change the ROM outputs.
    if config_path:
        try:
            raw_cfg = load_config(config_path)
            archive_section = raw_cfg.get("live_archive", raw_cfg.get("archive", {})) or {}
            if isinstance(archive_section, dict) and bool(archive_section.get("enabled", False)):
                arch_args = SimpleNamespace(**flatten_archive_config(raw_cfg))
                arch_args.run_dir = result.outdir
                require_archive_fields(arch_args)
                arch_cfg = LiveArchiveConfig(
                    root=arch_args.archive_root,
                    format=getattr(arch_args, "archive_format", "parquet"),
                    compression=getattr(arch_args, "archive_compression", "zstd"),
                    flush_rows=int(getattr(arch_args, "archive_flush_rows", 10000)),
                    flush_seconds=float(getattr(arch_args, "archive_flush_seconds", 30.0)),
                    write_csv_mirrors=bool(getattr(arch_args, "archive_write_csv_mirrors", False)),
                    strict_format=bool(getattr(arch_args, "archive_strict_format", False)),
                )
                archive_result = archive_live_run(result.outdir, arch_cfg, config_path=config_path)
                print(f"Archived live run to {archive_result.archive_root} ({archive_result.n_rows_archived} rows).")
                summaries = raw_cfg.get("summaries", {}) or {}
                if isinstance(summaries, dict) and bool(summaries.get("enabled", False)):
                    sum_args = SimpleNamespace(**flatten_archive_summary_config(raw_cfg))
                    require_archive_summary_fields(sum_args)
                    sum_result = summarize_live_archive(
                        LiveSummaryConfig(
                            archive_root=sum_args.archive_root,
                            outdir=getattr(sum_args, "summary_outdir", None),
                            windows_seconds=list(getattr(sum_args, "windows_seconds", None) or [60.0]),
                            max_files_per_kind=getattr(sum_args, "max_files_per_kind", None),
                            state_cols=list(getattr(sum_args, "state_cols", []) or []) or None,
                        ),
                        config_path=config_path,
                    )
                    print(f"Wrote archive summaries to {sum_result.outdir}.")
                quicklooks = raw_cfg.get("quicklooks", {}) or {}
                if isinstance(quicklooks, dict) and bool(quicklooks.get("enabled", False)):
                    q_args = SimpleNamespace(**flatten_archive_quicklook_config(raw_cfg))
                    require_archive_quicklook_fields(q_args)
                    q_result = make_archive_quicklooks(
                        QuicklookConfig(
                            archive_root=q_args.archive_root,
                            summaries_dir=getattr(q_args, "summaries_dir", None),
                            outdir=getattr(q_args, "quicklook_outdir", None),
                            window_label=getattr(q_args, "window_label", "60s"),
                        ),
                        config_path=config_path,
                    )
                    print(f"Wrote archive quicklooks to {q_result.outdir}.")
        except Exception as exc:
            print(f"Archive/summarize integration warning: {exc}")


def cmd_live_replay_adapt(args: argparse.Namespace) -> None:
    _cmd_live_adaptation(args, stream_type_override="csv_replay")


def cmd_live_run_adapt(args: argparse.Namespace) -> None:
    _cmd_live_adaptation(args, stream_type_override="csv_tail")


def cmd_live_dashboard(args: argparse.Namespace) -> None:
    """Launch the optional Streamlit dashboard for a live run directory."""

    if getattr(args, "config", None):
        cfg = load_config(args.config)
        apply_config_defaults(args, flatten_live_dashboard_config(cfg))
    require_live_dashboard_fields(args)
    mode = getattr(args, "mode", "auto") or "auto"
    archive_root = getattr(args, "archive_root", None)
    use_archive = mode == "archive" or (mode == "auto" and archive_root)
    if bool(getattr(args, "write_summary_only", False)):
        if use_archive:
            path = write_archive_dashboard_summary(archive_root or args.run_dir, window_label=getattr(args, "window_label", "60s"))
            print(f"Wrote archive dashboard summary to {path}")
        else:
            path = write_dashboard_summary(args.run_dir)
            print(f"Wrote live dashboard summary to {path}")
        return
    rc = launch_streamlit_dashboard(
        run_dir=args.run_dir,
        archive_root=archive_root,
        mode=mode,
        window_label=getattr(args, "window_label", "60s"),
        refresh_seconds=float(getattr(args, "refresh_seconds", 2.0)),
        host=getattr(args, "host", None),
        port=getattr(args, "port", None),
        theme=getattr(args, "theme", None),
        view=getattr(args, "view", "operator"),
        geometry_path=getattr(args, "geometry", None),
        residual_warning_threshold=float(getattr(args, "residual_warning_threshold", 2.0)),
        residual_critical_threshold=float(getattr(args, "residual_critical_threshold", 5.0)),
    )
    if rc != 0:
        raise SystemExit(rc)


def cmd_live_operator_report(args: argparse.Namespace) -> None:
    """Generate a compact live operator report."""

    outputs = generate_live_operator_report(
        run_dir=getattr(args, "run_dir", None),
        archive_root=getattr(args, "archive_root", None),
        outdir=getattr(args, "outdir", "outputs/live_operator_report"),
        window_label=getattr(args, "window_label", "60s"),
    )
    print(f"Wrote operator report Markdown: {outputs['markdown']}")
    print(f"Wrote operator report HTML: {outputs['html']}")


def cmd_archive_run(args: argparse.Namespace) -> None:
    """Archive one live run directory into partitioned storage."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_archive_config(cfg))
    require_archive_fields(args)
    cfg = LiveArchiveConfig(
        root=args.archive_root,
        format=getattr(args, "archive_format", "parquet"),
        compression=getattr(args, "archive_compression", "zstd"),
        flush_rows=int(getattr(args, "archive_flush_rows", 10000)),
        flush_seconds=float(getattr(args, "archive_flush_seconds", 30.0)),
        write_csv_mirrors=bool(getattr(args, "archive_write_csv_mirrors", False)),
        strict_format=bool(getattr(args, "archive_strict_format", False)),
    )
    result = archive_live_run(args.run_dir, cfg, config_path=config_path)
    print(f"Archived {result.n_rows_archived} rows from {result.n_files_archived} partition file(s).")
    print(f"Archive root: {result.archive_root}")
    print(f"Manifest: {result.manifest_path}")
    if result.format_used != result.format_requested:
        print(f"Note: requested {result.format_requested}, but wrote {result.format_used}. Install pyarrow for Parquet support.")


def cmd_archive_index(args: argparse.Namespace) -> None:
    """Display or export the live archive manifest."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_archive_config(cfg))
    if not getattr(args, "archive_root", None):
        args.archive_root = "live_archive"
    manifest = read_archive_manifest(args.archive_root)
    if getattr(args, "out", None):
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(args.out, index=False)
        print(f"Wrote manifest copy to {args.out}")
    if manifest.empty:
        print(f"No manifest rows found under {args.archive_root}")
        return
    print(f"Archive root: {args.archive_root}")
    print(f"Rows in manifest: {len(manifest)}")
    if "data_kind" in manifest:
        print(manifest["data_kind"].value_counts().to_string())


def cmd_archive_summarize(args: argparse.Namespace) -> None:
    """Create compact live archive summaries."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_archive_summary_config(cfg))
    require_archive_summary_fields(args)
    cfg = LiveSummaryConfig(
        archive_root=args.archive_root,
        outdir=getattr(args, "summary_outdir", None),
        windows_seconds=list(getattr(args, "windows_seconds", None) or [60.0, 300.0, 3600.0]),
        max_files_per_kind=getattr(args, "max_files_per_kind", None),
        state_cols=list(getattr(args, "state_cols", []) or []) or None,
    )
    result = summarize_live_archive(cfg, config_path=config_path)
    print(f"Wrote {result.n_summary_files} summary file(s) to {result.outdir}")


def cmd_archive_search(args: argparse.Namespace) -> None:
    """Search live archive rows for common conditions."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        vals = flatten_archive_config(cfg)
        if not getattr(args, "archive_root", None):
            args.archive_root = vals.get("archive_root")
    if not getattr(args, "archive_root", None):
        args.archive_root = "live_archive"
    result = search_archive(
        ArchiveSearchConfig(
            archive_root=args.archive_root,
            outdir=getattr(args, "outdir", "outputs/archive_search"),
            data_kind=getattr(args, "data_kind", None),
            alert_code=getattr(args, "alert_code", None),
            severity=getattr(args, "severity", None),
            state=getattr(args, "state", None),
            residual_above=getattr(args, "residual_above", None),
            trust_below=getattr(args, "trust_below", None),
            max_files_per_kind=getattr(args, "max_files_per_kind", None),
        ),
        config_path=config_path,
    )
    print(f"Found {result.n_matching_rows} matching row(s). Results: {result.results_csv}")
    print(f"Matching manifest files: {result.n_matching_manifest_files}. File list: {result.matching_files_txt}")


def cmd_archive_quicklook(args: argparse.Namespace) -> None:
    """Generate quicklook plots from live archive summaries."""

    config_path = getattr(args, "config", None)
    if config_path:
        cfg = load_config(config_path)
        apply_config_defaults(args, flatten_archive_quicklook_config(cfg))
    require_archive_quicklook_fields(args)
    cfg = QuicklookConfig(
        archive_root=args.archive_root,
        summaries_dir=getattr(args, "summaries_dir", None),
        outdir=getattr(args, "quicklook_outdir", None),
        window_label=getattr(args, "window_label", "60s"),
    )
    result = make_archive_quicklooks(cfg, config_path=config_path)
    print(f"Wrote {result.n_plots} quicklook plot(s) to {result.outdir}")


def cmd_model_register(args: argparse.Namespace) -> None:
    meta = register_model(args.model, name=args.name, registry_root=args.registry_root, stage=args.stage, version=args.version, model_type=args.model_type, metrics_path=args.metrics, notes=args.notes)
    print(f"Registered model: {meta.name}")
    print(f"Version: {meta.version}")
    print(f"Stage: {args.stage}")
    print(f"Model artifact: {meta.registered_model_path}")
    print(f"Registry index: {Path(args.registry_root) / 'registry_index.csv'}")
    print("Next: use [model].registry_name and [model].stage in live configs, or run model-promote to update production.")


def cmd_model_list(args: argparse.Namespace) -> None:
    idx = read_registry_index(args.registry_root)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True); idx.to_csv(args.out, index=False); print(f"Wrote registry index copy to {args.out}")
    if idx.empty:
        print(f"No registered models found under {args.registry_root}"); return
    cols = [c for c in ["name", "version", "stage", "model_type", "registered_utc", "registered_model_path"] if c in idx.columns]
    print(idx[cols].to_string(index=False))


def cmd_model_promote(args: argparse.Namespace) -> None:
    dep = promote_model(args.name, version=args.version, stage=args.stage, registry_root=args.registry_root)
    print(f"Promoted {args.name}@{args.version} to stage {args.stage}")
    print(f"Resolved path: {dep.get('model_path')}")


def cmd_model_resolve(args: argparse.Namespace) -> None:
    print(json.dumps(resolve_model(name=args.name, stage=args.stage, version=args.version, registry_root=args.registry_root), indent=2))


def cmd_validate_archive_schema(args: argparse.Namespace) -> None:
    if getattr(args, "config", None):
        cfg = load_config(args.config); vals = flatten_archive_config(cfg)
        if not getattr(args, "archive_root", None): args.archive_root = vals.get("archive_root")
    if not getattr(args, "archive_root", None): args.archive_root = "live_archive"
    result = validate_archive_schema(args.archive_root, outdir=getattr(args, "outdir", None))
    print(f"Archive schema status: {result.status}")
    print(f"Errors: {result.n_errors}; warnings: {result.n_warnings}; manifest rows: {result.manifest_rows}")
    print(f"Report: {result.validation_report}")
    print(f"Context index: {result.context_index_csv}")


def cmd_archive_context(args: argparse.Namespace) -> None:
    if getattr(args, "config", None):
        cfg = load_config(args.config); vals = flatten_archive_config(cfg)
        if not getattr(args, "archive_root", None): args.archive_root = vals.get("archive_root")
    if not getattr(args, "archive_root", None): args.archive_root = "live_archive"
    paths = build_archive_context_index(args.archive_root, outdir=getattr(args, "outdir", None))
    print(f"Context index: {paths['context_index_csv']}")
    print(f"Data-kind summary: {paths['data_kind_summary_csv']}")


def cmd_benchmark_archive(args: argparse.Namespace) -> None:
    archive_root = getattr(args, "archive_root", None) or str(Path(args.outdir) / "live_archive")
    result = run_archive_benchmark(
        ArchiveBenchmarkConfig(
            n_rows=int(args.n_rows),
            n_states=int(args.n_states),
            n_inputs=int(args.n_inputs),
            chunk_files=int(args.chunk_files),
            outdir=args.outdir,
            archive_root=archive_root,
            archive_format=args.archive_format,
            windows_seconds=list(args.windows_seconds or []),
            make_quicklooks=not bool(args.no_quicklooks),
        )
    )
    print(f"Archive benchmark complete: {result.outdir}")
    print(f"Rows: {result.n_rows:,}; archive write: {result.archive_write_mb_per_sec:.3g} MB/s; summary throughput: {result.summary_rows_per_sec:.3g} rows/s")
    print(f"Peak memory: {result.peak_memory_mb:.3g} MB")
    print(f"Metrics: {result.metrics_csv}")


def cmd_hpc_plan(args: argparse.Namespace) -> None:
    result = write_hpc_workflow_plan(args.config, outdir=args.outdir, steps=args.steps)
    print(f"Wrote HPC/local plan to {result.outdir}")
    print(f"Command plan: {result.command_plan}")
    print(f"Local runner: {result.local_runner}")
    print(f"Slurm campaign template: {result.slurm_campaign_template}")
    print(f"Slurm archive template: {result.slurm_archive_template}")
    print("Reminder: local workstation execution is the default. Slurm templates contain FIXME fields for account/partition/modules.")


def cmd_resources(args: argparse.Namespace) -> None:
    summary = get_resource_summary()
    if args.out:
        write_resource_summary(args.out); print(f"Wrote resource summary to {args.out}")
    print(json.dumps(summary, indent=2))


def cmd_campaign(args: argparse.Namespace) -> None:
    result = run_campaign(args.config, steps=args.steps, dry_run=bool(args.dry_run))
    print(f"Campaign directory: {result.campaign_dir}")
    print(f"Steps requested: {', '.join(result.steps_requested)}")
    print(f"Steps run: {', '.join(result.steps_run)}")
    print(f"Succeeded: {result.n_succeeded}; failed: {result.n_failed}; dry-run: {result.dry_run}")
    print(f"Plan: {result.plan_md}")
    print(f"Step index: {result.step_index_csv}")
    print(f"Next steps: {result.next_steps_md}")


def cmd_workflow(args: argparse.Namespace) -> None:
    """Run one or more configured fit jobs.

    This is intentionally a thin orchestration layer over ``cmd_fit`` so that configured and
    command-line runs use exactly the same model-fitting path.
    """

    cfg = load_config(args.config)
    runs = expand_case_runs(cfg)
    print(f"Running {len(runs)} configured fit job(s).")
    for i, run in enumerate(runs, start=1):
        print(f"[{i}/{len(runs)}] {run.get('name', 'fit')} -> {run['outdir']}")
        fit_args = SimpleNamespace(
            command="fit",
            config=None,
            data=run.get("data"),
            state_cols=run.get("state_cols"),
            input_cols=run.get("input_cols", []),
            time_col=run.get("time_col"),
            case_col=run.get("case_col"),
            case_id=run.get("case_id"),
            rank=str(run.get("rank", "full")),
            center=bool(run.get("center", False)),
            scale=bool(run.get("scale", False)),
            outdir=run.get("outdir"),
            plots=bool(run.get("plots", False)),
            n_delays=int(run.get("n_delays", 1)),
        )
        cmd_fit(fit_args)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "guide":
        cmd_guide(args)
    elif args.command == "import-data":
        cmd_import_data(args)
    elif args.command == "fit":
        cmd_fit(args)
    elif args.command == "predict":
        cmd_predict(args)
    elif args.command == "select-sensors":
        cmd_select_sensors(args)
    elif args.command == "pod":
        cmd_pod(args)
    elif args.command == "pod-sensors":
        cmd_pod_sensors(args)
    elif args.command == "pod-dmdc":
        cmd_pod_dmdc(args)
    elif args.command == "pod-ml":
        cmd_pod_ml(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "sweep":
        cmd_sweep(args)
    elif args.command == "continuous":
        cmd_continuous(args)
    elif args.command == "adaptive-fit":
        cmd_adaptive_fit(args)
    elif args.command == "make-thermal-loop-example":
        cmd_make_thermal_loop_example(args)
    elif args.command == "recommend":
        cmd_recommend(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "live-replay":
        cmd_live_replay(args)
    elif args.command == "live-run":
        cmd_live_run(args)
    elif args.command == "live-replay-predict":
        cmd_live_replay_predict(args)
    elif args.command == "live-run-predict":
        cmd_live_run_predict(args)
    elif args.command == "live-replay-estimate":
        cmd_live_replay_estimate(args)
    elif args.command == "live-run-estimate":
        cmd_live_run_estimate(args)
    elif args.command == "live-replay-monitor":
        cmd_live_replay_monitor(args)
    elif args.command == "live-run-monitor":
        cmd_live_run_monitor(args)
    elif args.command == "live-replay-adapt":
        cmd_live_replay_adapt(args)
    elif args.command == "live-run-adapt":
        cmd_live_run_adapt(args)
    elif args.command == "live-dashboard":
        cmd_live_dashboard(args)
    elif args.command == "live-operator-report":
        cmd_live_operator_report(args)
    elif args.command == "archive-run":
        cmd_archive_run(args)
    elif args.command == "archive-index":
        cmd_archive_index(args)
    elif args.command == "archive-summarize":
        cmd_archive_summarize(args)
    elif args.command == "archive-search":
        cmd_archive_search(args)
    elif args.command == "archive-quicklook":
        cmd_archive_quicklook(args)
    elif args.command == "model-register":
        cmd_model_register(args)
    elif args.command == "model-list":
        cmd_model_list(args)
    elif args.command == "model-promote":
        cmd_model_promote(args)
    elif args.command == "model-resolve":
        cmd_model_resolve(args)
    elif args.command == "validate-archive-schema":
        cmd_validate_archive_schema(args)
    elif args.command == "archive-context":
        cmd_archive_context(args)
    elif args.command == "benchmark-archive":
        cmd_benchmark_archive(args)
    elif args.command == "hpc-plan":
        cmd_hpc_plan(args)
    elif args.command == "resources":
        cmd_resources(args)
    elif args.command == "campaign":
        cmd_campaign(args)
    elif args.command == "inspect-data":
        cmd_inspect_data(args)
    elif args.command == "resample":
        cmd_resample(args)
    elif args.command == "workflow":
        cmd_workflow(args)
    else:
        raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
