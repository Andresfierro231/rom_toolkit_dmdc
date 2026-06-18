"""Modular campaign runner for reproducible ROM studies.

Campaigns let users keep one central config file and run only the steps needed
for a particular study.  The runner writes a plan, a step index, and next-step
prompts so users can see where outputs are going and what to do next.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from copy import deepcopy
import json
import subprocess, sys, uuid
import pandas as pd
from .config import load_config
from .resources import get_resource_summary

DEFAULT_STEP_ORDER=["import","inspect","adaptive_fit","pod_dmdc","compare","validate","live_replay_monitor","live_replay_adapt","archive_run","archive_summarize","archive_quicklook","archive_schema","dashboard","operator_report"]
STEP_COMMANDS={"import":["import-data"],"inspect":["inspect-data"],"adaptive_fit":["adaptive-fit"],"pod_dmdc":["pod-dmdc"],"compare":["compare"],"validate":["validate"],"live_replay_monitor":["live-replay-monitor"],"live_replay_adapt":["live-replay-adapt"],"archive_run":["archive-run"],"archive_summarize":["archive-summarize"],"archive_quicklook":["archive-quicklook"],"archive_schema":["validate-archive-schema"],"dashboard":["live-dashboard","--write-summary-only"],"operator_report":["live-operator-report"]}
NEXT_STEP_HINTS={"import":"Run inspect-data to verify columns, missing values, and time-step behavior.","inspect":"Use adaptive-fit/compare for nonuniform time, or resample only when you intentionally need fixed dt.","compare":"Review model_comparison.csv, then register the best model with model-register.","validate":"Check generalization gap before trusting live deployment.","live_replay_adapt":"Open the dashboard and operator report; inspect bias update events.","archive_run":"Run archive-summarize and archive-quicklook before browsing long runs.","archive_schema":"Open context/archive_context_index.csv for a human-readable archive map."}
@dataclass
class CampaignStepRecord:
    step:str; enabled:bool; status:str; command:str; outdir_hint:str|None; return_code:int|None=None; started_utc:str|None=None; finished_utc:str|None=None; notes:str|None=None
@dataclass
class CampaignResult:
    campaign_dir:str; campaign_group_dir:str; run_id:str; steps_requested:list[str]; steps_run:list[str]; n_succeeded:int; n_failed:int; dry_run:bool; step_index_csv:str; plan_md:str; next_steps_md:str; derived_config_path:str; run_index_csv:str

def _get(config:dict[str,Any], *path:str, default:Any=None)->Any:
    obj:Any=config
    for key in path:
        if not isinstance(obj,dict) or key not in obj: return default
        obj=obj[key]
    return obj


def infer_campaign_group_dir(config:dict[str,Any], config_path:str|Path)->Path:
    campaign=config.get("campaign",{}) or {}; output=config.get("output",{}) or {}
    root = Path(campaign.get("root", output.get("campaign_root", output.get("root","outputs/campaigns"))))
    return root / str(campaign.get("name") or Path(config_path).stem)


def make_campaign_run_id()->str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_{uuid.uuid4().hex[:8]}"


def _path_name(path_value: str | None, default_name: str) -> str:
    if not path_value:
        return default_name
    name = Path(path_value).name
    return name or default_name


def _set_path(config:dict[str,Any], section:str, key:str, value:Path)->None:
    bucket = config.setdefault(section, {})
    if not isinstance(bucket, dict):
        bucket = {}
        config[section] = bucket
    bucket[key] = str(value)


def _rebase_campaign_config(
    config: dict[str, Any],
    *,
    config_path: str | Path,
    group_dir: Path,
    run_dir: Path,
    steps: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    derived = deepcopy(config)
    workflow_root = run_dir / "workflow_outputs"
    output = derived.setdefault("output", {})
    if not isinstance(output, dict):
        output = {}
        derived["output"] = output
    campaign = derived.setdefault("campaign", {})
    if not isinstance(campaign, dict):
        campaign = {}
        derived["campaign"] = campaign

    original_import = str(_get(config, "importer", "out", default=output.get("imported_data", output.get("data", ""))) or "")
    original_data_path = str(_get(config, "data", "path", default="") or "")
    original_live_path = str(_get(config, "stream", "path", default=_get(config, "live", "path", default="")) or "")
    imported_name = _path_name(original_import or original_data_path, "imported_data.parquet")
    live_name = _path_name(_get(config, "live", "outdir", default=output.get("live_adaptation_outdir", output.get("live_outdir", ""))), "live_adaptation")

    imported_path = workflow_root / "import" / imported_name
    inspection_outdir = workflow_root / "inspection"
    adaptive_outdir = workflow_root / "adaptive_fit"
    pod_dmdc_outdir = workflow_root / "pod_dmdc"
    compare_outdir = workflow_root / "compare"
    validation_outdir = workflow_root / "validation"
    sweep_outdir = workflow_root / "sweep"
    pod_outdir = workflow_root / "pod"
    pod_ml_outdir = workflow_root / "pod_ml"
    pod_sensors_outdir = workflow_root / "pod_sensors"
    sensor_outdir = workflow_root / "sensor_selection"
    live_outdir = workflow_root / live_name
    operator_report_outdir = workflow_root / "operator_report"
    archive_root = workflow_root / "live_archive"

    output["root"] = str(workflow_root)
    output["campaign_root"] = str(group_dir)
    output["imported_data"] = str(imported_path)
    output["canonical_data"] = str(imported_path)
    output["data"] = str(imported_path)
    output["inspection_outdir"] = str(inspection_outdir)
    output["adaptive_outdir"] = str(adaptive_outdir)
    output["pod_outdir"] = str(pod_outdir)
    output["pod_dmdc_outdir"] = str(pod_dmdc_outdir)
    output["pod_ml_outdir"] = str(pod_ml_outdir)
    output["sensor_outdir"] = str(sensor_outdir)
    output["pod_sensors_outdir"] = str(pod_sensors_outdir)
    output["compare_outdir"] = str(compare_outdir)
    output["comparison_outdir"] = str(compare_outdir)
    output["validation_outdir"] = str(validation_outdir)
    output["sweep_outdir"] = str(sweep_outdir)
    output["live_outdir"] = str(live_outdir)
    output["live_monitor_outdir"] = str(live_outdir)
    output["live_monitoring_outdir"] = str(live_outdir)
    output["live_prediction_outdir"] = str(live_outdir)
    output["live_estimation_outdir"] = str(live_outdir)
    output["live_adaptation_outdir"] = str(live_outdir)
    output["operator_report_outdir"] = str(operator_report_outdir)

    campaign["root"] = str(group_dir.parent)
    campaign["group_dir"] = str(group_dir)
    campaign["run_dir"] = str(run_dir)
    campaign["run_id"] = run_dir.name
    campaign["dry_run"] = bool(dry_run)
    campaign["steps_resolved"] = list(steps)
    campaign["source_config"] = str(Path(config_path))

    _set_path(derived, "importer", "out", imported_path)
    _set_path(derived, "inspection", "outdir", inspection_outdir)
    _set_path(derived, "adaptive", "outdir", adaptive_outdir)
    _set_path(derived, "pod", "outdir", pod_outdir)
    _set_path(derived, "pod_dmdc", "outdir", pod_dmdc_outdir)
    _set_path(derived, "compare", "outdir", compare_outdir)
    _set_path(derived, "validation", "outdir", validation_outdir)
    _set_path(derived, "sweep", "outdir", sweep_outdir)
    _set_path(derived, "ml", "outdir", pod_ml_outdir)
    _set_path(derived, "sensor_selection", "outdir", sensor_outdir)
    _set_path(derived, "dashboard", "run_dir", live_outdir)
    _set_path(derived, "dashboard", "archive_root", archive_root)
    _set_path(derived, "summaries", "outdir", archive_root / "summaries")
    _set_path(derived, "quicklooks", "outdir", archive_root / "quicklooks")
    _set_path(derived, "quicklooks", "summaries_dir", archive_root / "summaries")
    _set_path(derived, "live", "outdir", live_outdir)
    _set_path(derived, "live_archive", "run_dir", live_outdir)
    _set_path(derived, "live_archive", "root", archive_root)
    _set_path(derived, "archive", "run_dir", live_outdir)
    _set_path(derived, "archive", "root", archive_root)

    if "data" in derived and isinstance(derived["data"], dict):
        should_rebase_data = "import" in steps or original_data_path in {original_import, output.get("imported_data")}
        if should_rebase_data and original_data_path:
            derived["data"]["path"] = str(imported_path)
    if original_live_path:
        if _get(derived, "stream", "path", default=None) is not None:
            derived["stream"]["path"] = str(imported_path) if original_live_path == original_data_path and _get(derived, "data", "path", default=None) == str(imported_path) else original_live_path
        if _get(derived, "live", "path", default=None) is not None:
            derived["live"]["path"] = str(imported_path) if original_live_path == original_data_path and _get(derived, "data", "path", default=None) == str(imported_path) else original_live_path
    return derived


def write_derived_config(run_dir:Path, config:dict[str,Any])->Path:
    derived_dir = run_dir / "config"
    derived_dir.mkdir(parents=True, exist_ok=True)
    path = derived_dir / "campaign_config.derived.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def update_run_index(group_dir:Path, *, run_dir:Path, config_path:str|Path, steps:list[str], dry_run:bool)->Path:
    group_dir.mkdir(parents=True, exist_ok=True)
    idx_path = group_dir / "campaign_runs.csv"
    row = {
        "run_id": run_dir.name,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "source_config": str(config_path),
        "steps_requested": " ".join(steps),
        "dry_run": bool(dry_run),
    }
    if idx_path.exists():
        df = pd.read_csv(idx_path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(idx_path, index=False)
    (group_dir / "latest_run.txt").write_text(str(run_dir), encoding="utf-8")
    return idx_path

def infer_campaign_dir(config:dict[str,Any], config_path:str|Path)->Path:
    return infer_campaign_group_dir(config, config_path)

def enabled_steps(config:dict[str,Any], explicit_steps:list[str]|None=None)->list[str]:
    if explicit_steps: return [s for item in explicit_steps for s in str(item).replace(","," ").split() if s]
    campaign=config.get("campaign",{}) or {}
    if isinstance(campaign.get("steps"), list): return [str(s) for s in campaign["steps"]]
    flags=campaign.get("enabled",{}) if isinstance(campaign.get("enabled",{}),dict) else {}
    return [s for s in DEFAULT_STEP_ORDER if bool(flags.get(s,False))] if flags else ["inspect","compare"]

def outdir_hint_for_step(config:dict[str,Any], step:str, campaign_dir:Path)->str|None:
    output=config.get("output",{}) or {}; live=config.get("live",{}) or {}; archive=config.get("live_archive",config.get("archive",{})) or {}
    mapping={
        "import":_get(config,"importer","out",default=output.get("imported_data", output.get("canonical_data"))),
        "inspect":_get(config,"inspection","outdir",default=output.get("inspection_outdir")),
        "adaptive_fit":_get(config,"adaptive","outdir",default=output.get("adaptive_outdir")),
        "pod_dmdc":output.get("pod_dmdc_outdir"),
        "compare":_get(config,"compare","outdir",default=output.get("compare_outdir", output.get("comparison_outdir"))),
        "validate":_get(config,"validation","outdir",default=output.get("validation_outdir")),
        "live_replay_monitor":live.get("outdir",output.get("live_monitor_outdir", output.get("live_monitoring_outdir"))),
        "live_replay_adapt":live.get("outdir",output.get("live_adaptation_outdir")),
        "archive_run":archive.get("root"),
        "archive_summarize":str(Path(archive.get("root","live_archive"))/"summaries"),
        "archive_quicklook":str(Path(archive.get("root","live_archive"))/"quicklooks"),
        "archive_schema":str(Path(archive.get("root","live_archive"))/"schema_validation"),
        "dashboard":live.get("outdir",archive.get("root")),
        "operator_report":output.get("operator_report_outdir"),
    }
    return str(mapping.get(step)) if mapping.get(step) else None

def build_step_command(step:str, config_path:str|Path)->list[str]:
    if step not in STEP_COMMANDS: raise ValueError(f"Unknown campaign step {step!r}. Known steps: {sorted(STEP_COMMANDS)}")
    return [sys.executable,"-m","dmdc.cli",*STEP_COMMANDS[step],"--config",str(config_path)]

def write_campaign_docs(campaign_dir:Path, records:list[CampaignStepRecord], config_path:str|Path, resources:dict[str,Any])->dict[str,Path]:
    campaign_dir.mkdir(parents=True,exist_ok=True)
    step_index=campaign_dir/"campaign_step_index.csv"; pd.DataFrame([asdict(r) for r in records]).to_csv(step_index,index=False)
    plan=["# Campaign Plan","",f"Config: `{config_path}`","","## Resource summary","",f"- CPU count: {resources.get('cpu_count')}",f"- Memory available bytes: {resources.get('memory_available_bytes')}",f"- Slurm available: {resources.get('slurm_available')}","","## Steps",""]
    for r in records:
        plan += [f"### {r.step}",f"- Status: {r.status}",f"- Writes/uses: `{r.outdir_hint}`" if r.outdir_hint else "- Writes/uses: see command/config",f"- Command: `{r.command}`",""]
    plan_md=campaign_dir/"campaign_plan.md"; plan_md.write_text("\n".join(plan),encoding="utf-8")
    nexts=["# Suggested Next Steps",""]+[f"- After `{r.step}`: {NEXT_STEP_HINTS[r.step]}" for r in records if r.step in NEXT_STEP_HINTS]+["","## General guidance","","- Not every step has to run every time. Select steps with `--steps inspect compare dashboard`.","- For live work, use replay mode first before tailing a real logger.","- For large archives, browse summaries and quicklooks before opening raw partitions."]
    next_md=campaign_dir/"next_steps.md"; next_md.write_text("\n".join(nexts),encoding="utf-8")
    (campaign_dir/"resource_summary.json").write_text(__import__('json').dumps(resources,indent=2),encoding="utf-8")
    return {"step_index_csv":step_index,"plan_md":plan_md,"next_steps_md":next_md}

def run_campaign(config_path:str|Path, *, steps:list[str]|None=None, dry_run:bool=False)->CampaignResult:
    config=load_config(config_path); campaign_group_dir=infer_campaign_group_dir(config,config_path); requested=enabled_steps(config,steps); resources=get_resource_summary()
    execution_mode=_get(config,"execution","mode",default="local")
    if execution_mode not in {"local","hpc"}: raise ValueError("execution.mode must be 'local' or 'hpc'.")
    if execution_mode=="hpc": dry_run=True
    run_id = make_campaign_run_id()
    campaign_dir = campaign_group_dir / run_id
    derived_config = _rebase_campaign_config(config, config_path=config_path, group_dir=campaign_group_dir, run_dir=campaign_dir, steps=requested, dry_run=dry_run)
    derived_config_path = write_derived_config(campaign_dir, derived_config)
    run_index_csv = update_run_index(campaign_group_dir, run_dir=campaign_dir, config_path=config_path, steps=requested, dry_run=dry_run)
    records=[]; ok=0; failed=0
    for step in requested:
        cmd=build_step_command(step,derived_config_path); rec=CampaignStepRecord(step,True,"dry_run" if dry_run else "running"," ".join(cmd),outdir_hint_for_step(derived_config,step,campaign_dir),notes="HPC mode writes a plan only; edit scripts/slurm templates before submitting." if execution_mode=="hpc" else None)
        rec.started_utc=datetime.now(timezone.utc).isoformat()
        if not dry_run:
            done=subprocess.run(cmd,cwd=Path.cwd()); rec.return_code=int(done.returncode); rec.status="succeeded" if done.returncode==0 else "failed"; ok += int(done.returncode==0); failed += int(done.returncode!=0)
        rec.finished_utc=datetime.now(timezone.utc).isoformat(); records.append(rec)
        if rec.status=="failed": break
    paths=write_campaign_docs(campaign_dir,records,derived_config_path,resources)
    return CampaignResult(str(campaign_dir),str(campaign_group_dir),run_id,requested,[r.step for r in records if r.status in {"succeeded","dry_run"}],ok,failed,dry_run,str(paths["step_index_csv"]),str(paths["plan_md"]),str(paths["next_steps_md"]),str(derived_config_path),str(run_index_csv))
