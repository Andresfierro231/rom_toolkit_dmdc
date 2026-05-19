#!/usr/bin/env python3
"""Scan a figures directory and create figure_manifest.csv."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import write_csv, relpath, repo_root, now_local_iso, print_written
FIG_EXTS = {'.pdf','.svg','.png','.jpg','.jpeg','.tex'}

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--figures-dir', required=True); ap.add_argument('--out', required=True); ap.add_argument('--campaign-id', default=''); a = ap.parse_args()
    root = repo_root('.'); groups = {}
    for p in sorted(Path(a.figures_dir).glob('*')):
        if p.suffix.lower() in FIG_EXTS and p.name != Path(a.out).name:
            stem = p.stem.replace('_pgfplots','').replace('_tikz','')
            groups.setdefault(stem, {})[p.suffix.lower().lstrip('.')] = relpath(p, root)
    rows = [{'figure_id': stem, 'campaign_id': a.campaign_id, 'title': stem.replace('_',' ').title(), 'data_path': '', 'script_path': '', 'pdf_path': exts.get('pdf',''), 'svg_path': exts.get('svg',''), 'png_path': exts.get('png',''), 'tex_path': exts.get('tex',''), 'caption_draft': '', 'notes': f'Scanned {now_local_iso()}'} for stem, exts in groups.items()]
    fields = ['figure_id','campaign_id','title','data_path','script_path','pdf_path','svg_path','png_path','tex_path','caption_draft','notes']
    write_csv(a.out, rows, fields); print_written(a.out); return 0
if __name__ == '__main__': raise SystemExit(main())
