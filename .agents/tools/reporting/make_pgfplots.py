#!/usr/bin/env python3
"""Generate a simple PGFPlots wrapper from CSV data."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from common import print_written

def esc(s): return str(s).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&').replace('#', r'\#')

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--csv', required=True); ap.add_argument('--out', required=True); ap.add_argument('--x', required=True); ap.add_argument('--y', required=True); ap.add_argument('--xlabel', default=None); ap.add_argument('--ylabel', default=None); ap.add_argument('--title', default=''); ap.add_argument('--plot-type', choices=['line','scatter','bar'], default='line'); ap.add_argument('--width', default=r'0.95\linewidth'); ap.add_argument('--height', default=r'0.55\linewidth'); a = ap.parse_args()
    add = {'line': rf'\addplot+[mark=*] table[x={a.x}, y={a.y}, col sep=comma] {{{a.csv}}};', 'scatter': rf'\addplot+[only marks] table[x={a.x}, y={a.y}, col sep=comma] {{{a.csv}}};', 'bar': rf'\addplot+[ybar] table[x={a.x}, y={a.y}, col sep=comma] {{{a.csv}}};'}[a.plot_type]
    symbolic = '\n  symbolic x coords={},\n  xtick=data,\n  x tick label style={rotate=45,anchor=east},' if a.plot_type == 'bar' else ''
    tex = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  width={a.width},
  height={a.height},
  title={{{esc(a.title)}}},
  xlabel={{{esc(a.xlabel or a.x)}}},
  ylabel={{{esc(a.ylabel or a.y)}}},
  grid=both,
  legend style={{at={{(0.5,-0.18)}},anchor=north}},
  tick align=outside,{symbolic}
]
{add}
\end{{axis}}
\end{{tikzpicture}}
"""
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(tex, encoding='utf-8'); print_written(out); return 0
if __name__ == '__main__': raise SystemExit(main())
