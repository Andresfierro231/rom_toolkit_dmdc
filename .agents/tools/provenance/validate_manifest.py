#!/usr/bin/env python3
"""Validate a campaign MANIFEST for basic completeness."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'reporting'))
from common import read_yaml, repo_root

REQUIRED = ['campaign_id','created_at_local','research_question','git','inputs','outputs','known_issues','next_actions']

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--manifest', required=True); ap.add_argument('--strict', action='store_true'); a = ap.parse_args()
    root = repo_root('.')
    m = read_yaml(a.manifest) or {}
    problems = [f'Missing required key: {k}' for k in REQUIRED if k not in m]
    for section, field in [('inputs','input_files'),('inputs','validation_files'),('outputs','figures'),('outputs','tables'),('outputs','reports')]:
        for item in ((m.get(section) or {}).get(field) or []):
            if item and not (root/str(item)).exists(): problems.append(f'Listed path does not exist in {section}.{field}: {item}')
    if problems:
        print('Manifest validation found issues:')
        for p in problems: print('-', p)
        return 2 if a.strict else 0
    print('Manifest validation passed.')
    return 0
if __name__ == '__main__': raise SystemExit(main())
