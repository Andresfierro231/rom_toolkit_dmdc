#!/usr/bin/env python3
"""Collect git state for a research campaign."""
from __future__ import annotations
import argparse, sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'reporting'))
from common import git_state, write_json, write_yaml, print_written

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='-')
    ap.add_argument('--format', choices=['json','yaml'], default='json')
    a = ap.parse_args()
    state = git_state('.')
    if a.out == '-':
        print(json.dumps(state, indent=2))
    elif a.format == 'yaml' or a.out.endswith(('.yaml','.yml')):
        write_yaml(a.out, state); print_written(a.out)
    else:
        write_json(a.out, state); print_written(a.out)
    return 0
if __name__ == '__main__': raise SystemExit(main())
