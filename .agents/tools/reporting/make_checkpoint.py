#!/usr/bin/env python3
"""Create CHECKPOINT.md from a campaign manifest."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import read_yaml, now_local_iso, print_written

def bullets(items):
    if not items: return '- None recorded.\n'
    if isinstance(items, dict): items = [f'{k}: {v}' for k,v in items.items()]
    return ''.join(f'- `{x}`\n' if isinstance(x, str) and '/' in x else f'- {x}\n' for x in items)

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--manifest', required=True); ap.add_argument('--out', required=True); ap.add_argument('--title', default=None); a = ap.parse_args()
    m = read_yaml(a.manifest) or {}; gid = m.get('campaign_id','unknown_campaign'); git = m.get('git',{}) or {}; inputs = m.get('inputs',{}) or {}; outputs = m.get('outputs',{}) or {}
    text = f"""# {a.title or 'Checkpoint — ' + gid}\n\nGenerated: {now_local_iso()}\n\n## Research question\n\n{m.get('research_question','Not recorded.')}\n\n## Repository state\n\n- Branch: `{git.get('branch','unknown')}`\n- Commit: `{git.get('commit_short', git.get('commit','unknown'))}`\n- Dirty working tree: `{git.get('dirty','unknown')}`\n\n## Files inspected / inputs\n\n{bullets(inputs.get('input_files', []))}\n## Validation or reference data\n\n{bullets(inputs.get('validation_files', []))}\n## Commands recorded\n\n{bullets([c.get('command', c) if isinstance(c, dict) else c for c in m.get('commands', [])])}\n## Scripts used\n\n{bullets(m.get('scripts_used', []))}\n## Outputs generated\n\n### Reports\n\n{bullets(outputs.get('reports', []))}\n### Figures\n\n{bullets(outputs.get('figures', []))}\n### Tables\n\n{bullets(outputs.get('tables', []))}\n## Key numerical results\n\nNot yet summarized. Add metrics here or update `MANIFEST.yaml.metrics`.\n\n## Interpretation\n\nNot yet written. Distinguish observed results from interpretation.\n\n## Limitations\n\n{bullets(m.get('known_issues', []))}\n## Missing information\n\nAdd missing files, failed runs, or incomplete provenance here.\n\n## Next actions\n\n{bullets(m.get('next_actions', []))}\n## Exact files future agents should inspect first\n\n- `{a.manifest}`\n- This checkpoint file\n- Campaign config listed in the manifest\n- Figure/table manifests under the report directory, if present\n"""
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text, encoding='utf-8'); print_written(out); return 0
if __name__ == '__main__': raise SystemExit(main())
