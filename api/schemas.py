from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    name: str = Field(min_length=1)
    registry: str = Field(pattern="^(pypi|npm)$")


class AnalyzeQueuedResponse(BaseModel):
    job_id: str
    status: str


class ResultResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None = None
