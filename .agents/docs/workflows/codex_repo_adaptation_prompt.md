# Prompt to give Codex when adapting this workflow to a specific repo

Use this prompt after copying the starter kit into a repository root.

---

You are working inside one specific research/code repository. I have added a starter workflow with:

- `AGENTS.md`
- `.agents/skills/`
- `tools/provenance/`
- `tools/reporting/`
- `tools/studies/`
- `templates/`
- `docs/workflows/`

Your task is to tailor this workflow to this repository without breaking existing functionality.

Follow these rules:

1. Inspect first. Do not modify files until you understand the current repo structure.
2. Read the root `AGENTS.md`, any nested `AGENTS.md` files, READMEs, major configs, existing scripts, and recent analysis/report outputs.
3. Identify the active workflow and distinguish it from legacy/obsolete scripts.
4. Find the current sources of truth for:
   - input files/templates/configs
   - run plans or experiment definitions
   - executable paths or environment setup
   - raw outputs
   - summarized result files
   - validation/reference data
   - plotting scripts
   - report/LaTeX files
5. Adapt the starter workflow to this repo:
   - Update `AGENTS.md` with repo-specific instructions.
   - Update skill descriptions and task steps under `.agents/skills/`.
   - Update `templates/campaign_template.yaml` for this repo’s typical campaign.
   - Update reporting/provenance tools only if needed.
   - Add repo-specific wrapper scripts rather than replacing generic tools.
   - Add docs under `docs/workflows/` explaining the actual repo workflow.
6. Preserve existing working scripts unless there is a clear reason to change them.
7. Do not invent test results or claim commands passed unless you actually ran them.
8. If commands are unsafe, expensive, or require unavailable credentials/HPC resources, create a dry-run path and document what remains unverified.
9. End by creating a test campaign named `workflow_adaptation_smoke_test` that records:
   - git state
   - files inspected
   - commands run
   - outputs generated
   - unresolved issues
   - next recommended actions

Deliverables:

A. Repository workflow map  
B. Files inspected  
C. Starter workflow changes made  
D. New or modified files  
E. Commands run and results  
F. Smoke-test campaign path  
G. Remaining risks or ambiguities  
H. Exact instructions for how I should use the tailored workflow next time

Be conservative, explicit, and provenance-first. The goal is not just to make scripts run; the goal is to make future analysis and report writing reproducible.
