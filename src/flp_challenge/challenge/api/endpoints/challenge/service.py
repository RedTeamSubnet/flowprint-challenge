import os
import tempfile
import time

import pandas as pd
import requests
from pydantic import validate_call

from api.config import config
from api.logger import logger

from api.endpoints.challenge import _utils
from .schemas import MinerInput, MinerOutput
from .payload_managers import (
    payload_manager,
    scoring_status_manager,
    scoring_telemetry_manager,
    ScoringStatus,
)


def get_task() -> MinerInput:
    return MinerInput()


@validate_call
def score(request_id: str, miner_output: MinerOutput) -> float:
    if scoring_status_manager.get_scoring_status() == ScoringStatus.SCORING:
        raise RuntimeError("Scoring is already in progress")
    runtime_seconds = 0.0
    payload_manager.restart_manager()
    _request_miss_counter = 0
    container = None

    scoring_status_manager.set_scoring_status(ScoringStatus.SCORING)
    final_score = 0.0

    total_file_size = 0

    with tempfile.TemporaryDirectory() as tmp_dir:

        training_path = os.path.join(tmp_dir, "train.py")
        submission_path = os.path.join(tmp_dir, "submissions.py")
        with open(training_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(miner_output.get_file_content("train.py"))
        with open(submission_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(miner_output.get_file_content("submissions.py"))
        total_file_size += os.path.getsize(training_path)
        total_file_size += os.path.getsize(submission_path)

        logger.info(
            f"[{request_id}] - Total submission file size: {total_file_size} bytes"
        )

        try:
            total_runtime_start = time.perf_counter()
            training_start = time.perf_counter()
            logger.info(
                f"[{request_id}] - Starting model training with timeout "
                f"{config.challenge.training_timeout_seconds}s"
            )
            container, ip_address = _utils.run_flowprint_container(
                request_id=request_id,
                file_path=submission_path,
                training_path=training_path,
                training_csv_path=config.challenge.train_csv_path,
                flowprint_port=config.challenge.flowprint_port,
            )
            _utils.start_log_streaming_thread(container)

            config.challenge.flowprint_ip = ip_address
            logger.info(f"[{request_id}] - Detector container started at {ip_address}")

            _utils.wait_for_health(
                ip_address, flowprint_port=config.challenge.flowprint_port
            )
            logger.info(f"[{request_id}] - Detector container is healthy")

            base_url = f"http://{ip_address}:{config.challenge.flowprint_port}"
            training_response = requests.post(  # nosec
                f"{base_url}/train",
                timeout=config.challenge.training_timeout_seconds + 10,
            )
            training_response.raise_for_status()
            training_result = training_response.json()
            training_seconds = time.perf_counter() - training_start
            model_size = int(training_result["model_size_bytes"])
            if (
                training_result.get("status") != "trained"
                or model_size < 1
                or model_size > config.challenge.model_json_size_limit
            ):
                raise ValueError("Detector returned an invalid training result")
            total_file_size += model_size
            logger.info(
                f"[{request_id}] - Training completed in {training_seconds:.3f}s; "
                f"model size={model_size} bytes"
            )

            df = pd.read_csv(config.challenge.test_csv_path)
            runtime_start = time.perf_counter()

            label_column = next(
                (column for column in ("device_os",) if column in df.columns),
                None,
            )
            if label_column is None:
                raise ValueError("Scoring CSV must contain 'device_os'")
            ground_truth = df.pop(label_column)

            df = df.astype(object).where(pd.notna(df), None)
            records = df.to_dict("records")
            row_ids = [str(index) for index in df.index]
            expected_os_by_row = [str(ground_truth.loc[index]) for index in df.index]
            batch_size = config.challenge.batch_request_size
            total_batches = (len(records) + batch_size - 1) // batch_size

            logger.info(
                f"[{request_id}] - Starting fingerprinting process for {len(records)} rows "
                f"with batch size {batch_size}"
            )

            with requests.Session() as request_session:
                for batch_start in range(0, len(records), batch_size):
                    batch_end = min(batch_start + batch_size, len(records))
                    batch_number = (batch_start // batch_size) + 1
                    batch_records = records[batch_start:batch_end]
                    batch_row_ids = row_ids[batch_start:batch_end]
                    batch_expected_os = expected_os_by_row[batch_start:batch_end]
                    batch_request_ids = [
                        f"{request_id}:{row_id}" for row_id in batch_row_ids
                    ]
                    expected_request_ids = set(batch_request_ids)

                    logger.info(
                        f"[{request_id}] - Scoring batch "
                        f"{batch_number}/{total_batches} "
                        f"rows {batch_start}:{batch_end} "
                        f"({len(batch_records)} records)"
                    )

                    try:
                        resp = request_session.post(
                            f"{base_url}/os_detector/batch",
                            json={
                                "products": batch_records,
                                "request_ids": batch_request_ids,
                            },
                            timeout=config.challenge.batch_request_timeout,
                        )
                        resp.raise_for_status()
                        batch_result = resp.json()
                    except requests.RequestException as e:
                        _request_miss_counter += len(batch_records)
                        logger.error(
                            f"[{request_id}] - Error during fingerprint batch "
                            f"{batch_start}:{batch_end}: {str(e)}"
                        )
                        if (
                            _request_miss_counter
                            > config.challenge.acceptable_miss_count
                        ):
                            logger.error(
                                f"[{request_id}] - Exceeded max request misses. "
                                "Stopping fingerprinting."
                            )
                            return 0.0
                        continue

                    results = batch_result.get("results")
                    if not isinstance(results, list):
                        _request_miss_counter += len(batch_records)
                        logger.error(
                            f"[{request_id}] - Invalid fingerprint batch response "
                            f"for rows {batch_start}:{batch_end}"
                        )
                        if (
                            _request_miss_counter
                            > config.challenge.acceptable_miss_count
                        ):
                            logger.error(
                                f"[{request_id}] - Exceeded max request misses. "
                                "Stopping fingerprinting."
                            )
                            return 0.0
                        continue

                    results_by_request_id = {}
                    duplicate_request_ids = set()
                    for result in results:
                        if not isinstance(result, dict):
                            _request_miss_counter += 1
                            continue

                        result_request_id = result.get("request_id")
                        if result_request_id not in expected_request_ids:
                            _request_miss_counter += 1
                            logger.warning(
                                f"[{request_id}] - Ignoring unknown fingerprint "
                                f"request_id={result_request_id}"
                            )
                            continue

                        if result_request_id in results_by_request_id:
                            duplicate_request_ids.add(result_request_id)
                            logger.warning(
                                f"[{request_id}] - Ignoring duplicate fingerprint "
                                f"request_id={result_request_id}"
                            )
                            continue

                        results_by_request_id[result_request_id] = result

                    if (
                        _request_miss_counter
                        > config.challenge.acceptable_miss_count
                    ):
                        logger.error(
                            f"[{request_id}] - Exceeded max request misses. "
                            "Stopping fingerprinting."
                        )
                        return 0.0

                    for row_id, expected_os, batch_request_id in zip(
                        batch_row_ids,
                        batch_expected_os,
                        batch_request_ids,
                        strict=True,
                    ):
                        result = results_by_request_id.get(batch_request_id)
                        device_os = None if result is None else result.get("device_os")

                        logger.debug(
                            f"[{request_id}] - Row {row_id}: device_os={device_os}, "
                            f"expected={expected_os}"
                        )

                        if result is None or batch_request_id in duplicate_request_ids:
                            _request_miss_counter += 1
                            logger.warning(
                                f"[{request_id}] - Missing valid fingerprint result "
                                f"for row {row_id}"
                            )
                        elif device_os is not None:
                            payload_manager.store_payload(
                                row_id=row_id,
                                predicted_os=str(device_os),
                                expected_os=expected_os,
                                request_id=batch_request_id,
                            )
                        else:
                            _request_miss_counter += 1
                            logger.warning(
                                f"[{request_id}] - No device_os returned for row {row_id}"
                            )

                        if (
                            _request_miss_counter
                            > config.challenge.acceptable_miss_count
                        ):
                            logger.error(
                                f"[{request_id}] - Exceeded max request misses. "
                                "Stopping fingerprinting."
                            )
                            return 0.0

            fingerprint_seconds = time.perf_counter() - runtime_start
            runtime_seconds = time.perf_counter() - total_runtime_start

            logger.info(
                f"[{request_id}] - Fingerprinting completed in {fingerprint_seconds:.3f}s. "
                f"Stored {payload_manager.payload_count()} fingerprints."
            )

            final_score = payload_manager.calculate_score()
            logger.success(f"[{request_id}] - Final Score: {final_score:.3f}")

        finally:

            network_stats = _utils.ContainerStatsResult()
            if container is not None:
                network_stats = _utils.get_container_network_stats(container)

            scoring_telemetry_manager.set_telemetry(
                request_id=request_id,
                total_file_size_bytes=total_file_size,
                runtime_seconds=round(runtime_seconds, 3),
                network_rx_bytes=network_stats.network_rx_bytes,
                network_tx_bytes=network_stats.network_tx_bytes,
                score=final_score,
            )

            if container:
                _utils.cleanup_container(container)
                logger.info(f"[{request_id}] - Detector container cleaned up")
            scoring_status_manager.set_scoring_status(ScoringStatus.AVAILABLE)

    return final_score


__all__ = [
    "get_task",
    "score",
]
