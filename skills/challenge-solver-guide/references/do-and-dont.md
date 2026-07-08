# Do and Don't

## Do

- train from the generated OS training CSV derived from the 350k source dataset.
- use `device_os` as the label.
- remove `device_os` from inference features.
- use multiple passive fingerprinting signals instead of a single trigger.
- normalize inputs aggressively: safe casting, missing/null fallback, and stable
  categorical handling.
- keep the generated model JSON compact, valid, and deterministic.
- generate all learned weights during the current scoring run.
- keep training in `train.py` and inference in `submissions.py`.
- tune for the macro F1 and inspect OS predictions, not only training behavior.
- keep runtime predictable and lightweight to avoid request misses/timeouts.
- iterate with score feedback and telemetry/logs after each meaningful change.

## Don't

- do not use `device_os` as an input feature; it is the answer.
- do not train from the old VPN datasets.
- do not embed pretrained weights, encoded model blobs, or learned parameter
  tables in either submitted script.
- do not use fallback hard-coded weights in inference; use only the generated
  `model` argument.
- do not expect `device_os` inside inference features; scoring removes it.
- do not assume optional values are always present or non-null.
- do not rely only on the majority class; it weakens general OS prediction quality.
- do not throw exceptions on malformed input; return a safe prediction path.
- do not change production-parity scoring env values for final validation
  (`FLP_CHALLENGE_ACCEPTABLE_MISS_COUNT`, `FLP_CHALLENGE_SINGLE_REQUEST_TIMEOUT`).
