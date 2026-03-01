from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select

from storage.database import init_database, session_scope
from storage.models import ScanJob


def upsert_scan_job(job_id: str, package_name: str, registry: str, status: str, payload: dict[str, Any] | None = None) -> None:
    init_database()
    with session_scope() as session:
        existing = session.scalar(select(ScanJob).where(ScanJob.job_id == job_id))
        if existing is None:
            existing = ScanJob(job_id=job_id, package_name=package_name, registry=registry)
            session.add(existing)

        existing.status = status
        if payload is not None:
            existing.result_json = payload
            existing.final_score = float(payload.get("final_score", 0.0))
            layers = payload.get("layers", {})
            existing.metadata_score = float(layers.get("layer1_metadata", {}).get("final_score", 0.0))
            existing.embedding_score = float(layers.get("layer2_embeddings", {}).get("risk_score", 0.0))
            existing.static_score = float(layers.get("layer3_static", {}).get("final_score", 0.0))
            existing.llm_score = float(layers.get("layer4_llm", {}).get("risk_score", 0.0))
            existing.graph_score = float(
                layers.get("layer5_graph", {}).get("propagated", {}).get("final_score", 0.0)
            )
            existing.classifier_score = float(payload.get("classifier", {}).get("risk_score", 0.0))
            existing.llm_triggered = bool(layers.get("layer4_llm", {}).get("llm_triggered", False))


def mark_scan_failed(job_id: str, package_name: str, registry: str, error_message: str) -> None:
    init_database()
    with session_scope() as session:
        existing = session.scalar(select(ScanJob).where(ScanJob.job_id == job_id))
        if existing is None:
            existing = ScanJob(job_id=job_id, package_name=package_name, registry=registry)
            session.add(existing)
        existing.status = "failed"
        existing.error_message = error_message


def get_scan_job(job_id: str) -> dict[str, Any] | None:
    init_database()
    with session_scope() as session:
        row = session.scalar(select(ScanJob).where(ScanJob.job_id == job_id))
        if row is None:
            return None
        return {
            "job_id": row.job_id,
            "status": row.status,
            "result_json": row.result_json,
            "error_message": row.error_message,
        }


def get_recent_scans(limit: int = 20) -> list[dict[str, Any]]:
    init_database()
    with session_scope() as session:
        rows = session.scalars(select(ScanJob).order_by(desc(ScanJob.updated_at)).limit(limit)).all()
        return [
            {
                "job_id": row.job_id,
                "package": row.package_name,
                "registry": row.registry,
                "status": row.status,
                "final_score": row.final_score,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]
