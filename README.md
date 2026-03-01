# Supply Chain Detector

**AI-powered software supply chain attack detection for PyPI and npm packages.**

An end-to-end, local-first analysis pipeline that scores third-party packages for supply chain risk **before installation** using a five-layer detection architecture, XGBoost classification, and weighted risk aggregation with consensus boosting.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License: Research](https://img.shields.io/badge/license-research-green.svg)](#license)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange.svg)](https://xgboost.readthedocs.io)

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Threat Model](#threat-model)
- [System Architecture](#system-architecture)
- [Five-Layer Detection Pipeline](#five-layer-detection-pipeline)
- [Risk Scoring & Aggregation](#risk-scoring--aggregation)
- [Model Training](#model-training)
- [LLM Integration](#llm-integration)
- [Performance Benchmarks](#performance-benchmarks)
- [Results](#results)
- [Setup & Deployment](#setup--deployment)
- [API Reference](#api-reference)
- [CI/CD & Testing](#cicd--testing)
- [GitHub Action Scanner](#github-action-scanner)
- [Notebooks](#notebooks)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Responsible Disclosure](#responsible-disclosure)
- [Documentation Index](#documentation-index)
- [Project Layout](#project-layout)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Executive Summary

### The Problem

Software supply chain attacks have become one of the fastest-growing threats in cybersecurity. Attackers upload malicious packages to public registries (PyPI, npm) that masquerade as legitimate libraries through typosquatting, dependency confusion, and account takeover. Once installed, these packages can exfiltrate credentials, establish reverse shells, or deploy ransomware.

**Scale of the problem:**
- Thousands of malicious packages are uploaded to PyPI and npm annually
- A single compromised dependency can cascade to millions of downstream consumers
- Most existing tools rely on a single detection signal, making them brittle against polymorphic attacks

### Why Current Solutions Are Insufficient

| Approach | Limitation |
|----------|-----------|
| Name-matching only | Misses dependency confusion and account takeover attacks |
| Signature-based scanning | Cannot detect novel obfuscation or zero-day payloads |
| Manual code review | Doesn't scale — top PyPI packages have hundreds of transitive deps |
| Post-installation monitoring | Damage already done by the time behavior is observed |

### Our Approach

**Supply Chain Detector** uses **defense-in-depth** — five independent analysis layers, each targeting a different attack surface, combined through a weighted aggregator with consensus boosting. The system operates **pre-installation**, analyzing packages before they enter your environment.

**Key value propositions:**
- **Multi-signal detection** — no single point of failure; if one layer is bypassed, others catch the threat
- **Pre-installation analysis** — risk scored before any code executes in your environment
- **Explainable decisions** — per-layer breakdowns show exactly why a package was flagged
- **Cost-optimized LLM** — expensive AI audit triggers only when cheaper layers indicate risk
- **Production-ready** — async API, background workers, database persistence, rate limiting, Docker orchestration

---

## Threat Model

### In-Scope Attacks

| Attack Vector | Detection Layer(s) | How Detected |
|---------------|-------------------|--------------|
| **Typosquatting** | L1 Metadata | Levenshtein distance against top-1000 packages |
| **Dependency confusion** | L1 Metadata, L5 Graph | Author reputation + unexpected graph topology |
| **Malicious code injection** | L3 Static, L4 LLM | AST pattern matching, obfuscation detection, LLM audit |
| **Account takeover** | L1 Metadata | Author age < 30 days, reputation change |
| **Obfuscated payloads** | L3 Static, L4 LLM | Base64/hex blob detection, eval/exec chains, LLM deobfuscation |
| **Transitive dependency risk** | L5 Graph | Distance-decayed risk propagation across dependency tree |
| **Code similarity anomalies** | L2 Embeddings | FAISS nearest-neighbor distance from known-good corpus |

### Out-of-Scope

- **Build-time attacks** (e.g., compromised CI/CD pipelines) — this tool analyzes published packages, not build infrastructure
- **Binary-only packages** — static analysis requires source code availability
- **Private registry attacks** — currently supports only public PyPI and npm
- **Runtime behavioral detection** — this is a pre-installation static analysis tool

### Assumptions

1. Package metadata from registries is accurate (registry APIs are not compromised)
2. The top-1000 package lists represent "known-good" baselines
3. Malicious packages exhibit at least one detectable signal across the five layers
4. LLM providers return honest analysis (not adversarial)

---

## System Architecture

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
│   Rate Limiter (120 req/min, sliding window)                        │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ Celery task dispatch
               ┌───────────────▼───────────────┐
               │         Redis (:6379)          │
               │   Broker (db0) + Backend (db1) │
               │   Metadata Cache + Rate Limits │
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

### Data Flow

1. **Client submits** package name + registry via `POST /analyze`
2. **API creates** a `ScanJob` record (status=queued), dispatches Celery task, returns `job_id`
3. **Worker picks up** the task:
   - Fetches metadata from PyPI/npm (cached in Redis, TTL 30 min)
   - Downloads and extracts source archive to temp directory
   - Runs all 5 detection layers in sequence
   - Feeds layer scores into XGBoost classifier
   - Aggregates with weighted scoring + consensus boost
4. **Worker persists** full results to PostgreSQL
5. **Client polls** `GET /results/{job_id}` until status = `completed`

### Trust Boundaries

| Boundary | Concern | Mitigation |
|----------|---------|-----------|
| Registry API → Fetcher | Tampered metadata | HTTPS only, response validation |
| Tarball → Static Analyzer | Malicious archive (path traversal, zip bombs) | Path traversal protection, extraction size limits, Python 3.12 `filter="data"` |
| Source code → LLM Provider | Code exfiltration to third-party | Configurable: use local Ollama for air-gapped environments |
| External Redis/DB | Data tampering | Docker internal network, no public port exposure in production |

> **Detailed architecture**: See [docs/architecture.md](docs/architecture.md)

---

## Five-Layer Detection Pipeline

### Layer 1 — Metadata Analysis

**Module:** `detector/layer1_metadata/` | **Weight:** 0.22

Analyzes package metadata for social engineering signals without examining source code.

| Sub-analyzer | Signal | Scoring Logic |
|-------------|--------|---------------|
| **Typosquat Detector** | Levenshtein distance to top-1000 packages | dist=1 → 90, dist=2 → 60, dist≤4 → 25, dist>4 or exact match → 0 |
| **Author Analyzer** | Account age, reputation, author presence | <7 days → +50, <30 days → +30, missing author → +10, low reputation → +15 |
| **Version Analyzer** | Version jump magnitude, release cadence | jump>5 → +30, dormant >365d → +35, velocity >1.0/day → +15 |

**Composite score:** `typosquat × 0.40 + author × 0.30 + version × 0.30`

**Failure mode:** Returns score 0 if metadata unavailable. **Performance:** ~50ms per package.

### Layer 2 — Code Embeddings

**Module:** `detector/layer2_embeddings/` | **Weight:** 0.15

Encodes source code into 384-dim vectors using `all-MiniLM-L6-v2` and compares against a FAISS index of known-good packages.

| Distance | Score | Interpretation |
|----------|-------|---------------|
| ≤ 0.8 | 0 | Close to known-good corpus |
| 0.8–1.6 | 20–60 | Linear interpolation |
| > 1.6 | 60+ | Outlier from known corpus |

**Failure mode:** Returns score 0 if no source code or FAISS index unbuilt. **Performance:** ~200ms.

### Layer 3 — Static Analysis

**Module:** `detector/layer3_static/` | **Weight:** 0.25

| Sub-analyzer | Technique | Key Patterns |
|-------------|-----------|-------------|
| **AST Analyzer** | Python AST visitor + regex fallback | `subprocess`(15), `socket`(15), `eval/exec`(20), `os.environ`(10), `base64`(15) |
| **Obfuscation Detector** | Regex pattern matching | Long base64 blobs(20), hex strings(15), eval chains(30), lambda-heavy(10) |
| **Semgrep Runner** | Custom rules + severity weights | ERROR=25, WARNING=15, INFO=5 |

**Composite score:** `ast × 0.40 + semgrep × 0.35 + obfuscation × 0.25`

**Failure mode:** Gracefully skips Semgrep if not installed. AST falls back to regex on SyntaxError. **Performance:** ~300ms (+ ~500ms with Semgrep).

### Layer 4 — LLM Audit

**Module:** `detector/layer4_llm/` | **Weight:** 0.18

On-demand AI code review. **Only triggered** when pre-LLM risk ≥ `LLM_TRIGGER_THRESHOLD` (default: 20).

1. Source code deobfuscated (base64/hex inlined as comments)
2. System prompt: cybersecurity expert role; structured JSON output
3. Returns `risk_score` (0–100), `risk_category`, `summary`, `evidence[]`
4. **Fail-closed**: parse error → score=100, category="suspicious"

| Provider | Latency | Cost/request |
|----------|---------|-------------|
| NVIDIA NIM (Llama 3.1 8B) | 2–5s | ~$0.001 |
| OpenAI (GPT-4o-mini) | 3–8s | ~$0.005 |
| Ollama (local) | 5–30s | $0 |
| Stub (dev) | <1ms | $0 |

> **Full guide**: See [docs/llm_configuration.md](docs/llm_configuration.md)

### Layer 5 — Dependency Graph

**Module:** `detector/layer5_graph/` | **Weight:** 0.15

Builds transitive dependency tree using NetworkX with bounded BFS (max depth=3, cycle detection).

- **Risk propagation:** `contribution = base_score × 0.6^(distance−1)`
- **Blast radius:** BFS on reversed graph → severity bands: critical(≥25), high(≥10), medium(≥4), low(≥1)

**Failure mode:** Returns score 0 if registry unreachable. **Performance:** 1–3s.

---

## Risk Scoring & Aggregation

### Formula

```
weighted_score = Σ (clamp(layer_score, 0, 100) × weight)
consensus = count(layers with score ≥ 60)
consensus_boost = 5 × max(0, consensus − 1)
final_score = clamp(weighted_score + consensus_boost, 0, 100)
```

### Default Weights & Rationale

| Layer | Weight | Rationale |
|-------|--------|-----------|
| Metadata (L1) | 0.22 | Highest offline signal; catches most common attack (typosquatting) |
| Static (L3) | 0.25 | Direct evidence of dangerous code patterns |
| LLM (L4) | 0.18 | Strong signal but expensive and latency-heavy |
| Embeddings (L2) | 0.15 | Code similarity is moderate signal; requires source availability |
| Graph (L5) | 0.15 | Transitive risk important but often indirect |
| Classifier | 0.05 | Meta-learner; low weight to avoid circular amplification |

When LLM is not triggered, its weight is **proportionally redistributed** to remaining layers.

### Decision Thresholds

| Score | Decision | Action |
|-------|----------|--------|
| 0–49 | **allow** | Package likely safe |
| 50–79 | **review** | Manual inspection recommended |
| 80–100 | **block** | Do not install |

---

## Model Training

| Aspect | Detail |
|--------|--------|
| **Algorithm** | XGBoost (`XGBClassifier`) |
| **Dataset** | 429 records: 400 benign (top PyPI + npm), 29 malicious (Backstabber's Knife Collection) |
| **Features** | 7: `metadata_score`, `embedding_score`, `static_score`, `graph_score`, `name_length`, `dep_count`, `author_missing` |
| **Hyperparameters** | 180 estimators, max_depth=4, lr=0.08, auto `scale_pos_weight` (~13.8) |
| **Split** | 300 train / 64 validation / 65 test |
| **Fallback** | If model file missing: `metadata×0.4 + static×0.4 + graph×0.2` |

```powershell
poetry run python ml/train_classifier.py
```

> **Deep dive**: See [docs/model_training.md](docs/model_training.md) and [docs/dataset.md](docs/dataset.md)

---

## LLM Integration

Layer 4 uses a Large Language Model to audit source code for patterns that evade static analysis.

| Step | Detail |
|------|--------|
| **Trigger** | Only when `pre_llm_risk ≥ LLM_TRIGGER_THRESHOLD` (~15% of scans at threshold=20) |
| **Pre-processing** | Deobfuscation: base64/hex strings inlined as plaintext |
| **Prompt** | System: cybersecurity expert; User: deobfuscated source code |
| **Output** | `risk_score`, `risk_category`, `summary`, `evidence[]` |
| **Fallback** | Parse error → score=100 (fail-closed); API error → score=0 (log warning) |
| **Cost savings** | ~85% fewer LLM calls vs. scanning every package |

> **Configuration**: See [docs/llm_configuration.md](docs/llm_configuration.md)

---

## Performance Benchmarks

| Scenario | Typical Latency |
|----------|----------------|
| Metadata-only (no source) | ~0.5s |
| Full scan, LLM not triggered | 2–4s |
| Full scan, LLM triggered (NVIDIA) | 5–9s |
| Full scan, LLM triggered (Ollama 7B) | 10–35s |

| Resource | Idle | Under Load |
|----------|------|-----------|
| Worker memory | ~300 MB | ~1.5 GB |
| API memory | ~80 MB | ~120 MB |
| Disk (ML models) | ~200 MB | — |

---

## Results

### Baseline Metrics (XGBoost, all features)

| Metric | Value |
|--------|-------|
| **ROC-AUC** | **0.950** |
| Recall | 0.800 |
| Precision | 0.400 |
| F1 Score | 0.533 |
| False Positives | 6 / 60 benign |
| False Negatives | 1 / 5 malicious |

### Ablation Study

| Configuration | Precision | Recall | F1 | ROC-AUC | ΔF1 |
|---------------|-----------|--------|-----|---------|-----|
| All features (baseline) | 0.400 | 0.800 | 0.533 | 0.950 | — |
| − Metadata | 0.148 | 0.800 | 0.250 | 0.688 | **−0.283** |
| − Embeddings | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Static | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Graph | 0.400 | 0.800 | 0.533 | 0.950 | 0.000 |
| − Identity | 1.000 | 0.800 | 0.889 | 0.900 | +0.356 |

**Key findings:**
- **Metadata is the most critical offline layer** — removing it causes the largest F1 drop (−0.283) and AUC drop (−0.262)
- Embeddings, Static, and Graph show zero impact in offline eval (dataset lacks source code); they activate in live scanning
- Identity features act as noise — removing them improves F1 to 0.889, indicating overfitting to name length

### Embedding Cluster Quality

| Metric | Value |
|--------|-------|
| Silhouette Score | 0.609 |
| Inter-class L2 distance | 1.12 |
| Intra-class (benign) L2 | 0.39 |

---

## Setup & Deployment

### Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| Poetry | latest | Dependency management |
| Docker Desktop | latest | Production deployment |
| Git | latest | Version control |

### Local Development

```powershell
git clone https://github.com/your-username/supply-chain-detector.git
cd supply-chain-detector
poetry install
copy .env.example .env

poetry run ruff check .
poetry run pytest -q
```

### Pre-compute Notebook Cache

```powershell
poetry run python notebooks/precompute_cache.py
```

### Train Classifier

```powershell
poetry run python ml/train_classifier.py
```

### Docker Production

```powershell
copy .env.example .env
docker compose up --build
```

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI REST gateway |
| `worker` | — | Celery background analysis (4 GB mem limit) |
| `db` | 5432 | PostgreSQL 17 with persistent volume |
| `redis` | 6379 | Message broker + cache |
| `ui` | 8501 | Streamlit dashboard |
| `grafana` | 3000 | Monitoring (optional, `--profile observability`) |

### Run Without Docker

```powershell
poetry run uvicorn api.main:app --reload --port 8000
poetry run celery -A api.celery_app.celery_app worker --loglevel=info
poetry run streamlit run ui/streamlit_app.py
```

> **Full deployment guide**: See [docs/deployment.md](docs/deployment.md) | **Environment variables**: See [docs/environment_variables.md](docs/environment_variables.md)

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Submit `{name, registry}` → returns `job_id` |
| `GET` | `/results/{job_id}` | Poll analysis status (pending / completed) |
| `GET` | `/results/recent?limit=20` | Latest scan jobs for threat feed |
| `GET` | `/health` | Service health check |

> **Full API documentation with examples**: See [docs/api_reference.md](docs/api_reference.md)

---

## CI/CD & Testing

```powershell
poetry run pytest -q              # All tests
poetry run ruff check .           # Lint
poetry run ruff format --check .  # Format check
```

| Test Suite | File | Coverage |
|------------|------|----------|
| Aggregator | `test_aggregator.py` | Scoring, consensus, decisions |
| API endpoints | `test_api_endpoints.py` | Health, analyze, results |
| E2E pipeline | `test_e2e_pipeline.py` | Full orchestration flow |
| Metadata L1 | `test_metadata_analyzer.py` | Typosquat + author + version |
| Embeddings L2 | `test_layer2_embeddings.py` | Embedding + FAISS |
| Graph L5 | `test_layer5_graph.py` | Graph building + propagation |
| Fetchers | `test_pypi_fetcher.py`, `test_npm_fetcher.py` | Registry API |
| Data layer | `test_data_layer.py` | Database CRUD |

---

## GitHub Action Scanner

```yaml
- uses: ./github_action
  with:
    api-url: http://localhost:8000
    threshold: 70
    poll-timeout: 90
```

Discovers `requirements.txt` and `package.json`, submits each dependency, **fails the workflow** if any score ≥ threshold.

---

## Notebooks

| # | Notebook | Purpose | Runtime |
|---|----------|---------|---------|
| 01 | `01_eda_and_dataset.ipynb` | Dataset construction, class distribution, missing-field analysis | ~3s |
| 02 | `02_feature_engineering.ipynb` | Feature extraction pipeline, correlation matrix | ~4s |
| 03 | `03_embedding_clustering.ipynb` | t-SNE visualization, silhouette scoring | ~3s |
| 04 | `04_model_training.ipynb` | XGBoost training, confusion matrix, ROC curve | ~4s |
| 05 | `05_evaluation_ablation.ipynb` | Ablation study, false positive analysis, weight sensitivity | ~5s |

All notebooks load from `data/processed/notebook_cache/`. Run `python notebooks/precompute_cache.py` first.

---

## Limitations

| Limitation | Impact | Severity | Mitigation |
|-----------|--------|----------|-----------|
| Small dataset (~429 records) | Overfitting risk | High | Expand with diverse attack samples |
| No source in offline eval | Layers 2, 3, 5 produce zero scores | Medium | Live pipeline fetches real tarballs |
| Typosquat-heavy malicious set | Detection bias | Medium | Add dependency confusion, account takeover |
| LLM excluded from offline eval | Unmeasured LLM contribution | Low | Tested via live API scans |
| No concept drift monitoring | Model degradation | Medium | Periodic retraining pipeline |
| No binary analysis | Compiled extensions bypass static | Low | Planned binary inspection layer |

### Adversarial Bypass Scenarios

| Attack | Bypasses | Counter |
|--------|----------|---------|
| Original name (not typosquat) | L1 | L3 Static + L4 LLM catch code patterns |
| Minimal obfuscation | L3 Obfuscation | L4 LLM understands semantic intent |
| No suspicious imports | L3 AST | L2 Embedding (code unlike known-good) |

---

## Roadmap

**Near-term:** Expand dataset, threshold optimization, online incremental learning

**Medium-term:** Cross-registry transfer (PyPI ↔ npm), concept drift detection, webhook notifications

**Long-term:** Multi-language support (Rust/Go/Ruby), binary analysis layer, federated learning

---

## Responsible Disclosure

This tool is for **defensive use only**. Detection results are **risk signals**, not definitive verdicts.

- Uses publicly available datasets only ([Backstabber's Knife Collection](https://dasfreak.github.io/Backstabbers-Knife-Collection/))
- No zero-day vulnerabilities disclosed or exploited
- Report vulnerabilities in this tool: See [SECURITY.md](SECURITY.md)
- Report malicious packages: [PyPI Security](https://pypi.org/security/) | [npm Security](https://docs.npmjs.com/reporting-malware-in-an-npm-package)

---

## Documentation Index

| Document | Path | Description |
|----------|------|-------------|
| Architecture Deep Dive | [docs/architecture.md](docs/architecture.md) | Components, data flow, trust boundaries |
| Model Training Guide | [docs/model_training.md](docs/model_training.md) | Dataset, features, training, evaluation |
| Dataset Documentation | [docs/dataset.md](docs/dataset.md) | Sources, labeling, preprocessing, splits |
| API Reference | [docs/api_reference.md](docs/api_reference.md) | Endpoints, schemas, error codes |
| Worker Flow | [docs/worker_flow.md](docs/worker_flow.md) | Celery lifecycle, retry logic |
| LLM Configuration | [docs/llm_configuration.md](docs/llm_configuration.md) | Provider setup, prompts, costs |
| Deployment Guide | [docs/deployment.md](docs/deployment.md) | Docker, local, production hardening |
| Environment Variables | [docs/environment_variables.md](docs/environment_variables.md) | Every env var explained |
| Technical Design | [docs/technical_design.md](docs/technical_design.md) | Design decisions, trade-offs, scalability |
| Troubleshooting | [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and solutions |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| Security Policy | [SECURITY.md](SECURITY.md) | Vulnerability reporting |

---

## Project Layout

```text
supply-chain-detector/
├── fetcher/                # PyPI / npm metadata + tarball fetchers
│   ├── pypi_fetcher.py     #   PyPI JSON API client
│   ├── npm_fetcher.py      #   npm registry client
│   └── source_extractor.py #   Safe archive extraction
├── detector/               # 5-layer detection + aggregator
│   ├── layer1_metadata/    #   Typosquat, author, version
│   ├── layer2_embeddings/  #   Sentence-transformer + FAISS
│   ├── layer3_static/      #   AST, obfuscation, Semgrep
│   ├── layer4_llm/         #   On-demand LLM audit
│   ├── layer5_graph/       #   Dependency graph + risk propagation
│   ├── classifier.py       #   XGBoost binary classifier
│   ├── aggregator.py       #   Weighted risk aggregation
│   └── orchestrator.py     #   Scan orchestration
├── api/                    # FastAPI REST service
│   ├── main.py             #   App factory + middleware
│   ├── routes/             #   /analyze, /results, /health
│   ├── tasks.py            #   Celery task definitions
│   ├── analysis_service.py #   Pipeline orchestration
│   ├── config.py           #   Settings from environment
│   ├── cache.py            #   Redis metadata cache
│   └── middleware/         #   Rate limiter
├── workers/                # Celery worker process
├── storage/                # Database + FAISS store
│   ├── database.py         #   SQLAlchemy (Postgres / SQLite)
│   ├── models.py           #   ScanJob ORM model
│   ├── repository.py       #   CRUD operations
│   └── migrations/         #   Alembic migrations
├── ui/                     # Streamlit dashboard
├── ml/                     # Training scripts
├── github_action/          # CI/CD GitHub Action
├── notebooks/              # Research notebooks
├── tests/                  # pytest suite
├── data/                   # Datasets, models, cache
├── docs/                   # Documentation
├── docker-compose.yml
├── Dockerfile.api / .worker
├── pyproject.toml
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Language | Python 3.11 | Primary runtime |
| ML | XGBoost | Binary risk classifier |
| Embeddings | sentence-transformers, FAISS | Code similarity search |
| Static Analysis | Semgrep, Python AST | Pattern matching |
| API | FastAPI, Uvicorn | Async REST service |
| Task Queue | Celery, Redis 7 | Background processing |
| Database | PostgreSQL 17, SQLAlchemy, Alembic | Persistence + migrations |
| UI | Streamlit | Interactive dashboard |
| Graphs | NetworkX | Dependency analysis |
| Containers | Docker, Docker Compose | Deployment |
| LLM | OpenAI, NVIDIA NIM, Ollama | AI code audit |
| Linting | Ruff | Fast Python linter |
| Testing | pytest | Test framework |

---

## License

This project is for educational and research purposes.

---

*— AI-powered supply chain security research.*
