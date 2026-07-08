from api.logger import logger
from enum import Enum
from dataclasses import dataclass


@dataclass
class ScoringTelemetry:
    request_id: str | None = None
    total_file_size_bytes: int = 0
    runtime_seconds: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    score: float | None = None


class ScoringTelemetryManager:
    def __init__(self):
        self._latest: ScoringTelemetry = ScoringTelemetry()

    def set_telemetry(
        self,
        request_id: str | None = None,
        total_file_size_bytes: int = 0,
        runtime_seconds: float = 0.0,
        network_rx_bytes: int = 0,
        network_tx_bytes: int = 0,
        score: float | None = None,
    ) -> None:
        self._latest = ScoringTelemetry(
            request_id=request_id,
            total_file_size_bytes=total_file_size_bytes,
            runtime_seconds=runtime_seconds,
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            score=score,
        )
        logger.info(
            f"[Telemetry] Recorded: runtime={runtime_seconds:.2f}s, "
            f"net_rx={network_rx_bytes}, net_tx={network_tx_bytes}"
        )

    def get_telemetry(self) -> ScoringTelemetry:
        return self._latest

    def reset(self) -> None:
        self._latest = ScoringTelemetry()


class PayloadManager:
    def __init__(self):
        self.payloads: list[dict] = []
        self.feedback: dict = {"classes": {}, "macro_f1": 0.0}

    def restart_manager(self) -> None:
        self.payloads = []
        self.feedback = {"classes": {}, "macro_f1": 0.0}

    def store_payload(
        self, row_id: str, predicted_os: str, expected_os: str, request_id: str = None
    ) -> None:
        self.payloads.append(
            {
                "row_id": row_id,
                "predicted_os": predicted_os,
                "expected_os": expected_os,
                "request_id": request_id,
            }
        )

    def get_payload(self) -> list[dict]:
        return self.payloads

    def get_feedback(self) -> dict:
        return self.feedback

    def get_payload_with_feedback(self) -> dict:
        return {"payload": self.payloads, "feedback": self.get_feedback()}

    def payload_count(self) -> int:
        return len(self.payloads)

    def calculate_score(self) -> float:
        if not self.payloads:
            logger.warning("No payloads to score")
            self.feedback = {"classes": {}, "macro_f1": 0.0}
            return 0.0

        labels = sorted(
            {payload["expected_os"] for payload in self.payloads}
            | {payload["predicted_os"] for payload in self.payloads}
        )
        class_feedback = {}
        f1_scores = []

        for label in labels:
            tp = fp = fn = 0
            for payload in self.payloads:
                predicted = payload["predicted_os"]
                expected = payload["expected_os"]
                if predicted == label and expected == label:
                    tp += 1
                elif predicted == label and expected != label:
                    fp += 1
                elif predicted != label and expected == label:
                    fn += 1

            precision = tp / (tp + fp) if tp + fp > 0 else 0.0
            recall = tp / (tp + fn) if tp + fn > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall > 0
                else 0.0
            )
            f1_scores.append(f1)
            class_feedback[label] = {
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3),
                "support": sum(
                    1 for payload in self.payloads if payload["expected_os"] == label
                ),
            }

            metrics = class_feedback[label]
            logger.info(
                f"Class {label}: precision={metrics['precision']:.3f}, "
                f"recall={metrics['recall']:.3f}, f1={metrics['f1']:.3f}"
            )

        macro_f1 = round(sum(f1_scores) / len(f1_scores), 3) if f1_scores else 0.0
        self.feedback = {"classes": class_feedback, "macro_f1": macro_f1}

        logger.info(
            f"Total predictions: {len(self.payloads)}, "
            f"classes={len(labels)}, macro_f1={macro_f1:.3f}"
        )

        return macro_f1


class ScoringStatus(str, Enum):
    STARTED = "started"
    SCORING = "scoring"
    AVAILABLE = "available"


class ScoringStatusManager:
    def __init__(self):
        self._scoring_status = ScoringStatus.STARTED

    def get_scoring_status(self) -> ScoringStatus:
        return self._scoring_status

    def set_scoring_status(self, status: ScoringStatus) -> None:
        self._scoring_status = status


payload_manager = PayloadManager()
scoring_status_manager = ScoringStatusManager()
scoring_telemetry_manager = ScoringTelemetryManager()

__all__ = [
    "PayloadManager",
    "payload_manager",
    "ScoringStatusManager",
    "scoring_status_manager",
    "ScoringTelemetry",
    "ScoringTelemetryManager",
    "scoring_telemetry_manager",
]
