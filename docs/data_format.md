# Data Format Guide

## Required concept

DMDc needs rows ordered in time. Each row is one sample.

You must identify:

- state columns: variables making up `x_k`
- input columns: variables making up `u_k`
- optional time column
- optional case/group column

## Example thermal-hydraulic dataset

```csv
time,case_id,TP1,TP2,TP3,TP4,massFlowRate,heater_power,inlet_temperature
0.0,salt_test_1,450,451,452,453,0.10,37.0,440
1.0,salt_test_1,450.5,451.4,452.2,453.1,0.11,37.0,440
2.0,salt_test_1,451.0,451.9,452.6,453.4,0.11,40.0,440
```

Fit example:

```bash
dmdc fit \
  --data data/salt_test.csv \
  --state-cols TP1 TP2 TP3 TP4 massFlowRate \
  --input-cols heater_power inlet_temperature \
  --time-col time \
  --case-col case_id \
  --case-id salt_test_1 \
  --rank 0.999 \
  --scale \
  --outdir outputs/salt_test_1 \
  --plots
```

## Handling multiple cases

The current CLI fits one trajectory at a time. For multiple experiments, filter using `--case-col` and `--case-id`, or write a Python loop over case IDs.

Future extension: block-stacked multi-trajectory DMDc, where each case contributes transitions but rollouts are not forced to cross case boundaries.
