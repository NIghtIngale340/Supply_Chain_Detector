# Architecture Deep Dive

This document provides a detailed technical walkthrough of the Supply Chain Detector's architecture, component interactions, data flow, and trust boundaries.

---

## System Overview

Supply Chain Detector is a distributed system with four main layers:

1. **Client Layer** — Streamlit UI, REST API consumers, GitHub Action CI/CD
2. **Gateway Layer** — FastAPI application with rate limiting and request validation
3. **Processing Layer** — Celery workers running the 5-layer detection pipeline
4. **Data Layer** — PostgreSQL for persistence, Redis for caching/queuing, FAISS for vector search

```text
┌──────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                │
│   Streamlit UI (:8501)  │  REST API (:8000)  │  GitHub Action CI/CD │
└──────────────┬───────────────────┬───────────────────┬───────────────┘
               │                   │                   │
               ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FastAPI Gateway                              │
│   POST /analyze → job_id    GET /results/{id}    GET /health        │
│   RateLimiterMiddleware (120 req/min, sliding window)               │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ Celery task dispatch
               ┌───────────────▼───────────────┐
               │         Redis (:6379)          │
               │   DB 0: Celery Broker          │
               │   DB 1: Celery Result Backend  │
               │   DB 0: Metadata Cache         │
               │   DB 0: Rate Limit Counters    │
               └───────────────┬───────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                        Celery Worker                                 │
│                                                                      │
│  ┌────────────┐    ┌─────────────────────────────────────────────┐   │
│  │  Fetcher   │───▶│          Detection Pipeline                 │   │
│  │ PyPI / npm │    │                                             │   │
│  │ + tarball  │    │  L1 Metadata ──┐                            │   │
│  └────────────┘    │  L2 Embedding ─┤                            │   │
│                    │  L3 Static ────┤──▶ Classifier ──▶ Aggregator│   │
│                    │  L4 LLM ───────┤    (XGBoost)    (Weighted) │   │
│                    │  L5 Graph ─────┘                            │   │
│                    └─────────────────────────────────────────────┘   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
               ┌───────────────▼───────────────┐
               │     PostgreSQL 17 (:5432)      │
               │   scan_jobs table (Alembic)    │
               └────────────────────────────────┘
```

---

## Component Details

### FastAPI Gateway (`api/`)

**Entry point:** `api/main.py`

The gateway is a FastAPI application with:

- **Lifespan hook**: Calls `init_database()` on startup to ensure tables exist
- **Rate limiter middleware**: `RateLimiterMiddleware(max_requests=120, window_seconds=60)`
  - **Redis mode** (production): Sliding window via Redis sorted sets — multi-replica safe
  - **Memory mode** (fallback): In-memory `deque` per IP — single-process only
  - **Fail-open**: If Redis is unavailable, requests are allowed through
- **Three routers**: `health`, `analyze`, `results`

**Request lifecycle (POST /analyze):**

```
1. Client → POST /analyze {"name": "requests", "registry": "pypi"}
2. Pydantic validates: name min_length=1, registry in ["pypi", "npm"]
3. Generate UUID job_id
4. Create ScanJob record in DB (status=queued)
5. Dispatch Celery task: analyze_package.delay(name, registry, job_id)
6. Return 200 {"job_id": "...", "status": "queued"}
```

### Celery Worker (`workers/`)

**Entry point:** `workers/worker.py` → imports `api.celery_app` and `api.tasks`

**Celery configuration** (`api/celery_app.py`):

| Setting | Value | Rationale |
|---------|-------|-----------|
| `task_serializer` | json | Language-agnostic |
| `result_serializer` | json | Consistent with task format |
| `accept_content` | ["json"] | Security: reject pickle |
| `task_acks_late` | True | Re-deliver on worker crash |
| `worker_prefetch_multiplier` | 1 | Fair scheduling for long tasks |
| `result_expires` | 86400 | Clean up after 24 hours |

**Task: `analyze.package`** (`api/tasks.py`):

- Auto-retry on `ConnectionError` and `TimeoutError`
- Max 2 retries, exponential backoff (base 30s, max 120s)
- Calls `run_analysis_for_package()` → persists results via `upsert_scan_job()`
- On failure: calls `mark_scan_failed()` to record error

