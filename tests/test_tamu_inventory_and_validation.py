from __future__ import annotations

from pathlib import Path

import pandas as pd

from dmdc.cli import main
from dmdc.tamu_data import build_nearest_fit_table, build_tamu_inventory, build_tamu_validation_catalog, export_tamu_validation_artifacts


def _write_sample_case(case_dir: Path) -> None:
    case_dir.mkdir(parents=True)
    (case_dir / "NC1_X.csv").write_text("1,2,3\n4,5,6\n", encoding="utf-8")
    (case_dir / "NC1_U.csv").write_text("7,8\n9,10\n", encoding="utf-8")
    (case_dir / "NC1_V.csv").write_text("11,12\n13,14\n", encoding="utf-8")
    (case_dir / "NC1_Y.csv").write_text("15,16\n17,18\n", encoding="utf-8")
    (case_dir / "03192025_NC1_TransientWorkspace.mat").write_bytes(b"MATLAB")
    (case_dir / "03192025_NC1_FiberOpticWorkspace.mat").write_bytes(b"MATLAB")
    (case_dir / "meta_data.json").write_text(
        '{\n'
        '  "start_date": "03/19/2025",\n'
        '  "start_time": "13:24",\n'
        '  "measurement_date": "03/19/2025"\n'
        '  "measurment_time": "17:55",\n'
        '  "system_settings": {\n'
        '    "power": {"hot_1": 150, "hot_2": 0, "cold_1_2": 0, "Test_Section": 0},\n'
        '    "temperature": {"hot_1": 40, "hot_2": 0, "cold_1_2": 0},\n'
        '    "volumetric_flow_rate": {"flow_rate": 100}\n'
        '    "piv_frame_rate": {"full_field": 300}\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )


def _write_validation_source(path: Path, *, fluid: str, case_name: str | None = None) -> None:
    case_name = case_name or f"{fluid.title()} 1"
    values = {
        "salt": [
            ("Air T inlet", 25.96, "C"),
            ("Air T outlet", 112.8, "C"),
            ("Air flow", 37.0, "L/min"),
            ("Heater Power", 232.3, "W"),
            ("Heat Removed", 55.58, "W"),
            ("TP1", 176.22, "C"),
            ("TP2", 170.12, "C"),
            ("TP3", 168.22, "C"),
            ("TP4", 173.26, "C"),
            ("TP5", 174.35, "C"),
            ("TP6", 179.38, "C"),
            ("TW1", 166.85, "C"),
            ("TW2", 168.42, "C"),
            ("TW3", 167.82, "C"),
            ("TW4", 169.11, "C"),
            ("TW5", 192.23, "C"),
            ("TW6", 187.92, "C"),
            ("TW7", 175.16, "C"),
            ("TW8", 173.60, "C"),
            ("TW9", 173.58, "C"),
            ("TW10 (on shell of HX)", 116.88, "C"),
            ("TW11", 171.72, "C"),
            ("Area-weighted mean velocity", 0.0185, "m/s"),
            ("Mass Flow rate", 0.0158, "kg/s"),
        ],
        "water": [
            ("Air T inlet", 23.7, "C"),
            ("Air T outlet", 30.96, "C"),
            ("Air flow", 188.0, "L/min"),
            ("Heater Power", 58.8, "W"),
            ("Heat Removed", 26.86, "W"),
            ("TP1", 40.88, "C"),
            ("TP2", 40.33, "C"),
            ("TP3", 41.33, "C"),
            ("TP4", 41.69, "C"),
            ("TP5", 41.74, "C"),
            ("TP6", 41.62, "C"),
            ("TW1", 39.47, "C"),
            ("TW2", 39.95, "C"),
            ("TW3", 39.76, "C"),
            ("TW4", 40.23, "C"),
            ("TW5", 43.68, "C"),
            ("TW6", 47.06, "C"),
            ("TW7", 41.90, "C"),
            ("TW8", 40.42, "C"),
            ("TW9", 41.34, "C"),
            ("TW10 (on shell of HX)", 30.34, "C"),
            ("TW11", 40.45, "C"),
            ("Area-weighted mean velocity", 0.0190, "m/s"),
            ("Mass Flow rate", 0.0083, "kg/s"),
        ],
    }[fluid]
    lines = ["measurement," + case_name + ",units"]
    lines.extend(f"{measurement},{value},{unit}" for measurement, value, unit in values)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_single_phase_workbook(path: Path, *, tp1_override: float | None = None) -> None:
    columns = [
        "measurement",
        "Salt Test 1",
        "Salt Test 2",
        "Salt Test 3",
        "Salt Test 4",
        "Water Test 1",
        "Water Test 2",
        "Water Test 3",
        "Water Test 4",
    ]
    rows = [
        ["Air T inlet (°C)", 25.96, 26.04, 26.64, 26.82, 23.7, 23.65, 23.72, 23.79],
        ["Air T outlet (°C)", 112.8, 114.29, 122.6, 132.96, 30.96, 33.43, 35.3, 39.63],
        ["Air flow (L/min)", 37.0, 37.0, 37.0, 37.0, 188.0, 186.0, 190.0, 189.0],
        ["Heater Power (W)", 232.3, 265.7, 297.5, 337.6, 58.8, 77.6, 93.0, 129.0],
        ["Heat Removed (W)", 55.58, 56.34, 60.55, 65.98, 26.86, 35.63, 43.02, 58.06],
        ["TP1 (°C)", tp1_override if tp1_override is not None else 176.22, 180.11, 192.66, 208.19, 40.88, 46.87, 50.65, 60.30],
        ["TP2 (°C)", 170.12, 173.48, 185.37, 202.59, 40.33, 45.89, 49.99, 59.56],
        ["TP3 (°C)", 168.22, 173.52, 186.17, 202.80, 41.33, 46.91, 50.87, 60.46],
        ["TP4 (°C)", 173.26, 176.59, 189.42, 205.74, 41.69, 47.44, 51.77, 61.49],
        ["TP5 (°C)", 174.35, 178.49, 190.50, 206.17, 41.74, 47.42, 51.64, 61.41],
        ["TP6 (°C)", 179.38, 183.57, 193.32, 208.21, 41.62, 47.32, 51.53, 61.23],
        ["TW1 (°C)", 166.85, 170.71, 181.85, 196.62, 39.47, 44.71, 48.92, 58.59],
        ["TW2 (°C)", 168.42, 171.93, 182.93, 198.00, 39.95, 45.38, 49.40, 58.81],
        ["TW3 (°C)", 167.82, 170.42, 181.75, 197.27, 39.76, 45.14, 49.12, 58.45],
        ["TW4 (°C)", 169.11, 172.34, 184.85, 201.71, 40.23, 45.73, 49.75, 59.23],
        ["TW5 (°C)", 192.23, 198.54, 212.44, 230.57, 43.68, 49.83, 54.47, 65.06],
        ["TW6 (°C)", 187.92, 193.87, 206.98, 223.61, 47.06, 54.29, 59.23, 70.99],
        ["TW7 (°C)", 175.16, 180.08, 191.69, 208.11, 41.90, 47.95, 51.47, 60.84],
        ["TW8 (°C)", 173.60, 177.17, 188.52, 204.22, 40.42, 46.12, 50.27, 59.53],
        ["TW9 (°C)", 173.58, 177.52, 189.34, 204.73, 41.34, 46.77, 50.76, 60.68],
        ["TW10 (on shell of HX) (°C)", 116.88, 116.59, 125.94, 136.78, 30.34, 32.61, 34.23, 38.31],
        ["TW11 (°C)", 171.72, 175.26, 187.40, 202.99, 40.45, 46.05, 50.01, 59.43],
        ["Area-weighted mean velocity (m/s)", 0.0185, 0.0196, 0.0205, 0.0237, 0.0190, 0.0230, 0.0277, 0.0350],
        ["Mass Flow rate (kg/s)", 0.0158, 0.0168, 0.0175, 0.0201, 0.0083, 0.0100, 0.0120, 0.0151],
    ]
    pd.DataFrame(rows, columns=columns).to_excel(path, index=False)


def _write_single_phase_workbook_with_noise_column(path: Path) -> None:
    frame = pd.DataFrame(
        [
            ["Air T inlet (°C)", 25.96, 26.04, 26.64, 26.82, 23.7, 23.65, 23.72, 23.79, "reference only"],
            ["Air T outlet (°C)", 112.8, 114.29, 122.6, 132.96, 30.96, 33.43, 35.3, 39.63, ""],
            ["Air flow (L/min)", 37.0, 37.0, 37.0, 37.0, 188.0, 186.0, 190.0, 189.0, ""],
            ["Heater Power (W)", 232.3, 265.7, 297.5, 337.6, 58.8, 77.6, 93.0, 129.0, ""],
            ["Heat Removed (W)", 55.58, 56.34, 60.55, 65.98, 26.86, 35.63, 43.02, 58.06, ""],
            ["TP1 (°C)", 176.22, 180.11, 192.66, 208.19, 40.88, 46.87, 50.65, 60.30, ""],
            ["TP2 (°C)", 170.12, 173.48, 185.37, 202.59, 40.33, 45.89, 49.99, 59.56, ""],
            ["TP3 (°C)", 168.22, 173.52, 186.17, 202.80, 41.33, 46.91, 50.87, 60.46, ""],
            ["TP4 (°C)", 173.26, 176.59, 189.42, 205.74, 41.69, 47.44, 51.77, 61.49, ""],
            ["TP5 (°C)", 174.35, 178.49, 190.50, 206.17, 41.74, 47.42, 51.64, 61.41, ""],
            ["TP6 (°C)", 179.38, 183.57, 193.32, 208.21, 41.62, 47.32, 51.53, 61.23, ""],
            ["TW1 (°C)", 166.85, 170.71, 181.85, 196.62, 39.47, 44.71, 48.92, 58.59, ""],
            ["TW2 (°C)", 168.42, 171.93, 182.93, 198.00, 39.95, 45.38, 49.40, 58.81, ""],
            ["TW3 (°C)", 167.82, 170.42, 181.75, 197.27, 39.76, 45.14, 49.12, 58.45, ""],
            ["TW4 (°C)", 169.11, 172.34, 184.85, 201.71, 40.23, 45.73, 49.75, 59.23, ""],
            ["TW5 (°C)", 192.23, 198.54, 212.44, 230.57, 43.68, 49.83, 54.47, 65.06, ""],
            ["TW6 (°C)", 187.92, 193.87, 206.98, 223.61, 47.06, 54.29, 59.23, 70.99, ""],
            ["TW7 (°C)", 175.16, 180.08, 191.69, 208.11, 41.90, 47.95, 51.47, 60.84, ""],
            ["TW8 (°C)", 173.60, 177.17, 188.52, 204.22, 40.42, 46.12, 50.27, 59.53, ""],
            ["TW9 (°C)", 173.58, 177.52, 189.34, 204.73, 41.34, 46.77, 50.76, 60.68, ""],
            ["TW10 (on shell of HX) (°C)", 116.88, 116.59, 125.94, 136.78, 30.34, 32.61, 34.23, 38.31, ""],
            ["TW11 (°C)", 171.72, 175.26, 187.40, 202.99, 40.45, 46.05, 50.01, 59.43, ""],
            ["Area-weighted mean velocity (m/s)", 0.0185, 0.0196, 0.0205, 0.0237, 0.0190, 0.0230, 0.0277, 0.0350, ""],
            ["Mass Flow rate (kg/s)", 0.0158, 0.0168, 0.0175, 0.0201, 0.0083, 0.0100, 0.0120, 0.0151, ""],
        ],
        columns=[
            "measurement",
            "Salt Test 1",
            "Salt Test 2",
            "Salt Test 3",
            "Salt Test 4",
            "Water Test 1",
            "Water Test 2",
            "Water Test 3",
            "Water Test 4",
            "Notes",
        ],
    )
    frame.to_excel(path, index=False)


def _write_two_phase_workbook(path: Path) -> None:
    frame = pd.DataFrame(
        [
            ["", "Big", "Med", "Small", "", "", "Big", "Med", "Small"],
            ["Heater Power (W)", 550, 551, 555, "", "", 77.6, 77.6, 77.6],
            ["Air flow (L/min)", 0, 182, 300, "", "", 188, 188, 188],
            ["Area-weighted mean velocity (m/s)", 0.032, 0.03, 0.028, "", "", 0.026, 0.026, 0.026],
        ],
        columns=["measurement", "Salt Test 1", "Salt Test 2", "Salt Test 3", "sep1", "sep2", "Water Test 1", "Water Test 2", "Water Test 3"],
    )
    frame.to_excel(path, index=False)


def _write_pseudo_case_dir(case_dir: Path) -> None:
    case_dir.mkdir(parents=True)
    (case_dir / "X.csv").write_text("1,2,3\n4,5,6\n", encoding="utf-8")
    (case_dir / "U.csv").write_text("7,8\n9,10\n", encoding="utf-8")
    (case_dir / "V.csv").write_text("11,12\n13,14\n", encoding="utf-8")
    (case_dir / "Y.csv").write_text("15,16\n17,18\n", encoding="utf-8")


def test_tamu_inventory_repairs_metadata_and_writes_reports(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    (root / "notes.txt").write_text("hello\n", encoding="utf-8")
    result = build_tamu_inventory(root, tmp_path / "inventory")
    case_df = pd.read_csv(result.case_inventory_csv)
    assert len(case_df) == 1
    assert case_df.loc[0, "metadata_parse_status"] == "repaired"
    assert Path(result.readme_md).exists()
    assert Path(result.executive_summary_md).exists()
    assert Path(result.folder_comparison_csv).exists()
    assert Path(result.subfolder_inventory_csv).exists()
    assert Path(result.table_of_contents_md).exists()
    assert Path(result.folder_summaries_md).exists()
    assert "Loop Operational Data" in Path(result.readme_md).read_text(encoding="utf-8")
    assert "2025_03_19" in Path(result.executive_summary_md).read_text(encoding="utf-8")
    assert "2025_03_19" in Path(result.folder_summaries_md).read_text(encoding="utf-8")


def test_tamu_validation_export_writes_normalized_and_physor_outputs(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    salt = tmp_path / "salt_validation_source.csv"
    water = tmp_path / "water_validation_source.csv"
    _write_validation_source(salt, fluid="salt")
    _write_validation_source(water, fluid="water")
    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt, water],
    )
    assert result.normalized_cases_csv is not None
    assert result.physor_wide_csv is not None
    assert result.nearest_fit_csv is not None
    normalized = pd.read_csv(result.normalized_cases_csv)
    assert set(normalized["fluid"]) == {"salt", "water"}
    physor = pd.read_csv(result.physor_wide_csv)
    assert "Kelvin" in physor.columns


def test_tamu_validation_export_writes_consistency_audit_and_dedupes_cases(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    salt_a = tmp_path / "salt_validation_source_a.csv"
    salt_b = tmp_path / "salt_validation_source_b.csv"
    _write_validation_source(salt_a, fluid="salt")
    _write_validation_source(salt_b, fluid="salt")

    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt_a, salt_b],
    )

    normalized = pd.read_csv(result.normalized_cases_csv)
    assert list(normalized["case_name"]) == ["Salt 1"]
    consistency = pd.read_csv(tmp_path / "validation_export" / "validation_source_consistency_report.csv")
    assert set(consistency["status"]) == {"match"}


