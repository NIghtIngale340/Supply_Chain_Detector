09# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main branch) | Yes |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in Supply Chain Detector, please report it responsibly:

1. **Email:** Send a detailed report to the project maintainer (see GitHub profile)
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

### What happens next

- **Acknowledgment** within 48 hours
- **Assessment** within 7 days
- **Fix timeline** communicated within 14 days
- **Credit** given in release notes (unless you prefer anonymity)

---

## Security Considerations

### Threat Surface

Supply Chain Detector processes **untrusted input** (package metadata and source code from public registries). The following security measures are in place:

#### Archive Extraction

- **Path traversal protection:** All extracted file paths are validated to stay within the target directory
- **Python 3.12+:** Uses `filter="data"` for additional extraction safety
- **Temporary directories:** Archives are extracted to ephemeral temp dirs, cleaned up after analysis

#### LLM Integration

- **Data exfiltration risk:** When using cloud LLM providers (OpenAI, NVIDIA), package source code is sent to third-party APIs
- **Mitigation:** Use `LLM_PROVIDER=ollama` for local inference, or `LLM_PROVIDER=disabled` to skip Layer 4
- **Prompt injection:** Malicious code may attempt to manipulate LLM output
- **Mitigation:** Strict JSON parsing with fail-closed default (score=100 on parse failure)

#### API Security

- **Rate limiting:** 120 requests per minute per IP (sliding window)
- **Input validation:** Pydantic schemas validate all request bodies
- **No authentication by default:** Add API key middleware for production deployments

#### Docker Security

- **Non-root containers:** All services run as non-privileged user `app`
- **No exposed internal services:** PostgreSQL and Redis are only accessible within the Docker network
- **Memory limits:** Worker containers have 4 GB memory ceiling
- **Health checks:** All services monitored via Docker health checks

#### Data Storage

- **No PII collected:** Only package names, scores, and analysis results are stored
- **Result TTL:** Celery results expire after 24 hours
- **Database credentials:** Use environment variables, never commit secrets

---

## Dependencies

This project depends on third-party packages that may have their own vulnerabilities:

| Category | Key Dependencies | Risk |
|----------|-----------------|------|
| ML | sentence-transformers, xgboost, scikit-learn | Low (well-maintained) |
| Web | FastAPI, uvicorn, Celery | Low (actively maintained) |
| Database | SQLAlchemy, psycopg2, alembic | Low |
| Analysis | semgrep | Medium (complex C binary) |
| HTTP | requests | Low |

### Keeping dependencies updated

```powershell
# Check for outdated packages
poetry show --outdated

# Update all dependencies
poetry update

# Run tests after updating
poetry run pytest tests/ -v
```

---

## Known Limitations

1. **No authentication on API** — Must be added for public-facing deployments
2. **LLM sends code to cloud** — Use Ollama for sensitive environments
3. **Rate limiter fails open** — If Redis is down, rate limiting is bypassed
4. **SQLite for local dev** — Not suitable for concurrent production use

---

## Responsible Use

Supply Chain Detector is a **defensive security tool**. It is designed to identify malicious packages, not to create them.

- Do **not** use this tool to develop or test malicious packages
- Do **not** upload malicious samples to public registries
- The malicious dataset used for training is sourced from an existing academic research collection (Backstabber's Knife Collection)
- All analysis is performed locally or through configured APIs — no data is shared with the project maintainers
