# Worker Flow Documentation

This document describes the Celery worker lifecycle, task execution flow, retry logic, and persistence behavior.

---

## Overview

The Supply Chain Detector uses Celery with Redis as the message broker to process package analysis tasks asynchronously. This decouples the API response time from the analysis duration (which can take 2–30+ seconds depending on whether the LLM is triggered).

---

## Task Lifecycle

```
POST /analyze
     │
     ▼
┌─────────────┐
│ API creates  │
│ ScanJob in DB│ status = "queued"
│ + dispatches │
│ Celery task  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Redis Broker │ Task queued in DB 0
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ Worker picks up task            │
│                                 │
│ 1. Fetch metadata (cached)      │ 200–500ms
│ 2. Download tarball             │ 500ms–2s
│ 3. Extract archive              │ ~100ms
│ 4. Collect source files         │ ~50ms
│ 5. Run Layer 1 (Metadata)       │ ~50ms
│ 6. Run Layer 2 (Embeddings)     │ ~200ms
│ 7. Run Layer 3 (Static)         │ ~300ms
│ 8. Run Layer 5 (Graph)          │ 1–3s
│ 9. Check LLM threshold          │
│ 10. Run Layer 4 (LLM) [if >20]  │ 2–30s
│ 11. Run Classifier (XGBoost)    │ <5ms
│ 12. Aggregate risk score        │ <1ms
│ 13. Persist to DB               │ ~10ms
│                                 │
│ status = "completed"            │
└─────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL   │ Full result persisted
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Client polls │ GET /results/{job_id}
│ → completed  │
└─────────────┘
```

---

## Celery Configuration

**File:** `api/celery_app.py`

| Setting | Value | Purpose |
|---------|-------|---------|
| `broker_url` | `redis://redis:6379/0` | Message queue location |
| `result_backend` | `redis://redis:6379/1` | Short-term result storage |
| `task_serializer` | `json` | Language-agnostic serialization |
| `result_serializer` | `json` | Consistent with broker |
| `accept_content` | `["json"]` | Reject pickle (security) |
| `task_acks_late` | `True` | Acknowledge after completion (crash safety) |
| `worker_prefetch_multiplier` | `1` | Fair scheduling for long tasks |
| `result_expires` | `86400` | Auto-cleanup after 24 hours |

### Late acknowledgment

`task_acks_late=True` means tasks are acknowledged **after** completion, not at pickup. If a worker crashes mid-analysis, the task is automatically re-delivered to another worker. Combined with `worker_prefetch_multiplier=1`, this ensures no task is lost.

---

## Task Definition

**File:** `api/tasks.py`

```python
@celery_app.task(
    name="analyze.package",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=30,
    retry_backoff_max=120,
    max_retries=2,
)
def analyze_package_task(self, name, registry, job_id):
    result = run_analysis_for_package(name, registry, job_id)
    return result
```

### Retry behavior

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `autoretry_for` | `ConnectionError`, `TimeoutError` | Network issues trigger auto-retry |
| `max_retries` | 2 | Up to 2 retries (3 total attempts) |
| `retry_backoff` | 30 | Initial backoff: 30 seconds |
| `retry_backoff_max` | 120 | Max backoff: 2 minutes |

**Retry schedule example:**
1. Attempt 1: immediate
2. Attempt 2 (first retry): +30 seconds
3. Attempt 3 (second retry): +60 seconds (exponential)

### Failure handling

If all retries are exhausted:
1. Task raises the original exception
2. Exception handler calls `mark_scan_failed(job_id, error_message)`
3. ScanJob record updated: `status="failed"`, `error_message=str(exception)`
4. Client sees `{"status": "failed", "error": "..."}` when polling

---

## Analysis Service

**File:** `api/analysis_service.py`

The `run_analysis_for_package()` function orchestrates the complete scan:

### Step 1: Fetch metadata

```python
# Check Redis cache first
cached = cache.get_json(f"cache:{registry}:{name}")
if cached:
    metadata = cached
else:
    metadata = fetch_pypi_metadata(name)  # or fetch_npm_metadata
    cache.set_json(f"cache:{registry}:{name}", metadata, ttl=1800)
```

**Cache TTL:** 30 minutes. Prevents redundant API calls when scanning the same package multiple times.

### Step 2: Download and extract source

```python
# Download tarball to temp directory
tarball_path = download_tarball(metadata.tarball_url, temp_dir)

# Safe extraction with path traversal protection
source_dir = extract_archive(tarball_path, temp_dir)
```

### Step 3: Collect source files

```python
TEXT_EXTENSIONS = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}

# Walk source directory, collect up to 30 files / 120K chars
source_context = collect_source_files(source_dir, extensions=TEXT_EXTENSIONS,
                                       max_files=30, max_chars=120000)
```

### Step 4: Run detection pipeline

```python
result = orchestrate_analysis(
    package_name=name,
    registry=registry,
    metadata=metadata,
    source_context=source_context,
    source_path=source_dir,
)
```

### Step 5: Persist results

```python
upsert_scan_job(
    job_id=job_id,
    package_name=name,
    registry=registry,
    status="completed",
    result=result,
)
```

---

## Worker Scaling

### Single worker (default)

```powershell
poetry run celery -A api.celery_app.celery_app worker --loglevel=info
```

### Multiple workers

```powershell
# Worker 1
poetry run celery -A api.celery_app.celery_app worker --loglevel=info -n worker1@%h

# Worker 2
poetry run celery -A api.celery_app.celery_app worker --loglevel=info -n worker2@%h
```

### Docker scaling

```powershell
docker compose up --scale worker=3
```

### Concurrency

By default, Celery uses process-based concurrency with the number of CPU cores. For CPU-bound ML workloads, this is appropriate. If you need to tune:

```powershell
celery -A api.celery_app.celery_app worker --concurrency=2
```

---

## Monitoring

### Task states

Monitor task states in Redis:

```python
from api.celery_app import celery_app
from celery.result import AsyncResult

result = AsyncResult(job_id, app=celery_app)
print(result.state)    # PENDING, STARTED, SUCCESS, FAILURE, RETRY
print(result.result)   # Task return value (if SUCCESS)
print(result.traceback) # Exception traceback (if FAILURE)
```

### Worker health

```powershell
# Check active workers
celery -A api.celery_app.celery_app inspect active

# Check registered tasks
celery -A api.celery_app.celery_app inspect registered

# Queue statistics
celery -A api.celery_app.celery_app inspect stats
```

---

## Memory Considerations

| Component | Memory Usage |
|-----------|-------------|
| Celery worker base | ~100 MB |
| sentence-transformers model | ~300 MB (lazy-loaded, cached) |
| XGBoost model | ~5 MB |
| Source code processing | ~50 MB (per task) |
| **Total per worker** | **~500 MB idle, ~1.5 GB under load** |

The Docker Compose configuration limits worker memory to 4 GB to prevent OOM from loading multiple large models simultaneously.
