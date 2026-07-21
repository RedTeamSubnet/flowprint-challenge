import os
from typing_extensions import Self

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    model_validator,
)
from pydantic_settings import SettingsConfigDict

from api.core.constants import ENV_PREFIX
from ._base import BaseConfig

_API_DIR_ENV = "FLP_API_DIR"
_DEFAULT_API_DIR = "/app/flowprint-challenge"


class FlowprintContainerConfig(BaseModel):
    network_name: str = Field(default="internal_net")
    image: str = Field(default="redteamsubnet61/flp_collector:latest")
    build_path: str = Field(
        default="{api_dir}/flowprint",
        description=(
            "Path to the flowprint build context. "
            "Use {api_dir} as a placeholder to expand against FLP_API_DIR."
        ),
    )

    @model_validator(mode="after")
    def _expand_paths(self) -> Self:
        api_dir = os.getenv(_API_DIR_ENV, _DEFAULT_API_DIR)
        if "{api_dir}" in self.build_path:
            self.build_path = self.build_path.format(api_dir=api_dir)
        return self


class ChallengeConfig(BaseConfig):
    api_key: SecretStr = Field(..., min_length=8, max_length=128)
    single_request_timeout: float = Field(default=0.1, ge=0)
    batch_request_size: int = Field(default=5000, ge=1)
    batch_request_timeout: float = Field(default=30.0, ge=0)
    acceptable_miss_count: int = Field(default=10, ge=0)
    flowprint_ip: str = Field(
        "127.0.0.1", strip_whitespace=True, min_length=7, max_length=15
    )
    flowprint_port: int = Field(default=8000, ge=1, le=65535)
    test_csv_path: str = Field(
        "{data_dir}/v1_test_data.csv",
        strip_whitespace=True,
        min_length=2,
        max_length=256,
    )
    train_csv_path: str = Field(
        "{data_dir}/v1_train_data.csv",
        strip_whitespace=True,
        min_length=2,
        max_length=256,
        description="Mandatory v1 CSV passed to the miner training script.",
    )
    training_timeout_seconds: float = Field(
        default=600,
        gt=0,
        description="Maximum seconds allowed for miner training.",
    )
    model_json_size_limit: int = Field(
        default=20 * 1024 * 1024,
        ge=1,
        description="Maximum generated model JSON size in bytes.",
    )
    submission_fns: list[str] = Field(
        default=["initializer", "metrics_collector", "linker"], min_items=1
    )
    submission_length_limit: int = Field(default=1000, ge=1)
    fp_container: FlowprintContainerConfig = Field(
        default_factory=FlowprintContainerConfig
    )
    model_config = SettingsConfigDict(env_prefix=f"{ENV_PREFIX}CHALLENGE_")

    @model_validator(mode="after")
    def _check_all(self) -> Self:
        DATA_DIR = os.getenv(
            f"{ENV_PREFIX}API_DATA_DIR", "/var/lib/flowprint-challenge"
        )
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

        if "{data_dir}" in self.test_csv_path:
            self.test_csv_path = self.test_csv_path.format(data_dir=DATA_DIR)

        elif not os.path.isdir(os.path.dirname(self.test_csv_path)):
            os.makedirs(os.path.dirname(self.test_csv_path), exist_ok=True)

        if "{data_dir}" in self.train_csv_path:
            self.train_csv_path = self.train_csv_path.format(data_dir=DATA_DIR)

        elif not os.path.isdir(os.path.dirname(self.train_csv_path)):
            os.makedirs(os.path.dirname(self.train_csv_path), exist_ok=True)

        if not os.access(os.path.dirname(self.test_csv_path), os.W_OK):
            raise ValueError(
                f"Directory for metrics CSV not writable: {os.path.dirname(self.test_csv_path)}"
            )

        if not os.access(os.path.dirname(self.train_csv_path), os.R_OK):
            raise ValueError(
                "Directory for training metrics CSV not readable: "
                f"{os.path.dirname(self.train_csv_path)}"
            )

        return self


__all__ = [
    "ChallengeConfig",
    "FlowprintContainerConfig",
]
