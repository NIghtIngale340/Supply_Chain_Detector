# Technical Design Document

This document covers the key design decisions, trade-offs, scalability considerations, and future architectural directions for Supply Chain Detector.

---

## Design Philosophy

1. **Defense in depth** — No single layer is a silver bullet. Five independent detection layers reduce the probability of evasion.
2. **Fail-open for availability, fail-closed for security** — Infrastructure failures (Redis, DB) degrade gracefully. Parsing failures (LLM) default to high risk.
3. **Cost-aware** — The LLM (most expensive component) is conditionally triggered, not applied to every scan.
4. **Offline-capable** — The system functions without network-dependent layers (LLM, graph) by using heuristic fallbacks.

---

## Key Architectural Decisions

### 1. Asynchronous processing via Celery

**Decision:** Use Celery with Redis broker for async task processing.

**Alternatives considered:**
- Synchronous processing in the API → Rejected: scans take 2–30s, would block API threads
- Background threads → Rejected: no crash recovery, no multi-machine scaling
- RQ (Redis Queue) → Considered: simpler but fewer features (no retry, no result backend)

**Trade-offs:**
- (+) Scalable: add workers by `docker compose up --scale worker=N`
- (+) Crash recovery: `task_acks_late=True` re-delivers failed tasks
- (+) Monitoring: Celery inspect commands, Flower dashboard
- (−) Complexity: requires Redis, adds eventual consistency
- (−) Latency: polling-based result retrieval (no WebSocket push)

### 2. Five-layer detection pipeline

**Decision:** Use 5 specialized detection layers + ML classifier + weighted aggregation.

**Rationale:** Each layer detects different attack vectors:

| Layer | Detects | Misses |
|-------|---------|--------|
| L1 Metadata | Typosquat, missing author, suspicious versioning | Compromised legitimate packages |
| L2 Embedding | Code similarity to known malware | Novel/zero-day attacks |
| L3 Static | Dangerous API calls, obfuscation, Semgrep rule matches | Context-dependent malice |
| L4 LLM | Contextual abuse, subtle backdoors | Prompt injection, hallucination |
| L5 Graph | Transitive risk propagation, dependency chains | Direct attacks (no deps) |

**Why not a single end-to-end model?**
- Interpretability: each layer produces an independent, explainable score
- Debugging: isolate which layer is wrong
- Modularity: add/remove layers without retraining
- Robustness: adversary must evade all layers, not just one

### 3. Conditional LLM triggering

**Decision:** Only invoke the LLM when pre-LLM risk ≥ threshold (default: 20).

**Rationale:**
- LLM inference costs $0.001–$0.002 per call
- At 10,000 scans/day, unconditional LLM = $10–20/day
- With threshold filtering (~20% trigger rate), cost drops to $2–4/day
- Safe packages (score < 20) don't benefit from LLM scrutiny

**Trade-off:** A sophisticated attacker who evades Layers 1–3 and 5 entirely may avoid LLM scrutiny. Mitigated by setting `LLM_TRIGGER_THRESHOLD=0` for high-security environments.

### 4. Weighted aggregation with consensus boosting

**Decision:** Combine layer scores via weighted sum, then add +5 per additional layer agreeing on ≥60 risk (consensus boost).

**Formula:**
```
final_score = Σ(layer_score × weight) + 5 × max(0, consensus_count − 1)
```

**Weight rationale:**

| Layer | Weight | Justification |
|-------|--------|---------------|
| Static | 0.25 | Most reliable signal in offline evaluation |
| Metadata | 0.22 | Strong signal for typosquat detection |
| LLM | 0.18 | Powerful but expensive and nondeterministic |
| Embedding | 0.15 | Useful for known-pattern matching |
| Graph | 0.15 | Important for transitive risk |
| Classifier | 0.05 | Low weight: trained on limited data |

**LLM weight redistribution:** When LLM is not triggered, its 0.18 weight is redistributed proportionally to the other 5 layers. This prevents inactive layers from artificially suppressing the total score.

**Consensus boosting:** If metadata (85) and static (70) both flag high risk, that's more convincing than one layer at 85. The +5 bonus per additional high-risk layer captures this correlation.

### 5. SQLite fallback for local development

**Decision:** Auto-detect Docker vs local and use PostgreSQL or SQLite accordingly.

**Logic:**
```python
if os.getenv("RUNNING_IN_DOCKER") == "1":
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/scd")
else:
    url = os.getenv("DATABASE_URL", "sqlite:///data/scd_local.db")
```

**Trade-off:**
- (+) Zero-config local development
- (+) No PostgreSQL required for casual use
- (−) SQLite doesn't support concurrent writes (single worker only)
- (−) Different SQL dialects may cause bugs

### 6. Path traversal protection in source extraction

