from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException

from api.schemas import AnalyzeQueuedResponse, AnalyzeRequest, ResultResponse
from api.tasks import analyze_package_task


app = FastAPI(title="Supply Chain Detector API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeQueuedResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeQueuedResponse:
    job = analyze_package_task.delay(payload.name.strip().lower(), payload.registry)
    return AnalyzeQueuedResponse(job_id=job.id, status="queued")


@app.get("/results/{job_id}", response_model=ResultResponse)
def get_results(job_id: str) -> ResultResponse:
    result = AsyncResult(job_id)

    if result.state in {"PENDING", "RECEIVED", "STARTED", "RETRY"}:
        return ResultResponse(job_id=job_id, status="pending")

    if result.state == "FAILURE":
        raise HTTPException(status_code=500, detail=str(result.result))

    return ResultResponse(job_id=job_id, status="completed", result=result.result)
