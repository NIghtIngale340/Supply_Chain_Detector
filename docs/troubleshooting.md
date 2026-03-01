# Troubleshooting Guide

Common issues, diagnostics, and solutions for Supply Chain Detector.

---

## Quick Diagnostics

```powershell
# Check all service health
docker compose ps

# View recent logs
docker compose logs --tail=50 api
docker compose logs --tail=50 worker

# Test API health
curl http://localhost:8000/health

# Test Redis connectivity
docker compose exec redis redis-cli ping

# Test PostgreSQL connectivity
docker compose exec db pg_isready -U postgres -d scd
```

---

## Installation Issues

### `poetry install` fails with dependency conflicts

**Symptom:** Poetry cannot resolve dependencies.

**Fix:**
```powershell
# Clear Poetry cache
poetry cache clear --all .

# Retry
poetry install
```

### Semgrep installation fails on Windows

**Symptom:** `pip install semgrep` fails or Semgrep is not found.

**Note:** Semgrep has limited Windows support. Layer 3 static analysis will gracefully skip the Semgrep sub-analyzer and still use AST + obfuscation analyzers.

**Fix for CI/Docker:** Use Docker deployment where Semgrep is pre-installed in the worker image.

### `sentence-transformers` takes very long to install

**Cause:** PyTorch and model dependencies are large (~2 GB).

**Fix:** Be patient — first install takes 5–10 minutes. Subsequent installs use cached wheels.

---

## Docker Issues

### `docker compose up` fails: "port already in use"

**Cause:** Another service is using port 8000, 5432, 6379, or 8501.

**Fix:**
```powershell
# Find what's using the port (example: 8000)
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <pid> /F

# Or change the port in docker-compose.yml
```

### Worker exits with OOM (Out of Memory)

**Symptom:** Worker container restarts repeatedly; `docker compose logs worker` shows "Killed".

**Cause:** Loading sentence-transformers model + XGBoost + source processing exceeds memory limit.

**Fix:**
```yaml
# In docker-compose.yml, increase worker memory
worker:
  mem_limit: 6g    # Increase from 4g
  memswap_limit: 6g
```

### API health check fails during startup

**Symptom:** `docker compose ps` shows API as "unhealthy" for the first minute.

**Cause:** API is running Alembic migrations before serving requests.

**Fix:** This is normal — the health check has a 30-second `start_period`. Wait for migrations to complete. If it persists:
```powershell
docker compose logs api | Select-String "migration"
```

### Database migrations fail

**Symptom:** API logs show "alembic upgrade head" errors.

**Cause:** Database is not ready when API starts.

**Fix:** Docker Compose dependency health checks should handle this. If not:
```powershell
# Manually run migrations
docker compose exec api python -m alembic upgrade head
```

---

## Analysis Issues

### Scans stuck in "queued" status

**Symptom:** `GET /results/{job_id}` always returns `status: "pending"`.

**Possible causes:**

1. **Worker not running:**
   ```powershell
   docker compose ps worker  # Should show "running"
   docker compose logs worker --tail=20
   ```

2. **Redis broker not reachable:**
   ```powershell
   docker compose exec worker python -c "from api.celery_app import celery_app; print(celery_app.control.ping(timeout=2))"
   ```

3. **Worker crashed mid-task:** Check worker logs for tracebacks.

### "Rate limit exceeded" (429 errors)

**Cause:** More than 120 requests per minute from the same IP.

**Fix:**
- Wait 60 seconds for the sliding window to reset
- Or adjust the rate limit in `api/main.py`:
  ```python
  app.add_middleware(RateLimiterMiddleware, max_requests=500, window_seconds=60)
  ```

### LLM audit returns score 0 for suspicious packages

**Cause:** Pre-LLM risk is below `LLM_TRIGGER_THRESHOLD` (default: 20).

**Fix:** Lower the threshold:
```env
LLM_TRIGGER_THRESHOLD=10  # More sensitive
```

Or check that other layers are producing non-zero scores:
```powershell
# Check full result
curl http://localhost:8000/results/{job_id} | python -m json.tool
```

### Layer 2 (embedding) always returns 0

**Cause:** FAISS index not built or not found.

**Fix:**
```powershell
# Build the FAISS index
poetry run python ml/build_faiss_index.py

# Verify
ls data/processed/faiss.index
```

### Layer 3 (static) Semgrep sub-analyzer returns 0

**Cause:** Semgrep is not installed.

**Fix:** Install Semgrep or use Docker (pre-installed in worker image):
```powershell
pip install semgrep
```

The AST and obfuscation sub-analyzers still function without Semgrep.

---

## Performance Issues

### First scan takes 30+ seconds

**Cause:** Cold start — loading sentence-transformers model (~300 MB).

**Fix:** This is expected for the first scan. Subsequent scans reuse the cached model and complete in 2–10 seconds. The Docker worker pre-downloads the model during image build.

### Notebook cells run slowly

**Cause:** Heavy imports (sentence-transformers, XGBoost) are loaded on every run.

**Fix:** Use the precompute cache:
```powershell
poetry run python notebooks/precompute_cache.py
```

Notebooks load pre-computed data from cache instead of running heavy analysis.

---

## Database Issues

### "Table does not exist" errors

**Symptom:** `sqlalchemy.exc.OperationalError: no such table: scan_jobs`

**Fix (SQLite):**
```powershell
# Delete and recreate
Remove-Item data/scd_local.db -ErrorAction SilentlyContinue
poetry run python -c "from storage.database import init_database; init_database()"
```

**Fix (PostgreSQL):**
```powershell
# Run migrations
poetry run alembic upgrade head
```

### SQLite "database is locked" errors

**Cause:** Multiple workers trying to write to SQLite simultaneously.

**Fix:** SQLite is single-writer. For concurrent workers, use PostgreSQL:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scd
```

---

## Redis Issues

### "Connection refused" errors

**Symptom:** `redis.exceptions.ConnectionError: Error connecting to redis://localhost:6379`

**Fix:** Ensure Redis is running:
```powershell
# Docker
docker ps | findstr redis
docker start scd-redis  # If stopped

# Or start fresh
docker run -d --name scd-redis -p 6379:6379 redis:7
```

### Rate limiter not working (all requests allowed)

**Cause:** Rate limiter falls back to memory mode when Redis is unavailable.

**Fix:** Verify Redis connectivity and `RATE_LIMITER_BACKEND=redis` is set. Check:
```powershell
docker compose exec redis redis-cli keys "ratelimit:*"
```

---

## Getting Help

1. Check this troubleshooting guide
2. Review `docker compose logs` for error messages
3. Run the test suite: `poetry run pytest tests/ -v`
4. Open an issue on GitHub with:
   - Error message / stack trace
   - Docker Compose version (`docker compose version`)
   - Python version (`python --version`)
   - OS and architecture