**Decision:** Validate every extracted file path stays within the target directory.

**Implementation:**
```python
def _safe_extract(archive_path, target_dir):
    # Resolve all paths to absolute
    # Reject if resolved path is outside target_dir
    # Python 3.12+: use filter="data" for additional safety
```

**Threat model:** A malicious package tarball could contain entries like `../../etc/passwd` to write files outside the extraction directory. This defense is critical since we're extracting untrusted archives.

### 7. Fail-closed LLM response parsing

**Decision:** If the LLM response is unparseable, default to `risk_score=100`.

**Rationale:** An adversary could embed prompt injection in their source code to manipulate the LLM into returning "benign". If the manipulation partially succeeds (producing malformed JSON), defaulting to high risk is safer than defaulting to low risk.

**Alternative considered:** Default to 0 (fail-open) → Rejected: creates an easy bypass

### 8. Rate limiter with dual backend

**Decision:** Support both Redis (production) and in-memory (development) rate limiting.

**Redis implementation:** Sliding window via sorted sets — each request adds a timestamped entry. Entries outside the window are removed. Count of remaining entries determines rate.

**Memory implementation:** Per-IP `deque` with timestamp entries. Simple but single-process only.

**Fail-open:** If Redis is unreachable, the rate limiter allows the request. This prevents Redis failures from causing a total service outage.

### 9. Multi-stage Docker builds

**Decision:** Use multi-stage builds for both API and Worker images.

**Benefits:**
- Builder stage installs/compiles dependencies
- Runtime stage contains only necessary files
- Smaller final images (though worker is still ~1.5 GB due to ML models)

### 10. Pre-cached ML models in worker image

**Decision:** Download the sentence-transformers model during Docker build.

```dockerfile
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Trade-off:**
- (+) First scan is fast — no cold start model download
- (+) Works in air-gapped environments
- (−) Larger Docker image (~1.5 GB)
- (−) Model updates require image rebuild

---

## Scalability Analysis

### Current bottlenecks

| Component | Bottleneck | Scaling Strategy |
|-----------|-----------|-----------------|
| Worker | CPU-bound ML inference | Horizontal: add workers |
| Worker | Memory: model loading | One model instance per worker |
| Redis | Broker throughput | Redis Enterprise or cluster |
| PostgreSQL | Write throughput | Connection pooling, read replicas |
| LLM API | External rate limits | Provider-specific quotas |

### Scaling estimates

| Scale | Workers | Throughput | Infra Requirements |
|-------|---------|------------|-------------------|
| Dev | 1 | ~3 scans/min | Single machine, 4 GB RAM |
| Small team | 2–4 | ~10 scans/min | 8–16 GB RAM |
| Enterprise | 10–20 | ~50 scans/min | Kubernetes, 64+ GB RAM |

### What would need to change for 1000+ scans/min

1. **Replace polling with WebSockets** — Push results to clients instead of polling
2. **Shard Redis** — Use Redis Cluster for broker partitioning
3. **Read replicas** — PostgreSQL read replicas for result queries
4. **Model serving** — Separate model inference into a gRPC service (Triton, TorchServe)
5. **CDN for registry data** — Cache PyPI/npm metadata at edge

---

## Security Threat Model

### Attacker goals

1. Get a malicious package rated as "allow" (false negative)
2. Cause the system to crash or become unavailable (denial of service)
3. Exfiltrate package data being scanned (data theft)

### Attack surface

| Vector | Severity | Mitigation | Residual Risk |
|--------|----------|-----------|---------------|
| Typosquat evasion | High | L1 edit distance to top-1000 packages | Novel names not in top-1000 |
| Obfuscated payload | High | L3 obfuscation detection + L4 deobfuscation | Multi-layer encoding |
| Prompt injection | Medium | Strict JSON parsing, fail-closed | Sophisticated prompt injection |
| Registry API spoofing | Medium | HTTPS, response validation | Compromised CDN/DNS |
| Path traversal in tarball | High | `_safe_extract()` + Python 3.12 filters | Zero-day in extraction |
| DDoS | Medium | Rate limiting (120 req/min) | Distributed attack |
| Dependency confusion | High | L5 graph analysis | New package names |

---

## Future Architectural Directions

### Near-term (next release)

- **Webhook notifications** — Push results instead of polling
- **Batch scanning** — Multiple packages in one API call
- **CLI tool** — Direct terminal usage without API

### Medium-term

- **gRPC model serving** — Decouple ML inference from Celery workers
- **Kubernetes Helm chart** — Production deployment template
- **Multi-registry support** — RubyGems, Cargo, Maven

### Long-term

- **Federated learning** — Share model updates without sharing data
- **Real-time registry monitoring** — Continuous scanning of new package publications
- **SBOM integration** — CycloneDX/SPDX input/output support
