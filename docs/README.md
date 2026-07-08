# OS Classification Docs

This documentation describes the OS Classification challenge flow.

The platform now asks miners to:

1. Train a model from an OS training CSV generated from the 350k source dataset.
2. Score an OS test CSV with the temporary model inside the detector container.
3. Return a `device_os` prediction for each replayed row.
4. Receive a macro F1 score for OS predictions.

## Primary Dataset

| Path | Purpose |
| --- | --- |
| `volumes/storage/flowradar-challenge/data/flow_data_sampled_350k.csv` | Source OS dataset. Despite the suffix, this file is Parquet. |
| `volumes/storage/flowradar-challenge/data/os_train_data.csv` | Recommended generated training CSV. |
| `volumes/storage/flowradar-challenge/data/os_test_data.csv` | Recommended generated scoring CSV. |

The label column is `device_os`. All other columns are inference features.

## Main Contract

Submitted files:

- `train.py`
    - called as `python train.py <training_csv> <model_json>`
    - reads the generated OS training CSV
    - writes valid JSON to `<model_json>`
- `submissions.py`
    - exposes `detect_os(features, model) -> str`
    - returns an OS label string for one row

## Runtime Flow

1. `/score` receives `train.py` and `submissions.py`.
2. The scorer starts an isolated FlowRadar detector container.
3. The detector runs `POST /train`.
4. The scorer replays the OS test CSV through `POST /os_detector`.
5. The scorer compares returned `device_os` values against hidden labels.
6. The final score is the macro F1 score.

## Useful Docs

- `docs/DOCUMENTATION.md` - OS fingerprinting background and feature notes.
- `docs/testing-manual.md` - local validation commands.
- `docs/miner-v2-submission.md` - miner submission format, retained under its
  historical filename.
