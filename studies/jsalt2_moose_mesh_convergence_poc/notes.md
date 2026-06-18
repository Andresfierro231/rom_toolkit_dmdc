# JSALT2 POC Notes

Use this file as the runbook for the external-data proof-of-concept.

## Data source

Record:

```text
External source root:
Expected case naming pattern:
Expected state columns:
Expected input columns:
Known reference run:
Known bad or short cases:
```

## After import

Check:

```text
Did `case_id` come from filenames as expected?
Did `columns_summary.csv` contain TP1, TP2, TP3, TP6, massFlowRate, and h?
Did import sidecars confirm eleven files for the current maintained collection?
Did any source-file warnings appear?
```

## After inspection

Open:

```text
outputs/jsalt2_moose_mesh_convergence_poc/inspection/warnings.txt
outputs/jsalt2_moose_mesh_convergence_poc/inspection/dt_summary_by_case.csv
outputs/jsalt2_moose_mesh_convergence_poc/inspection/case_lengths.csv
```

Decide:

```text
Is `dt` materially nonuniform across cases?
Is `h` constant enough that DMDc control input is not meaningful?
Do any cases need to be excluded before the full pass?
Should the full pass keep `input_cols = ["h"]` or switch to `[]`?
```

## After POD-DMDc

Check:

```text
How many modes were retained?
Do the retained-energy and reconstruction plots look reasonable?
Are there stability warnings or obvious mode-collapse issues?
```

## After compare/report

Check:

```text
How does plain DMDc compare against POD-DMDc on held-out cases?
Do the baselines remain surprisingly competitive?
Did the report write `report/report.tex` under the compare outdir?
Does the campaign plan reflect the exact commands and output folders used?
```

## Provenance checklist

- Record the exact external source path.
- Record the exact `dmdc campaign` command used.
- Record whether the run was smoke-only or full-pass.
- Record whether `h` stayed in `input_cols`.
- Record the campaign plan, step index, and compare report paths.
