#!/usr/bin/env python3
"""Upload staged analysis artifacts from to_box/ to the TAMU flow-loop Box folder.

This helper is intentionally conservative:

- it only reads local files from dmdc-analysis/to_box/
- it only writes to the configured outputs Box folder
- it never touches the raw-data Box folder used by tamu_loop_data/
- it defaults to dry-run

The destination folder is:
All Files / Andres_Obsidian_Notes_Box / tamu_flow_loop / analyzing_operational_data
Box folder ID: 385169164073
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "to_box"
DEFAULT_BOX_FOLDER_ID = "385169164073"
DEFAULT_BOX_FOLDER_PATH = (
    "All Files/Andres_Obsidian_Notes_Box/tamu_flow_loop/analyzing_operational_data"
)

SKIP_NAMES = {".DS_Store", ".gitkeep"}
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help=f"Local folder to stage from. Default: {DEFAULT_SOURCE_ROOT}",
    )
    parser.add_argument(
        "--box-folder-id",
        default=DEFAULT_BOX_FOLDER_ID,
        help=f"Destination Box folder ID. Default: {DEFAULT_BOX_FOLDER_ID}",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=1000,
        help="Maximum entries to request per Box folder listing.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform uploads and folder creation. Default is dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly request dry-run mode.",
    )
    parser.add_argument(
        "--overwrite-changed",
        action="store_true",
        help="Upload a new Box version when a same-name file exists with a different size.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include dotfiles and files inside dot-directories.",
    )
    parser.add_argument(
        "--include-root-readme",
        action="store_true",
        help="Include to_box/README.md in the upload set.",
    )
    return parser.parse_args()


def run_box_json(args: list[str]) -> Any:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "box.json"
        err_path = Path(tmpdir) / "box.stderr"
        cmd = ["box", *args, "--json"]
        with out_path.open("w", encoding="utf-8") as stdout_handle, err_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            result = subprocess.run(
                cmd,
                check=False,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
        stdout_text = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        stderr_text = err_path.read_text(encoding="utf-8") if err_path.exists() else ""
        if result.returncode != 0:
            raise RuntimeError(
                f"Box command failed ({' '.join(cmd)}):\n"
                f"stdout:\n{stdout_text}\n"
                f"stderr:\n{stderr_text}"
            )
        try:
            return json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Box command returned non-JSON output ({' '.join(cmd)}):\n{stdout_text}\n"
                f"stderr:\n{stderr_text}"
            ) from exc


def list_folder_items(folder_id: str, max_items: int) -> list[dict[str, Any]]:
    data = run_box_json(
        [
            "folders:items",
            folder_id,
            "--max-items",
            str(max_items),
            "--fields",
            "type,id,name,size",
        ]
    )
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected folder listing shape for folder {folder_id}: {type(data)!r}")
    return data


def upload_file(local_path: Path, parent_id: str, overwrite: bool) -> dict[str, Any]:
    cmd = ["files:upload", str(local_path), "--parent-id", parent_id]
    if overwrite:
        cmd.append("--overwrite")
    data = run_box_json(cmd)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected upload response for {local_path}: {type(data)!r}")
    return data


def create_folder(parent_id: str, name: str) -> dict[str, Any]:
    data = run_box_json(["folders:create", parent_id, name])
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected create-folder response for {name}: {type(data)!r}")
    return data


def iter_local_files(
    root: Path,
    *,
    include_hidden: bool,
    include_root_readme: bool,
) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name in SKIP_NAMES:
            continue
        if not include_hidden and any(part.startswith(".") for part in rel.parts):
            continue
        if rel == Path("README.md") and not include_root_readme:
            continue
        files.append(path)
    return files


def main() -> int:
    args = parse_args()
    if args.execute and args.dry_run:
        print("Use either --execute or --dry-run, not both.", file=sys.stderr)
        return 2
    source_root = Path(args.source_root).resolve()
    if not source_root.exists():
        print(f"Missing source root: {source_root}", file=sys.stderr)
        return 2
    if not source_root.is_dir():
        print(f"Source root is not a directory: {source_root}", file=sys.stderr)
        return 2

    print(f"Destination Box folder path: {DEFAULT_BOX_FOLDER_PATH}")
    print(f"Destination Box folder ID: {args.box_folder_id}")
    print("WARNING: This helper is for dmdc-analysis/to_box only.")
    print("WARNING: Never use this helper or this repo to upload to the raw-data Box folder.")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")

    local_files = iter_local_files(
        source_root,
        include_hidden=args.include_hidden,
        include_root_readme=args.include_root_readme,
    )
    if not local_files:
        print(f"No eligible files found under {source_root}")
        return 0

    folder_cache: dict[str, dict[str, dict[str, Any]]] = {}
    created_folders = 0
    uploaded_new = 0
    uploaded_overwrite = 0
    skipped_same = 0
    skipped_changed = 0

    def get_items(folder_id: str) -> dict[str, dict[str, Any]]:
        if folder_id not in folder_cache:
            folder_cache[folder_id] = {
                item["name"]: item for item in list_folder_items(folder_id, args.max_items)
            }
        return folder_cache[folder_id]

    def ensure_remote_folder(parent_id: str, name: str, rel_path: Path) -> str:
        nonlocal created_folders
        items = get_items(parent_id)
        existing = items.get(name)
        if existing:
            if existing["type"] != "folder":
                raise RuntimeError(
                    f"Remote path collision: expected folder at {rel_path.as_posix()}, "
                    f"found {existing['type']}"
                )
            return str(existing["id"])
        print(f"MKDIR   {rel_path.as_posix()}")
        created_folders += 1
        if not args.execute:
            dry_id = f"DRYRUN::{parent_id}/{name}"
            items[name] = {"id": dry_id, "type": "folder", "name": name}
            folder_cache[dry_id] = {}
            return dry_id
        created = create_folder(parent_id, name)
        items[name] = created
        folder_cache[str(created["id"])] = {}
        return str(created["id"])

    for local_path in local_files:
        rel = local_path.relative_to(source_root)
        remote_parent_id = args.box_folder_id
        current_rel = Path(".")
        for part in rel.parent.parts:
            if part in {"", "."}:
                continue
            current_rel = current_rel / part
            remote_parent_id = ensure_remote_folder(remote_parent_id, part, current_rel)

        parent_items = get_items(remote_parent_id)
        existing = parent_items.get(local_path.name)
        size = local_path.stat().st_size
        rel_text = rel.as_posix()

        if existing is None:
            print(f"PUT     {rel_text}")
            uploaded_new += 1
            if args.execute:
                created = upload_file(local_path, remote_parent_id, overwrite=False)
                parent_items[local_path.name] = created
            continue

        if existing["type"] != "file":
            raise RuntimeError(
                f"Remote path collision: expected file at {rel_text}, found {existing['type']}"
            )

        remote_size = existing.get("size")
        if remote_size == size:
            print(f"KEEP    {rel_text}")
            skipped_same += 1
            continue

        if not args.overwrite_changed:
            print(f"SKIP    {rel_text} (size differs: local={size}, remote={remote_size})")
            skipped_changed += 1
            continue

        print(f"UPDATE  {rel_text}")
        uploaded_overwrite += 1
        if args.execute:
            updated = upload_file(local_path, remote_parent_id, overwrite=True)
            parent_items[local_path.name] = updated

    print(
        "Summary: "
        f"files={len(local_files)}, "
        f"mkdir={created_folders}, "
        f"new={uploaded_new}, "
        f"updated={uploaded_overwrite}, "
        f"kept={skipped_same}, "
        f"skipped_changed={skipped_changed}, "
        f"dry_run={not args.execute}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
