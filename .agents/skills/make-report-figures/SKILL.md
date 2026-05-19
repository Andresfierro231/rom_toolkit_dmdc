---
name: make-report-figures
description: Use when asked to generate, repair, improve, export, or document report figures for dmdc studies, validation runs, dashboards, or LaTeX reports.
---

# Make report figures skill

## Goal

Generate publication-quality figures from saved data with full provenance.

## Required outputs per figure

For each figure, produce when practical:

- source data CSV
- figure script or documented command
- PDF figure
- SVG figure
- PGFPlots/TikZ `.tex` wrapper
- manifest entry
- proposed LaTeX caption

## Figure style rules

- Prefer figure inputs that already exist under `outputs/` or `analysis/reports/`.
- Include units in axis labels.
- Avoid overlapping text.
- Prefer direct labels or external legends when legends become crowded.
- Prefer PGFPlots reading CSV data for final LaTeX figures.
- Do not only export PNG unless raster is necessary.
