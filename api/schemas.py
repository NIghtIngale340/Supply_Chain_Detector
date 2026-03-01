from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    name: str = Field(min_length=1)
    registry: Literal["pypi", "npm"]


class AnalyzeQueuedResponse(BaseModel):
    job_id: str
    status: Literal["queued"]


class ResultResponse(BaseModel):
    job_id: str
    status: Literal["pending", "completed"]
    result: dict[str, Any] | None = None
