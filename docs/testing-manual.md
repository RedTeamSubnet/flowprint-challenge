# Testing Manual

This guide covers local validation for the OS Classification challenge.

## Dataset Preparation

The source dataset is:

```text
volumes/storage/flowprint-challenge/data/flow_data_sampled_350k.csv
```

Despite the `.csv` suffix, it is Parquet. Convert it into real CSV train/test
files before running the platform scorer:

```python
import pandas as pd

src = "volumes/storage/flowprint-challenge/data/flow_data_sampled_350k.csv"
train_out = "volumes/storage/flowprint-challenge/data/os_train_data.csv"
test_out = "volumes/storage/flowprint-challenge/data/os_test_data.csv"

df = pd.read_parquet(src)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

split = int(len(df) * 0.8)
df.iloc[:split].to_csv(train_out, index=False)
df.iloc[split:].to_csv(test_out, index=False)
```

The label is `device_os`. Inference rows must not include `device_os`.

## Syntax Validation

```sh
python3 -m py_compile \
  src/flp_challenge/challenge/flowprint/src/train.py \
  src/flp_challenge/challenge/flowprint/src/submissions.py \
  src/flp_challenge/challenge/flowprint/src/app.py \
  src/flp_challenge/challenge/api/endpoints/challenge/payload_managers.py
```

## Training Smoke Test

```sh
python3 src/flp_challenge/challenge/flowprint/src/train.py \
  volumes/storage/flowprint-challenge/data/os_train_data.csv \
  /tmp/flowprint-os-model.json
```

Inspect the generated model:

```sh
python3 -m json.tool /tmp/flowprint-os-model.json | head -80
```

The model should include:

- `features`
- `classes`
- `class_total`
- `default_class`
- `counts`

## Inference Smoke Test

After training, import `submissions.py` directly and call `detect_os` with one
row from the generated test CSV:

```python
import csv
import importlib.util
import json

model = json.load(open("/tmp/flowprint-os-model.json"))

spec = importlib.util.spec_from_file_location(
    "submissions",
    "src/flp_challenge/challenge/flowprint/src/submissions.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with open("volumes/storage/flowprint-challenge/data/os_test_data.csv", newline="") as f:
    row = next(csv.DictReader(f))

row.pop("device_os", None)
print(mod.detect_os(row, model))
```

Expected result: one OS label string.

## Full Platform Score

Ensure the API server is running and the `.env` contains `FLP_CHALLENGE_API_KEY`.
Configure the OS CSV paths:

```sh
export FLP_CHALLENGE_TRAIN_CSV_PATH="{data_dir}/os_train_data.csv"
export FLP_CHALLENGE_TEST_CSV_PATH="{data_dir}/os_test_data.csv"
```

Then run:

```sh
python3 skills/challenge-score/scripts/check_score.py
```

Expected result: a macro F1 score from `0` to `1`.

## Troubleshooting

- Missing CSV files:
    - convert the 350k Parquet source into `os_train_data.csv` and
      `os_test_data.csv`.
- Invalid JSON model:
    - confirm `train.py` writes valid JSON to `sys.argv[2]`.
- Model too large:
    - reduce high-cardinality raw features, prune rare values, or summarize
      sequence-like columns.
- Request errors:
    - confirm `detect_os(features, model)` never throws and always returns a
      string.
- Score unexpectedly low:
    - inspect `/results` and score logs from `payload_managers.py`.
