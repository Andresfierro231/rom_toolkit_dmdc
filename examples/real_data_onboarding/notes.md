# Real Data Onboarding Notes

Use this file as your lab notebook while connecting real data.

## Before Step 1: raw data inventory

Record:

```text
Raw path:
File type:
Approximate size:
Number of files:
Expected time column:
Expected case/run column:
Expected sensor columns:
Expected input/control columns:
Units:
Known failed runs:
Known short runs:
```

## After Step 1: import

Check:

```text
Did the importer produce data/processed/simple_loop_canonical.parquet or .csv?
Did import_metadata.json list the expected number of rows?
Did columns_summary.csv contain all canonical columns?
Were any expected columns missing after column mapping?
Did case_id get created correctly from filenames, if needed?
```

## After Step 2: inspection

Open:

```text
outputs/real_data_onboarding/inspection/warnings.txt
outputs/real_data_onboarding/inspection/dt_summary_by_case.csv
outputs/real_data_onboarding/inspection/case_lengths.csv
outputs/real_data_onboarding/inspection/missing_values.csv
```

Decide:

```text
Are time steps nonuniform/adaptive? Usually yes.
Do I need to filter out startup or failed tails?
Do I need to remove short/failed cases?
Do I need to fix units or column names?
Do I need to update [split] train/test case lists?
```

## After Step 3: adaptive-fit

Check:

```text
Does adaptive_fit diagnostics show reasonable residuals?
Does continuous/adaptive model behave better than sample-to-sample DMDc?
Are eigenvalues/stability warnings present?
```

## After Step 4: POD-DMDc

Check:

```text
How many POD modes were retained?
Does cumulative energy look reasonable?
Do reconstructed states match the original states?
Does POD-DMDc reduce noise or lose important dynamics?
```

## After Step 5: compare

Check:

```text
Which model has the best test rollout RMSE?
Which model is stable?
Is the generalization gap large?
Does adaptive_dmdc outperform sample-index DMDc for nonuniform data?
Do baselines perform surprisingly well?
```

## After Step 6: validation

Check:

```text
Are test cases truly unseen operating conditions?
Are test cases inside the training operating envelope?
Which states have the highest error?
Does forecast error grow with horizon?
```

## After Step 7/8: live replay

Check:

```text
Does live replay run without timestamp or buffer warnings?
Are alerts dominated by a few sensors?
Does bias correction reduce residuals or mask a real model issue?
Are trust scores meaningful?
```

## After Step 9/10: dashboard and operator report

Check:

```text
Can someone understand the system status in 30 seconds?
Are the worst residuals and alerts visible?
Is the model provenance visible?
Can you explain what the trust score means?
Are bias-correction updates auditable?
```

## Open TODOs discovered on real data

- [ ] TODO: record issue here
- [ ] TODO: record issue here
- [ ] TODO: record issue here