def test_tamu_validation_export_canonicalizes_test_style_case_names(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    salt_a = tmp_path / "salt_validation_source_a.csv"
    salt_b = tmp_path / "salt_validation_source_b.csv"
    _write_validation_source(salt_a, fluid="salt", case_name="Salt 1")
    _write_validation_source(salt_b, fluid="salt", case_name="Salt Test 1")

    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt_a, salt_b],
    )

    normalized = pd.read_csv(result.normalized_cases_csv)
    assert list(normalized["case_name"]) == ["Salt 1"]
    consistency = pd.read_csv(tmp_path / "validation_export" / "validation_source_consistency_report.csv")
    assert set(consistency["case_name"]) == {"Salt 1"}
    assert set(consistency["status"]) == {"match"}


def test_tamu_validation_export_parses_office_workbooks_and_blocks_mismatches(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    office = root / "Jadyn_runs" / "Jadyn_runs_Office"
    office.mkdir(parents=True)
    _write_single_phase_workbook(office / "SinglePhaseDataBase.xlsx", tp1_override=176.25)
    _write_two_phase_workbook(office / "TwoPhaseDataBase.xlsx")

    salt = tmp_path / "salt_validation_source.csv"
    water = tmp_path / "water_validation_source.csv"
    _write_validation_source(salt, fluid="salt")
    _write_validation_source(water, fluid="water")

    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt, water],
    )

    office_rows = pd.read_csv(result.office_workbook_rows_csv)
    assert "Salt 1" in set(office_rows["case_name"])
    assert "Salt 1 Big" in set(office_rows["case_name"])

    promotion = pd.read_csv(result.office_workbook_promotion_csv)
    single_phase = promotion[promotion["source_profile"] == "jadyn_office_workbook_single_phase"]
    assert "blocked_by_mismatch" in set(single_phase["promotion_status"])
    mismatched = single_phase[single_phase["promotion_status"] == "blocked_by_mismatch"]
    assert "TP1_C" in ";".join(mismatched["mismatch_fields"].fillna(""))


