#!/usr/bin/env python3
"""Convert a CSV file to a simple LaTeX table."""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import print_written

def esc(s):
    repl = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(repl.get(c,c) for c in str(s if s is not None else ''))

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--csv', required=True); ap.add_argument('--out', required=True); ap.add_argument('--caption', default='Table caption.'); ap.add_argument('--label', default='tab:generated'); ap.add_argument('--max-rows', type=int, default=80); a = ap.parse_args()
    with Path(a.csv).open(newline='', encoding='utf-8') as f: rows = list(csv.DictReader(f))
    if not rows: raise SystemExit(f'No rows in {a.csv}')
    headers = list(rows[0].keys()); colspec = 'l'*len(headers); lines = [r'\begin{table}[htbp]', r'\centering', r'\small', r'\begin{tabular}{'+colspec+'}', r'\toprule', ' & '.join(esc(h) for h in headers)+r' \\', r'\midrule']
    for row in rows[:a.max_rows]: lines.append(' & '.join(esc(row.get(h,'')) for h in headers)+r' \\')
    if len(rows) > a.max_rows: lines.append(r'\multicolumn{'+str(len(headers))+r'}{l}{\emph{Table truncated; see source CSV for full data.}} \\')
    lines += [r'\bottomrule', r'\end{tabular}', rf'\caption{{{esc(a.caption)}}}', rf'\label{{{esc(a.label)}}}', r'\end{table}', '']
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text('\n'.join(lines), encoding='utf-8'); print_written(out); return 0
if __name__ == '__main__': raise SystemExit(main())
