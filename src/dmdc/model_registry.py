"""Local model registry and deployment helpers for live ROM workflows.

A live dashboard should not depend on a mysterious path like
``outputs/sweep_12/model.pkl``.  This module provides a lightweight file-system
registry so validated models can be registered, promoted to stages such as
``production``, and referenced from live configs by ``registry_name`` and
``stage``.

The implementation is deliberately local-workstation friendly: no database,
server, or cloud service is required.  A registry is just an inspectable folder
with an index CSV and deployment JSON.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib, json, shutil, uuid
import pandas as pd

REGISTRY_SCHEMA_VERSION = "model_registry_v1"

@dataclass
class RegisteredModel:
    registry_root: str
    name: str
    version: str
    stage: str
    model_path: str
    registered_model_path: str
    metadata_path: str
    registered_utc: str
    model_sha256: str
    model_type: str | None = None
    metrics_path: str | None = None
    notes: str | None = None

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _slug(value: str) -> str:
    return ("".join(ch if ch.isalnum() or ch in {"-","_","."} else "_" for ch in str(value).strip()).strip("._") or "model")

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

def _load_json(path: Path, default: Any) -> Any:
    if path.exists() and path.stat().st_size > 0:
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def index_path(registry_root: str | Path) -> Path:
    return Path(registry_root) / "registry_index.csv"

def deployments_path(registry_root: str | Path) -> Path:
    return Path(registry_root) / "deployments.json"

def read_registry_index(registry_root: str | Path = "models/registry") -> pd.DataFrame:
    p = index_path(registry_root)
    return pd.read_csv(p) if p.exists() and p.stat().st_size > 0 else pd.DataFrame()

def _append_index(root: Path, row: dict[str, Any]) -> None:
    old = read_registry_index(root)
    new = pd.DataFrame([row])
    (pd.concat([old, new], ignore_index=True) if not old.empty else new).to_csv(index_path(root), index=False)

def load_deployments(registry_root: str | Path = "models/registry") -> dict[str, Any]:
    return _load_json(deployments_path(registry_root), {"schema_version": REGISTRY_SCHEMA_VERSION, "deployments": {}})

def promote_model(name: str, *, stage: str = "production", version: str, registry_root: str | Path = "models/registry") -> dict[str, Any]:
    root = Path(registry_root)
    idx = read_registry_index(root)
    if idx.empty:
        raise FileNotFoundError(f"No registry index found under {root}")
    matches = idx[(idx["name"].astype(str) == str(name)) & (idx["version"].astype(str) == str(version))]
    if matches.empty:
        raise ValueError(f"No registered model named {name!r} with version {version!r}.")
    row = matches.iloc[-1].to_dict()
    dep = load_deployments(root)
    dep.setdefault("deployments", {}).setdefault(str(name), {})[str(stage)] = {
        "version": str(version), "model_path": row.get("registered_model_path"),
        "metadata_path": row.get("metadata_path"), "promoted_utc": _utc_now(),
        "model_sha256": row.get("model_sha256"),
    }
    _write_json(deployments_path(root), dep)
    return dep["deployments"][str(name)][str(stage)]

def register_model(model_path: str | Path, *, name: str, registry_root: str | Path = "models/registry", stage: str = "candidate", version: str | None = None, model_type: str | None = None, metrics_path: str | Path | None = None, notes: str | None = None, extra_metadata: dict[str, Any] | None = None) -> RegisteredModel:
    src = Path(model_path)
    if not src.exists():
        raise FileNotFoundError(f"Model file not found: {src}")
    root = Path(registry_root); root.mkdir(parents=True, exist_ok=True)
    safe_name = _slug(name)
    version = _slug(version or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    dest_dir = root / safe_name / version; dest_dir.mkdir(parents=True, exist_ok=True)
    dest_model = dest_dir / src.name; shutil.copy2(src, dest_model)
    metrics_dest = None
    if metrics_path and Path(metrics_path).exists():
        out = dest_dir / Path(metrics_path).name; shutil.copy2(metrics_path, out); metrics_dest = str(out)
    meta = RegisteredModel(str(root), safe_name, version, stage, str(src), str(dest_model), str(dest_dir / "metadata.json"), _utc_now(), _sha256(dest_model), model_type, metrics_dest, notes)
    payload = {"schema_version": REGISTRY_SCHEMA_VERSION, **asdict(meta), "extra_metadata": extra_metadata or {}}
    _write_json(dest_dir / "metadata.json", payload)
    _append_index(root, payload)
    promote_model(safe_name, stage=stage, version=version, registry_root=root)
    return meta

def resolve_model(*, name: str | None = None, stage: str = "production", version: str | None = None, registry_root: str | Path = "models/registry", path: str | Path | None = None) -> dict[str, Any]:
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found: {p}")
        return {"model_path": str(p), "registry_name": None, "stage": None, "version": None, "metadata_path": None, "source": "direct_path"}
    if not name:
        raise ValueError("Provide either direct path or registry name.")
    root = Path(registry_root)
    if version:
        idx = read_registry_index(root)
        m = idx[(idx["name"].astype(str)==str(name)) & (idx["version"].astype(str)==str(version))]
        if m.empty: raise ValueError(f"No registered model named {name!r} with version {version!r}.")
        row = m.iloc[-1].to_dict()
        return {"model_path": str(row["registered_model_path"]), "registry_name": str(name), "stage": stage, "version": str(version), "metadata_path": row.get("metadata_path"), "source": "registry_version"}
    dep = load_deployments(root).get("deployments", {})
    try: row = dep[str(name)][str(stage)]
    except KeyError as exc: raise ValueError(f"No deployment found for model {name!r} at stage {stage!r}.") from exc
    return {"model_path": str(row["model_path"]), "registry_name": str(name), "stage": str(stage), "version": str(row.get("version")), "metadata_path": row.get("metadata_path"), "source": "registry_stage"}

def write_model_identity(outdir: str | Path, identity: dict[str, Any]) -> Path:
    path = Path(outdir) / "model_identity.json"
    _write_json(path, {"schema_version": REGISTRY_SCHEMA_VERSION, **identity})
    return path
