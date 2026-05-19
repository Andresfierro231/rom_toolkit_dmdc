# Figure Generation Contract

A report figure is not complete unless future users can regenerate it.

## Required per figure

- Source CSV
- Figure script or documented command
- PDF output
- SVG output
- TikZ/PGFPlots `.tex` output when practical
- Caption draft
- Figure manifest row

## Style rules

- Use short labels.
- Put units in axis labels.
- Avoid diagonal labels when possible.
- Use horizontal bar charts for long categorical labels.
- Use direct labels or external legends when legends overlap data.
- Avoid raster-only figures unless the figure is inherently image-based.
- Do not hide failed or excluded cases; list them in notes or a separate table.
