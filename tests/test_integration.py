"""Integration test — full scan lifecycle via the API.

Mocks the Celery task to run synchronously and verifies the complete
POST /analyze -> GET /results/{job_id} flow.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


class TestFullScanLifecycle:
    """End-to-end lifecycle: enqueue -> poll -> completed result."""

    @patch("api.routes.analyze.analyze_package_task.apply_async")
    @patch("api.routes.analyze.uuid.uuid4")
    def test_analyze_returns_job_id(self, mock_uuid4: MagicMock, mock_apply_async: MagicMock) -> None:
        mock_uuid4.return_value = "integ-job-001"
        resp = client.post("/analyze", json={"name": "requests", "registry": "pypi"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == "integ-job-001"
        assert body["status"] == "queued"
        mock_apply_async.assert_called_once_with(
            args=["requests", "pypi"],
            task_id="integ-job-001",
        )

    @patch("api.routes.results.AsyncResult")
    def test_results_pending_then_completed(self, mock_ar: MagicMock) -> None:
        # First call: pending
        mock_ar.return_value.state = "PENDING"
        resp = client.get("/results/integ-job-001")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

        # Second call: completed with result
        mock_ar.return_value.state = "SUCCESS"
        mock_ar.return_value.result = {
            "final_score": 42.5,
            "decision": "review",
            "layers": {
                "layer1_metadata": {"final_score": 60},
                "layer2_embeddings": {"risk_score": 10},
                "layer3_static": {"final_score": 30},
                "layer4_llm": {"risk_score": 0},
                "layer5_graph": {"final_score": 5},
            },
        }
        resp = client.get("/results/integ-job-001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["result"]["final_score"] == 42.5

    @patch("api.routes.results.AsyncResult")
    def test_results_failure(self, mock_ar: MagicMock) -> None:
        mock_ar.return_value.state = "FAILURE"
        mock_ar.return_value.result = Exception("worker crash")
        resp = client.get("/results/integ-job-fail")
        assert resp.status_code == 500

    def test_health_endpoint(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_analyze_bad_payload(self) -> None:
        resp = client.post("/analyze", json={"bad": "payload"})
        assert resp.status_code == 422  # validation error
