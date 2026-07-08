---
name: challenge-solver-guide
description: Use for designing and implementing high-score OS classification submissions for this challenge.
---

# Purpose

Guide agents to solve the FlowRadar challenge with robust passive OS
fingerprinting logic.

Primary objective:

- maximize the macro F1 score across replayed OS predictions.

# Quick Start

1. Convert the 350k Parquet source file into OS train/test CSVs.
2. Set up and run challenge services:
   - `./skills/challenge-setup/scripts/setup.sh`
   - `./skills/challenge-setup/scripts/healthcheck.sh`
3. Implement the two submission scripts:
   - `src/flr_challenge/challenge/flowradar/src/train.py`
   - `src/flr_challenge/challenge/flowradar/src/submissions.py`
4. Score after each meaningful iteration:
   - `python3 skills/challenge-score/scripts/check_score.py`
5. Inspect diagnostics:
   - `GET /telemetry`, `GET /results`, and container logs.

# Important Files

See full map in:

- `skills/challenge-solver-guide/references/important-files.md`

Core challenge data/input locations:

- source dataset: `volumes/storage/flowradar-challenge/data/flow_data_sampled_350k.csv`
- recommended training CSV: `volumes/storage/flowradar-challenge/data/os_train_data.csv`
- recommended scoring CSV: `volumes/storage/flowradar-challenge/data/os_test_data.csv`
- trainer: `src/flr_challenge/challenge/flowradar/src/train.py`
- inference: `src/flr_challenge/challenge/flowradar/src/submissions.py`

The source dataset has a `.csv` suffix but is Parquet. The generated train/test
files must be real CSV files because the platform trainer and scorer read CSV.

# Architecture Overview

High-level pipeline:

1. Challenge API `/score` receives both files through
   `miner_output.commit_files`.
2. API starts an isolated FlowRadar container with both scripts and the OS
   training CSV mounted read-only.
3. `POST /train` runs `train.py` and loads its temporary JSON model.
4. OS test rows are replayed through `/os_detector`.
5. `detect_os(features, model)` returns an OS label string.
6. API computes the final macro F1 score.

Implementation implication:

- strong solutions combine passive fingerprinting signals and robust handling of
  noisy or missing values.

# Scoring System

Current scoring logic (`payload_managers.py`):

- tracks `predicted_os` and `expected_os` for each replayed row.
- computes per-class precision, recall, and F1.
- returns macro F1 rounded to 3 decimals.

Hard failure behavior:

- if misses exceed `FLR_CHALLENGE_ACCEPTABLE_MISS_COUNT`, scoring stops early.
- excessive misses/timeouts reduce the number of scored rows and usually hurt
  macro F1.

# Solver Workflow

1. Baseline
   - run current score and capture telemetry.
2. Training strategy
   - learn only from the generated OS training CSV.
   - keep the serialized JSON model compact and deterministic.
   - generate all learned weights during the current scoring run.
3. Feature strategy
   - use OS fingerprinting signals such as TTL, TCP SYN option order, window
     size, MSS, SACK, timestamps, and JA4 hashes.
   - define safe normalization/casting for every used key.
4. Decision strategy
   - combine multiple feature likelihoods or scores.
   - avoid one-feature hard dependence.
5. Iterate
   - run scoring, inspect the macro F1, and improve weak predictions.
6. Harden
   - ensure logic handles missing fields and unexpected values gracefully.

# Investigation Priorities

1. Feature extraction quality in `submissions.py`
   - robust parsing, missing/null fallback, and stable categorical handling.
2. Model construction quality in `train.py`
   - use `device_os` as the label.
   - produce valid JSON within the configured limit.
3. Signal design
   - TTL buckets, TCP options order, TCP window/MSS defaults, TLS JA4 hashes,
     and aggregate flow timing/length metrics.
4. Class imbalance
   - monitor predicted labels so the model does not collapse to one OS class.
5. Failure resilience
   - never throw for malformed payloads; fallback to a model-derived default.

# Do / Don't

See:

- `skills/challenge-solver-guide/references/do-and-dont.md`

# Helper Scripts

- Setup:
    - `./skills/challenge-setup/scripts/setup.sh`
    - `./skills/challenge-setup/scripts/healthcheck.sh`
- Score:
    - `python3 skills/challenge-score/scripts/check_score.py`

# Verification Steps

1. Run scoring script and record the macro F1 score in `[0, 1]`.
2. Check `GET /telemetry` for runtime, network usage, and reported score.
3. Check `GET /results` to inspect prediction vs expected OS behavior.
4. Review container logs when behavior is unexpected.
5. Repeat after each strategic change and compare score deltas.

# Troubleshooting

- Score remains near zero:
    - inspect the macro F1 and confirm predictions are valid OS labels.
- Training fails:
    - confirm `train.py` reads `sys.argv[1]`, writes `sys.argv[2]`, and handles
      `device_os`.
- Model JSON exceeds the size limit:
    - reduce high-cardinality raw features, prune rare values, or summarize
      sequence/list-like fields.
- Many request errors/timeouts:
    - simplify expensive logic and keep runtime predictable.
- No meaningful improvement after changes:
    - revisit feature combinations and class imbalance handling.

# Example Requests

- "Analyze current `detect_os` logic and propose a macro-F1 improvement plan."
- "Implement robust feature normalization for OS fingerprinting fields."
- "Refactor detection logic to combine TTL, TCP options, and JA4 evidence."
- "Run score, inspect telemetry, and explain the weakest OS classes."

# Expected Success States

- the macro F1 is consistently non-zero and trending upward across iterations.
- misses stay below `FLR_CHALLENGE_ACCEPTABLE_MISS_COUNT`.
- inference handles feature noise without frequent invalid predictions.
