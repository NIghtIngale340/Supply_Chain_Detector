# Contributing to Supply Chain Detector

Thank you for your interest in contributing! This document covers the development workflow, coding standards, and how to submit changes.

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Poetry | 1.7+ | Dependency management |
| Redis | 7+ | Message broker (for integration tests) |
| Docker | 24+ | Container builds (optional) |
| Git | 2.40+ | Version control |

### Setup

```powershell
# Clone the repository
git clone https://github.com/your-org/supply-chain-detector.git
cd supply-chain-detector

# Install dependencies
poetry install

# Verify setup
poetry run pytest tests/test_smoke.py -v
```

---

## Project Structure

```
supply-chain-detector/
├── api/              # FastAPI REST API + Celery configuration
│   ├── middleware/    # Rate limiter
│   ├── models/       # Pydantic schemas for API
│   └── routes/       # Endpoint handlers (analyze, results, health)
├── detector/         # Core detection pipeline
│   ├── layer1_metadata/   # Typosquat, author, version analysis
│   ├── layer2_embeddings/ # Sentence-transformer similarity
│   ├── layer3_static/     # AST, Semgrep, obfuscation detection
│   ├── layer4_llm/        # LLM-based code audit
│   ├── layer5_graph/      # Dependency graph risk propagation
│   ├── aggregator.py      # Weighted score aggregation
│   ├── classifier.py      # XGBoost binary classifier
│   └── orchestrator.py    # Pipeline coordination
├── fetcher/          # Registry API clients (PyPI, npm)
├── storage/          # Database models, repository, FAISS store
├── workers/          # Celery worker entry point
├── ml/               # Model training scripts
├── data/             # Datasets, processed artifacts, Semgrep rules
├── tests/            # Test suite
├── ui/               # Streamlit web interface
├── github_action/    # CI/CD GitHub Action
├── notebooks/        # Jupyter analysis notebooks
└── docs/             # Documentation
```

---

## Development Workflow

### 1. Create a feature branch

```powershell
git checkout -b feature/your-feature-name
```

### 2. Make your changes

Follow the coding standards below.

### 3. Run tests

```powershell
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_aggregator.py -v

# Run with coverage
poetry run pytest tests/ --cov=detector --cov=api --cov-report=term-missing
```

### 4. Check for errors

```powershell
# Type checking (if mypy is configured)
poetry run mypy detector/ api/

# Lint (if ruff/flake8 is configured)
poetry run ruff check .
```

### 5. Submit a pull request

- Write a clear PR title and description
- Reference any related issues
- Ensure all tests pass
- Request review from a maintainer

---

## Coding Standards

### Style

- **Python version:** 3.11+ (use modern syntax: `X | Y` unions, `match` statements)
- **Formatting:** Follow PEP 8. Use `black` or `ruff format` if available
- **Imports:** Group as: stdlib → third-party → local. Use absolute imports
- **Type hints:** Required on all public function signatures
- **Docstrings:** Required on all public functions and classes (Google style)

### Example

```python
from __future__ import annotations

from typing import Any

from detector.aggregator import AggregationWeights


def calculate_risk(
    scores: dict[str, float],
    weights: AggregationWeights | None = None,
) -> dict[str, Any]:
    """Calculate aggregated risk score from layer scores.

    Args:
        scores: Dictionary mapping layer names to risk scores (0-100).
        weights: Custom aggregation weights. Defaults to standard weights.

    Returns:
        Dictionary with final_score, decision, and component breakdown.
    """
    ...
```

### Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `analyze_metadata_risk()` |
| Classes | `PascalCase` | `AggregationWeights` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FILES = 30` |
| Private | `_leading_underscore` | `_safe_extract()` |
| Files | `snake_case.py` | `llm_auditor.py` |
| Env vars | `UPPER_SNAKE_CASE` | `LLM_TRIGGER_THRESHOLD` |

---

## Adding a New Detection Layer

To add a new detection layer (e.g., Layer 6: behavioral analysis):

1. **Create the module:**
   ```
   detector/layer6_behavioral/
   ├── __init__.py
   └── behavioral_analyzer.py
   ```

2. **Implement the analyzer:**
   ```python
   def analyze_behavioral_risk(source_context: str) -> dict:
       """Analyze behavioral patterns in source code.
       
       Returns:
           dict with at minimum: {"risk_score": int, ...}
       """
       ...
   ```

3. **Integrate into the orchestrator** (`detector/orchestrator.py`):
   ```python
   from detector.layer6_behavioral.behavioral_analyzer import analyze_behavioral_risk
   
   # Call in orchestrate_analysis()
   behavioral_result = analyze_behavioral_risk(source_context)
   ```

4. **Add weight to aggregator** (`detector/aggregator.py`):
   ```python
   @dataclass(frozen=True)
   class AggregationWeights:
       ...
       behavioral: float = 0.10  # New weight (adjust others to sum to ~1.0)
   ```

5. **Add feature to classifier** (`detector/classifier.py`):
   ```python
   # Add "behavioral_score" to the feature vector
   ```

6. **Write tests:**
   ```
   tests/test_behavioral_analyzer.py
   ```

7. **Update documentation:**
   - `README.md` — Add layer description
   - `docs/architecture.md` — Update pipeline diagram
   - `docs/technical_design.md` — Document design decision

---

## Test Structure

| File | Tests |
|------|-------|
| `test_smoke.py` | Basic import and instantiation |
| `test_aggregator.py` | Aggregation logic, consensus boost, edge cases |
| `test_metadata_analyzer.py` | Layer 1 typosquat, author, version |
| `test_layer2_embeddings.py` | Layer 2 embedding similarity |
| `test_semgrep_rules.py` | Layer 3 Semgrep rule matching |
| `test_layer5_graph.py` | Layer 5 graph risk propagation |
| `test_orchestrator.py` | Full pipeline orchestration |
| `test_pypi_fetcher.py` | PyPI API client |
| `test_npm_fetcher.py` | npm API client |
| `test_source_extractor.py` | Archive extraction, path traversal |
| `test_typosquat.py` | Name similarity detection |
| `test_api_endpoints.py` | REST API endpoint behavior |
| `test_data_layer.py` | Database operations |
| `test_integration.py` | Multi-component integration |
| `test_e2e_pipeline.py` | End-to-end scan pipeline |

### Testing philosophy

- **Unit tests** cover individual functions in isolation
- **Integration tests** verify component interactions (e.g., API → Celery → DB)
- **End-to-end tests** run the full scan pipeline against real registries
- Mock external services (PyPI, npm, LLM) in unit tests

---

## Reporting Issues

When reporting a bug:

1. **Search existing issues** to avoid duplicates
2. Include:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages / stack traces
   - Environment (OS, Python version, Docker version)
3. Tag appropriately: `bug`, `enhancement`, `documentation`, `question`

---

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Welcome newcomers
- No harassment, discrimination, or personal attacks
