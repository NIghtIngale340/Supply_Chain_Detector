# Deployment Guide

This document covers local development, Docker deployment, production hardening, and environment configuration.

---

## Deployment Options

| Mode | Use Case | Prerequisites |
|------|----------|--------------|
| **Docker Compose** | Recommended for production & demos | Docker, Docker Compose |
| **Local (Poetry)** | Development & debugging | Python 3.11+, Redis, PostgreSQL (optional) |
| **GitHub Action** | CI/CD pipeline integration | GitHub repository |

---

## Docker Compose Deployment (Recommended)

### Prerequisites

- Docker Engine ≥ 24.0
- Docker Compose V2
- 4 GB RAM minimum (worker loads ML models)

### Quick start

```powershell
# Clone and enter the project
git clone https://github.com/your-org/supply-chain-detector.git
cd supply-chain-detector

# Create .env file for secrets (optional)
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up --build -d

# Verify health
docker compose ps
curl http://localhost:8000/health
```

### Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `api` | `Dockerfile.api` | 8000 | FastAPI REST API |
| `worker` | `Dockerfile.worker` | — | Celery analysis worker |
| `db` | `postgres:17-alpine` | 5432 | PostgreSQL database |
| `redis` | `redis:7` | 6379 | Message broker & cache |
| `ui` | `Dockerfile.api` + Streamlit | 8501 | Web UI |
| `grafana` | `grafana/grafana:11.5.2` | 3000 | Monitoring (optional profile) |

### Enable observability

Grafana is in the `observability` profile and not started by default:

```powershell
docker compose --profile observability up -d
```

Access at `http://localhost:3000` (admin/admin).

### Scale workers

```powershell
# Run 3 parallel analysis workers
docker compose up --scale worker=3 -d
```

### Stop and clean up

```powershell
# Stop all services
docker compose down

# Stop and remove volumes (deletes database!)
docker compose down -v
```

---

## Local Development Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Poetry | 1.7+ | Dependency management |
| Redis | 7+ | Broker & cache |
| PostgreSQL | 17+ (optional) | Persistent storage |
| Semgrep | Latest (optional) | Layer 3 static analysis |

### Install dependencies

```powershell
# Install Poetry (if not already installed)
pip install poetry

# Install project dependencies
poetry install

# Verify installation
poetry run python -c "import detector; print('OK')"
```

### Start Redis

```powershell
# Windows (via Docker)
docker run -d --name scd-redis -p 6379:6379 redis:7

# macOS (via Homebrew)
brew services start redis

# Linux
sudo systemctl start redis
```

### Start PostgreSQL (optional)

Without PostgreSQL, the system falls back to SQLite (`data/scd_local.db`):

```powershell
# Via Docker
docker run -d --name scd-postgres \
  -e POSTGRES_DB=scd \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:17-alpine
```

### Configure environment

```powershell
# Required
$env:CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
$env:REDIS_URL = "redis://localhost:6379/0"

# Optional: PostgreSQL (defaults to SQLite if unset)
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/scd"

# Optional: LLM provider
$env:LLM_PROVIDER = "stub"  # or "nvidia", "openai", "ollama"
```

### Run services

```powershell
# Terminal 1: Start the API
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the Celery worker
poetry run celery -A api.celery_app.celery_app worker --loglevel=info

# Terminal 3: Start the UI (optional)
poetry run streamlit run ui/streamlit_app.py
```

### Verify

```powershell
# Health check
curl http://localhost:8000/health

# Submit a test scan
curl -X POST http://localhost:8000/analyze `
  -H "Content-Type: application/json" `
  -d '{"name": "requests", "registry": "pypi"}'
```

---

## GitHub Action CI/CD

The included GitHub Action scans Python dependencies in CI pipelines.

**Setup:**

```yaml
# .github/workflows/supply-chain-scan.yml
name: Supply Chain Scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./github_action
        with:
          requirements_file: requirements.txt
          fail_on_block: true
```

See `github_action/README.md` for full configuration options.

---

## Environment Variables Reference

See [docs/environment_variables.md](environment_variables.md) for the complete reference.

### Quick reference (most important)

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Redis result backend |
| `DATABASE_URL` | auto-detect | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis URL for cache/rate limiter |
| `LLM_PROVIDER` | `stub` | LLM provider: stub/nvidia/openai/ollama/disabled |
| `LLM_TRIGGER_THRESHOLD` | `20` | Pre-LLM score threshold to invoke LLM |
| `RUN_MIGRATIONS` | `0` | Run Alembic migrations on API startup |
| `RUNNING_IN_DOCKER` | `0` | Set to `1` in Docker for DB auto-detection |

---

## Production Hardening

### Security

- [ ] **Use non-root Docker user** — Already configured (user `app`)
- [ ] **Set strong DB passwords** — Replace default `postgres:postgres`
- [ ] **Restrict exposed ports** — Only expose 8000 (API) and 8501 (UI) to the internet
- [ ] **Enable HTTPS** — Add a reverse proxy (nginx, Caddy, Traefik) with TLS
- [ ] **API authentication** — Add API key or OAuth2 middleware (not included by default)
- [ ] **Rate limit tuning** — Adjust `RATE_LIMITER_BACKEND=redis` and limits for your traffic

### Reliability

- [ ] **Health checks** — All services have Docker health checks configured
- [ ] **Restart policy** — `unless-stopped` is set for all services
- [ ] **Worker memory limit** — 4 GB limit prevents OOM from model loading
- [ ] **Late acknowledgment** — Celery `task_acks_late=True` prevents task loss on crash
- [ ] **Auto-retry** — Network errors retry up to 2× with exponential backoff

### Monitoring

- [ ] **Grafana** — Enable the `observability` profile for dashboards
- [ ] **Application logs** — Workers and API log to stdout (Docker captures these)
- [ ] **Celery monitoring** — Use `celery inspect` commands or Flower

### Backup

```powershell
# Backup PostgreSQL data
docker compose exec db pg_dump -U postgres scd > backup.sql

# Restore
docker compose exec -i db psql -U postgres scd < backup.sql
```

---

## Reverse Proxy Configuration

### Nginx (example)

```nginx
server {
    listen 443 ssl;
    server_name scd.yourcompany.com;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ui/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Troubleshooting Deployment

| Issue | Cause | Fix |
|-------|-------|-----|
| API won't start | Missing Redis/DB | Ensure `redis` and `db` are healthy first |
| Worker OOM killed | Model loading spike | Increase `mem_limit` in docker-compose.yml |
| Migrations fail | DB not ready | Check `db` health check; increase `start_period` |
| Rate limiter fails | Redis unavailable | Rate limiter fails open — check Redis connectivity |
| Scans stuck in "queued" | Worker not running | `docker compose logs worker` to check status |

See [docs/troubleshooting.md](troubleshooting.md) for comprehensive troubleshooting.
