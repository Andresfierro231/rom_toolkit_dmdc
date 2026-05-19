#!/usr/bin/env python3
"""Create a structured research journal entry."""
from __future__ import annotations
import argparse, sys
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import now_local_iso, slugify, ensure_dir, print_written

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--title', required=True); ap.add_argument('--campaign-id', default=''); ap.add_argument('--summary', default=''); ap.add_argument('--journal-root', default='analysis/journals'); ap.add_argument('--append', action='store_true'); a = ap.parse_args()
    now = datetime.now(); out = ensure_dir(Path(a.journal_root)/now.strftime('%Y-%m'))/f"{now.strftime('%Y-%m-%d')}_{slugify(a.title)}.md"
    entry = f"""# {a.title}\n\nGenerated: {now_local_iso()}\n\n## Campaign\n\n{a.campaign_id or 'Not specified.'}\n\n## Summary\n\n{a.summary or 'Not yet summarized.'}\n\n## Files inspected\n\n- \n\n## Commands run\n\n```bash\n\n```\n\n## Outputs generated\n\n- \n\n## Key results\n\n- \n\n## Interpretation\n\n- \n\n## Limitations / unresolved issues\n\n- \n\n## Next actions\n\n- \n"""
    mode = 'a' if a.append and out.exists() else 'w'
    with out.open(mode, encoding='utf-8') as f:
        if mode == 'a': f.write('\n\n---\n\n')
        f.write(entry)
    print_written(out); return 0
if __name__ == '__main__': raise SystemExit(main())
