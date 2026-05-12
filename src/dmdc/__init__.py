"""Dynamic Mode Decomposition with control (DMDc) and ROM live-monitoring toolkit."""

__version__ = "0.1.0a0"

from .config import expand_case_runs, load_config
from .data import TimeSeriesDataset, load_timeseries, load_trajectories
from .delayed import make_delay_embedding, make_delay_embeddings_for_trajectories
from .graph import GraphConstrainedDMDcModel, LoopGraph
from .model import DMDcModel
from .pod import PODBasis
from .reduced import PODDMDcPipeline
from .ml import PODDynamicsRegressor
from .resampling import inspect_table, resample_all_cases
from .stability import analyze_transition_matrix
from .reports import generate_latex_report
from .sensor_selection import SensorSelectionResult, qr_sensor_ranking, reconstruction_error_vs_sensors
from .pod_sensors import (
    PODSensorSelectionResult,
    estimate_coefficients_from_sensors,
    reconstruct_from_sensors,
    select_pod_sensors,
)
from .sweeps import run_rank_delay_sweep
from .regularized import RegularizedDMDcModel
from .continuous import ContinuousDMDcModel, discrete_to_continuous
from .adaptive import AdaptiveDMDcModel
from .kalman import LinearKalmanFilter, estimate_pod_state_with_kalman, pod_measurement_matrix
from .loop_geometry import LoopGeometry as PhysicalLoopGeometry
from .operating_conditions import summarize_operating_conditions
from .uncertainty import bootstrap_mean_ci, bootstrap_metric_ci
from .recommendations import recommend_best_model
from .provenance import write_provenance
from .thermal_loop_example import generate_thermal_loop_dataframe, write_thermal_loop_example
from .streaming import LiveSample, CSVReplayAdapter, CSVTailAdapter, make_stream_adapter
from .live_buffer import RollingLiveBuffer, LiveBufferWarning
from .live import LiveIngestionConfig, LiveIngestionResult, run_live_ingestion
from .live_predictor import ForecastSettings, ForecastResult, LivePredictor, forecast_frame_to_wide
from .live_forecast import LivePredictionConfig, LivePredictionResult, run_live_prediction
from .live_estimation import (
    LiveEstimationConfig,
    LiveEstimationResult,
    LivePODKalmanEstimator,
    PODKalmanEstimatorSettings,
    run_live_estimation,
)
from .live_monitoring import (
    LiveMonitoringConfig,
    LiveMonitoringResult,
    run_live_monitoring,
    build_live_monitoring_tables,
    compute_forecast_residuals,
)

from .live_adaptation import (
    BiasCorrector,
    LiveAdaptationConfig,
    LiveAdaptationResult,
    apply_bias_history_to_forecasts,
    build_live_adaptation_tables,
    compute_bias_update_events,
    run_live_adaptation,
)
from .live_archive import LiveArchiveConfig, ArchiveRunResult, LiveArchiveWriter, archive_live_run, read_archive_manifest
from .live_summaries import LiveSummaryConfig, LiveSummaryResult, summarize_live_archive
from .live_quicklooks import QuicklookConfig, QuicklookResult, make_archive_quicklooks
from .archive_search import ArchiveSearchConfig, ArchiveSearchResult, search_archive
from .importers import TabularFileImporter, FolderTableImporter, LabVIEWDAQFolderImporter, EPICSPVImporter, ImportResult
from .import_workflow import run_import_workflow
from .operator_schematic import build_sensor_status_table, write_schematic_status_outputs
from .archive_benchmark import ArchiveBenchmarkConfig, ArchiveBenchmarkResult, run_archive_benchmark
from .hpc_workflows import HPCPlanResult, write_hpc_workflow_plan
from .live_dashboard import (
    LiveDashboardSummary,
    ArchiveDashboardSummary,
    launch_streamlit_dashboard,
    read_live_dashboard_tables,
    summarize_live_dashboard,
    write_dashboard_summary,
    read_archive_dashboard_tables,
    summarize_archive_dashboard,
    write_archive_dashboard_summary,
)

__all__ = [
    "__version__",
    "DMDcModel",
    "PODBasis",
    "PODDMDcPipeline",
    "PODDynamicsRegressor",
    "GraphConstrainedDMDcModel",
    "LoopGraph",
    "SensorSelectionResult",
    "PODSensorSelectionResult",
    "TimeSeriesDataset",
    "expand_case_runs",
    "load_config",
    "load_timeseries",
    "load_trajectories",
    "inspect_table",
    "resample_all_cases",
    "analyze_transition_matrix",
    "generate_latex_report",
    "make_delay_embedding",
    "make_delay_embeddings_for_trajectories",
    "qr_sensor_ranking",
    "reconstruction_error_vs_sensors",
    "select_pod_sensors",
    "estimate_coefficients_from_sensors",
    "reconstruct_from_sensors",
    "RegularizedDMDcModel",
    "AdaptiveDMDcModel",
    "ContinuousDMDcModel",
    "discrete_to_continuous",
    "LinearKalmanFilter",
    "estimate_pod_state_with_kalman",
    "pod_measurement_matrix",
    "PhysicalLoopGeometry",
    "summarize_operating_conditions",
    "bootstrap_mean_ci",
    "bootstrap_metric_ci",
    "recommend_best_model",
    "write_provenance",
    "generate_thermal_loop_dataframe",
    "write_thermal_loop_example",
    "run_rank_delay_sweep",
    "LiveSample",
    "CSVReplayAdapter",
    "CSVTailAdapter",
    "make_stream_adapter",
    "RollingLiveBuffer",
    "LiveBufferWarning",
    "LiveIngestionConfig",
    "LiveIngestionResult",
    "run_live_ingestion",
    "ForecastSettings",
    "ForecastResult",
    "LivePredictor",
    "forecast_frame_to_wide",
    "LivePredictionConfig",
    "LivePredictionResult",
    "run_live_prediction",
    "LiveEstimationConfig",
    "LiveEstimationResult",
    "LivePODKalmanEstimator",
    "PODKalmanEstimatorSettings",
    "run_live_estimation",
    "LiveMonitoringConfig",
    "LiveMonitoringResult",
    "run_live_monitoring",
    "build_live_monitoring_tables",
    "compute_forecast_residuals",
    "BiasCorrector",
    "LiveAdaptationConfig",
    "LiveAdaptationResult",
    "run_live_adaptation",
    "build_live_adaptation_tables",
    "compute_bias_update_events",
    "apply_bias_history_to_forecasts",
    "LiveArchiveConfig",
    "ArchiveRunResult",
    "LiveArchiveWriter",
    "archive_live_run",
    "read_archive_manifest",
    "LiveSummaryConfig",
    "LiveSummaryResult",
    "summarize_live_archive",
    "QuicklookConfig",
    "QuicklookResult",
    "make_archive_quicklooks",
    "ArchiveSearchConfig",
    "ArchiveSearchResult",
    "search_archive",
    "ImportResult",
    "TabularFileImporter",
    "FolderTableImporter",
    "LabVIEWDAQFolderImporter",
    "EPICSPVImporter",
    "run_import_workflow",
    "LiveDashboardSummary",
    "ArchiveDashboardSummary",
    "build_sensor_status_table",
    "write_schematic_status_outputs",
    "ArchiveBenchmarkConfig",
    "ArchiveBenchmarkResult",
    "run_archive_benchmark",
    "HPCPlanResult",
    "write_hpc_workflow_plan",
    "read_archive_dashboard_tables",
    "summarize_archive_dashboard",
    "write_archive_dashboard_summary",
]
