# Phase 1 — Data Pipeline Foundation

## Objective

Create a reproducible local data pipeline that ingests package metadata/source references from PyPI and npm and stores normalized outputs.

## In Scope

- `fetcher/pypi_fetcher.py`
- `fetcher/npm_fetcher.py`
- `fetcher/source_extractor.py`
- `data/datasets/download_backstabbers.py` (dataset bootstrap placeholder)
- Simple EDA notebook scaffold in `notebooks/01_eda_and_dataset.ipynb`

## Out of Scope

- FastAPI endpoints
- Celery/Redis orchestration
- PostgreSQL/Alembic
- FAISS/embeddings/ML training
- LLM-assisted audit

## Entry Criteria

- Python + Poetry + Git installed
- Project dependencies installed

## Exit Criteria

- Can fetch metadata for one PyPI and one npm package
- Can extract one source archive into `data/raw`
- Can produce one normalized JSON/CSV output in `data/processed`
- Baseline lint and tests pass

## Validation Commands

```powershell
poetry run ruff check .
poetry run pytest -q
```

## Active Next Step

Complete all Phase 1 step guides in order:

- `fetcher/pypi_fetcher.py`
- `phase-1-step-1-pypi-fetcher.md`
- `phase-1-step-2-npm-fetcher.md`
- `phase-1-step-3-source-extractor.md`
- `phase-1-step-4-backstabbers-bootstrap.md`
- `phase-1-step-5-benign-sample-builder.md`
- `phase-1-step-6-normalized-output.md`
- `phase-1-step-7-tests.md`
- `phase-1-step-8-eda-checkpoint.md`

## Recommended Sequence Inside Phase 1

1. PyPI fetcher
2. npm fetcher
3. source extractor
4. dataset bootstrap script
5. benign sample builder
6. normalized output pipeline
7. test suite for fetch/extract/normalize
8. first EDA notebook checkpoint
