# Config Cheat Sheet

Use TOML configs to avoid long commands.

Minimum validation config:

```toml
[data]
path = "data.csv"
time_col = "time"
case_col = "case_id"
state_cols = ["TP1", "TP2", "massFlowRate"]
input_cols = ["q_heater", "T_amb"]

[split]
train_cases = ["case_001", "case_002"]
test_cases = ["case_003"]

[pod]
rank = 0.999
center = true
scale = false

[model]
dmdc_rank = "full"

[output]
outdir = "outputs/my_study"
plots = true
```

Useful templates live in `configs/templates/`.
