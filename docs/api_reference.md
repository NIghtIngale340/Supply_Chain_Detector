# API Reference

Complete REST API documentation for the Supply Chain Detector.

**Base URL:** `http://localhost:8000` (local) or your deployment URL.

---

## Authentication

No authentication is required. Rate limiting is enforced at 120 requests per minute per IP address.

---

## Endpoints

### `POST /analyze`

Submit a package for asynchronous analysis.

**Request Body:**

```json
{
  "name": "requests",
  "registry": "pypi"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | min_length=1 | Package name |
| `registry` | string | Yes | "pypi" or "npm" | Package registry |

**Response (200 OK):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 422 | Invalid request body | Pydantic validation errors |
| 429 | Rate limit exceeded | `{"detail": "Rate limit exceeded"}` |

**Example:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"name": "requests", "registry": "pypi"}'
```

---

### `GET /results/{job_id}`

Retrieve the analysis results for a specific job.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string (UUID) | The job ID returned by `/analyze` |

**Response (pending):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "result": null
}
```

**Response (completed):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "final_score": 12.5,
    "decision": "allow",
    "consensus_signals": 0,
    "weighted_score": 12.5,
    "consensus_boost": 0.0,
    "weights": {
      "metadata": 0.22,
      "embedding": 0.15,
      "static": 0.25,
      "llm": 0.18,
      "graph": 0.15,
      "classifier": 0.05
    },
    "layers": {
      "metadata": {
        "risk_score": 0,
        "risk_level": "low",
        "typosquat": {"score": 0, "nearest_match": null},
        "author": {"score": 0, "reputation": "high"},
        "version": {"score": 0, "anomaly": null}
      },
      "embedding": {
        "risk_score": 15.2,
        "distance": 0.92,
        "nearest_neighbors": [
          {"name": "similar-pkg", "distance": 0.85}
        ]
      },
      "static": {
        "risk_score": 5.0,
        "ast_score": 10,
        "semgrep_score": 0,
        "obfuscation_score": 0,
        "findings": []
      },
      "llm": {
        "triggered": false,
        "risk_score": 0,
        "reason": "Pre-LLM risk below threshold"
      },
      "graph": {
        "risk_score": 20.5,
        "blast_radius": "low",
        "dependency_count": 3,
        "max_depth": 2
      }
    },
    "classifier": {
      "risk_score": 8.5,
      "confidence": 0.92,
      "model": "xgboost"
    }
  }
}
```

**Response (failed):**

```json
{
  "job_id": "550e8400-...",
  "status": "failed",
  "result": null,
  "error": "Connection timeout to PyPI API"
}
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Job ID not found | `{"detail": "Job not found"}` |

**Example:**

```bash
curl http://localhost:8000/results/550e8400-e29b-41d4-a716-446655440000
```

---

### `GET /results/recent`

Retrieve the most recent scan results. Used by the threat feed UI.

**Query Parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | integer | 20 | 1–100 | Number of results to return |

**Response (200 OK):**

```json
[
  {
    "job_id": "550e8400-...",
    "package_name": "requests",
    "registry": "pypi",
    "status": "completed",
    "final_score": 12.5,
    "decision": "allow",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  {
    "job_id": "660f9500-...",
    "package_name": "evilpkg",
    "registry": "pypi",
    "status": "completed",
    "final_score": 85.2,
    "decision": "block",
    "updated_at": "2025-01-15T10:28:00Z"
  }
]
```

**Example:**

```bash
curl "http://localhost:8000/results/recent?limit=10"
```

---

### `GET /health`

Health check endpoint.

**Response (200 OK):**

```json
{
  "status": "ok"
}
```

---

## Rate Limiting

| Parameter | Value |
|-----------|-------|
| Max requests | 120 per minute |
| Window type | Sliding window |
| Scope | Per IP address |
| Backend | Redis sorted sets (production), in-memory deque (fallback) |
| Failure mode | Fail-open (allow request if Redis unavailable) |

When rate limited, the API returns `429 Too Many Requests`.

---

## Decision Reference

| Score Range | Decision | Meaning |
|-------------|----------|---------|
| 0–49 | `allow` | Package is likely safe to install |
| 50–79 | `review` | Package has risk signals; manual inspection recommended |
| 80–100 | `block` | Package is likely malicious; do not install |

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 404 | Resource not found |
| 422 | Validation error (invalid request body) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Polling Pattern

The recommended pattern for consuming the API:

```python
import time
import requests

# 1. Submit analysis
resp = requests.post("http://localhost:8000/analyze", json={
    "name": "suspicious-pkg",
    "registry": "pypi"
})
job_id = resp.json()["job_id"]

# 2. Poll for results
for _ in range(30):  # Max 30 attempts
    result = requests.get(f"http://localhost:8000/results/{job_id}").json()
    if result["status"] == "completed":
        print(f"Score: {result['result']['final_score']}")
        print(f"Decision: {result['result']['decision']}")
        break
    elif result["status"] == "failed":
        print(f"Error: {result.get('error')}")
        break
    time.sleep(2)  # Wait 2 seconds between polls
```
