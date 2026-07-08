# Important Files

Use these files first when solving this challenge.

## Submission entry points

Both files are submitted in `miner_output.commit_files` using `file_name` and
`content`.

- `src/flr_challenge/challenge/flowradar/src/train.py`
    - receives the generated OS training CSV as `sys.argv[1]`.
    - writes model JSON to `sys.argv[2]`.
- `src/flr_challenge/challenge/flowradar/src/submissions.py`
    - contains `detect_os(features, model)` used for every replayed row.

## Runtime and API flow

- `src/flr_challenge/challenge/flowradar/src/app.py`
    - `/train` executes the mounted trainer inside the isolated container.
    - `/os_detector` request flow.
    - passes `products` and parsed model into `detect_os`.
- `src/flr_challenge/challenge/flowradar/src/data_types.py`
    - request/response schema for detector service.

## Scoring and dataset behavior

- `src/flr_challenge/challenge/api/endpoints/challenge/service.py`
    - starts the isolated container, calls `/train`, replays OS test rows, and
      computes final score.
- `src/flr_challenge/challenge/api/endpoints/challenge/payload_managers.py`
    - stores `predicted_os` / `expected_os`.
    - computes per-class precision, recall, F1, and macro F1.
- `src/flr_challenge/challenge/api/core/configs/_challenge.py`
    - challenge config: train/test paths, timeouts, model size, and submission
      limits.

## Local operations

- `skills/challenge-setup/SKILL.md`
    - setup/run/health checks and environment guidance.
- `skills/challenge-score/SKILL.md`
    - scoring flow and endpoint references.
- `skills/challenge-score/scripts/check_score.py`
    - quick local score command.

## Dataset location

- `volumes/storage/flowradar-challenge/data/flow_data_sampled_350k.csv`
    - source dataset. It has a `.csv` suffix but is Parquet.
- `volumes/storage/flowradar-challenge/data/os_train_data.csv`
    - recommended generated training CSV.
- `volumes/storage/flowradar-challenge/data/os_test_data.csv`
    - recommended generated scoring CSV.
