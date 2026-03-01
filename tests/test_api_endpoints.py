from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("api.routes.analyze.upsert_scan_job")
@patch("api.routes.analyze.analyze_package_task")
def test_analyze_endpoint_enqueues_job(mock_task, mock_upsert) -> None:
    response = client.post("/analyze", json={"name": "requests", "registry": "pypi"})

    assert response.status_code == 200
    payload = response.json()
    assert "job_id" in payload
    assert payload["status"] == "queued"
    mock_task.apply_async.assert_called_once()
    mock_upsert.assert_called_once()


@patch("api.routes.results.get_scan_job", return_value={"status": "queued"})
@patch("api.routes.results.AsyncResult")
def test_results_endpoint_pending(mock_async_result, mock_get_scan) -> None:
    mock_async_result.return_value.state = "PENDING"

    response = client.get("/results/job-123")

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-123", "status": "pending", "result": None}


@patch("api.routes.results.get_scan_job", return_value={"status": "completed"})
@patch("api.routes.results.AsyncResult")
def test_results_endpoint_completed(mock_async_result, mock_get_scan) -> None:
    mock_async_result.return_value.state = "SUCCESS"
    mock_async_result.return_value.result = {"final_score": 12}

    response = client.get("/results/job-123")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"]["final_score"] == 12
