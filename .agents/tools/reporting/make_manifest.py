#!/usr/bin/env python3
"""Create a research campaign MANIFEST.yaml."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import git_state, now_local_iso, write_yaml, ensure_dir, print_written

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--campaign-id', required=True); ap.add_argument('--question', required=True); ap.add_argument('--report-dir', required=True)
    ap.add_argument('--input-files', nargs='*', default=[]); ap.add_argument('--validation-files', nargs='*', default=[]); ap.add_argument('--scripts-used', nargs='*', default=[]); ap.add_argument('--commands', nargs='*', default=[]); ap.add_argument('--notes', nargs='*', default=[])
    a = ap.parse_args(); rd = ensure_dir(a.report_dir)
    m = {'campaign_id': a.campaign_id, 'created_at_local': now_local_iso(), 'research_question': a.question, 'git': git_state('.'), 'inputs': {'input_files': a.input_files, 'validation_files': a.validation_files, 'campaign_config': f'analysis/campaigns/{a.campaign_id}.yaml'}, 'commands': [{'command': c, 'status': 'recorded'} for c in a.commands], 'scripts_used': a.scripts_used, 'outputs': {'report_dir': str(rd), 'runtime_rows_dir': 'analysis/runtime_rows', 'runtimes_master': 'analysis/runtimes_master.csv', 'figures': [], 'tables': [], 'reports': [str(rd/'CHECKPOINT.md'), str(rd/'CHANGELOG.md')]}, 'metrics': {}, 'known_issues': [], 'notes': a.notes, 'next_actions': []}
    out = rd/'MANIFEST.yaml'; write_yaml(out, m); print_written(out); return 0
if __name__ == '__main__': raise SystemExit(main())