def test_tamu_validation_export_audits_single_phase_workbook_rows_even_with_noise_columns(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    office = root / "Jadyn_runs" / "Jadyn_runs_Office"
    office.mkdir(parents=True)
    _write_single_phase_workbook_with_noise_column(office / "SinglePhaseDataBase.xlsx")
    _write_two_phase_workbook(office / "TwoPhaseDataBase.xlsx")

    salt = tmp_path / "salt_validation_source.csv"
    water = tmp_path / "water_validation_source.csv"
    _write_validation_source(salt, fluid="salt")
    _write_validation_source(water, fluid="water")

    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt, water],
    )

    source_index = pd.read_csv(result.source_index_csv)
    single_phase_index = source_index[source_index["source_profile"] == "jadyn_office_workbook_single_phase"].iloc[0]
    assert int(single_phase_index["repeated_source_rows"]) == 8

    promotion = pd.read_csv(result.office_workbook_promotion_csv)
    single_phase = promotion[promotion["source_profile"] == "jadyn_office_workbook_single_phase"]
    matched_cases = single_phase[single_phase["case_name"].isin(["Salt 1", "Water 1"])]
    assert set(matched_cases["promotion_status"]) == {"duplicate_consistent"}
    assert set(matched_cases["consistency_status"]) == {"match"}
    unmatched_cases = single_phase[~single_phase["case_name"].isin(["Salt 1", "Water 1"])]
    assert "blocked_by_mismatch" in set(unmatched_cases["promotion_status"])


