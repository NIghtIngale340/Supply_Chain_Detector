from api.analysis_service import run_analysis_for_package
from api.celery_app import celery_app


@celery_app.task(name="analyze.package")
def analyze_package_task(name: str, registry: str) -> dict:
    return run_analysis_for_package(name, registry)