### Analysis Service (`api/analysis_service.py`)

Orchestrates the full scan pipeline within the worker:

```
1. Fetch metadata from PyPI/npm (Redis-cached, TTL 30 min)
2. Download source archive (tarball) to temp directory
3. Extract archive safely (path traversal protection)
4. Collect source files (.py, .js, .ts, .jsx, .mjs, .cjs, .tsx)
   - Max 30 files, 120,000 characters total
5. Call orchestrate_analysis() with metadata + source
6. Persist full results to PostgreSQL via upsert_scan_job()
7. Return result dict
```

**Source collection limits:**
- File extensions: `.py`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`
- Max files: 30
- Max total chars: 120,000

### Detection Orchestrator (`detector/orchestrator.py`)

Central coordination that runs all 5 layers sequentially:

```python
def orchestrate_analysis(package_name, registry, metadata, source_context, source_path):
    # 1. Layer 1: Metadata analysis
    metadata_result = analyze_metadata_risk(package_name, registry, metadata)
    
    # 2. Layer 2: Embedding analysis
    embedding_result = analyze_embedding_risk(source_context)
    
    # 3. Layer 3: Static analysis
    static_result = analyze_static_risk(source_context, source_path)
    
    # 4. Layer 5: Graph analysis (before LLM for threshold calculation)
    graph_result = analyze_graph_risk(package_name, registry)
    
    # 5. Classifier: XGBoost prediction
    features = build_feature_vector(...)
    classifier_result = predict_classifier_risk(features)
    
    # 6. Pre-LLM risk calculation (for trigger threshold)
    pre_llm_risk = weighted_sum(metadata, embedding, static, graph)
    
    # 7. Layer 4: LLM audit (conditional)
    if pre_llm_risk >= settings.llm_trigger_threshold:
        llm_result = audit_code_with_llm(source_context, pre_llm_risk)
    
    # 8. Final aggregation
    return aggregate_risk(all_scores, weights)
```

### Storage Layer (`storage/`)

**Database engine** (`storage/database.py`):
- Auto-detects environment: Docker → PostgreSQL, local → SQLite
- SQLite: creates tables directly via `create_all()`
- PostgreSQL: Alembic handles migrations
- Session management via context manager

**ScanJob model** (`storage/models.py`):

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer (PK) | Auto-increment |
| `job_id` | String (unique, indexed) | UUID from API |
| `package_name` | String | Package being scanned |
| `registry` | String | "pypi" or "npm" |
| `status` | String | queued/running/completed/failed |
| `final_score` | Float | Aggregated risk score |
| `metadata_score` | Float | Layer 1 score |
| `embedding_score` | Float | Layer 2 score |
| `static_score` | Float | Layer 3 score |
| `llm_score` | Float | Layer 4 score |
| `graph_score` | Float | Layer 5 score |
| `classifier_score` | Float | XGBoost score |
| `decision` | String | allow/review/block |
| `llm_triggered` | Boolean | Whether LLM was invoked |
| `error_message` | Text | Error details (if failed) |
| `result_json` | JSON | Full result payload |
| `created_at` | DateTime | Job creation time |
| `updated_at` | DateTime | Last status update |

### Redis Usage

Redis serves three purposes:

1. **Celery broker** (DB 0): Task queue for async job dispatch
2. **Celery result backend** (DB 1): Short-lived task results (24h TTL)
3. **Application cache** (DB 0): 
   - Metadata cache (`cache:{registry}:{name}`, TTL 30 min)
   - Rate limiter sliding window (sorted sets per IP)

### FAISS Vector Store (`storage/faiss_store.py`)

- File-based persistence: `data/processed/faiss.index` + `faiss_id_mapping.json`
- Lazy-loaded singleton pattern
- Flat L2 index (exact search, suitable for <100K vectors)
- Used by Layer 2 for nearest-neighbor similarity queries

---

## Trust Boundaries

```text
                    UNTRUSTED                    BOUNDARY                    TRUSTED
                    
  PyPI/npm API ─────────────┐
                             │── HTTPS + validation ──── Fetcher Module
  Tarball contents ──────────┘                          │
                                                        │── Path traversal  ── Source Extractor
                                                        │   protection
                                                        │
  Source code ───────────────┐                          │
                             │── Deobfuscation ───────── L4 LLM Provider
  LLM response ─────────────┘   + JSON validation       (external API)
