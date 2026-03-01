from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("api.routes.analyze.analyze_package_task.delay")
def test_analyze_endpoint_enqueues_job(mock_delay) -> None:
    mock_delay.return_value.id = "job-123"

    response = client.post("/analyze", json={"name": "requests", "registry": "pypi"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == "job-123"
    assert payload["status"] == "queued"


@patch("api.routes.results.AsyncResult")
def test_results_endpoint_pending(mock_async_result) -> None:
    mock_async_result.return_value.state = "PENDING"

    response = client.get("/results/job-123")

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-123", "status": "pending", "result": None}


@patch("api.routes.results.AsyncResult")
def test_results_endpoint_completed(mock_async_result) -> None:
    mock_async_result.return_value.state = "SUCCESS"
    mock_async_result.return_value.result = {"final_score": 12}

    response = client.get("/results/job-123")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"]["final_score"] == 12
