import logging
import uuid

from api.analysis_service import run_analysis_for_package
from api.celery_app import celery_app
from storage.repository import mark_scan_failed, upsert_scan_job

logger = logging.getLogger(__name__)


@celery_app.task(
    name="analyze.package",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=120,
    max_retries=2,
)
def analyze_package_task(self, name: str, registry: str) -> dict:
    task_id = getattr(self.request, "id", None) or str(uuid.uuid4())
    upsert_scan_job(task_id, name, registry, status="running")
    try:
        return run_analysis_for_package(name, registry, job_id=task_id)
    except Exception as exc:
        logger.exception("Task %s failed for %s/%s", task_id, registry, name)
        mark_scan_failed(task_id, name, registry, str(exc))
        raise
