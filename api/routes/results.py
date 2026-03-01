from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from api.celery_app import celery_app
from api.schemas import ResultResponse
from storage.repository import get_recent_scans, get_scan_job

router = APIRouter(tags=["results"])


@router.get("/results/recent")
def get_recent_results(limit: int = 20) -> dict:
    bounded_limit = max(1, min(limit, 100))
    return {"items": get_recent_scans(limit=bounded_limit)}


@router.get("/results/{job_id}", response_model=ResultResponse)
def get_results(job_id: str) -> ResultResponse:
    stored = get_scan_job(job_id)
    result = AsyncResult(job_id, app=celery_app)

    if result.state in {"PENDING", "RECEIVED", "STARTED", "RETRY"}:
        if stored and stored.get("status") == "completed" and stored.get("result_json"):
            return ResultResponse(job_id=job_id, status="completed", result=stored["result_json"])
        if stored and stored.get("status") == "failed":
            raise HTTPException(status_code=500, detail=stored.get("error_message") or "Task failed")
        if not stored and result.state == "PENDING":
            raise HTTPException(status_code=404, detail="Job not found")
        return ResultResponse(job_id=job_id, status="pending")

    if result.state == "FAILURE":
        if stored and stored.get("error_message"):
            raise HTTPException(status_code=500, detail=stored["error_message"])
        raise HTTPException(status_code=500, detail=str(result.result))

    return ResultResponse(job_id=job_id, status="completed", result=result.result)
