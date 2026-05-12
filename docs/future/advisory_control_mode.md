# Future Advisory Control Mode

The live ROM toolkit is currently **read-only and advisory**. It can ingest data,
estimate state, forecast, monitor residuals, track bias correction, archive data,
and display dashboards. It does not actuate hardware.

A future advisory-control mode could suggest actions such as:

```text
TP6 is forecast to exceed the operator threshold in 60 s.
Suggested advisory action: reduce heater power by 5 W and continue monitoring.
```

This future feature should remain separate from direct control and should include:

- explicit operator acknowledgement,
- hard safety interlocks outside this repo,
- uncertainty-aware recommendations,
- full audit logging,
- independent validation before any experiment.

This is documented as a future direction, not an active implementation target for
the current local-workstation live monitoring workflow.
