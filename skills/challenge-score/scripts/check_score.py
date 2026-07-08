import json
import os
import secrets
import sys
from pathlib import Path
from urllib import error, request


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> int:
    root_dir = Path(__file__).resolve().parents[3]
    _load_env_file(root_dir / ".env")

    api_key = os.environ.get("FLP_CHALLENGE_API_KEY")
    if not api_key:
        print("FLP_CHALLENGE_API_KEY is not set", file=sys.stderr)
        return 1

    train_csv = os.environ.get(
        "FLP_CHALLENGE_TRAIN_CSV_PATH", "{data_dir}/os_train_data.csv"
    )
    test_csv = os.environ.get(
        "FLP_CHALLENGE_TEST_CSV_PATH", "{data_dir}/os_test_data.csv"
    )
    if Path(train_csv).name != "os_train_data.csv":
        print(
            "FLP_CHALLENGE_TRAIN_CSV_PATH must point to os_train_data.csv",
            file=sys.stderr,
        )
        return 1
    if Path(test_csv).name != "os_test_data.csv":
        print(
            "Warning: test data is not os_test_data.csv; "
            "this is not production-equivalent.",
            file=sys.stderr,
        )

    local_train_csv = (
        root_dir / "volumes/storage/flowprint-challenge/data/os_train_data.csv"
    )
    if not local_train_csv.exists() or local_train_csv.stat().st_size < 1_000_000:
        print(
            "os_train_data.csv is missing or is still an LFS pointer; "
            "run `git lfs pull`",
            file=sys.stderr,
        )
        return 1

    flowprint_src = root_dir / "src/flp_challenge/challenge/flowprint/src"
    training_file = flowprint_src / "train.py"
    submission_file = flowprint_src / "submissions.py"

    if not training_file.exists():
        print(f"Missing training file: {training_file}", file=sys.stderr)
        return 1
    if not submission_file.exists():
        print(f"Missing submission file: {submission_file}", file=sys.stderr)
        return 1

    try:
        training_content = training_file.read_text(encoding="utf-8")
        inference_content = submission_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read submission files: {exc}", file=sys.stderr)
        return 1

    payload = {
        "miner_input": {"random_val": secrets.token_hex(8)},
        "miner_output": {
            "commit_files": [
                {"file_name": "train.py", "content": training_content},
                {
                    "file_name": "submissions.py",
                    "content": inference_content,
                },
            ],
        },
    }

    port = os.environ.get("FLP_API_PORT", "10001")
    req = request.Request(
        f"http://localhost:{port}/score",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )

    try:
        training_timeout = float(
            os.environ.get("FLP_CHALLENGE_TRAINING_TIMEOUT_SECONDS", "600")
        )
        with request.urlopen(req, timeout=training_timeout + 300) as resp:  # nosec
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body or str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return 0

    if isinstance(data, dict) and "score" in data:
        print(data["score"])
        return 0
    if isinstance(data, (int, float)):
        print(data)
        return 0

    print(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
