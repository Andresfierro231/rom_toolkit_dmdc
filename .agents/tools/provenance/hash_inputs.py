#!/usr/bin/env python3
"""Hash input files or directories for provenance."""
from __future__ import annotations
import argparse, sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'reporting'))
from common import iter_files, relpath, repo_root, sha256_file, write_json, write_yaml, now_local_iso, print_written

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--paths', nargs='+', required=True)
    ap.add_argument('--out', default='-')
    ap.add_argument('--max-mb', type=float, default=200.0)
    a = ap.parse_args()
    root = repo_root('.')
    max_bytes = int(a.max_mb*1024*1024)
    rows = []
    for p in iter_files(a.paths):
        try:
            size = p.stat().st_size
            row = {'path': relpath(p, root), 'size_bytes': size}
            if size > max_bytes:
                row.update({'sha256': None, 'status': f'skipped_larger_than_{a.max_mb:g}_MB'})
            else:
                row.update({'sha256': sha256_file(p), 'status': 'hashed'})
            rows.append(row)
        except Exception as e:
            rows.append({'path': relpath(p, root), 'status': 'error', 'error': str(e)})
    payload = {'timestamp_local': now_local_iso(), 'repo_root': str(root), 'requested_paths': a.paths, 'file_count': len(rows), 'files': rows}
    if a.out == '-': print(json.dumps(payload, indent=2))
    elif a.out.endswith(('.yaml','.yml')): write_yaml(a.out, payload); print_written(a.out)
    else: write_json(a.out, payload); print_written(a.out)
    return 0
if __name__ == '__main__': raise SystemExit(main())
