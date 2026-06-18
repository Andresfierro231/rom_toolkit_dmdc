# Methods Expansion Agent Brief

## Purpose

Expand the manuscript's secondary DMDc methods section without overstating what
has been proven. The agent should make the workflow mathematically legible in
the main text, while also making it obvious that a fuller derivation belongs in
an appendix and eventual code-audit note.

## Primary files to edit

- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/04_methods_workflow.tex`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/06_trust_limits.tex`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/frontmatter/abstract.tex` only if the methods boundary needs one sentence of clarification
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/main.tex`
- `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/appendices/app_a_source_of_truth_audit.tex`
- a new appendix file for DMDc derivation and implementation-audit outline

## Required main-text additions

1. Explain the study contract in repo-native terms.
   - Central config.
   - `compare` as the fixed-surface first pass.
   - `sweep` as the broader tuned search surface.

2. Explain the current JSALT2 selection result in workflow language.
   - Why the winner changes between the narrow compare surface and the broader
     tuned sweep surface.
   - Why that is a result about workflow contract and search surface, not a
     universal theorem about one model family.

3. Explain the stability filter operationally.
   - Lower raw error can be rejected if the candidate is spectrally unstable.
   - The paper should say why that rejection exists and what kind of instability
     marker is being screened.

4. Explain the split limitation explicitly.
   - Current result is current-split only.
   - Robustness across alternative case-aware splits remains future work.

5. Explain keep-`h` versus no-`h` in operational rather than mystical terms.
   - This is an input/state-contract choice, not a purely symbolic option.

## Required math-outline additions

The main text does not need a full derivation, but it should at least name:

- the lifted discrete state vector
- the control/input vector
- the one-step linear evolution form
- delay embedding as state augmentation
- POD projection as a reduced-coordinate map
- ridge regularization or adaptive variants as estimation choices layered onto
  the same workflow family

## Required appendix scaffolding

Create an appendix with a title equivalent to:

- `DMDc derivation and implementation-audit outline`

That appendix should include a full outline for the eventual write-up:

1. notation and state/input definitions
2. discrete-time DMDc regression objective
3. delay embedding construction
4. POD reduction and lifting back to physical coordinates
5. stability-screening metrics and thresholds
6. compare-versus-sweep search-surface definitions
7. keep-`h` versus no-`h` contract options
8. implementation hooks to audit in `dmdc-analysis`
9. unresolved assumptions and what still requires code audit

## Tone and claim discipline

- Keep methods explanatory but modest.
- Do not imply that the appendix itself is a completed proof.
- Make the appendix a roadmap for the full derivation and implementation audit,
  not a bluff that those steps are already finished.

## Validation

After edits, rebuild the manuscript and check:

- the DMDc methods section is no longer a placeholder paragraph
- the new appendix is included in `main.tex`
- no new unresolved LaTeX errors were introduced