def test_tamu_validation_catalog_writes_buckets_and_velocity_plots(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    (root / "2025_03_19" / "03192025_Water1.txt").write_text(
        "NC1 steady state\nNC2 transient\n",
        encoding="utf-8",
    )
    office = root / "Jadyn_runs" / "Jadyn_runs_Office"
    office.mkdir(parents=True)
    _write_single_phase_workbook(office / "SinglePhaseDataBase.xlsx")
    _write_two_phase_workbook(office / "TwoPhaseDataBase.xlsx")
    pd.DataFrame([["Y/H", 0.25, 0.5], ["", 0.01, 0.02]], columns=["measurement", "Pr = 54.3", "Pr = 50.8"]).to_excel(
        office / "Full Velocity Profiles.xlsx",
        index=False,
    )
    salt = tmp_path / "salt_validation_source.csv"
    water = tmp_path / "water_validation_source.csv"
    _write_validation_source(salt, fluid="salt")
    _write_validation_source(water, fluid="water")

    result = build_tamu_validation_catalog(
        tmp_path / "validation_catalog",
        inventory_root=root,
        source_tables=[salt, water],
    )

    catalog = pd.read_csv(result.validation_catalog_csv)
    assert "steady_velocity_profile_candidates" in set(catalog["candidate_bucket"])
    assert "transient_sensor_candidates" in set(catalog["candidate_bucket"])
    assert "steady_sensor_candidates" in set(catalog["candidate_bucket"])
    plot_index = pd.read_csv(result.velocity_plot_index_csv)
    assert set(plot_index["status"]) == {"plotted"}
    office_rows = pd.read_csv(result.office_workbook_rows_csv)
    assert "jadyn_office_workbook_single_phase" in set(office_rows["source_profile"])
    promotion = pd.read_csv(result.office_workbook_promotion_csv)
    assert "duplicate_consistent" in set(promotion["promotion_status"])
    assert Path(result.summary_md).exists()
    assert Path(result.source_provenance_index_csv).exists()


def test_tamu_validation_export_filters_example_and_pseudo_inventory_rows(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    _write_sample_case(root / "2025_01_01_(ExampleFolder)" / "0001")
    _write_pseudo_case_dir(root / "2025_06_19")
    salt = tmp_path / "salt_validation_source.csv"
    _write_validation_source(salt, fluid="salt")

    result = export_tamu_validation_artifacts(
        tmp_path / "validation_export",
        inventory_root=root,
        source_tables=[salt],
    )

    candidates = pd.read_csv(result.inventory_candidates_csv)
    candidate_names = set(candidates["candidate_case_name"])
    assert "2025_03_19__1" in candidate_names
    assert "2025_01_01_(ExampleFolder)__0001" not in candidate_names
    assert "2025_06_19" not in candidate_names

    nearest = pd.read_csv(result.nearest_fit_csv)
    nearest_names = set(nearest["candidate_case_name"])
    assert "2025_01_01_(ExampleFolder)__0001" not in nearest_names
    assert "2025_06_19" not in nearest_names


def test_tamu_validation_export_uses_manual_salt_subfolder_mapping():
    case_inventory = pd.DataFrame(
        [
            {
                "case_dir": "2024_05_04/2",
                "top_level_folder": "2024_05_04",
                "candidate_heater_power_W": 258.0,
                "candidate_air_flow_Lpm": 37.0,
                "candidate_test_section_power_W": 44.8,
                "metadata_path": "2024_05_04/2/meta_data.json",
            },
            {
                "case_dir": "2024_05_04/3",
                "top_level_folder": "2024_05_04",
                "candidate_heater_power_W": 295.0,
                "candidate_air_flow_Lpm": 37.0,
                "candidate_test_section_power_W": 44.8,
                "metadata_path": "2024_05_04/3/meta_data.json",
            },
            {
                "case_dir": "2024_05_04/4",
                "top_level_folder": "2024_05_04",
                "candidate_heater_power_W": 362.0,
                "candidate_air_flow_Lpm": 37.0,
                "candidate_test_section_power_W": 44.8,
                "metadata_path": "2024_05_04/4/meta_data.json",
            },
            {
                "case_dir": "2024_05_04/6",
                "top_level_folder": "2024_05_04",
                "candidate_heater_power_W": 395.0,
                "candidate_air_flow_Lpm": 37.0,
                "candidate_test_section_power_W": 44.8,
                "metadata_path": "2024_05_04/6/meta_data.json",
            },
        ]
    )
    normalized_cases = pd.DataFrame(
        [
            {"case_name": "Salt 1", "heater_power_W": 232.3, "air_flow_Lpm": 37.0, "heat_removed_W": 55.58},
            {"case_name": "Salt 2", "heater_power_W": 265.7, "air_flow_Lpm": 37.0, "heat_removed_W": 56.34},
            {"case_name": "Salt 3", "heater_power_W": 297.5, "air_flow_Lpm": 37.0, "heat_removed_W": 60.55},
            {"case_name": "Salt 4", "heater_power_W": 337.6, "air_flow_Lpm": 37.0, "heat_removed_W": 65.98},
        ]
    )

    nearest = build_nearest_fit_table(case_inventory, normalized_cases)
    assert set(nearest["review_status"]) == {"known_case_subfolder"}
    assert set(nearest["compared_fields"]) == {"manual_case_map"}
    mapping = dict(zip(nearest["target_case_name"], nearest["candidate_case_dir"]))
    assert mapping == {
        "Salt 1": "2024_05_04/2",
        "Salt 2": "2024_05_04/3",
        "Salt 3": "2024_05_04/4",
        "Salt 4": "2024_05_04/6",
    }


def test_tamu_validation_catalog_surfaces_recognized_case_names(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2024_05_04" / "2")

    result = build_tamu_validation_catalog(
        tmp_path / "validation_catalog",
        inventory_root=root,
    )

    steady_velocity = pd.read_csv(result.steady_velocity_csv)
    row = steady_velocity.loc[steady_velocity["candidate_case_name"] == "2024_05_04__2"].iloc[0]
    assert row["recognized_case_name"] == "Salt 1"
    plot_index = pd.read_csv(result.velocity_plot_index_csv)
    plot_row = plot_index.loc[plot_index["candidate_case_name"] == "2024_05_04__2"].iloc[0]
    assert plot_row["recognized_case_name"] == "Salt 1"


def test_tamu_cli_commands(tmp_path: Path):
    root = tmp_path / "Loop Operational Data"
    _write_sample_case(root / "2025_03_19" / "1")
    salt = tmp_path / "salt_validation_source.csv"
    _write_validation_source(salt, fluid="salt")
    inventory_out = tmp_path / "inventory_out"
    export_out = tmp_path / "export_out"
    main(["tamu-inventory", "--root", str(root), "--outdir", str(inventory_out)])
    main(
        [
            "tamu-validation-export",
            "--inventory-root",
            str(root),
            "--source-tables",
            str(salt),
            "--outdir",
            str(export_out),
        ]
    )
    main(
        [
            "tamu-validation-catalog",
            "--inventory-root",
            str(root),
            "--source-tables",
            str(salt),
            "--outdir",
            str(tmp_path / "catalog_out"),
        ]
    )
    assert (inventory_out / "case_inventory.csv").exists()
    assert (inventory_out / "README.md").exists()
    assert (inventory_out / "EXECUTIVE_SUMMARY.md").exists()
    assert (inventory_out / "folder_comparison.csv").exists()
    assert (inventory_out / "subfolder_inventory.csv").exists()
    assert (export_out / "validation_cases.csv").exists()
    assert (tmp_path / "catalog_out" / "validation_catalog.csv").exists()
