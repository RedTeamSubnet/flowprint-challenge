# Miner Submission Format

This file keeps its historical name, but the current challenge is OS
classification.

## Submitted Files

`miner_output.commit_files` must contain exactly two files:

- `train.py`
- `submissions.py`

Example payload shape:

```json
{
  "miner_output": {
    "commit_files": [
      {
        "file_name": "train.py",
        "content": "..."
      },
      {
        "file_name": "submissions.py",
        "content": "..."
      }
    ]
  }
}
```

## Training Contract

`train.py` is called as:

```sh
python train.py <training_csv> <model_json>
```

It must:

- read the generated OS training CSV from `sys.argv[1]`
- use `device_os` as the label
- write valid JSON to `sys.argv[2]`
- generate all learned weights during the current scoring run

## Inference Contract

`submissions.py` must expose:

```python
def detect_os(features: dict, model: dict) -> str:
    ...
```

The `features` argument contains one row from the generated OS test CSV after
the scorer removes `device_os`. Empty CSV cells may arrive as JSON `null`.

The return value must be an OS label string, for example:

- `Android`
- `iOS`
- `Windows`
- `Linux`
- `Chromium OS`
- `Mac OS`

## Dataset

The source dataset is:

```text
volumes/storage/flowradar-challenge/data/flow_data_sampled_350k.csv
```

This file is Parquet despite the `.csv` suffix. Convert it into real CSV files
before scoring:

```text
volumes/storage/flowradar-challenge/data/os_train_data.csv
volumes/storage/flowradar-challenge/data/os_test_data.csv
```

Set:

```sh
FLR_CHALLENGE_TRAIN_CSV_PATH="{data_dir}/os_train_data.csv"
FLR_CHALLENGE_TEST_CSV_PATH="{data_dir}/os_test_data.csv"
```

## Scoring

The platform replays the OS test CSV through `/os_detector`, stores
`predicted_os` and `expected_os`, then returns multiclass macro F1.

## Prohibited

- pretrained, embedded, serialized, or encoded learned weights in either file
- fallback embedded model state in `submissions.py`
- using `device_os` as an inference feature
- reading any dataset path directly from `submissions.py`
