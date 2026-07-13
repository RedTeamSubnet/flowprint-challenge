# Miner Commit - FlowPrint: OS Classification

This is a miner commit API example for FlowPrint: OS Classification.

## ✨ Features

- Miner commit
- Health check endpoint
- FastAPI
- Web service

---

## 🛠 Installation

### 1. 🚧 Prerequisites

- Install **Python (>= v3.10)** and **pip (>= 23)**:
    - **[RECOMMENDED] [Miniconda (v3)](https://www.anaconda.com/docs/getting-started/miniconda/install)**
    - *[arm64/aarch64] [Miniforge (v3)](https://github.com/conda-forge/miniforge)*
    - *[Python virtual environment] [venv](https://docs.python.org/3/library/venv.html)*

[OPTIONAL] For **DEVELOPMENT** environment:

- Install [**git**](https://git-scm.com/downloads)
- Setup an [**SSH key**](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

### 2. 📦 Install dependencies

```sh
pip install -r ./requirements.txt
```

### 3. 🏁 Start the server

```sh
cd src
uvicorn app:app --host="0.0.0.0" --port=10002 --no-access-log --no-server-header --proxy-headers --forwarded-allow-ips="*"

# For DEVELOPMENT:
uvicorn app:app --host="0.0.0.0" --port=10002 --no-access-log --no-server-header --proxy-headers --forwarded-allow-ips="*" --reload
```

### 4. ✅ Check server is running

Check with CLI (curl):

```sh
# Send a ping request with 'curl' to API server:
curl -s http://localhost:10002/ping
```

Check with web browser:

- Health check: <http://localhost:10002/health>
- Swagger: <http://localhost:10002/docs>
- Redoc: <http://localhost:10002/redoc>
- OpenAPI JSON: <http://localhost:10002/openapi.json>

### 5. 🧹 Format check before submission

Miner output contains exactly two commit files:

```json
{
  "commit_files": [
    {"file_name": "train.py", "content": "..."},
    {"file_name": "submissions.py", "content": "..."}
  ]
}
```

- `train.py` is called as `python train.py <training_csv> <model_json>`.
- `submissions.py` exposes `detect_os(features, model)`.

Pretrained or hard-coded learned weights are prohibited in both files.
`train.py` must generate the model from the provided v1 training CSV during the
current scoring run, and `submissions.py` must use only the generated `model`
argument.

Production always passes
`volumes/storage/flowprint-challenge/data/v1_train_data.csv` to the trainer.
Miners cannot choose a different training dataset. The label column is
`device_os`. Run `git lfs pull` if the dataset was not downloaded with the
repository.
The test dataset is private to the official scoring server and is not provided
to miners, including for local testing.
Each `/os_detector` request must complete within 100 milliseconds. More than 10
missed or timed-out requests stops scoring.


After finishing development, miners must check formatting for their submission files using Ruff. The validation pipeline runs:

```sh
ruff check --config=.ruff.toml --output-format=json --no-fix src/commit/submissions.py
ruff check --config=.ruff.toml --output-format=json --no-fix src/commit/train.py
```

> [!CAUTION]
> Miners should not use any type of bypass technique.

---

## 🏗️ Build Docker Image

To build the docker image, run the following command:

```sh
docker build -t myhub/rest-flp-commit:0.0.1 .

# For MacOS (Apple Silicon) to build AMD64:
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t myhub/rest-flp-commit:0.0.1 .
```
