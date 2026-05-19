---
name: source-audit
description: Use for literature review, equation audits, provenance of technical claims, or validation of whether repo examples are synthetic, reference, or field-validated.
---

# Source audit skill

## Goal

Ensure every technical claim, equation, property correlation, validity range, and closure choice is traceable to a reliable source.

## Required fields per source

- citation key
- full bibliographic entry
- DOI/report number/ISBN if available
- source type
- original source or secondary source
- exact claim supported
- equation or table number if available
- validity range
- units
- assumptions
- conflicts with other sources
- confidence level
- recommended use in this project

## Rules

- Verify or downgrade unsupported claims.
- Distinguish synthetic example data from validation or operational data.
- Do not treat secondary citations as original evidence unless clearly labeled.
- Put uncertain sources in `Unverified or Not Yet Usable Sources`.
- Produce BibTeX entries when requested.
- Keep source-audit tables usable in LaTeX.
