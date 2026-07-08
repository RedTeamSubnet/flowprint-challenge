---
name: challenge-score
description: Use for scoring current submission and inspecting score-related endpoints.
---

# Purpose

This skill provides a reliable way to score the current OS Classification
submission and quickly inspect score-related outputs.

# Quick Start

From challenge root:

```bash
python3 skills/challenge-score/scripts/check_score.py
```

What it does:

1. Loads `FLP_CHALLENGE_API_KEY` from root `.env` (if present).
2. Reads training and inference files from `src/flp_challenge/challenge/flowprint/src/train.py` and `submissions.py`.
3. Sends `POST http://localhost:10001/score` with `X-API-Key` header.
4. Prints score output (macro F1 expected from `0` to `1`).

# Important Files

- `skills/challenge-score/scripts/check_score.py` - local scoring helper script.
- `src/flp_challenge/challenge/api/endpoints/challenge/schemas.py` - `MinerOutput` and score telemetry schema.
- `src/flp_challenge/challenge/api/endpoints/challenge/router.py` - challenge endpoint definitions.
- `src/flp_challenge/challenge/flowprint/src/submissions.py` - current solver submission.

# Scoring System

The script builds payload using the challenge submission format:

```json
{
  "miner_input": {
    "random_val": "<random string>"
  },
  "miner_output": {
    "commit_files": [
      {
        "file_name": "train.py",
        "content": "<contents of train.py>"
      },
      {
        "file_name": "submissions.py",
        "content": "<contents of submissions.py>"
      }
    ]
  }
}
```

`MinerOutput` constraints (from schema):

- `commit_files` must contain exactly one `train.py` and one `submissions.py`.
- additional files, duplicate names, path-based names, and empty content are rejected.
- `train.py` is called as `python train.py <training_csv> <model_json>`.
- `submissions.py` must expose `detect_os(features, model)`.
- each file must respect the configured submission line limit.

Expected `/score` behavior:

- endpoint trains with the generated OS training CSV.
- endpoint scores provided `miner_output` by replaying the generated OS test CSV.
- endpoint removes `device_os` before inference.
- empty CSV cells are sent as JSON `null`.
- response is a score float in `[0, 1]`.

# Do / Don't

Do:

- keep training logic in `src/flp_challenge/challenge/flowprint/src/train.py`.
- keep inference logic in `src/flp_challenge/challenge/flowprint/src/submissions.py`.
- read the training CSV from `sys.argv[1]` and write JSON to `sys.argv[2]`.
- train only from the generated OS training CSV derived from the 350k source dataset.
- generate all learned weights during the current scoring run.
- score after every meaningful submission change.
- inspect telemetry/results when score changes unexpectedly.

Don't:

- send empty or partial script content.
- replace mandatory production training with v1 data.
- embed pretrained, serialized, encoded, or hard-coded learned weights in
  either submitted file.
- add fallback model weights to `submissions.py`; use only the generated
  `model` argument.
- move submission logic outside `submissions.py` without updating challenge config.
- assume stale score state; rerun scoring after edits.

# Helper Scripts

- `python3 skills/challenge-score/scripts/check_score.py`
    - reads `train.py` and `submissions.py`
    - reads `train.py` and `submissions.py`
    - calls `/score` with the configured OS train/test CSV paths
    - calls `/score`
    - allows the configured training timeout plus scoring time
    - prints score or raw error response

# Verification Steps

1. Ensure API server is running on `localhost:10001`.
2. Ensure root `.env` has `FLP_CHALLENGE_API_KEY`.
3. Ensure `FLP_CHALLENGE_TRAIN_CSV_PATH` points to `os_train_data.csv`.
4. Ensure `FLP_CHALLENGE_TEST_CSV_PATH` points to `os_test_data.csv`.
5. Convert `flow_data_sampled_350k.csv` from Parquet if the OS CSV files are missing.
6. Run script and confirm numeric output between `0` and `1`.
7. Optional: inspect `GET /telemetry` and `GET /results` for deeper validation.

# Troubleshooting

- Missing file error:
    - confirm both `train.py` and `submissions.py` exist.
    - confirm the generated OS train/test CSV files exist.
- Invalid JSON model:
    - confirm `train.py` writes valid JSON to its second argument.
- Fingerprint serialization error:
    - ensure inference handles missing features and JSON `null`.
- Auth failure:
    - confirm `FLP_CHALLENGE_API_KEY` value in root `.env`.
- Validation error:
    - compare payload to `MinerOutput` in `src/flp_challenge/challenge/api/endpoints/challenge/schemas.py`.
- Connection error:
    - verify local API is reachable at `http://localhost:10001`.
- Need detailed scoring breakdown:
    - inspect Docker container logs for challenge API/scorer service; logs include request errors and macro F1 details.

# Related Endpoints

From `src/flp_challenge/challenge/api/endpoints/challenge/router.py`:

- `GET /task` - returns current miner input (randomized string).
- `POST /score` - scores submission payload.
- `GET /status` - current scoring status.
- `GET /results` - stored prediction results.
- `GET /telemetry` - latest scoring telemetry (`request_id`, runtime, network bytes, score).

# Expected Success States

- scoring script exits with code `0`.
- output is a float score in `[0, 1]`.
- telemetry endpoint shows latest run metrics with a populated `score`.