```

| Boundary | Threat | Mitigation |
|----------|--------|-----------|
| Registry → Fetcher | Tampered metadata, DNS hijack | HTTPS, response schema validation |
| Tarball → Extractor | Path traversal, symlink attacks, zip bombs | `_safe_extract()` validates all paths stay within target dir, Python 3.12 `filter="data"` |
| Source → LLM | Code exfiltration to third party | Configurable provider; use Ollama for air-gapped |
| LLM → Parser | Malicious/malformed JSON response | Strict JSON parsing, fallback to fail-closed (score=100) |
| Client → API | DDoS, enumeration | Rate limiter (120 req/min/IP), input validation |
| Redis/DB → App | Data tampering | Docker internal network, no public exposure |

---

## Failure Modes & Graceful Degradation

Every external dependency has explicit fallback behavior:

| Component Failure | Behavior |
|-------------------|---------|
| **PyPI/npm API down** | Metadata fetch returns None; Layer 1 scores 0 |
| **Redis down** | Rate limiter fails open; cache returns None (always fetches fresh) |
| **PostgreSQL down** | Scan job not persisted; result returned from Celery only |
| **FAISS index missing** | Layer 2 returns score 0; logs warning |
| **Semgrep not installed** | Layer 3 skips Semgrep sub-analyzer; AST + obfuscation still run |
| **LLM provider error** | Layer 4 returns score 0; logs warning |
| **XGBoost model missing** | Classifier falls back to heuristic: `meta×0.4 + static×0.4 + graph×0.2` |
| **Worker crash mid-task** | `task_acks_late=True` → task re-delivered to another worker |

---

## Docker Networking

```text
┌─ Docker Compose Network (scd-net) ──────────────────────┐
│                                                          │
│  ┌─────┐     ┌──────┐     ┌────┐     ┌───────┐         │
│  │ API │────▶│Worker│────▶│ DB │     │ Redis │         │
│  │:8000│     │      │     │:5432│◀───│:6379  │         │
│  └──┬──┘     └──────┘     └────┘     └───┬───┘         │
│     │                                     │              │
│  ┌──▼──┐                                  │              │
│  │ UI  │──────────────────────────────────┘              │
│  │:8501│                                                 │
│  └─────┘                                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
     ↑ :8000 (API)    ↑ :8501 (UI)
     Exposed to host   Exposed to host
```

- Internal services (DB, Redis) are **not exposed** to the host by default in production
- Health checks run on every service to detect failures
- Worker has 4 GB memory limit to prevent OOM from large model loading
- API runs Alembic migrations on startup (`RUN_MIGRATIONS=1`)

---

## Multi-Stage Docker Builds

### API Image (`Dockerfile.api`)

```
Stage 1 (builder): pip install all Python dependencies
Stage 2 (runtime): Copy installed packages, add non-root user, install curl for healthcheck
Entrypoint: docker-entrypoint.sh → uvicorn api.main:app
```

### Worker Image (`Dockerfile.worker`)

```
Stage 1 (builder): pip install + install Semgrep + download sentence-transformer model
Stage 2 (runtime): Copy all artifacts, add non-root user
Entrypoint: docker-entrypoint.sh → celery worker
```

The worker image is larger (~1.5 GB) because it pre-caches:
- `all-MiniLM-L6-v2` sentence transformer model (~90 MB)
- Semgrep binary (~200 MB)
- XGBoost and scikit-learn packages

---

## Alembic Migrations

Database migrations are managed by Alembic:

- Config: `alembic.ini` (points to `storage/migrations/`)
- Auto-run on API startup when `RUN_MIGRATIONS=1`
- Local development with SQLite: tables created via `create_all()` (no Alembic needed)
- Production with PostgreSQL: Alembic `upgrade head` runs via `docker-entrypoint.sh`

```powershell
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one step
poetry run alembic downgrade -1
```
