#!/usr/bin/env python3
"""Common utilities for Codex research workflow scripts."""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, os, re, subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

IGNORE_DIRS = {'.git','.venv','venv','__pycache__','.mypy_cache','.pytest_cache','node_modules','build','dist'}

def repo_root(start: str | Path = '.') -> Path:
    start = Path(start).resolve()
    try:
        out = subprocess.check_output(['git','rev-parse','--show-toplevel'], cwd=start, text=True, stderr=subprocess.DEVNULL).strip()
        if out: return Path(out)
    except Exception:
        pass
    for p in [start, *start.parents]:
        if (p/'AGENTS.md').exists(): return p
    return start

def now_local_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')

def slugify(text: str, max_len: int = 80) -> str:
    text = re.sub(r'[^a-z0-9]+', '_', text.strip().lower())
    return (re.sub(r'_+', '_', text).strip('_') or 'untitled')[:max_len]

def run_cmd(args: Sequence[str], cwd: str | Path | None = None) -> dict[str, Any]:
    try:
        p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
        return {'command': list(args), 'cwd': str(Path(cwd or '.').resolve()), 'returncode': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}
    except FileNotFoundError as e:
        return {'command': list(args), 'cwd': str(Path(cwd or '.').resolve()), 'returncode': 127, 'stdout': '', 'stderr': str(e)}

def git_state(cwd: str | Path = '.') -> dict[str, Any]:
    root = repo_root(cwd)
    def g(*parts: str) -> str:
        r = run_cmd(['git', *parts], cwd=root)
        return r['stdout'] if r['returncode'] == 0 else ''
    status = g('status','--short')
    return {'repo_root': str(root), 'timestamp_local': now_local_iso(), 'branch': g('rev-parse','--abbrev-ref','HEAD'), 'commit': g('rev-parse','HEAD'), 'commit_short': g('rev-parse','--short','HEAD'), 'dirty': bool(status.strip()), 'status_short': status.splitlines(), 'diff_name_status': g('diff','--name-status').splitlines()}

def sha256_file(path: str | Path, chunk_size: int = 1024*1024) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()

def iter_files(paths: Iterable[str | Path], ignore_dirs: set[str] | None = None):
    ignore_dirs = ignore_dirs or IGNORE_DIRS
    for raw in paths:
        p = Path(raw)
        if not p.exists(): continue
        if p.is_file():
            yield p
        else:
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for name in names:
                    fp = Path(root)/name
                    if fp.is_file(): yield fp

def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=False) + '\n', encoding='utf-8')

def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_yaml(path: str | Path, obj: Any) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        p.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding='utf-8')
    except Exception:
        p.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')

def read_yaml(path: str | Path) -> Any:
    text = Path(path).read_text(encoding='utf-8')
    try:
        import yaml
        return yaml.safe_load(text)
    except Exception:
        return json.loads(text)

def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for k in row:
                if k not in fieldnames: fieldnames.append(k)
    with p.open('w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction='ignore')
        wr.writeheader()
        for row in rows:
            wr.writerow({k: json.dumps(row.get(k,''), sort_keys=True) if isinstance(row.get(k,''),(dict,list,tuple)) else row.get(k,'') for k in fieldnames})

def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def relpath(path: str | Path, start: str | Path | None = None) -> str:
    start = Path(start or repo_root()).resolve()
    try: return str(Path(path).resolve().relative_to(start))
    except Exception: return str(Path(path))

def ensure_dir(path: str | Path) -> Path:
    p = Path(path); p.mkdir(parents=True, exist_ok=True); return p

def print_written(path: str | Path) -> None:
    print(f'Wrote {Path(path).as_posix()}')
