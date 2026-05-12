"""Local/HPC campaign planning helpers.

The default repo workflow is local-workstation execution.  This module creates
transparent command plans and Slurm skeletons for later HPC use without assuming
any account, partition, modules, or filesystem layout.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from .config import load_config
from .resources import get_resource_summary


@dataclass
class HPCPlanResult:
    outdir: str
    execution_mode: str
    command_plan: str
    local_runner: str
    slurm_campaign_template: str
    slurm_archive_template: str
    resource_summary_json: str


DEFAULT_STEPS = ["import", "inspect", "compare", "validate", "live_replay_adapt", "archive", "dashboard", "operator_report"]


def write_hpc_workflow_plan(config_path: str | Path, *, outdir: str | Path = "outputs/hpc_plan", steps: list[str] | None = None) -> HPCPlanResult:
    """Write a local/HPC execution plan from a central config.

    The generated Slurm files intentionally contain FIXME fields.  Users should
    fill in account, partition, walltime, modules, and environment details for
    their cluster before submitting.
    """

    cfg = load_config(config_path)
    execution = cfg.get("execution", {}) if isinstance(cfg, dict) else {}
    mode = str(execution.get("mode", "local")) if isinstance(execution, dict) else "local"
    selected_steps = steps or list(execution.get("steps", DEFAULT_STEPS) if isinstance(execution, dict) else DEFAULT_STEPS)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    commands = _commands_for_steps(config_path, selected_steps)
    command_plan = out / "hpc_command_plan.md"
    command_plan.write_text(_render_command_plan(config_path, mode, commands), encoding="utf-8")
    local_runner = out / "run_local_campaign.sh"
    local_runner.write_text("#!/usr/bin/env bash\nset -euo pipefail\n\n" + "\n".join(commands) + "\n", encoding="utf-8")
    local_runner.chmod(0o755)
    slurm_campaign = out / "run_campaign.sbatch.FIXME"
    slurm_campaign.write_text(_render_slurm_template(config_path, commands, title="dmdc_campaign"), encoding="utf-8")
    slurm_archive = out / "run_archive_summarize.sbatch.FIXME"
    slurm_archive.write_text(_render_slurm_template(config_path, [c for c in commands if "archive" in c], title="dmdc_archive"), encoding="utf-8")
    resources = out / "resource_summary.json"
    resources.write_text(json.dumps(get_resource_summary(), indent=2), encoding="utf-8")
    result = HPCPlanResult(str(out), mode, str(command_plan), str(local_runner), str(slurm_campaign), str(slurm_archive), str(resources))
    (out / "hpc_plan_summary.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    return result


def _commands_for_steps(config_path: str | Path, steps: list[str]) -> list[str]:
    cfg = str(config_path)
    mapping = {
        "import": f"dmdc import-data --config {cfg}",
        "inspect": f"dmdc inspect-data --config {cfg}",
        "adaptive_fit": f"dmdc adaptive-fit --config {cfg}",
        "compare": f"dmdc compare --config {cfg}",
        "validate": f"dmdc validate --config {cfg}",
        "sweep": f"dmdc sweep --config {cfg}",
        "live_replay_adapt": f"dmdc live-replay-adapt --config {cfg}",
        "archive": f"dmdc archive-run --config {cfg} && dmdc archive-summarize --config {cfg} && dmdc archive-quicklook --config {cfg}",
        "dashboard": f"dmdc live-dashboard --config {cfg}",
        "operator_report": f"dmdc live-operator-report --config {cfg}",
    }
    return [mapping.get(step, f"# TODO: no built-in command mapping for step {step!r}") for step in steps]


def _render_command_plan(config_path: str | Path, mode: str, commands: list[str]) -> str:
    lines = [
        "# DMDc Campaign Execution Plan",
        "",
        f"Config: `{config_path}`",
        f"Requested execution mode: `{mode}`",
        "",
        "Default recommendation: run locally first.  Switch to HPC only after the local workflow is proven on a representative subset.",
        "",
        "## Commands",
        "",
    ]
    for i, cmd in enumerate(commands, 1):
        lines.append(f"{i}. `{cmd}`")
    lines.extend([
        "",
        "## HPC notes",
        "",
        "The Slurm files generated next to this plan are incomplete by design. Fill in account, partition, walltime, module loads, environment activation, and filesystem paths before submission.",
    ])
    return "\n".join(lines) + "\n"


def _render_slurm_template(config_path: str | Path, commands: list[str], *, title: str) -> str:
    body = "\n".join(commands) if commands else "echo 'No archive commands selected; edit this file.'"
    return f"""#!/usr/bin/env bash
#SBATCH -J {title}
#SBATCH -o logs/%x_%j.out
#SBATCH -e logs/%x_%j.err
#SBATCH -t FIXME_WALLTIME
#SBATCH -p FIXME_PARTITION
#SBATCH -A FIXME_ACCOUNT
#SBATCH -N 1
#SBATCH --ntasks-per-node=FIXME_TASKS

set -euo pipefail

# FIXME: load modules / activate environment
# module load python3
# source /path/to/venv/bin/activate

CONFIG={config_path}
mkdir -p logs

{body}
"""
