import uuid

from fastapi import APIRouter

from api.schemas import AnalyzeQueuedResponse, AnalyzeRequest
from api.tasks import analyze_package_task
from storage.repository import upsert_scan_job

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeQueuedResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeQueuedResponse:
    normalized = payload.name.strip().lower()
    job_id = str(uuid.uuid4())
    upsert_scan_job(job_id, normalized, payload.registry, status="queued")
    analyze_package_task.apply_async(args=[normalized, payload.registry], task_id=job_id)
    return AnalyzeQueuedResponse(job_id=job_id, status="queued")
