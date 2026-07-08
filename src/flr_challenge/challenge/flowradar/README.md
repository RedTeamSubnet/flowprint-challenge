# OS Classification

Passive operating-system classification API using network flow features.

## Overview

This project provides the isolated detector and training container used by the
FlowRadar scoring API. Miners submit one training script and one inference
script. Training runs inside this container against a generated CSV split from
the 350k FlowRadar OS dataset.

The source dataset is stored at:

```text
volumes/storage/flowradar-challenge/data/flow_data_sampled_350k.csv
```

The file has a `.csv` suffix but is Parquet. Convert it to real train/test CSV
files before scoring. The target column is `device_os`; every other column is an
inference feature.

## Architecture

- **Training Logic**: `train.py` receives the training CSV and writes model JSON
- **Detection Logic**: `submissions.py` exposes `detect_os(features, model)`
- **Model Loading**: `POST /train` loads the generated `/tmp/model.json`
- **API**: FastAPI for serving OS classification requests

## Key Components

| File             | Description                                            |
| ---------------- | ------------------------------------------------------ |
| `train.py`       | Training script that writes a model JSON               |
| `submissions.py` | OS detector exposing `detect_os(features, model)`      |
| `app.py`         | FastAPI application and endpoints                      |
| `data_types.py`  | Pydantic models for OS classification input/output     |

## Miner Contract

Training is called as:

```sh
python train.py /path/to/os_train_data.csv /tmp/model.json
```

The inference script must define:

```python
def detect_os(features: dict, model: dict) -> str:
    ...
```

The returned string must be one of the supported OS labels, such as `Android`,
`iOS`, `Windows`, `Linux`, `Chromium OS`, or `Mac OS`.

The challenge enforces `FLR_CHALLENGE_TRAINING_TIMEOUT_SECONDS`, defaulting to
`600` seconds. The generated model JSON remains temporary inside this container
for the current scoring run.

Pretrained or embedded learned weights are prohibited in `train.py` and
`submissions.py`. Training must generate the model from the provided OS training
CSV during the current run, and inference may only use the loaded generated
model.

## API Endpoints

### GET /health

Health check endpoint.

### POST /train

Run the mounted training script inside the container, validate its model JSON,
and load that model for detection.

### POST /os_detector

Predict the operating system from network flow features and the trained model.

**Request:**

```json
{
  "products": {
    "flow_duration": 1504,
    "fwd_num_pkts": 11,
    "bwd_num_pkts": 10,
    "tcp_window_size_syn": 64240,
    "tcp_options_ordered_syn": "MSS,NOP,WS,NOP,NOP,SACK"
  }
}
```

**Response:**

```json
{
  "device_os": "Windows",
  "request_id": "abc123..."
}
```
