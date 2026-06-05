#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
ETHAN_ROOT = (REPO_ROOT.parent / "ethan_runs").resolve()
ETHAN_REPORTS = ETHAN_ROOT / "reports"
OF_ENV_SCRIPT = ETHAN_ROOT / "jadyn_runs" / "salt2" / "2026-06-02_runtime_recovery" / "scripts" / "of13-env.sh"
EXTRA_LD_LIBRARY = "/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data"
OUTPUT_ROOT = REPO_ROOT / "analysis" / "reports" / "2026-06-05_ethan_zero_advance_transport_phase1_2"
TMP_ROOT = Path("/tmp") / "ethan_zero_advance_transport"
D_H = 0.022098
SMALL = 1.0e-12
PILOT_SOURCE_IDS = [
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
]
REP8_SOURCE_IDS = [
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
]
STATION_DEFS = [
    ("mdot_pipeleg_lower_05_straight", "lower_leg", 0.50),
    ("mdot_pipeleg_right_02_middle", "right_leg", 0.50),
    ("mdot_pipeleg_upper_05_cooler", "upper_leg", 0.50),
    ("mdot_pipeleg_left_04_test_section", "left_leg", 0.50),
]
HEATER_PATCHES = {"pipeleg_lower_04_straight", "pipeleg_lower_05_straight", "pipeleg_lower_06_straight"}
TEST_SECTION_PATCHES = {"pipeleg_left_04_test_section"}
COOLING_BRANCH_PATCHES = {"pipeleg_upper_04_reducer", "pipeleg_upper_05_cooler", "pipeleg_upper_06_reducer"}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_dump(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_metadata_map() -> dict[str, dict[str, str]]:
    path = ETHAN_REPORTS / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"
    return {row["source_id"]: row for row in load_csv_rows(path) if row.get("source_id")}


def load_run_summary_map() -> dict[str, dict[str, str]]:
    path = REPO_ROOT / "analysis" / "reports" / "2026-06-05_ethan_representative8_postprocess" / "representative_8_postprocess_summary.csv"
    return {row["source_id"]: row for row in load_csv_rows(path) if row.get("source_id")}


def latest_processor_time(runtime_root: Path) -> str:
    latest_value: float | None = None
    latest_label = ""
    for root in sorted(p for p in runtime_root.iterdir() if p.is_dir() and p.name.startswith("processors")):
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            if not child.name.replace(".", "", 1).isdigit():
                continue
            value = float(child.name)
            if latest_value is None or value > latest_value:
                latest_value = value
                latest_label = child.name
    return latest_label


def ensure_extract_case(source_id: str, runtime_root: Path) -> Path:
    case_dir = TMP_ROOT / source_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    ensure_dir(case_dir)
    for name in ["0", "constant"]:
        (case_dir / name).symlink_to(runtime_root / name)
    if (runtime_root / "dynamicCode").exists():
        (case_dir / "dynamicCode").symlink_to(runtime_root / "dynamicCode")
    for processors_dir in runtime_root.glob("processors*"):
        (case_dir / processors_dir.name).symlink_to(processors_dir)
    shutil.copytree(runtime_root / "system", case_dir / "system", dirs_exist_ok=True)
    if (runtime_root / "case_config.yaml").exists():
        shutil.copy2(runtime_root / "case_config.yaml", case_dir / "case_config.yaml")
    return case_dir


def shell_run(case_dir: Path, command: str) -> subprocess.CompletedProcess[str]:
    env_cmd = (
        f"source {shlex.quote(str(OF_ENV_SCRIPT))} && "
        f"export LD_LIBRARY_PATH={shlex.quote(EXTRA_LD_LIBRARY)}:${{LD_LIBRARY_PATH:-}} && "
        f"{command}"
    )
    return subprocess.run(["bash", "-lc", env_cmd], cwd=str(case_dir), check=True, text=True, capture_output=True)


def parse_wall_heatflux_patch_rows(runtime_root: Path) -> list[dict[str, Any]]:
    candidates = sorted(runtime_root.glob("postProcessing/wallHeatFlux/*/wallHeatFlux.dat"), key=lambda p: float(p.parent.name))
    if not candidates:
        return []
    path = candidates[-1]
    rows_all: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 6:
                continue
            patch = parts[1]
            if patch.startswith("ncc_"):
                continue
            time_value = safe_float(parts[0])
            q_min = safe_float(parts[2])
            q_max = safe_float(parts[3])
            q_total = safe_float(parts[4])
            q_avg = safe_float(parts[5])
            if None in (time_value, q_min, q_max, q_total, q_avg):
                continue
            rows_all.append({
                "time_s": time_value,
                "patch_name": patch,
                "q_min_w_m2": q_min,
                "q_max_w_m2": q_max,
                "q_total_w": q_total,
                "q_avg_w_m2": q_avg,
            })
    if not rows_all:
        return []
    latest_time = max(float(row["time_s"]) for row in rows_all)
    return [row for row in rows_all if float(row["time_s"]) == latest_time]


def leg_group_for_patch(patch: str) -> str:
    if patch.startswith("pipeleg_lower_"):
        return "lower_leg"
    if patch.startswith("pipeleg_right_"):
        return "right_leg"
    if patch.startswith("pipeleg_upper_"):
        return "upper_leg"
    if patch.startswith("pipeleg_left_"):
        return "left_leg"
    if patch.startswith("junction_"):
        return "junctions"
    return "other"


def thermal_role_for_patch(patch: str) -> str:
    if patch in HEATER_PATCHES:
        return "heater"
    if patch in COOLING_BRANCH_PATCHES:
        return "cooling_branch"
    if patch in TEST_SECTION_PATCHES:
        return "test_section"
    if patch.startswith("junction_"):
        return "junction"
    if patch.startswith("pipeleg_"):
        return "transport"
    return "other"


def patch_order_value(patch: str) -> int:
    match = re.search(r"_(\d+)_", patch)
    return int(match.group(1)) if match else 999


def enrich_patch_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(leg_group_for_patch(row["patch_name"]), []).append(row)
    out: list[dict[str, Any]] = []
    for leg_group, items in grouped.items():
        items.sort(key=lambda row: (patch_order_value(row["patch_name"]), row["patch_name"]))
        count = len(items)
        for idx, row in enumerate(items):
            payload = dict(row)
            payload["leg_group"] = leg_group
            payload["thermal_role"] = thermal_role_for_patch(row["patch_name"])
            payload["patch_rank_in_leg"] = idx + 1
            payload["patch_count_in_leg"] = count
            payload["section_progress_0to1"] = 0.0 if count == 1 else idx / (count - 1)
            out.append(payload)
    return out


def write_sampling_dict(path: Path, patch_names: list[str]) -> None:
    lines = [
        "FoamFile",
        "{",
        '    format      ascii;',
        '    class       dictionary;',
        '    location    "system";',
        '    object      functions;',
        "}",
        "",
    ]
    for patch_name in patch_names:
        obj = f"patch_{patch_name}"
        lines.extend([
            obj,
            "{",
            '    type            surfaceFieldValue;',
            '    libs            ("libfieldFunctionObjects.so");',
            '    writeControl    timeStep;',
            '    writeInterval   1;',
            '    surfaceFormat   none;',
            '    writeFields     false;',
            '    writeToFile     true;',
            '    log             false;',
            f'    patch           {patch_name};',
            '    operation       areaAverage;',
            '    fields          (T wallHeatFlux);',
            "}",
            "",
        ])
    lines.extend([
        "bulkStations",
        "{",
        '    type    coded;',
        '    libs    ("libutilityFunctionObjects.so");',
        '    name    bulkStations;',
        '    writeControl timeStep;',
        '    writeInterval 1;',
        '    codeInclude',
        '    #{',
        '        #include "fvc.H"',
        '    #};',
        '    codeExecute',
        '    #{',
        '        const fvMesh& mesh = this->mesh();',
        '        if (!mesh.foundObject<surfaceScalarField>("phi") || !mesh.foundObject<volScalarField>("T") || !mesh.foundObject<volScalarField>("p_rgh"))',
        '        {',
        '            return true;',
        '        }',
        '        const surfaceScalarField& phi = mesh.lookupObject<surfaceScalarField>("phi");',
        '        const volScalarField& T = mesh.lookupObject<volScalarField>("T");',
        '        const volScalarField& p_rgh = mesh.lookupObject<volScalarField>("p_rgh");',
        '        tmp<surfaceScalarField> tTf = fvc::interpolate(T);',
        '        const surfaceScalarField& Tf = tTf();',
        '        tmp<surfaceScalarField> tPf = fvc::interpolate(p_rgh);',
        '        const surfaceScalarField& Pf = tPf();',
        '        const scalarField& magSf = mesh.magSf();',
        '        const auto& fzm = mesh.faceZones();',
        '        const word zones[] = {"mdot_pipeleg_lower_05_straight", "mdot_pipeleg_right_02_middle", "mdot_pipeleg_upper_05_cooler", "mdot_pipeleg_left_04_test_section"};',
        '        const word legs[] = {"lower_leg", "right_leg", "upper_leg", "left_leg"};',
        '        const scalar progress[] = {0.5, 0.5, 0.5, 0.5};',
        '        const string fpath = mesh.time().globalPath() + "/postProcessing/zeroAdvanceBulkStations.dat";',
        '        FILE* fp = fopen(fpath.c_str(), "w");',
        '        if (!fp) return true;',
        '        fprintf(fp, "time_s\\tstation_name\\tleg_group\\tsection_progress_0to1\\tmdot_kg_s\\tabs_mdot_kg_s\\tareaAverage_p_rgh_pa\\tbulk_T_k\\n");',
        '        for (label zi = 0; zi < 4; ++zi)',
        '        {',
        '            label zonei = -1;',
        '            forAll(fzm, fzi)',
        '            {',
        '                if (fzm[fzi].name() == zones[zi])',
        '                {',
        '                    zonei = fzi;',
        '                    break;',
        '                }',
        '            }',
        '            if (zonei < 0) continue;',
        '            const faceZone& zone = fzm[zonei];',
        '            scalar sumPhi = 0.0, sumMagPhi = 0.0, sumPhiT = 0.0, sumArea = 0.0, sumAreaP = 0.0;',
        '            forAll(zone, faceIdx)',
        '            {',
        '                const label facei = zone[faceIdx];',
        '                const scalar phiv = phi[facei];',
        '                const scalar tf = Tf[facei];',
        '                const scalar pf = Pf[facei];',
        '                const scalar area = magSf[facei];',
        '                sumPhi += phiv;',
        '                sumMagPhi += mag(phiv);',
        '                sumPhiT += phiv*tf;',
        '                sumArea += area;',
        '                sumAreaP += area*pf;',
        '            }',
        '            reduce(sumPhi, sumOp<scalar>());',
        '            reduce(sumMagPhi, sumOp<scalar>());',
        '            reduce(sumPhiT, sumOp<scalar>());',
        '            reduce(sumArea, sumOp<scalar>());',
        '            reduce(sumAreaP, sumOp<scalar>());',
        '            const scalar denomPhi = mag(sumPhi) > SMALL ? sumPhi : (sumMagPhi > SMALL ? sumMagPhi : SMALL);',
        '            const scalar bulkT = sumPhiT / denomPhi;',
        '            const scalar avgP = sumArea > SMALL ? sumAreaP / sumArea : 0.0;',
        '            fprintf(fp, "%.12g\\t%s\\t%s\\t%.6g\\t%.12g\\t%.12g\\t%.12g\\t%.12g\\n", double(mesh.time().value()), zones[zi].c_str(), legs[zi].c_str(), double(progress[zi]), double(sumPhi), double(sumMagPhi), double(avgP), double(bulkT));',
        '        }',
        '        fclose(fp);',
        '    #};',
        "}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_patch_surface_output(path: Path) -> dict[str, Any]:
    payload = {"area_m2": "", "areaAverage_T_w_k": "", "areaAverage_wallHeatFlux_w_m2": "", "sample_time_s": ""}
    if not path.exists():
        return payload
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# Area"):
                area = stripped.split(":", 1)[-1].strip()
                payload["area_m2"] = safe_float(area, area)
                continue
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 3:
                payload["sample_time_s"] = safe_float(parts[0], parts[0])
                payload["areaAverage_T_w_k"] = safe_float(parts[1], parts[1])
                payload["areaAverage_wallHeatFlux_w_m2"] = safe_float(parts[2], parts[2])
    return payload


def parse_bulk_station_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle, delimiter='	')
        for row in reader:
            rows.append({
                "sample_time_s": safe_float(row.get("time_s"), row.get("time_s", "")),
                "station_name": row.get("station_name", ""),
                "leg_group": row.get("leg_group", ""),
                "section_progress_0to1": safe_float(row.get("section_progress_0to1"), row.get("section_progress_0to1", "")),
                "mdot_kg_s": safe_float(row.get("mdot_kg_s"), row.get("mdot_kg_s", "")),
                "abs_mdot_kg_s": safe_float(row.get("abs_mdot_kg_s"), row.get("abs_mdot_kg_s", "")),
                "areaAverage_p_rgh_pa": safe_float(row.get("areaAverage_p_rgh_pa"), row.get("areaAverage_p_rgh_pa", "")),
                "bulk_T_k": safe_float(row.get("bulk_T_k"), row.get("bulk_T_k", "")),
            })
    return rows


def parse_simple_numeric_list(path: Path, marker: str | None = None) -> list[float]:
    values: list[float] = []
    count: int | None = None
    in_list = marker is None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if marker is not None and not in_list:
                if marker in stripped:
                    in_list = True
                continue
            if count is None:
                if stripped.isdigit():
                    count = int(stripped)
                continue
            if stripped == '(':
                continue
            if stripped == ')':
                break
            values.append(float(stripped))
            if len(values) >= count:
                break
    return values


def parse_label_list(path: Path) -> list[int]:
    return [int(value) for value in parse_simple_numeric_list(path)]


def parse_internal_scalar_field(path: Path) -> list[float]:
    return parse_simple_numeric_list(path, 'internalField')


def parse_face_zone_labels(path: Path, target_zone_names: list[str]) -> dict[str, list[int]]:
    targets = set(target_zone_names)
    found: dict[str, list[int]] = {}
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line not in targets:
            i += 1
            continue
        zone_name = line
        i += 1
        while i < len(lines) and 'faceLabels' not in lines[i]:
            i += 1
        if i >= len(lines):
            break
        i += 1
        while i < len(lines) and not lines[i].strip().isdigit():
            i += 1
        if i >= len(lines):
            break
        count = int(lines[i].strip())
        i += 1
        while i < len(lines) and lines[i].strip() != '(':
            i += 1
        i += 1
        labels: list[int] = []
        while i < len(lines):
            stripped = lines[i].strip()
            i += 1
            if stripped == ')':
                break
            if stripped:
                labels.append(int(stripped))
                if len(labels) >= count:
                    break
        found[zone_name] = labels
    return found


def compute_bulk_stations_from_reconstructed_case(case_dir: Path, latest_time: str) -> list[dict[str, Any]]:
    time_dir = case_dir / latest_time
    owner = parse_label_list(case_dir / 'constant' / 'polyMesh' / 'owner')
    neighbour = parse_label_list(case_dir / 'constant' / 'polyMesh' / 'neighbour')
    t_vals = parse_internal_scalar_field(time_dir / 'T')
    p_vals = parse_internal_scalar_field(time_dir / 'p_rgh')
    phi_vals = parse_internal_scalar_field(time_dir / 'phi')
    zones = parse_face_zone_labels(case_dir / 'constant' / 'polyMesh' / 'faceZones', [name for name, _, _ in STATION_DEFS])
    rows: list[dict[str, Any]] = []
    for station_name, leg_group, progress in STATION_DEFS:
        faces = zones.get(station_name, [])
        sum_phi = 0.0
        sum_mag_phi = 0.0
        sum_phi_t = 0.0
        sum_p = 0.0
        face_count = 0
        for facei in faces:
            if facei >= len(neighbour) or facei >= len(phi_vals) or facei >= len(owner):
                continue
            own = owner[facei]
            nei = neighbour[facei]
            if own >= len(t_vals) or nei >= len(t_vals) or own >= len(p_vals) or nei >= len(p_vals):
                continue
            t_face = 0.5 * (t_vals[own] + t_vals[nei])
            p_face = 0.5 * (p_vals[own] + p_vals[nei])
            phi_face = phi_vals[facei]
            sum_phi += phi_face
            sum_mag_phi += abs(phi_face)
            sum_phi_t += phi_face * t_face
            sum_p += p_face
            face_count += 1
        denom = sum_phi if abs(sum_phi) > SMALL else (sum_mag_phi if sum_mag_phi > SMALL else None)
        bulk_t = sum_phi_t / denom if denom is not None else ''
        rows.append({
            'sample_time_s': safe_float(latest_time, latest_time),
            'station_name': station_name,
            'leg_group': leg_group,
            'section_progress_0to1': progress,
            'mdot_kg_s': sum_phi if face_count else '',
            'abs_mdot_kg_s': abs(sum_phi) if face_count else '',
            'areaAverage_p_rgh_pa': (sum_p / face_count) if face_count else '',
            'bulk_T_k': bulk_t,
        })
    return rows


def eval_poly(coeffs: list[float], temp: float) -> float:
    value = 0.0
    for coeff in reversed(coeffs):
        value = value * temp + coeff
    return value


def kappa_at_temp(meta_row: dict[str, str], temp: float) -> float:
    summary = meta_row.get("kappa_coeff_summary", "")
    nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", summary)]
    if not nums:
        return math.nan
    return eval_poly(nums[:8], temp)


def ambient_temp_for_role(meta_row: dict[str, str], thermal_role: str) -> float | None:
    mapping = {
        "heater": safe_float(meta_row.get("heater_Ta_K")),
        "cooling_branch": safe_float(meta_row.get("cooler_Ta_K")),
        "test_section": safe_float(meta_row.get("test_section_Ta_K")),
        "transport": safe_float(meta_row.get("insulated_Ta_K")),
        "junction": safe_float(meta_row.get("insulated_Ta_K")),
        "other": safe_float(meta_row.get("insulated_Ta_K")),
    }
    return mapping.get(thermal_role)


def section_name_for_row(row: dict[str, Any]) -> str:
    role = row["thermal_role"]
    leg = row["leg_group"]
    if role == "heater":
        return "heater_branch"
    if role == "cooling_branch":
        return "cooling_branch"
    if role == "test_section":
        return "test_section_branch"
    if role == "junction":
        return "junctions"
    if role == "transport" and leg == "lower_leg":
        return "lower_transport"
    if role == "transport" and leg == "upper_leg":
        return "upper_transport"
    if role == "transport" and leg == "left_leg":
        return "left_transport"
    if role == "transport" and leg == "right_leg":
        return "right_transport"
    return f"{leg}_{role}"


def join_profiles(source_id: str, patch_rows: list[dict[str, Any]], station_rows: list[dict[str, Any]], meta_row: dict[str, str]) -> list[dict[str, Any]]:
    station_by_leg = {row["leg_group"]: row for row in station_rows}
    joined: list[dict[str, Any]] = []
    for row in patch_rows:
        station = station_by_leg.get(row["leg_group"], {})
        tw = safe_float(row.get("areaAverage_T_w_k"))
        tb = safe_float(station.get("bulk_T_k"))
        qavg = safe_float(row.get("areaAverage_wallHeatFlux_w_m2"))
        delta = None if tw is None or tb is None else tw - tb
        h_internal = None
        nu_internal = None
        if qavg is not None and tw is not None and tb is not None and abs(tw - tb) > SMALL:
            h_internal = abs(qavg) / abs(tw - tb)
            kappa = kappa_at_temp(meta_row, tb)
            if kappa and not math.isnan(kappa) and abs(kappa) > SMALL:
                nu_internal = h_internal * D_H / kappa
        joined.append({
            "source_id": source_id,
            "patch_name": row["patch_name"],
            "leg_group": row["leg_group"],
            "thermal_role": row["thermal_role"],
            "section_name": section_name_for_row(row),
            "section_progress_0to1": row["section_progress_0to1"],
            "station_name": station.get("station_name", ""),
            "T_w_k": row.get("areaAverage_T_w_k", ""),
            "T_bulk_k": station.get("bulk_T_k", ""),
            "deltaT_fw_k": delta if delta is not None else "",
            "wallHeatFlux_w_m2": row.get("areaAverage_wallHeatFlux_w_m2", ""),
            "q_total_w": row.get("q_total_w", ""),
            "patch_area_m2": row.get("area_m2", ""),
            "h_internal_w_m2K": h_internal if h_internal is not None else "",
            "Nu_internal": nu_internal if nu_internal is not None else "",
            "Nu_ref_field": row.get("areaAverage_Nu_ref", ""),
            "mdot_kg_s": station.get("mdot_kg_s", ""),
            "abs_mdot_kg_s": station.get("abs_mdot_kg_s", ""),
            "areaAverage_p_rgh_pa": station.get("areaAverage_p_rgh_pa", ""),
        })
    return joined


def build_section_resistance_rows(source_id: str, joined_rows: list[dict[str, Any]], meta_row: dict[str, str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in joined_rows:
        grouped.setdefault(str(row["section_name"]), []).append(row)
    out: list[dict[str, Any]] = []
    for section_name, rows in sorted(grouped.items()):
        q_total = sum(float(row["q_total_w"]) for row in rows if row.get("q_total_w") not in ("", None))
        area_total = sum(float(row["patch_area_m2"]) for row in rows if row.get("patch_area_m2") not in ("", None))
        tw_num = sum(float(row["patch_area_m2"]) * float(row["T_w_k"]) for row in rows if row.get("patch_area_m2") not in ("", None) and row.get("T_w_k") not in ("", None))
        tw = tw_num / area_total if area_total > SMALL else math.nan
        bulk_vals = [float(row["T_bulk_k"]) for row in rows if row.get("T_bulk_k") not in ("", None)]
        tb = sum(bulk_vals) / len(bulk_vals) if bulk_vals else math.nan
        role = str(rows[0]["thermal_role"])
        ta = ambient_temp_for_role(meta_row, role)
        r_fw = abs(tb - tw) / abs(q_total) if not math.isnan(tb) and not math.isnan(tw) and abs(q_total) > SMALL else ""
        r_wa = abs(tw - ta) / abs(q_total) if ta is not None and not math.isnan(tw) and abs(q_total) > SMALL else ""
        r_fa = abs(tb - ta) / abs(q_total) if ta is not None and not math.isnan(tb) and abs(q_total) > SMALL else ""
        p_vals = [float(row["areaAverage_p_rgh_pa"]) for row in rows if row.get("areaAverage_p_rgh_pa") not in ("", None)]
        out.append({
            "source_id": source_id,
            "section_name": section_name,
            "thermal_role": role,
            "Q_section_w": q_total,
            "T_bulk_section_k": tb if not math.isnan(tb) else "",
            "T_wall_section_k": tw if not math.isnan(tw) else "",
            "T_amb_section_k": ta if ta is not None else "",
            "R_fluid_to_wall_K_per_W": r_fw,
            "R_wall_to_ambient_K_per_W": r_wa,
            "R_fluid_to_ambient_K_per_W": r_fa,
            "mean_p_rgh_pa": sum(p_vals) / len(p_vals) if p_vals else "",
            "patch_count": len(rows),
            "area_total_m2": area_total,
        })
    return out


def build_thermal_circuit_rows(source_id: str, section_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = [
        "heater_branch",
        "lower_transport",
        "test_section_branch",
        "left_transport",
        "cooling_branch",
        "upper_transport",
        "right_transport",
        "junctions",
    ]
    lookup = {row["section_name"]: row for row in section_rows}
    out: list[dict[str, Any]] = []
    for idx, section_name in enumerate(order, start=1):
        row = lookup.get(section_name)
        if not row:
            continue
        out.append({
            "source_id": source_id,
            "element_order": idx,
            "element_name": section_name,
            "Q_section_w": row.get("Q_section_w", ""),
            "T_bulk_section_k": row.get("T_bulk_section_k", ""),
            "T_wall_section_k": row.get("T_wall_section_k", ""),
            "T_amb_section_k": row.get("T_amb_section_k", ""),
            "R_fluid_to_wall_K_per_W": row.get("R_fluid_to_wall_K_per_W", ""),
            "R_wall_to_ambient_K_per_W": row.get("R_wall_to_ambient_K_per_W", ""),
            "R_fluid_to_ambient_K_per_W": row.get("R_fluid_to_ambient_K_per_W", ""),
        })
    return out


def process_case(source_id: str, meta_row: dict[str, str], summary_row: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    runtime_root = Path(meta_row.get("active_runtime_root") or meta_row.get("source_root") or "").resolve()
    case_dir = ensure_extract_case(source_id, runtime_root)
    latest_time = latest_processor_time(runtime_root)
    if not latest_time:
        raise RuntimeError(f"No latest processor time found for {source_id}")
    wall_rows = enrich_patch_rows(parse_wall_heatflux_patch_rows(runtime_root))
    patch_names = sorted({row["patch_name"] for row in wall_rows})
    functions_path = case_dir / "system" / "zero_advance_transport_functions"
    write_sampling_dict(functions_path, patch_names)
    commands = [
        f"reconstructPar -case {shlex.quote(str(case_dir))} -time {latest_time} -fields '(T wallHeatFlux p_rgh phi)'",
        f"foamPostProcess -case {shlex.quote(str(case_dir))} -dict {shlex.quote(str(functions_path))} -time {latest_time}",
    ]
    logs: list[dict[str, Any]] = []
    for command in commands:
        result = shell_run(case_dir, command)
        logs.append({"command": command, "stdout_tail": result.stdout[-2000:], "stderr_tail": result.stderr[-2000:]})
    patch_out_rows: list[dict[str, Any]] = []
    for row in wall_rows:
        path = case_dir / "postProcessing" / f"patch_{row['patch_name']}" / latest_time / "surfaceFieldValue.dat"
        parsed = parse_patch_surface_output(path)
        patch_out_rows.append({
            "source_id": source_id,
            "study_case": summary_row.get("study_case", ""),
            **row,
            "latest_processor_time": latest_time,
            **parsed,
            "areaAverage_Nu_ref": "",
        })
    raw_bulk_rows = parse_bulk_station_file(case_dir / "postProcessing" / "zeroAdvanceBulkStations.dat")
    if not raw_bulk_rows:
        raw_bulk_rows = compute_bulk_stations_from_reconstructed_case(case_dir, latest_time)
    bulk_rows = [
        {"source_id": source_id, "study_case": summary_row.get("study_case", ""), **row, "latest_processor_time": latest_time}
        for row in raw_bulk_rows
    ]
    joined_rows = join_profiles(source_id, patch_out_rows, bulk_rows, meta_row)
    section_rows = build_section_resistance_rows(source_id, joined_rows, meta_row)
    circuit_rows = build_thermal_circuit_rows(source_id, section_rows)
    readiness = {
        "source_id": source_id,
        "study_case": summary_row.get("study_case", ""),
        "run_status": summary_row.get("run_status", ""),
        "convergence_reached": summary_row.get("convergence_reached", ""),
        "runtime_root": str(runtime_root),
        "tmp_case_dir": str(case_dir),
        "latest_processor_time": latest_time,
        "wall_patch_rows": len(patch_out_rows),
        "bulk_station_rows": len(bulk_rows),
        "joined_rows": len(joined_rows),
        "section_rows": len(section_rows),
        "circuit_rows": len(circuit_rows),
        "nonempty_Tw_rows": sum(1 for row in patch_out_rows if row.get("areaAverage_T_w_k") not in ("", None)),
        "nonempty_qw_rows": sum(1 for row in patch_out_rows if row.get("areaAverage_wallHeatFlux_w_m2") not in ("", None)),
        "nonempty_Tbulk_rows": sum(1 for row in bulk_rows if row.get("bulk_T_k") not in ("", None)),
        "nonempty_h_rows": sum(1 for row in joined_rows if row.get("h_internal_w_m2K") not in ("", None)),
        "success": "yes" if patch_out_rows and bulk_rows and any(row.get("h_internal_w_m2K") not in ("", None) for row in joined_rows) else "partial",
        "note": "Salt 2 should always use the latest written processor time rather than the older probe-history horizon." if source_id == "val_salt_test_2_coarse_mesh_laminar" else "",
        "command_log_json": json.dumps(logs),
    }
    return patch_out_rows, bulk_rows, joined_rows, section_rows, circuit_rows, readiness


def build_summary_md(readiness_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Ethan Zero-Advance Transport Phase 1/2",
        "",
        "This package tests whether the missing transport layer can be extracted from the latest written OpenFOAM state without advancing the solver.",
        "",
        "## Case status",
        "",
    ]
    for row in readiness_rows:
        lines.append(
            f"- `{row['study_case']}` (`{row['source_id']}`): latest processor time `{row['latest_processor_time']}`, wall rows `{row['wall_patch_rows']}`, bulk rows `{row['bulk_station_rows']}`, joined rows `{row['joined_rows']}`, success `{row['success']}`."
        )
    lines.extend([
        "",
        "## Notes",
        "",
        "- Kirst should be treated as not fully converged for decision purposes even where an older coded-convergence flag exists.",
        "- Salt 2 uses the actual latest written processor time, not the older probe-history horizon.",
        "- The current extractor derives internal HTC and internal Nusselt from sampled `T_w`, sampled mass-flux-weighted `T_bulk`, and sampled `wallHeatFlux`.",
        "- The pre-existing OpenFOAM `Nu` field in the Ethan cases is reference-temperature-based and is not used as the final internal-Nusselt definition here.",
        "",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a zero-advance Ethan transport package from latest written states.")
    parser.add_argument("--representative8", action="store_true", help="Process the current representative 8 instead of the pilot 3.")
    parser.add_argument("--source-id", action="append", dest="source_ids", help="Override source IDs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_ids = args.source_ids or (REP8_SOURCE_IDS if args.representative8 else PILOT_SOURCE_IDS)
    ensure_dir(OUTPUT_ROOT)
    ensure_dir(TMP_ROOT)
    meta_map = load_metadata_map()
    summary_map = load_run_summary_map()
    all_patch_rows: list[dict[str, Any]] = []
    all_bulk_rows: list[dict[str, Any]] = []
    all_joined_rows: list[dict[str, Any]] = []
    all_section_rows: list[dict[str, Any]] = []
    all_circuit_rows: list[dict[str, Any]] = []
    readiness_rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        if source_id not in meta_map:
            raise KeyError(f"Missing metadata row for {source_id}")
        summary_row = summary_map.get(source_id, {"study_case": source_id, "run_status": "", "convergence_reached": ""})
        patch_rows, bulk_rows, joined_rows, section_rows, circuit_rows, readiness = process_case(source_id, meta_map[source_id], summary_row)
        all_patch_rows.extend(patch_rows)
        all_bulk_rows.extend(bulk_rows)
        all_joined_rows.extend(joined_rows)
        all_section_rows.extend(section_rows)
        all_circuit_rows.extend(circuit_rows)
        readiness_rows.append(readiness)
    csv_dump(OUTPUT_ROOT / "axial_wall_patch_table.csv", all_patch_rows)
    csv_dump(OUTPUT_ROOT / "axial_bulk_station_table.csv", all_bulk_rows)
    csv_dump(OUTPUT_ROOT / "axial_joined_profile_table.csv", all_joined_rows)
    csv_dump(OUTPUT_ROOT / "section_resistance_table.csv", all_section_rows)
    csv_dump(OUTPUT_ROOT / "thermal_circuit_table.csv", all_circuit_rows)
    csv_dump(OUTPUT_ROOT / "representative8_postprocess_readiness.csv", readiness_rows)
    (OUTPUT_ROOT / "README.md").write_text(build_summary_md(readiness_rows), encoding="utf-8")
    (OUTPUT_ROOT / "MANIFEST.json").write_text(json.dumps({
        "source_ids": source_ids,
        "output_root": str(OUTPUT_ROOT),
        "tmp_root": str(TMP_ROOT),
        "files": [
            "axial_wall_patch_table.csv",
            "axial_bulk_station_table.csv",
            "axial_joined_profile_table.csv",
            "section_resistance_table.csv",
            "thermal_circuit_table.csv",
            "representative8_postprocess_readiness.csv",
            "README.md",
        ],
    }, indent=2), encoding="utf-8")
    print(json.dumps({"output_root": str(OUTPUT_ROOT), "case_count": len(source_ids)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
