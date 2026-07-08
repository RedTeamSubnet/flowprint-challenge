from pydantic import BaseModel, Field


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


__all__ = [
    "OSDetectionInput",
    "OSDetectionOutput",
]
