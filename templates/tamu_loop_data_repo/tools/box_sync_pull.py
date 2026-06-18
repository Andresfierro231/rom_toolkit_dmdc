#!/usr/bin/env python3
"""One-way Box -> local sync for the TAMU loop data repository.

This script is intentionally conservative:

- it only reads from Box
- it never uploads, renames, moves, or deletes anything on Box
- it only updates files under the chosen local destination
- it never deletes local-only files by default
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".box_sync_state"
DEFAULT_FOLDER_ID = "246873664013"
DEFAULT_DEST = REPO_ROOT / "Loop Operational Data"
DEFAULT_STATE = STATE_DIR / "loop_operational_data_manifest.json"


@dataclass
class BoxItem:
    item_id: str
    item_type: str
    name: str
    path: str
    size: int | None = None
    sha1: str | None = None
    modified_at: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--box-folder-id", default=DEFAULT_FOLDER_ID)
    parser.add_argument("--destination", default=str(DEFAULT_DEST))
    parser.add_argument("--state-file", default=str(DEFAULT_STATE))
    parser.add_argument("--max-items", type=int, default=1000)
    parser.add_argument("--prune-box-files", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def run_box_json(args: list[str]) -> Any:
    cmd = ["box", *args, "--json"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Box command failed ({' '.join(cmd)}):\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def list_folder_items(folder_id: str, max_items: int) -> list[dict[str, Any]]:
    data = run_box_json(["folders:items", folder_id, "--max-items", str(max_items)])
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected folder listing shape for folder {folder_id}: {type(data)!r}")
    return data


def build_manifest(folder_id: str, max_items: int) -> tuple[dict[str, BoxItem], dict[str, BoxItem]]:
    files: dict[str, BoxItem] = {}
    folders: dict[str, BoxItem] = {}

    def walk(current_folder_id: str, relative_root: Path) -> None:
        items = list_folder_items(current_folder_id, max_items=max_items)
        for raw in items:
            item_type = raw["type"]
            name = raw["name"]
            item_id = raw["id"]
            rel_path = (relative_root / name).as_posix()
            if item_type == "folder":
                folders[rel_path] = BoxItem(
                    item_id=item_id,
                    item_type=item_type,
                    name=name,
                    path=rel_path,
                    modified_at=raw.get("modified_at"),
                )
                walk(item_id, relative_root / name)
            elif item_type == "file":
                files[rel_path] = BoxItem(
                    item_id=item_id,
                    item_type=item_type,
                    name=name,
                    path=rel_path,
                    size=raw.get("size"),
                    sha1=raw.get("sha1"),
                    modified_at=raw.get("modified_at"),
                )

    walk(folder_id, Path("."))
    return files, folders


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def should_download(item: BoxItem, dest: Path, prev_state: dict[str, Any]) -> bool:
    if not dest.exists():
        return True
    if item.size is not None and dest.stat().st_size != item.size:
        return True
    prev = prev_state.get("files", {}).get(item.path)
    if not prev:
        return True
    if prev.get("sha1") != item.sha1:
        return True
    if prev.get("box_file_id") != item.item_id:
        return True
    return False


def adopt_existing_local_file(item: BoxItem, dest: Path) -> bool:
    if not dest.exists():
        return False
    if item.size is not None and dest.stat().st_size != item.size:
        return False
    if item.sha1:
        return sha1_file(dest) == item.sha1
    return True


def download_file(item: BoxItem, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmpdir:
        tmp_path = Path(tmpdir) / item.name
        cmd = [
            "box",
            "files:download",
            item.item_id,
            "--destination",
            tmpdir,
            "--save-as",
            item.name,
            "--overwrite",
            "--create-path",
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Download failed for {item.path} ({item.item_id}):\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        shutil.move(str(tmp_path), str(dest))


def main() -> int:
    args = parse_args()
    destination = Path(args.destination).resolve()
    state_file = Path(args.state_file).resolve()
    prev_state = load_state(state_file)

    print("WARNING: This script is one-way only: Box -> local.")
    print("WARNING: Never use this repo or these scripts to upload, move, rename, or delete content on Box.")

    files, folders = build_manifest(args.box_folder_id, args.max_items)

    for folder_path in sorted(folders):
        local_dir = destination / folder_path
        if args.dry_run:
            if not local_dir.exists():
                print(f"MKDIR   {local_dir}")
        else:
            local_dir.mkdir(parents=True, exist_ok=True)

    downloads = 0
    skipped = 0
    for rel_path in sorted(files):
        item = files[rel_path]
        local_file = destination / rel_path
        if should_download(item, local_file, prev_state):
            if adopt_existing_local_file(item, local_file):
                skipped += 1
                print(f"ADOPT   {item.path}")
                continue
            downloads += 1
            print(f"GET     {item.path}")
            if not args.dry_run:
                download_file(item, local_file)
        else:
            skipped += 1
            print(f"KEEP    {item.path}")

    deleted = 0
    if args.prune_box_files:
        previous_files = prev_state.get("files", {})
        current_paths = set(files)
        for rel_path in sorted(previous_files):
            if rel_path in current_paths:
                continue
            local_file = destination / rel_path
            if local_file.exists():
                deleted += 1
                print(f"PRUNE   {local_file}")
                if not args.dry_run:
                    local_file.unlink()

    if not args.dry_run:
        new_state = {
            "box_folder_id": args.box_folder_id,
            "destination": str(destination),
            "files": {
                rel_path: {
                    "box_file_id": item.item_id,
                    "sha1": item.sha1,
                    "size": item.size,
                    "modified_at": item.modified_at,
                }
                for rel_path, item in sorted(files.items())
            },
        }
        save_state(state_file, new_state)

    print(
        f"Summary: files in Box manifest={len(files)}, "
        f"downloaded={downloads}, skipped={skipped}, pruned={deleted}, dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
