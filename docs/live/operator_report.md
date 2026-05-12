# Live operator report

The operator report is a compact Markdown/HTML summary for meetings and reviews.  It is different from the full LaTeX research report: it focuses on status, trust, alerts, residuals, and bias correction.

Generate from one live run folder:

```bash
dmdc live-operator-report \
  --run-dir outputs/live_adaptation_replay \
  --outdir outputs/operator_report
```

Generate from a long-term archive:

```bash
dmdc live-operator-report \
  --archive-root live_archive \
  --window-label 60s \
  --outdir outputs/operator_archive_report
```

Outputs:

```text
live_operator_report.md
live_operator_report.html
live_operator_report_summary.json
```

The report is advisory only.  It does not control hardware and should not be treated as a safety-system output.
