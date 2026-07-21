from pydantic import BaseModel, Field, model_validator


class OSDetectionInput(BaseModel):
    products: dict = Field(
        ...,
        title="Products",
        description="Raw network flow features from CSV row.",
    )


class OSDetectionOutput(BaseModel):
    device_os: str = Field(
        ...,
        title="Device OS",
        description="The operating system detected from the flow.",
    )
    request_id: str = Field(
        ...,
        title="Request ID",
        description="Unique identifier for the request.",
    )


class BatchOSDetectionInput(BaseModel):
    products: list[dict] = Field(
        ...,
        title="Products",
        description="Raw network flow feature rows from CSV.",
    )
    request_ids: list[str] = Field(
        ...,
        title="Request IDs",
        description="Unique identifiers corresponding to each product row.",
    )

    @model_validator(mode="after")
    def _validate_request_ids(self):
        if len(self.products) != len(self.request_ids):
            raise ValueError("products and request_ids must have the same length")
        return self


class BatchOSDetectionOutput(BaseModel):
    results: list[OSDetectionOutput] = Field(
        ...,
        title="Results",
        description="Detected operating systems keyed by request ID.",
    )


__all__ = [
    "BatchOSDetectionInput",
    "BatchOSDetectionOutput",
    "OSDetectionInput",
    "OSDetectionOutput",
]
