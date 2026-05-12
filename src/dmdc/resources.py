"""Local/HPC resource summary helpers. Local workstation execution is the default."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json, os, platform, shutil, subprocess

def get_resource_summary() -> dict[str, Any]:
    cpu=os.cpu_count() or 1; mem_total=None; mem_avail=None
    try:
        import psutil  # type: ignore
        vm=psutil.virtual_memory(); mem_total=int(vm.total); mem_avail=int(vm.available)
    except Exception: pass
    out={"platform":platform.platform(),"python":platform.python_version(),"cpu_count":cpu,"memory_total_bytes":mem_total,"memory_available_bytes":mem_avail,"slurm_available":shutil.which("sbatch") is not None,"recommended_default_execution_mode":"local","notes":["Local workstation execution is the default.","Use execution.mode='hpc' only after editing scripts/slurm templates with account/partition details."]}
    if out["slurm_available"]:
        try:
            r=subprocess.run(["sinfo","-h","-o","%P %D %c %m"],capture_output=True,text=True,timeout=5)
            if r.returncode==0: out["slurm_sinfo_preview"]=r.stdout.strip().splitlines()[:10]
        except Exception: pass
    return out

def write_resource_summary(path: str | Path) -> Path:
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(get_resource_summary(), indent=2), encoding="utf-8"); return p
