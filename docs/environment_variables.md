# Environment Variables Reference

Complete reference for all environment variables used by Supply Chain Detector.

---

## Core Infrastructure

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Yes | Redis URL for Celery message broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Yes | Redis URL for Celery result storage |
| `DATABASE_URL` | auto-detect | No | PostgreSQL connection string. Auto-detects Docker vs local |
| `REDIS_URL` | `redis://redis:6379/0` | No | Redis URL for application cache and rate limiter |
| `RUNNING_IN_DOCKER` | `0` | No | Set to `1` in Docker. Controls DB auto-detection |
| `RUN_MIGRATIONS` | `0` | No | Set to `1` to run Alembic migrations on API startup |

### Database auto-detection logic

```
if RUNNING_IN_DOCKER == "1":
    use DATABASE_URL (defaults to postgresql://postgres:postgres@db:5432/scd)
else:
    use DATABASE_URL if set, otherwise use SQLite (data/scd_local.db)
```

---

## LLM Provider Configuration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `LLM_PROVIDER` | `stub` (Docker) / `disabled` (local) | No | LLM provider: `stub`, `nvidia`, `openai`, `ollama`, `disabled` |
| `LLM_TRIGGER_THRESHOLD` | `20` | No | Pre-LLM risk score threshold (0–100) to invoke LLM audit |

### NVIDIA NIM

| Variable | Default | Required When | Description |
|----------|---------|---------------|-------------|
| `NVIDIA_API_KEY` | — | `LLM_PROVIDER=nvidia` | NVIDIA NIM API key |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | No | NVIDIA API endpoint |
| `NVIDIA_MODEL` | `meta/llama-3.1-8b-instruct` | No | Model identifier |
| `NVIDIA_MAX_OUTPUT_TOKENS` | `600` | No | Maximum output tokens |

### OpenAI

| Variable | Default | Required When | Description |
|----------|---------|---------------|-------------|
| `OPENAI_API_KEY` | — | `LLM_PROVIDER=openai` | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | No | Model name |
| `OPENAI_MAX_OUTPUT_TOKENS` | `600` | No | Maximum output tokens |

### Ollama (Local)

| Variable | Default | Required When | Description |
|----------|---------|---------------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | No | Ollama server URL |
| `OLLAMA_MODEL` | `huihui_ai/qwen2.5-coder-abliterate:7b` | No | Model name |
| `OLLAMA_MAX_OUTPUT_TOKENS` | `600` | No | Maximum output tokens |

---

## Application Settings

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `CACHE_TTL_SECONDS` | `1800` | No | Redis metadata cache TTL (30 minutes) |
| `RESULT_TTL_SECONDS` | `86400` | No | Celery result expiry (24 hours) |
| `RATE_LIMITER_BACKEND` | `redis` | No | Rate limiter backend: `redis` or `memory` |

---

## PostgreSQL (Docker)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `POSTGRES_DB` | `scd` | No | Database name |
| `POSTGRES_USER` | `postgres` | No | Database user |
| `POSTGRES_PASSWORD` | `postgres` | No | Database password |

---

## Grafana (Observability Profile)

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `GRAFANA_ADMIN_USER` | `admin` | No | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | No | Grafana admin password |

---

## UI

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SCD_API_BASE_URL` | `http://api:8000` | Docker only | API base URL for the Streamlit UI |

---

## Model & Data Paths

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SENTENCE_TRANSFORMERS_HOME` | System default | No | Path to cached sentence-transformer models. Set to `/app/.cache/sentence_transformers` in Docker worker |

---

## Example `.env` File

```env
# Infrastructure
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
DATABASE_URL=postgresql://postgres:changeme@db:5432/scd
REDIS_URL=redis://redis:6379/0

# PostgreSQL
POSTGRES_PASSWORD=changeme

# LLM (choose one provider)
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key-here
LLM_TRIGGER_THRESHOLD=20

# Tuning
CACHE_TTL_SECONDS=1800
RATE_LIMITER_BACKEND=redis
```

---

## Validation Rules

| Variable | Constraint | Error |
|----------|-----------|-------|
| `LLM_TRIGGER_THRESHOLD` | Must be integer in [0, 100] | `ValueError` on startup |
| `CACHE_TTL_SECONDS` | Must be integer > 0 | `ValueError` on startup |
| `RESULT_TTL_SECONDS` | Must be integer > 0 | `ValueError` on startup |
| `LLM_PROVIDER` | Must be one of: `stub`, `nvidia`, `openai`, `ollama`, `disabled`, `off`, `none`, `` | `RuntimeError` on LLM invocation |

---

## Precedence

1. Shell environment variables (highest priority)
2. `.env` file (loaded by Docker Compose)
3. Default values in code (lowest priority)
